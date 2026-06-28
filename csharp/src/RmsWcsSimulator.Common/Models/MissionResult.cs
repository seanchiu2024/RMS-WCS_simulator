using System.Text.Json.Serialization;

namespace RmsWcsSimulator.Common.Models
{
    public class MissionResult
    {
        [JsonPropertyName("protocol_version")]
        public string ProtocolVersion { get; set; } = "2.0";

        [JsonPropertyName("sequence")]
        public string Sequence { get; set; } = string.Empty;

        [JsonPropertyName("timestamp")]
        public string Timestamp { get; set; } = string.Empty;

        [JsonPropertyName("priority")]
        public string Priority { get; set; } = "128";

        [JsonPropertyName("space")]
        public string Space { get; set; } = string.Empty;

        [JsonPropertyName("action")]
        public string Action { get; set; } = string.Empty;

        [JsonPropertyName("result")]
        public string Result { get; set; } = "OK";

        [JsonPropertyName("reason")]
        public string Reason { get; set; } = "NA";
    }
}
