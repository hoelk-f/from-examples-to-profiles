using System.Globalization;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;
using Microsoft.ProgramSynthesis.AST;
using Microsoft.ProgramSynthesis.Transformation.Formula;
using Microsoft.ProgramSynthesis.Transformation.Formula.Constraints;
using Microsoft.ProgramSynthesis.Wrangling;

internal static class Qualification {
 static void Emit(object value)=>Console.WriteLine(JsonSerializer.Serialize(value));
 public static void Main() {
  var init=System.Diagnostics.Stopwatch.StartNew();
  CultureInfo.CurrentCulture=CultureInfo.InvariantCulture;
  CultureInfo.CurrentUICulture=CultureInfo.InvariantCulture;
  Console.InputEncoding=new UTF8Encoding(false);Console.OutputEncoding=new UTF8Encoding(false);
  _=Language.Grammar;
  Emit(new {event_type="ready",initialization_seconds=init.Elapsed.TotalSeconds});
  foreach(var line in Lines()) {
   var req=JsonNode.Parse(line)!.AsObject();
   try {
    var taskId=req["task_id"]!.GetValue<string>();
    if(req["operation"]?.GetValue<string>()=="execute") {
     var program=AstCodec.Load(req["program"]!.AsObject());
     var outputs=req["inputs"]!.AsArray().Select(x=>program.Run(new InputRow(x!.GetValue<string>()))).ToArray();
     Emit(new {task_id=taskId,status="executed",outputs,roundtrip_equal=JsonNode.DeepEquals(AstCodec.Save(program),req["program"])});continue;
    }
    var examples=req["examples"]!.AsArray().Select(e=>(x:e!["input"]!.GetValue<string>(),y:e!["output"]!.GetValue<string>())).ToArray();
    if(examples.Length<1 || examples.Length>5)throw new ArgumentException("One to five synthesis pairs");
    Program? native;
    bool synthesis;
    if(req["legacy"] is JsonObject legacy) {
     var node=ProgramNode.Parse(legacy["serialization"]!.GetValue<string>(),Language.Grammar);
     if(node is null)throw new ArgumentException("Legacy AST cannot be loaded");
     native=new Program(node,legacy["score"]!.GetValue<double>());synthesis=false;
    } else {
     var session=new Session();foreach(var e in examples)session.Constraints.Add(new Example(new InputRow(e.x),e.y));
     session.Constraints.Add(new LearnConstraint {EnableMatchUnicode=false});native=session.Learn();synthesis=true;
    }
    Emit(new {event_type="search_complete",task_id=taskId});
    if(native is null) {Emit(new {task_id=taskId,status="no_program"});continue;}
    var saved=AstCodec.Save(native);var restored=AstCodec.Load(saved);
    var nativeOutputs=examples.Select(e=>native.Run(new InputRow(e.x))).ToArray();
    var restoredOutputs=examples.Select(e=>restored.Run(new InputRow(e.x))).ToArray();
    bool structural=native.ProgramNode.Equals(restored.ProgramNode);
    bool fits=nativeOutputs.SequenceEqual(examples.Select(e=>(object)e.y))&&restoredOutputs.SequenceEqual(nativeOutputs);
    Emit(new {task_id=taskId,status=structural&&fits?"program":"mismatch",synthesis_repeated=synthesis,structural_equal=structural,native_outputs=nativeOutputs,restored_outputs=restoredOutputs,program=saved});
   } catch(Exception e) {Emit(new {task_id=req["task_id"]?.GetValue<string>(),status="adapter_error",type=e.GetType().FullName,message=e.Message,stack=e.StackTrace});}
  }
 }
 static IEnumerable<string> Lines(){string? line;while((line=Console.ReadLine())!=null)yield return line;}
}
