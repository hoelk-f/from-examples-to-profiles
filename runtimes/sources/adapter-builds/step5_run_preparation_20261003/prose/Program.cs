using System.Globalization;
using System.Text;
using System.Text.Json;
using Microsoft.ProgramSynthesis.Transformation.Formula;
using Microsoft.ProgramSynthesis.Transformation.Formula.Constraints;
using Microsoft.ProgramSynthesis.Wrangling;

// Thin transport adapter around the pinned SDK. No reference rules or test data.
internal static class Step5Prose
{
    static void Emit(object value) => Console.WriteLine(JsonSerializer.Serialize(value));

    public static int Main(string[] args)
    {
        CultureInfo.CurrentCulture = CultureInfo.InvariantCulture;
        CultureInfo.CurrentUICulture = CultureInfo.InvariantCulture;
        Console.InputEncoding = new UTF8Encoding(false);
        Console.OutputEncoding = new UTF8Encoding(false);
        try
        {
            using var doc = JsonDocument.Parse(Console.In.ReadToEnd());
            var root = doc.RootElement;
            var operation = root.GetProperty("operation").GetString();
            if (operation == "inspect_public_api")
            {
                var types = typeof(Session).Assembly.GetExportedTypes();
                Emit(types.Select(type => new { type = type.FullName, fields = type.GetFields().Where(m => m.FieldType == typeof(Microsoft.ProgramSynthesis.Grammar)).Select(m => m.ToString()).ToArray(), properties = type.GetProperties().Where(m => m.PropertyType == typeof(Microsoft.ProgramSynthesis.Grammar)).Select(m => m.ToString()).ToArray() }).Where(t => t.fields.Length + t.properties.Length > 0).ToArray());
                return 0;
            }
            if (operation == "synthesize")
            {
                var session = new Session();
                foreach (var item in root.GetProperty("examples").EnumerateArray())
                    session.Constraints.Add(new Example(new InputRow(item.GetProperty("input").GetString()), item.GetProperty("output").GetString()));
                session.Constraints.Add(new LearnConstraint { EnableMatchUnicode = false });
                var program = session.Learn();
                if (program is null)
                {
                    Emit(new { status = "no_program" });
                    return 0;
                }
                var serialization = program.Serialize();
                if (root.TryGetProperty("serialization_probe", out var probe) && probe.GetBoolean())
                {
                    Emit(new { status = "serialization_probe", serialization, score = program.Score, node_type = program.ProgramNode.GetType().FullName, grammar_type = program.ProgramNode.Grammar.GetType().FullName, grammar = program.ProgramNode.Grammar.ToString() });
                    return 0;
                }
                var restored = new Microsoft.ProgramSynthesis.Transformation.Formula.Program(
                    Microsoft.ProgramSynthesis.AST.ProgramNode.Parse(serialization, Language.Grammar), program.Score);
                var checks = root.GetProperty("examples").EnumerateArray().Select(item => new {
                    expected = item.GetProperty("output").GetString(),
                    native = program.Run(new InputRow(item.GetProperty("input").GetString())),
                    restored = restored.Run(new InputRow(item.GetProperty("input").GetString()))
                }).ToArray();
                Emit(new { status = "program", serialization, score = program.Score, checks });
                return 0;
            }
            if (operation == "execute")
            {
                var program = new Microsoft.ProgramSynthesis.Transformation.Formula.Program(
                    Microsoft.ProgramSynthesis.AST.ProgramNode.Parse(root.GetProperty("serialization").GetString(), Language.Grammar), root.GetProperty("score").GetDouble());
                var output = program.Run(new InputRow(root.GetProperty("input").GetString()));
                Emit(new { status = "returned", output });
                return 0;
            }
            throw new ArgumentException("Unknown operation");
        }
        catch (Exception error)
        {
            Emit(new { status = "adapter_error", type = error.GetType().FullName, message = error.Message, stack = error.StackTrace });
            return 1;
        }
    }
}
