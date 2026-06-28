using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace RmsWcsSimulator.Common.Models
{
    public class MissionRequest
    {
        [JsonPropertyName("protocol_version")]
        public string ProtocolVersion { get; set; } = "2.0";

        [JsonPropertyName("sequence")]
        public string Sequence { get; set; } = string.Empty;

        [JsonPropertyName("timestamp")]
        public string Timestamp { get; set; } = string.Empty;

        [JsonPropertyName("priority")]
        public string Priority { get; set; } = "128";

        [JsonPropertyName("sub_missions")]
        public List<SubMission> SubMissions { get; set; } = new();

        // 用於 HTTP 回覆 (Reply)
        [JsonPropertyName("reply")]
        public string? Reply { get; set; }

        [JsonPropertyName("reason")]
        public string? Reason { get; set; }
    }

    public class SubMission
    {
        [JsonPropertyName("space")]
        public string Space { get; set; } = string.Empty;

        [JsonPropertyName("action")]
        public string Action { get; set; } = string.Empty;
    }
}
