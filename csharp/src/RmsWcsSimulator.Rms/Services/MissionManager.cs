using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Net.Http.Json;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using RmsWcsSimulator.Common.Config;
using RmsWcsSimulator.Common.Models;

namespace RmsWcsSimulator.Rms.Services
{
    public class MissionContext
    {
        public string VehicleId { get; set; } = string.Empty;
        public string ExpectedAction { get; set; } = string.Empty;
        public string? AckStatus { get; set; }
        public TaskCompletionSource<string> AckCompletionSource { get; set; } = new(TaskCreationOptions.RunContinuationsAsynchronously);
    }

    public class MissionManager
    {
        private readonly SimulationConfig _config;
        private readonly HttpClient _httpClient;
        private readonly List<string> _availableVehicles = new() { "AMR01", "AMR02" };
        private readonly List<MissionRequest> _pendingQueue = new();
        private readonly Dictionary<string, MissionContext> _activeMissions = new();
        private readonly SemaphoreSlim _lock = new(1, 1);
        private int _onlineSequenceCounter = 0;

        public MissionManager(SimulationConfig config, HttpClient httpClient)
        {
            _config = config;
            _httpClient = httpClient;
        }

        private string GetTimestamp()
        {
            var now = DateTime.Now;
            return now.ToString("yyyy-MM-dd HH:mm:ss.") + $"{now.Millisecond:D3}";
        }

        private void Log(string message)
        {
            string formatted = $"{GetTimestamp()} [INFO] {message}";
            Console.WriteLine(formatted);
            try
            {
                File.AppendAllText(_config.Rms.LogFile, formatted + Environment.NewLine, Encoding.UTF8);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[Log Error] 無法寫入日誌檔: {ex.Message}");
            }
        }

        private void LogError(string message)
        {
            string formatted = $"{GetTimestamp()} [ERROR] {message}";
            Console.Error.WriteLine(formatted);
            try
            {
                File.AppendAllText(_config.Rms.LogFile, formatted + Environment.NewLine, Encoding.UTF8);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[Log Error] 無法寫入日誌檔: {ex.Message}");
            }
        }

        private void LogWarning(string message)
        {
            string formatted = $"{GetTimestamp()} [WARNING] {message}";
            Console.WriteLine(formatted);
            try
            {
                File.AppendAllText(_config.Rms.LogFile, formatted + Environment.NewLine, Encoding.UTF8);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[Log Error] 無法寫入日誌檔: {ex.Message}");
            }
        }

        public async Task SendOnlineStatusAsync(string status = "remote")
        {
            int seqNum = Interlocked.Increment(ref _onlineSequenceCounter);
            string seq = seqNum.ToString("D6");

            var payload = new OnlineStatus
            {
                ProtocolVersion = "2.0",
                Sequence = seq,
                Timestamp = GetTimestamp(),
                Priority = "128",
                Device = "RMS01",
                Status = status
            };

            string url = $"http://{_config.Wcs.Host}:{_config.Wcs.Port}/awd/rms/online";
            Log($"\n[主動上報] 向 WCS 發送上線狀態 (status: {status})...");
            await SendPostRequestAsync(url, payload);
        }

        public async Task<(bool Success, string Reason)> StartMissionAsync(MissionRequest request)
        {
            await _lock.WaitAsync();
            try
            {
                string seq = request.Sequence;
                if (_activeMissions.ContainsKey(seq) || _pendingQueue.Any(m => m.Sequence == seq))
                {
                    LogWarning($"任務 {seq} 已經在執行中或等待佇列中，拒絕重複的任務請求。");
                    return (false, "Mission sequence already active or queued");
                }

                _pendingQueue.Add(request);
                Log($"[任務排隊] 任務 {seq} 已成功接收並加入等待佇列。目前排隊數量: {_pendingQueue.Count}");

                // 背景非同步觸發，不阻塞 HTTP 回應
                _ = TriggerNextMissionAsync();
                return (true, "NA");
            }
            finally
            {
                _lock.Release();
            }
        }

        private async Task TriggerNextMissionAsync()
        {
            await _lock.WaitAsync();
            try
            {
                while (_pendingQueue.Count > 0 && _availableVehicles.Count > 0)
                {
                    var nextMission = _pendingQueue[0];
                    _pendingQueue.RemoveAt(0);

                    var vehicleId = _availableVehicles[0];
                    _availableVehicles.RemoveAt(0);

                    var context = new MissionContext
                    {
                        VehicleId = vehicleId
                    };
                    _activeMissions[nextMission.Sequence] = context;

                    Log($"[分配車輛] 任務 {nextMission.Sequence} 取得車輛 {vehicleId}。剩餘可用車輛: {string.Join(", ", _availableVehicles)}");

                    // 背景啟動狀態機
                    _ = RunMissionStateMachineAsync(nextMission.Sequence, nextMission);
                }
            }
            finally
            {
                _lock.Release();
            }
        }

        private async Task RunMissionStateMachineAsync(string seq, MissionRequest mission)
        {
            string vehicleId = "UNKNOWN";
            await _lock.WaitAsync();
            try
            {
                if (_activeMissions.TryGetValue(seq, out var ctx))
                {
                    vehicleId = ctx.VehicleId;
                }
            }
            finally
            {
                _lock.Release();
            }

            Log($"==================================================");
            Log($"[狀態機啟動] 任務序號: {seq}, 指派車輛: {vehicleId}, 共 {mission.SubMissions.Count} 個子任務。");
            Log($"==================================================");

            try
            {
                for (int i = 0; i < mission.SubMissions.Count; i++)
                {
                    var sub = mission.SubMissions[i];
                    string space = sub.Space;
                    string action = sub.Action;
                    string reason = (action == "load") ? _config.Simulation.DefaultPalletId : "NA";

                    var resultPayload = new MissionResult
                    {
                        ProtocolVersion = "2.0",
                        Sequence = seq,
                        Timestamp = GetTimestamp(),
                        Priority = mission.Priority,
                        Space = space,
                        Action = action,
                        Result = "OK",
                        Reason = reason
                    };

                    TaskCompletionSource<string> tcs;
                    await _lock.WaitAsync();
                    try
                    {
                        if (!_activeMissions.TryGetValue(seq, out var context))
                        {
                            LogError($"任務 {seq} ({vehicleId}) 的 Context 已遺失，終止。");
                            return;
                        }
                        context.ExpectedAction = action;
                        context.AckCompletionSource = new TaskCompletionSource<string>(TaskCreationOptions.RunContinuationsAsynchronously);
                        tcs = context.AckCompletionSource;
                    }
                    finally
                    {
                        _lock.Release();
                    }

                    string wcsUrl = $"http://{_config.Wcs.Host}:{_config.Wcs.Port}/awd/rms/set_mission_result";
                    Log($"\n[任務步驟 {i + 1}/{mission.SubMissions.Count}] 任務 {seq} ({vehicleId}) 發送任務執行結果 ({action}於{space})...");
                    
                    await SendPostRequestAsync(wcsUrl, resultPayload);

                    Log($"[任務步驟 {i + 1}/{mission.SubMissions.Count}] 任務 {seq} ({vehicleId}) 等待 WCS 發送 ACK (action='{action}')...");

                    var ackTask = tcs.Task;
                    var timeoutTask = Task.Delay(TimeSpan.FromSeconds(_config.Simulation.AckTimeoutSeconds));

                    var completedTask = await Task.WhenAny(ackTask, timeoutTask);
                    if (completedTask == timeoutTask)
                    {
                        LogError($"[超時錯誤] 任務 {seq} ({vehicleId}) 超過 {_config.Simulation.AckTimeoutSeconds} 秒未收到 WCS ACK (action='{action}')！任務終止。");
                        return;
                    }

                    string ackStatus = await ackTask;
                    if (ackStatus != "OK")
                    {
                        LogError($"[狀態錯誤] 任務 {seq} ({vehicleId}) 收到非 OK 的 ACK 狀態: '{ackStatus}'！任務終止。");
                        return;
                    }

                    Log($"[步驟確認] 任務 {seq} ({vehicleId}) 成功收到 WCS ACK (action='{action}')。");

                    if (i < mission.SubMissions.Count - 1)
                    {
                        Log($"[延遲等待] 任務 {seq} ({vehicleId}) 依照規範，等待 {_config.Simulation.StepDelaySeconds} 秒後再執行下一步子任務...");
                        await Task.Delay(TimeSpan.FromSeconds(_config.Simulation.StepDelaySeconds));
                    }
                }

                Log($"==================================================");
                Log($"[任務完成] 任務 {seq} ({vehicleId}) 搬運執行完成！");
                Log($"==================================================");
            }
            catch (Exception ex)
            {
                LogError($"任務 {seq} 狀態機執行時發生錯誤: {ex.Message}");
            }
            finally
            {
                await _lock.WaitAsync();
                try
                {
                    if (_activeMissions.TryGetValue(seq, out var context))
                    {
                        var vehicle = context.VehicleId;
                        _availableVehicles.Add(vehicle);
                        _availableVehicles.Sort();
                        _activeMissions.Remove(seq);
                        Log($"[資源釋放] 任務 {seq} 結束，釋放車輛 {vehicle}。目前可用車輛: {string.Join(", ", _availableVehicles)}");
                    }

                    // 觸發下一個排隊任務
                    _ = TriggerNextMissionAsync();
                }
                finally
                {
                    _lock.Release();
                }
            }
        }

        public async Task<(bool Success, string Message)> ReceiveAckAsync(MissionAck ack)
        {
            await _lock.WaitAsync();
            try
            {
                string seq = ack.Sequence;
                string action = ack.Action;

                if (_activeMissions.TryGetValue(seq, out var context))
                {
                    if (context.ExpectedAction == action)
                    {
                        context.AckStatus = ack.Ack;
                        context.AckCompletionSource.TrySetResult(ack.Ack);
                        return (true, "ACK matched");
                    }
                    else
                    {
                        var msg = $"未預期的 ACK 動作 (收到: seq={seq}, action={action} | 預期: seq={seq}, action={context.ExpectedAction})";
                        LogWarning(msg);
                        return (false, msg);
                    }
                }
                else
                {
                    var msg = $"未預期的 ACK 任務序號或任務已結束 (收到: seq={seq}, action={action})";
                    LogWarning(msg);
                    return (false, msg);
                }
            }
            finally
            {
                _lock.Release();
            }
        }

        private async Task SendPostRequestAsync<T>(string url, T payload)
        {
            try
            {
                var content = JsonContent.Create(payload, options: new JsonSerializerOptions { WriteIndented = true });
                // 使用內嵌超時時間
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
