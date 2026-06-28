using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Net.Http.Json;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Channels;
using System.Threading.Tasks;
using Microsoft.Extensions.Hosting;
using RmsWcsSimulator.Common.Config;
using RmsWcsSimulator.Common.Models;

namespace RmsWcsSimulator.Wcs.Services
{
    public class PendingAck
    {
        public MissionResult Result { get; set; } = new();
        public string Status { get; set; } = "pending"; // "pending" 或 "refused"
        public DateTime? FirstRefusalTime { get; set; }
        public DateTime LastPromptTime { get; set; }
    }

    public class WcsCliService : BackgroundService
    {
        private readonly SimulationConfig _config;
        private readonly HttpClient _httpClient;
        private readonly IHostApplicationLifetime _lifetime;
        private readonly Channel<MissionResult> _resultsChannel = Channel.CreateUnbounded<MissionResult>();
        private readonly Channel<string> _inputChannel = Channel.CreateUnbounded<string>();

        public WcsCliService(SimulationConfig config, HttpClient httpClient, IHostApplicationLifetime lifetime)
        {
            _config = config;
            _httpClient = httpClient;
            _lifetime = lifetime;
        }

        public void QueueResult(MissionResult result)
        {
            _resultsChannel.Writer.TryWrite(result);
        }

        private string GetTimestamp()
        {
            var now = DateTime.Now;
            return now.ToString("yyyy-MM-dd HH:mm:ss.") + $"{now.Millisecond:D3}";
        }

        private void Log(string message)
        {
            string formatted = $"{GetTimestamp()} [INFO] {message}";
            try
            {
                File.AppendAllText(_config.Wcs.LogFile, formatted + Environment.NewLine, Encoding.UTF8);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[Log Error] 無法寫入日誌檔: {ex.Message}");
            }
        }

        private void LogError(string message)
        {
            string formatted = $"{GetTimestamp()} [ERROR] {message}";
            try
            {
                File.AppendAllText(_config.Wcs.LogFile, formatted + Environment.NewLine, Encoding.UTF8);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[Log Error] 無法寫入日誌檔: {ex.Message}");
            }
        }

        protected override async Task ExecuteAsync(CancellationToken stoppingToken)
        {
            // 啟動鍵盤輸入讀取
            StartInputReader(stoppingToken);

            // 稍微等待一下確保 Host 啟動 Log 先印出
            await Task.Delay(500, stoppingToken);

            PrintMenu();

            var pendingAcks = new List<PendingAck>();
            bool promptNeeded = true;
            string? lastMode = null;

            while (!stoppingToken.IsCancellationRequested)
            {
                // 1. 讀取所有新進的 Results
                bool newResultsReceived = false;
                while (_resultsChannel.Reader.TryRead(out var res))
                {
                    pendingAcks.Add(new PendingAck
                    {
                        Result = res,
                        LastPromptTime = DateTime.MinValue
                    });
                    Console.WriteLine($"\n[結果通知] 收到任務結果: 序號={res.Sequence}, 動作={res.Action}, 位置={res.Space}, 結果={res.Result}, 原因={res.Reason}");
                    newResultsReceived = true;
                }

                if (newResultsReceived)
                {
                    promptNeeded = true;
                }

                var now = DateTime.Now;

                // 2. 處理當前處於 ACK 確認模式
                if (pendingAcks.Count > 0)
                {
                    var current = pendingAcks[0];

                    // 檢查是否已拒絕且超過 30 秒，若是則自動回覆 ACK
                    if (current.Status == "refused" && current.FirstRefusalTime.HasValue)
                    {
                        if ((now - current.FirstRefusalTime.Value).TotalSeconds >= 30.0)
                        {
                            Console.WriteLine($"\n[自動確認] 任務 {current.Result.Sequence} 動作 {current.Result.Action} 拒絕後已超過 30 秒未確認，系統自動發送 ACK。");
                            await SendAckToRmsAsync(current.Result);
                            pendingAcks.RemoveAt(0);
                            promptNeeded = true;
                            continue;
                        }
                    }

                    // 判斷是否需要提示 (若未拒絕，或已拒絕且距離上次提示已過 5 秒)
                    bool shouldPrompt = false;
                    if (current.Status != "refused")
                    {
                        if (promptNeeded || lastMode != "ack")
                        {
                            shouldPrompt = true;
                        }
                    }
                    else
                    {
                        if ((now - current.LastPromptTime).TotalSeconds >= 5.0)
                        {
                            shouldPrompt = true;
                        }
                    }

                    if (shouldPrompt)
                    {
                        Console.Write($"\n是否針對任務 {current.Result.Sequence} 動作 {current.Result.Action} (位置: {current.Result.Space}) 回覆 ACK? (y/n): ");
                        current.LastPromptTime = now;
                        promptNeeded = false;
                        lastMode = "ack";
                    }

                    // 讀取鍵盤輸入 (非阻塞，若無輸入則 Delay 100ms 後重試)
                    if (_inputChannel.Reader.TryRead(out var userInput))
                    {
                        promptNeeded = true;
                        var lowerInput = userInput.ToLower();

                        if (lowerInput == "y" || lowerInput == "yes")
                        {
                            await SendAckToRmsAsync(current.Result);
                            pendingAcks.RemoveAt(0);
                        }
                        else if (lowerInput == "n" || lowerInput == "no")
                        {
                            var msg = $"拒絕回覆任務 {current.Result.Sequence} 動作 {current.Result.Action} 的 ACK。將於 5 秒後重新詢問。";
                            Log(msg);
                            Console.WriteLine($"\n[INFO] {msg}");
                            if (current.Status != "refused")
                            {
                                current.Status = "refused";
                                current.FirstRefusalTime = now;
                            }
                            current.LastPromptTime = now;
                        }
                        else
                        {
                            Console.WriteLine("請輸入 'y' 或 'n' 以確認是否回覆 ACK！");
                        }
                    }
                }
                else
                {
                    // 3. 處理指令模式
                    if (promptNeeded || lastMode != "cmd")
                    {
                        Console.Write("WCS> ");
                        promptNeeded = false;
                        lastMode = "cmd";
                    }

                    if (_inputChannel.Reader.TryRead(out var userInput))
                    {
                        promptNeeded = true;
                        if (!string.IsNullOrEmpty(userInput))
                        {
                            if (userInput.Equals("exit", StringComparison.OrdinalIgnoreCase))
                            {
                                Log("結束 WCS 模擬器。");
                                Console.WriteLine("結束 WCS 模擬器。");
                                _lifetime.StopApplication();
                                break;
                            }
                            else if (userInput.Equals("send", StringComparison.OrdinalIgnoreCase))
                            {
                                await TriggerTestMissionAsync(null, "mission.json");
                            }
                            else if (userInput.StartsWith("send ", StringComparison.OrdinalIgnoreCase))
                            {
                                var parts = userInput.Split(' ', StringSplitOptions.RemoveEmptyEntries);
                                string? customSeq = null;
                                string customFile = "mission.json";

                                if (parts.Length == 2)
                                {
                                    var arg = parts[1];
                                    if (arg.EndsWith(".json", StringComparison.OrdinalIgnoreCase))
                                    {
                                        customFile = arg;
                                    }
                                    else
                                    {
                                        customSeq = arg;
                                    }
                                }
                                else if (parts.Length >= 3)
                                {
                                    customSeq = parts[1];
                                    customFile = parts[2];
                                }

                                await TriggerTestMissionAsync(customSeq, customFile);
                            }
                            else
                            {
                                Console.WriteLine("無法辨識的指令，請輸入 'send'、'send <參數>' 或 'exit'");
                            }
                        }
                    }
                }

                await Task.Delay(100, stoppingToken);
            }
        }

        private void StartInputReader(CancellationToken ct)
        {
            Task.Run(() =>
            {
                while (!ct.IsCancellationRequested)
                {
                    try
                    {
                        var line = Console.ReadLine();
                        if (line != null)
                        {
                            _inputChannel.Writer.TryWrite(line.Trim());
                        }
                    }
                    catch
                    {
                        break;
                    }
                }
            }, ct);
        }

        private void PrintMenu()
        {
            Console.WriteLine("\n" + new string('=', 60));
            Console.WriteLine(" 互動指令選單:");
            Console.WriteLine(" - 輸入 'send'  : 發送預設的 A-01-2 -> L-01-0 搬運任務 (seq: 自動產生，檔案: mission.json)");
            Console.WriteLine(" - 輸入 'send <序號>' : 發送指定序號任務 (例如: send M20260619)");
            Console.WriteLine(" - 輸入 'send <JSON檔名>' : 發送指定任務檔並自動產生序號 (例如: send RMS_02_mission.json)");
            Console.WriteLine(" - 輸入 'send <序號> <JSON檔名>' : 發送指定序號與任務檔");
            Console.WriteLine(" - 輸入 'exit'  : 退出程式");
            Console.WriteLine(new string('=', 60) + "\n");
        }

        private string? FindJsonFile(string filename)
        {
            if (File.Exists(filename)) return Path.GetFullPath(filename);
            var currentDir = AppDomain.CurrentDomain.BaseDirectory;
            while (currentDir != null)
            {
                var checkPath = Path.Combine(currentDir, filename);
                if (File.Exists(checkPath)) return checkPath;
                currentDir = Directory.GetParent(currentDir)?.FullName;
            }
            return null;
        }

        private async Task TriggerTestMissionAsync(string? seq, string configFile)
        {
            if (string.IsNullOrEmpty(seq))
            {
                seq = $"M{DateTime.Now:yyMMddHHmmss}";
            }

            var subMissions = new List<SubMission>
            {
                new() { Space = "A-01-2", Action = "start" },
                new() { Space = "A-01-2", Action = "load" },
                new() { Space = "L-01-0", Action = "unload" },
                new() { Space = "L-01-0", Action = "end" }
            };
            string priority = "128";

            var fullPath = FindJsonFile(configFile);
            if (fullPath == null)
            {
                var errMsg = $"[錯誤] 找不到指定的任務設定檔: {configFile}！發送失敗。";
                LogError(errMsg);
                Console.WriteLine($"\n{errMsg}");
                return;
            }

            try
            {
                var json = await File.ReadAllTextAsync(fullPath);
                using var doc = JsonDocument.Parse(json);
                var root = doc.RootElement;
                if (root.TryGetProperty("sub_missions", out var subsProp))
                {
                    subMissions = JsonSerializer.Deserialize<List<SubMission>>(subsProp.GetRawText()) ?? subMissions;
                    Console.WriteLine($"成功自 {configFile} 載入自訂子任務組合，共 {subMissions.Count} 個步驟。");
                }
                if (root.TryGetProperty("priority", out var priProp))
                {
                    priority = priProp.ToString();
                }
            }
            catch (Exception ex)
            {
                var errMsg = $"讀取 {configFile} 失敗，終止發送。錯誤: {ex.Message}";
                LogError(errMsg);
                Console.WriteLine($"\n{errMsg}");
                return;
            }

            var missionPayload = new MissionRequest
            {
                ProtocolVersion = "2.0",
                Sequence = seq,
                Timestamp = GetTimestamp(),
                Priority = priority,
                SubMissions = subMissions
            };

            string url = $"http://{_config.Rms.Host}:{_config.Rms.Port}/awd/rms/set_mission_request";
            Log($"\n[主動派工] 向 RMS 發送任務請求 (sequence: {seq}, 檔案: {configFile})...");
            Console.WriteLine($"\n[主動派工] 向 RMS 發送任務請求 (sequence: {seq}, 檔案: {configFile})...");
            await SendPostRequestAsync(url, missionPayload);
        }

        private async Task SendAckToRmsAsync(MissionResult res)
        {
            var ackPayload = new MissionAck
            {
                ProtocolVersion = res.ProtocolVersion,
                Sequence = res.Sequence,
                Timestamp = GetTimestamp(),
                Priority = res.Priority,
                Action = res.Action,
                Ack = "OK"
            };

            string url = $"http://{_config.Rms.Host}:{_config.Rms.Port}/awd/rms/set_mission_ack";
            Log($"\n[發送確認] 發送 ACK (action='{res.Action}') 給 RMS...");
            Console.WriteLine($"\n[發送確認] 發送 ACK (action='{res.Action}') 給 RMS...");
            await SendPostRequestAsync(url, ackPayload);
        }

        private async Task SendPostRequestAsync<T>(string url, T payload)
        {
            try
            {
                var content = JsonContent.Create(payload, options: new JsonSerializerOptions { WriteIndented = true });
                using var cts = new CancellationTokenSource(TimeSpan.FromSeconds(_config.Simulation.RequestTimeoutSeconds));
                var response = await _httpClient.PostAsync(url, content, cts.Token);
                var resBody = await response.Content.ReadAsStringAsync();

                Log($"HTTP POST 成功 -> {url}\n回應狀態: {(int)response.StatusCode}\n回應內容:\n{resBody}");
            }
            catch (TaskCanceledException)
            {
                LogError($"HTTP POST 逾時 -> {url} (超過 {_config.Simulation.RequestTimeoutSeconds} 秒)");
            }
            catch (Exception ex)
            {
                LogError($"HTTP POST 連線失敗 -> {url}: {ex.Message}");
            }
        }
    }
}
