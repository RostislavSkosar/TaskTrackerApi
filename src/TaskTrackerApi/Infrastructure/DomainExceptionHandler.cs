using Microsoft.AspNetCore.Diagnostics;
using Microsoft.AspNetCore.Mvc;
using TaskTrackerApi.Models;

namespace TaskTrackerApi.Infrastructure;

/// <summary>
/// Глобальный обработчик исключений: преобразует ошибки бизнес-логики
/// (DomainException) в ответ 400, а остальные — в 500.
/// </summary>
public class DomainExceptionHandler : IExceptionHandler
{
    private readonly ILogger<DomainExceptionHandler> _logger;

    public DomainExceptionHandler(ILogger<DomainExceptionHandler> logger) => _logger = logger;

    public async ValueTask<bool> TryHandleAsync(
        HttpContext httpContext, Exception exception, CancellationToken cancellationToken)
    {
        var (status, title) = exception switch
        {
            DomainException => (StatusCodes.Status400BadRequest, "Нарушено бизнес-правило"),
            KeyNotFoundException => (StatusCodes.Status404NotFound, "Объект не найден"),
            _ => (StatusCodes.Status500InternalServerError, "Внутренняя ошибка сервера")
        };

        if (status == StatusCodes.Status500InternalServerError)
            _logger.LogError(exception, "Необработанное исключение при {Path}", httpContext.Request.Path);

        httpContext.Response.StatusCode = status;
        await httpContext.Response.WriteAsJsonAsync(new ProblemDetails
        {
            Status = status,
            Title = title,
            Detail = exception.Message,
            Instance = httpContext.Request.Path
        }, cancellationToken);

        return true;
    }
}
