package com.googleresearch.bustle;

import com.google.gson.*;
import com.googleresearch.bustle.value.*;
import com.googleresearch.bustle.propertysignatures.PropertySummary;
import java.util.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import picocli.CommandLine;

/** Transport and exact candidate observation around the unmodified author search. */
public final class RunAdapter {
  static final Gson JSON=new GsonBuilder().disableHtmlEscaping().create();
  static final PrintStream OUTPUT=new PrintStream(new FileOutputStream(FileDescriptor.out),true,StandardCharsets.UTF_8);
  static class ObservedValues extends HashSet<Value> {
    Value last;
    @Override public boolean add(Value v) { last=v; return super.add(v); }
  }
  static class ObservedModel extends SavedModelWrapper {
    long calls=0,values=0;
    ObservedModel(String path) throws Exception { super(path); }
    @Override public float[][] doInference(List<PropertySummary> io,List<List<PropertySummary>> vs) {
      calls++;values+=vs.size();return super.doInference(io,vs);
    }
  }
  static JsonObject save(Value value) {
    JsonObject result=new JsonObject();
    if (value instanceof OperationValue) {
      OperationValue v=(OperationValue)value;result.addProperty("kind","operation");
      result.addProperty("name",v.getOperation().getName());
      JsonArray args=new JsonArray();for(Value child:v.getArguments())args.add(save(child));
      result.add("args",args);
    } else if (value instanceof InputValue) {
      if(!value.expression().equals("var_0"))throw new IllegalArgumentException("Unexpected input name");
      result.addProperty("kind","input");result.addProperty("name","var_0");
    } else if (value instanceof ConstantValue) {
      result.addProperty("kind","literal");
      Object c=value.getWrappedValue(0);
      result.addProperty("type",c instanceof String?"string":c instanceof Integer?"integer":"unsupported");
      if(!(c instanceof String || c instanceof Integer))throw new IllegalArgumentException("Unexpected literal type");
      result.add("value",JSON.toJsonTree(c));
    } else throw new IllegalArgumentException("Unexpected native node "+value.getClass());
    return result;
  }
  static Value load(JsonObject node,List<String> inputs) {
    switch(node.get("kind").getAsString()) {
      case "input":
        if(!node.get("name").getAsString().equals("var_0"))throw new IllegalArgumentException("input");
        return new InputValue(new ArrayList<Object>(inputs),"var_0");
      case "literal":
        Object c;
        switch(node.get("type").getAsString()) {
          case "string":c=node.get("value").getAsString();break;
          case "integer":c=node.get("value").getAsInt();break;
          default:throw new IllegalArgumentException("literal");
        }
        return new ConstantValue(c,inputs.size());
      case "operation":
        List<Value> children=new ArrayList<>();
        for(JsonElement e:node.getAsJsonArray("args"))children.add(load(e.getAsJsonObject(),inputs));
        Value result=Operation.lookupOperation(node.get("name").getAsString(),children.size()).apply(children);
        if(result==null)throw new IllegalArgumentException("Native operation undefined for input");
        return result;
      default:throw new IllegalArgumentException("node");
    }
  }
  static List<Object> values(Value v,int count) {
    List<Object> result=new ArrayList<>();for(int i=0;i<count;i++)result.add(v.getWrappedValue(i));return result;
  }
  public static void main(String[] args) throws Exception {
    System.setOut(System.err);
    boolean executeOnly=args.length>0 && args[0].equals("execute-only");
    ObservedModel model=executeOnly?null:new ObservedModel("/opt/bustle/models/1000_epochs__64_64__e2__1e-5");
    OUTPUT.println(JSON.toJson(Map.of("event","ready","model_loaded",model!=null)));
    BufferedReader reader=new BufferedReader(new InputStreamReader(System.in,StandardCharsets.UTF_8));
    String line;
    while((line=reader.readLine())!=null) {
      JsonObject req=JSON.fromJson(line,JsonObject.class);Map<String,Object> record=new LinkedHashMap<>();
      record.put("task_id",req.get("task_id").getAsString());
      long start=System.nanoTime();
      try {
        if(req.has("ast")) {
          List<String> inputs=new ArrayList<>();for(JsonElement e:req.getAsJsonArray("inputs"))inputs.add(e.getAsString());
          Value v=load(req.getAsJsonObject("ast"),inputs);
          record.put("status","executed");record.put("outputs",values(v,inputs.size()));record.put("ast",save(v));
        } else {
          if(model==null)throw new IllegalStateException("Synthesis disabled");
          List<Example> examples=new ArrayList<>();List<String> inputs=new ArrayList<>();List<Object> expected=new ArrayList<>();
          for(JsonElement e:req.getAsJsonArray("examples")) {
            JsonObject row=e.getAsJsonObject();String x=row.get("input").getAsString(),y=row.get("output").getAsString();
            examples.add(Example.create(List.of(x),y));inputs.add(x);expected.add(y);
          }
          if(examples.size()<1 || examples.size()>5)throw new IllegalArgumentException("One to five examples required");
          new CommandLine(new Synthesizer()).parseArgs("--time_limit="+(req.has("timeout_seconds")?req.get("timeout_seconds").getAsDouble():60),"--max_expressions="+(req.has("max_expressions")?req.get("max_expressions").getAsInt():30000000),"--max_weight=100","--model_reweighting=true","--heuristic_reweighting=true","--premise_selection=false","--log_predictions=false");
          Benchmark benchmark=Benchmark.createBenchmarkWithNoTags(req.get("task_id").getAsString(),"",examples,List.of(),"");
          ObservedValues seen=new ObservedValues();long calls=model.calls;
          SynthesisResult result=Synthesizer.synthesize(benchmark,model,null,seen);
          OUTPUT.println(JSON.toJson(Map.of("event","search_complete","task_id",req.get("task_id").getAsString())));OUTPUT.flush();
          record.put("native_result",result);record.put("model_calls",model.calls-calls);
          if(result.getSuccess()) {
            Value candidate=seen.last;
            if(!candidate.expression().equals(result.getSolution()) || !values(candidate,examples.size()).equals(expected))throw new IllegalStateException("Exact first candidate observation failed");
            JsonObject ast=save(candidate);Value restored=load(ast,inputs);
            if(!values(restored,examples.size()).equals(expected) || !save(restored).equals(ast))throw new IllegalStateException("AST round trip failed");
            record.put("status","program");record.put("ast",ast);record.put("native_outputs",values(candidate,examples.size()));record.put("restored_outputs",values(restored,examples.size()));
          } else record.put("status","no_program_within_budget");
        }
      } catch(Exception e) {
        record.put("status","adapter_error");record.put("error",e.toString());e.printStackTrace(System.err);
      }
      record.put("seconds",(System.nanoTime()-start)/1e9);OUTPUT.println(JSON.toJson(record));OUTPUT.flush();
    }
  }
}
