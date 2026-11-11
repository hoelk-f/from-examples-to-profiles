using System.Globalization;
using System.Text;
using System.Text.Json;
using Microsoft.ProgramSynthesis.Transformation.Formula;
using Microsoft.ProgramSynthesis.Transformation.Formula.Constraints;
using Microsoft.ProgramSynthesis.Wrangling;
using Microsoft.ProgramSynthesis.AST;

internal static class Audit {
 static object Attempt(Func<object?> action) {
  try { return new {ok=true,value=action()}; }
  catch(Exception e) { return new {ok=false,type=e.GetType().FullName,message=e.Message,stack=e.StackTrace}; }
 }
 public static void Main() {
  CultureInfo.CurrentCulture=CultureInfo.InvariantCulture;
  Console.InputEncoding=new UTF8Encoding(false); Console.OutputEncoding=new UTF8Encoding(false);
  using var doc=JsonDocument.Parse(Console.In.ReadToEnd());
  var root=doc.RootElement;
  var result=Attempt(()=> {
   if (root.TryGetProperty("inspect",out var inspect)) {
    return new []{typeof(Program),typeof(Language),typeof(Session),typeof(ProgramNode),typeof(ParseSettings),typeof(DeserializationContext),typeof(ProgramNodeParser),typeof(ASTSerializationSettings),typeof(ASTSerializationFormat),typeof(Microsoft.ProgramSynthesis.Grammar),typeof(LiteralNode)}.Concat(typeof(Session).Assembly.GetExportedTypes().Where(t=>t.Name.Contains("Loader") || t.Name.Contains("Parser"))).Select(t=>new {
      type=t.FullName,methods=t.GetMethods().Where(m=>m.IsPublic).Select(m=>m.ToString()).ToArray(),
      constructors=t.GetConstructors().Select(c=>c.ToString()).ToArray(),
      properties=t.GetProperties().Select(p=>p.ToString()).ToArray(),fields=t.GetFields().Select(p=>p.ToString()).ToArray()
    }).ToArray();
   }
   var examples=root.GetProperty("examples").EnumerateArray().Select(e=>(input:e.GetProperty("input").GetString()!,output:e.GetProperty("output").GetString()!)).ToArray();
   if (root.TryGetProperty("serialization",out var saved)) {
    var fresh=new Session();
    if(root.TryGetProperty("loaderProbe",out var loaderProbe)) {
     var p=fresh.Load(saved.GetString()!);
     return new {status="loader",checks=examples.Select(e=>Attempt(()=>p.Run(new InputRow(e.input)))).ToArray()};
    }
    var restoredNode=ProgramNode.ParseXML(Language.Grammar,
      System.Xml.Linq.XElement.Parse(saved.GetString()!),new ParseSettings(fresh.DeserializationContext));
    if(restoredNode is null) return new {status="parse_returned_null"};
    var restoredProgram=new Program(restoredNode,root.GetProperty("score").GetDouble());
    return new {status="reloaded",checks=examples.Select(e=>Attempt(()=>restoredProgram.Run(new InputRow(e.input)))).ToArray(),
      serialization=restoredProgram.Serialize(),code=restoredProgram.ToString()};
   }
   var session=new Session();
   foreach(var e in examples) session.Constraints.Add(new Example(new InputRow(e.input),e.output));
   session.Constraints.Add(new LearnConstraint {EnableMatchUnicode=false});
   var program=session.Learn();
   if(program is null) return new {status="no_program"};
   var serialization=program.Serialize();
   var native=examples.Select(e=>Attempt(()=>program.Run(new InputRow(e.input)))).ToArray();
   var restored=Attempt(()=> {
     var node=ProgramNode.Parse(serialization,Language.Grammar);
     var p=new Program(node,program.Score);
     return new {nodeIsNull=node is null, checks=examples.Select(e=>Attempt(()=>p.Run(new InputRow(e.input)))).ToArray()};
   });
   var ownGrammar=Attempt(()=> {
     var node=ProgramNode.Parse(serialization,program.ProgramNode.Grammar);
     var p=new Program(node,program.Score);
     return new {nodeIsNull=node is null, checks=examples.Select(e=>Attempt(()=>p.Run(new InputRow(e.input)))).ToArray()};
   });
   return new {serialization,score=program.Score,native,restored,ownGrammar,
     grammarEquals=Object.ReferenceEquals(Language.Grammar,program.ProgramNode.Grammar),
     grammar=program.ProgramNode.Grammar.ToString(),code=program.ToString(),nodeType=program.ProgramNode.GetType().FullName};
  });
  Console.WriteLine(JsonSerializer.Serialize(result));
 }
}
