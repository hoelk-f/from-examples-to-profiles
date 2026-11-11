using System.Reflection;
using System.Text.Json.Nodes;
using System.Xml.Linq;
using Microsoft.ProgramSynthesis.AST;
using Microsoft.ProgramSynthesis.Rules;
using Microsoft.ProgramSynthesis.Transformation.Formula;
using Microsoft.ProgramSynthesis.Transformation.Formula.Semantics.Learning.Models;

// Pinned codec for Formula 8.25.0. Execution still uses the original native AST.
internal static class AstCodec {
 const string Format="prose-formula-8.25.0-typed-literals-v1";
 static IEnumerable<LiteralNode> Literals(ProgramNode node) {
  if(node is LiteralNode literal) yield return literal;
  foreach(var child in node.Children) foreach(var descendant in Literals(child)) yield return descendant;
 }
 public static JsonObject Save(Program program) {
  var xml=program.Serialize();
  var nodes=XElement.Parse(xml).DescendantsAndSelf("LiteralNode").ToArray();
  var literals=Literals(program.ProgramNode).ToArray();
  if(nodes.Length!=literals.Length)throw new InvalidOperationException("Literal traversal mismatch");
  var metadata=new JsonObject();
  for(int i=0;i<literals.Length;i++) {
   var literal=literals[i];
   if((string?)nodes[i].Attribute("symbol")!=literal.Symbol.Name)throw new InvalidOperationException("Literal symbol mismatch");
   if(literal.Value is MatchDescriptor m) metadata[i.ToString()]=new JsonObject { ["type"]="MatchDescriptor",["pattern"]=m.Pattern,["name"]=m.Name.ToString() };
   else if(literal.Value is DateTimeDescriptor d) metadata[i.ToString()]=new JsonObject { ["type"]="DateTimeDescriptor",["formatMask"]=d.FormatMask,["locale"]=d.Locale,["isPartial"]=d.IsPartial };
  }
  return new JsonObject { ["format"]=Format,["serialization"]=xml,["score"]=program.Score,["literals"]=metadata };
 }
 public static Program Load(JsonObject stored) {
  if(stored["format"]?.GetValue<string>()!=Format)throw new ArgumentException("Unrecognized codec");
  int index=0;var metadata=stored["literals"]!.AsObject();
  ProgramNode Visit(XElement element) {
   string symbolName=(string?)element.Attribute("symbol")??throw new ArgumentException("Missing symbol");
   var symbol=Language.Grammar.Symbols[symbolName];
   switch(element.Name.LocalName) {
    case "VariableNode":return new VariableNode(symbol);
    case "LiteralNode":
     var key=(index++).ToString();object value;
     if(metadata.TryGetPropertyValue(key,out var special)) {
      var m=special!.AsObject();
      switch(m["type"]!.GetValue<string>()) {
       case "MatchDescriptor":
        if(symbol.ResolvedType!=typeof(MatchDescriptor))throw new ArgumentException("Wrong match type");
        var constructor=typeof(MatchDescriptor).GetConstructor(BindingFlags.NonPublic|BindingFlags.Instance,null,new[]{typeof(string),typeof(MatchName)},null)
          ??throw new NotSupportedException("Pinned MatchDescriptor constructor changed");
        value=constructor.Invoke(new object[]{m["pattern"]!.GetValue<string>(),Enum.Parse<MatchName>(m["name"]!.GetValue<string>())});break;
       case "DateTimeDescriptor":
        if(symbol.ResolvedType!=typeof(DateTimeDescriptor))throw new ArgumentException("Wrong date type");
        value=new DateTimeDescriptor { FormatMask=m["formatMask"]!.GetValue<string>(),Locale=m["locale"]!.GetValue<string>(),IsPartial=m["isPartial"]!.GetValue<bool>() };break;
       default:throw new NotSupportedException("Unsupported special literal");
      }
     } else {
      var parsed=StdLiteralParsing.TryParse(element,symbol.ResolvedType);
      if(!parsed.HasValue)throw new NotSupportedException("Native literal parser rejected "+symbolName);
      value=parsed.Value;
     }
     return new LiteralNode(symbol,value);
    case "LetNode":
     var let=Language.Grammar.Rule((string?)element.Attribute("id")??throw new ArgumentException("Missing let rule")) as LetRule
       ??throw new ArgumentException("Unknown let rule");
     var binding=element.Elements("Variable").Single();
     if((string?)binding.Attribute("symbol")!=let.Variable.Name)throw new ArgumentException("Let binding mismatch");
     return new LetNode(let,Visit(binding.Elements().Single()),Visit(element.Elements().Single(e=>e.Name!="Variable")));
    case "NonterminalNode":
     var rule=Language.Grammar.Rule((string?)element.Attribute("rule")??throw new ArgumentException("Missing rule")) as NonterminalRule
       ??throw new ArgumentException("Unknown rule");
     if(rule.Head.Name!=symbolName)throw new ArgumentException("Rule head mismatch");
     return new NonterminalNode(rule,element.Elements().Select(Visit).ToArray());
    default:throw new NotSupportedException("Unsupported AST node "+element.Name);
   }
  }
  var result=new Program(Visit(XElement.Parse(stored["serialization"]!.GetValue<string>())),stored["score"]!.GetValue<double>());
  if(!JsonNode.DeepEquals(Save(result),stored))throw new InvalidOperationException("Codec did not preserve all stored fields");
  return result;
 }
}
