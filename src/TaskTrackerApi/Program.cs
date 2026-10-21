using System.Text.Json.Serialization;
using Microsoft.EntityFrameworkCore;
using TaskTrackerApi.Data;
using TaskTrackerApi.Infrastructure;

var builder = WebApplication.CreateBuilder(args);

// ---- Сервисы ----
builder.Services.AddControllers()
    .AddJsonOptions(options =>
    {
        // перечисления в JSON — строками, а не числами
        options.JsonSerializerOptions.Converters.Add(new JsonStringEnumConverter());
        options.JsonSerializerOptions.WriteIndented = true;
    });

builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

// InMemory-провайдер EF Core: не требует установки СУБД, данные живут в процессе приложения
builder.Services.AddDbContext<AppDbContext>(options =>
    options.UseInMemoryDatabase(builder.Configuration["DatabaseName"] ?? "TaskTrackerDb"));

builder.Services.AddExceptionHandler<DomainExceptionHandler>();
builder.Services.AddProblemDetails();

var app = builder.Build();

// ---- Заполнение БД демонстрационными данными ----
using (var scope = app.Services.CreateScope())
{
    var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
    DbInitializer.Seed(db);
}

// ---- Конвейер обработки запросов ----
app.UseSwagger();
app.UseSwaggerUI();

app.UseExceptionHandler();

app.MapControllers();

app.MapGet("/", () => Results.Redirect("/swagger"));

app.Run();
