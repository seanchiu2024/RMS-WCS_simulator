using System;
using System.IO;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace RmsWcsSimulator.Common.Config
{
    public class SimulationConfig
    {
        [JsonPropertyName("rms")]
        public RmsConfig Rms { get; set; } = new();

        [JsonPropertyName("wcs")]
        public WcsConfig Wcs { get; set; } = new();

        [JsonPropertyName("simulation")]
        public SimulationSettings Simulation { get; set; } = new();

        public static SimulationConfig Load(string filename = "config.json")
        {
            string foundPath = filename;
            if (!File.Exists(foundPath))
            {
                // 往上尋找根目錄的 config.json
                var currentDir = AppDomain.CurrentDomain.BaseDirectory;
                while (currentDir != null)
                {
                    var checkPath = Path.Combine(currentDir, filename);
                    if (File.Exists(checkPath))
                    {
                        foundPath = checkPath;
                        break;
                    }
                    currentDir = Directory.GetParent(currentDir)?.FullName;
                }
            }

            if (File.Exists(foundPath))
            {
                try
                {
                    var json = File.ReadAllText(foundPath);
                    var options = new JsonSerializerOptions { PropertyNameCaseInsensitive = true };
                    var loaded = JsonSerializer.Deserialize<SimulationConfig>(json, options);
                    if (loaded != null)
                    {
                        Console.WriteLine($"[Config] 成功載入設定檔: {Path.GetFullPath(foundPath)}");
                        return loaded;
                    }
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"[Config] 讀取設定檔 {filename} 發生錯誤: {ex.Message}，使用預設值。");
                }
            }
            else
            {
                Console.WriteLine($"[Config] 找不到設定檔 {filename}，使用預設值。");
            }

            return GetDefault();
        }

        public static SimulationConfig GetDefault()
        {
            return new SimulationConfig
            {
                Rms = new RmsConfig { Host = "localhost", Port = 31111, LogFile = "rms_simulator.log" },
                Wcs = new WcsConfig { Host = "localhost", Port = 31112, LogFile = "wcs_simulator.log" },
                Simulation = new SimulationSettings
                {
                    StepDelaySeconds = 10.0,
                    AckDelaySeconds = 10.0,
                    DefaultPalletId = "01",
                    RequestTimeoutSeconds = 5.0,
                    AckTimeoutSeconds = 60.0
                }
            };
        }
    }

    public class RmsConfig
    {
        [JsonPropertyName("host")]
        public string Host { get; set; } = "localhost";

        [JsonPropertyName("port")]
        public int Port { get; set; } = 31111;

        [JsonPropertyName("log_file")]
        public string LogFile { get; set; } = "rms_simulator.log";
    }

    public class WcsConfig
    {
        [JsonPropertyName("host")]
        public string Host { get; set; } = "localhost";

        [JsonPropertyName("port")]
        public int Port { get; set; } = 31112;

        [JsonPropertyName("log_file")]
        public string LogFile { get; set; } = "wcs_simulator.log";
    }

    public class SimulationSettings
    {
        [JsonPropertyName("step_delay_seconds")]
        public double StepDelaySeconds { get; set; } = 10.0;

        [JsonPropertyName("ack_delay_seconds")]
        public double AckDelaySeconds { get; set; } = 10.0;

        [JsonPropertyName("default_pallet_id")]
        public string DefaultPalletId { get; set; } = "01";

        [JsonPropertyName("request_timeout_seconds")]
        public double RequestTimeoutSeconds { get; set; } = 5.0;

        [JsonPropertyName("ack_timeout_seconds")]
        public double AckTimeoutSeconds { get; set; } = 60.0;
    }
}
