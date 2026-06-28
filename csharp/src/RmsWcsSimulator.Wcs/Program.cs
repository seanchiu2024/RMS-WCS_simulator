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
using RmsWcsSimulator.Wcs.Services;

var config = SimulationConfig.Load();

var builder = WebApplication.CreateBuilder(args);

// 設定 Kestrel 監聽的 Port
builder.WebHost.ConfigureKestrel(options =>
{
    options.ListenAnyIP(config.Wcs.Port);
});

// 註冊服務
builder.Services.AddSingleton(config);
builder.Services.AddHttpClient();

// 同時註冊為 Singleton 與 BackgroundService 共享狀態
builder.Services.AddSingleton<WcsCliService>();
builder.Services.AddHostedService(sp => sp.GetRequiredService<WcsCliService>());

var app = builder.Build();

var wcsCliService = app.Services.GetRequiredService<WcsCliService>();

// 格式化輸出請求 Log 輔助方法
void LogRequest(string path, string body)
{
    var now = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss.fff");
    var logMsg = $"\n======== 接收到 POST 請求 ========\n時間: {now}\n端點: {path}\n方法: POST\nBody 內容:\n{body}\n==================================";
    try
    {
        File.AppendAllText(config.Wcs.LogFile, logMsg + Environment.NewLine);
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
    try
    {
        File.AppendAllText(config.Wcs.LogFile, logMsg + Environment.NewLine);
    }
    catch (Exception ex)
    {
        Console.WriteLine($"[Log Error] 無法寫入日誌檔: {ex.Message}");
    }
}

// 註冊 POST /awd/rms/set_mission_result
app.MapPost("/awd/rms/set_mission_result", async (HttpContext httpContext, MissionResult result) =>
{
    httpContext.Request.EnableBuffering();
    using var reader = new StreamReader(httpContext.Request.Body, System.Text.Encoding.UTF8, leaveOpen: true);
    var bodyStr = await reader.ReadToEndAsync();
    httpContext.Request.Body.Position = 0;

    LogRequest("/awd/rms/set_mission_result", bodyStr);

    if (string.IsNullOrEmpty(result.Sequence) || string.IsNullOrEmpty(result.Action))
    {
        var error = new { status = "error", message = "缺少必要欄位 'sequence' 或 'action'" };
        LogResponse(error);
        return Results.BadRequest(error);
    }

    // 立即同步回覆已接收
    var replyPayload = new
    {
        status = "success",
        message = $"成功收到步驟 {result.Action} 的結果"
    };

    // 放進 Queue 由 WCS CLI 互動邏輯處理
    wcsCliService.QueueResult(result);

    LogResponse(replyPayload);
    return Results.Ok(replyPayload);
});

// 註冊 POST /awd/rms/online
app.MapPost("/awd/rms/online", async (HttpContext httpContext, OnlineStatus online) =>
{
    httpContext.Request.EnableBuffering();
    using var reader = new StreamReader(httpContext.Request.Body, System.Text.Encoding.UTF8, leaveOpen: true);
    var bodyStr = await reader.ReadToEndAsync();
    httpContext.Request.Body.Position = 0;

    LogRequest("/awd/rms/online", bodyStr);

    var logMsg = $"收到 RMS 上線狀態報告 -> 設備: {online.Device}, 狀態: {online.Status}";
    Console.WriteLine($"\n[狀態通知] {logMsg}");
    try
    {
        File.AppendAllText(config.Wcs.LogFile, $"{DateTime.Now:yyyy-MM-dd HH:mm:ss.fff} [INFO] {logMsg}\n");
    }
    catch (Exception ex)
    {
        Console.WriteLine($"[Log Error] 無法寫入日誌檔: {ex.Message}");
    }

    var replyPayload = new
    {
        status = "success",
        message = $"成功收到 {online.Device} 的上線狀態: {online.Status}"
    };

    LogResponse(replyPayload);
    return Results.Ok(replyPayload);
});

await app.RunAsync();
