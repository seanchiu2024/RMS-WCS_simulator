using System.Text.Json.Serialization;

namespace RmsWcsSimulator.Common.Models
{
    public class MissionAck
    {
        [JsonPropertyName("protocol_version")]
        public string ProtocolVersion { get; set; } = "2.0";

        [JsonPropertyName("sequence")]
        public string Sequence { get; set; } = string.Empty;

        [JsonPropertyName("timestamp")]
        public string Timestamp { get; set; } = string.Empty;

        [JsonPropertyName("priority")]
        public string Priority { get; set; } = "128";

        [JsonPropertyName("action")]
        public string Action { get; set; } = string.Empty;

        [JsonPropertyName("ack")]
        public string Ack { get; set; } = "OK";
    }
}
