using System;
using System.IO;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using RmsWcsSimulator.Common.Config;
using RmsWcsSimulator.Common.Models;
using RmsWcsSimulator.Rms.Services;

var config = SimulationConfig.Load();

var builder = WebApplication.CreateBuilder(args);

// 設定 Kestrel 監聽的 Port 與 Host
builder.WebHost.ConfigureKestrel(options =>
{
    // 如果 config 指定了 localhost 以外的 IP，在此綁定；一般綁定 Any (0.0.0.0) 或是 localhost
    options.ListenAnyIP(config.Rms.Port);
});

// 註冊服務
builder.Services.AddSingleton(config);
builder.Services.AddHttpClient();
builder.Services.AddSingleton<MissionManager>();

var app = builder.Build();

var manager = app.Services.GetRequiredService<MissionManager>();

// 格式化輸出請求 Log 輔助方法
void LogRequest(string path, string body)
{
    var now = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss.fff");
    var logMsg = $"\n======== 接收到 POST 請求 ========\n時間: {now}\n端點: {path}\n方法: POST\nBody 內容:\n{body}\n==================================";
    Console.WriteLine(logMsg);
    try
    {
        File.AppendAllText(config.Rms.LogFile, logMsg + Environment.NewLine);
    }
    catch (Exception ex)
    {
        Console.WriteLine($"[Log Error] 無法寫入日誌檔: {ex.Message}");
    }
}

void LogResponse(object responseData)
{
    var jsonString = JsonSerializer.Serialize(responseData, new JsonSerializerOptions { WriteIndented = true });
    var logMsg = $"已回覆響應:\n{jsonString}";
    Console.WriteLine(logMsg);
    try
    {
        File.AppendAllText(config.Rms.LogFile, logMsg + Environment.NewLine);
    }
    catch (Exception ex)
    {
        Console.WriteLine($"[Log Error] 無法寫入日誌檔: {ex.Message}");
    }
}

// 註冊 POST /awd/rms/set_mission_request
app.MapPost("/awd/rms/set_mission_request", async (HttpContext httpContext, MissionRequest request) =>
{
    // 取得 JSON Body 字串用以 Log 輸出
    httpContext.Request.EnableBuffering();
    using var reader = new StreamReader(httpContext.Request.Body, System.Text.Encoding.UTF8, leaveOpen: true);
    var bodyStr = await reader.ReadToEndAsync();
    httpContext.Request.Body.Position = 0; // 重設位置以便 JSON 繫結

    LogRequest("/awd/rms/set_mission_request", bodyStr);

    if (string.IsNullOrEmpty(request.Sequence))
    {
        var error = new { status = "error", message = "缺少必要欄位 'sequence'" };
        LogResponse(error);
        return Results.BadRequest(error);
    }

    var (success, reason) = await manager.StartMissionAsync(request);
    var replyVal = success ? "ACK" : "NAK";

    var now = DateTime.Now;
    var replyPayload = new MissionRequest
    {
        ProtocolVersion = request.ProtocolVersion,
        Sequence = request.Sequence,
        Timestamp = now.ToString("yyyy-MM-dd HH:mm:ss.") + $"{now.Millisecond:D3}",
        Priority = request.Priority,
        Reply = replyVal,
        Reason = reason
    };

    LogResponse(replyPayload);
    return success ? Results.Ok(replyPayload) : Results.BadRequest(replyPayload);
});

// 註冊 POST /awd/rms/set_mission_ack
app.MapPost("/awd/rms/set_mission_ack", async (HttpContext httpContext, MissionAck ack) =>
{
    httpContext.Request.EnableBuffering();
    using var reader = new StreamReader(httpContext.Request.Body, System.Text.Encoding.UTF8, leaveOpen: true);
    var bodyStr = await reader.ReadToEndAsync();
    httpContext.Request.Body.Position = 0;

    LogRequest("/awd/rms/set_mission_ack", bodyStr);

    var (success, msg) = await manager.ReceiveAckAsync(ack);
    var replyPayload = new
    {
        status = success ? "success" : "error",
        message = msg
    };

    LogResponse(replyPayload);
    return success ? Results.Ok(replyPayload) : Results.BadRequest(replyPayload);
});

// 開機後自動延遲 1.5 秒發送 RMS 上線上報狀態給 WCS
app.Lifetime.ApplicationStarted.Register(async () =>
{
    await Task.Delay(1500);
    try
    {
        await manager.SendOnlineStatusAsync("remote");
    }
    catch (Exception ex)
    {
        Console.Error.WriteLine($"[Startup] 啟動時自動發送上線狀態失敗: {ex.Message}");
    }
});

Console.WriteLine($"==================================================");
Console.WriteLine($"RMS 模擬伺服器已啟動，監聽 Port: {config.Rms.Port} ...");
Console.WriteLine($"==================================================");

await app.RunAsync();
