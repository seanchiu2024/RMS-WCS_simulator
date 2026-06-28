using System.Text.Json.Serialization;

namespace RmsWcsSimulator.Common.Models
{
    public class OnlineStatus
    {
        [JsonPropertyName("protocol_version")]
        public string ProtocolVersion { get; set; } = "2.0";

        [JsonPropertyName("sequence")]
        public string Sequence { get; set; } = string.Empty;

        [JsonPropertyName("timestamp")]
        public string Timestamp { get; set; } = string.Empty;

        [JsonPropertyName("priority")]
        public string Priority { get; set; } = "128";

        [JsonPropertyName("device")]
        public string Device { get; set; } = "RMS01";

        [JsonPropertyName("status")]
        public string Status { get; set; } = "remote";
    }
}
