using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using TaskTrackerApi.Data;
using TaskTrackerApi.DTOs;
using TaskTrackerApi.Models;

namespace TaskTrackerApi.Controllers;

/// <summary>CRUD-операции над задачами и команды бизнес-логики (статусы, исполнитель, трудозатраты).</summary>
[ApiController]
[Route("api/tasks")]
[Produces("application/json")]
public class TasksController : ControllerBase
{
    private readonly AppDbContext _db;

    public TasksController(AppDbContext db) => _db = db;

    /// <summary>
    /// GET api/tasks — список задач с данными проекта (объединение «задача + проект»).
    /// </summary>
    /// <param name="projectId">Фильтр по проекту.</param>
    /// <param name="status">Фильтр по статусу задачи.</param>
    /// <param name="priority">Фильтр по приоритету.</param>
    /// <param name="assignee">Фильтр по исполнителю (частичное совпадение).</param>
    /// <param name="overdueOnly">Только просроченные задачи.</param>
    [HttpGet]
    [ProducesResponseType(typeof(IEnumerable<TaskResponse>), StatusCodes.Status200OK)]
    public async Task<ActionResult<IEnumerable<TaskResponse>>> GetAll(
        [FromQuery] int? projectId,
        [FromQuery] Models.TaskStatus? status,
        [FromQuery] Priority? priority,
        [FromQuery] string? assignee,
        [FromQuery] bool overdueOnly = false)
    {
        var tasks = await _db.Tasks
            .Include(t => t.Project)
            .Include(t => t.Comments)
            .ToListAsync();

        // LINQ: цепочка Where + проекция Select в DTO
        var query = tasks.AsQueryable()
            .Where(t => projectId == null || t.ProjectId == projectId)
            .Where(t => status == null || t.Status == status)
            .Where(t => priority == null || t.Priority == priority)
            .Where(t => string.IsNullOrWhiteSpace(assignee)
                        || (t.Assignee != null && t.Assignee.Contains(assignee, StringComparison.OrdinalIgnoreCase)))
            .Where(t => !overdueOnly || t.IsOverdue);

        var result = query
            .OrderByDescending(t => t.Priority)
            .ThenBy(t => t.DueDateUtc ?? DateTime.MaxValue)
            .Select(t => t.ToResponse())
            .ToList();

        return Ok(result);
    }

    /// <summary>GET api/tasks/{id} — задача вместе с названием и кодом её проекта.</summary>
    [HttpGet("{id:int}")]
    [ProducesResponseType(typeof(TaskResponse), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<TaskResponse>> GetById(int id)
    {
        var task = await _db.Tasks
            .Include(t => t.Project)
            .Include(t => t.Comments)
            .FirstOrDefaultAsync(t => t.Id == id);

        if (task is null)
            return NotFound(new { message = $"Задача с Id={id} не найдена." });

        return Ok(task.ToResponse());
    }

    /// <summary>POST api/tasks — создание задачи в проекте (проверки выполняет модель Project).</summary>
    [HttpPost]
    [ProducesResponseType(typeof(TaskResponse), StatusCodes.Status201Created)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<TaskResponse>> Create([FromQuery] int projectId, [FromBody] TaskRequest request)
    {
        var project = await _db.Projects
            .Include(p => p.Tasks)
            .FirstOrDefaultAsync(p => p.Id == projectId);

        if (project is null)
            return NotFound(new { message = $"Проект с Id={projectId} не найден." });

        // бизнес-логика: закрытый проект, дубликаты названия, срок задачи vs срок проекта
        var task = project.AddTask(request.Title, request.Priority, request.Assignee, request.DueDateUtc);
        task.Description = request.Description?.Trim() ?? string.Empty;

        _db.Tasks.Add(task);
        await _db.SaveChangesAsync();

        task.Project = project;
        return CreatedAtAction(nameof(GetById), new { id = task.Id }, task.ToResponse());
    }

    /// <summary>PUT api/tasks/{id} — обновление названия, описания, приоритета, исполнителя.</summary>
    [HttpPut("{id:int}")]
    [ProducesResponseType(typeof(TaskResponse), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public async Task<ActionResult<TaskResponse>> Update(int id, [FromBody] UpdateTaskRequest request)
    {
        var task = await _db.Tasks
            .Include(t => t.Project)
            .Include(t => t.Comments)
            .FirstOrDefaultAsync(t => t.Id == id);

        if (task is null)
            return NotFound(new { message = $"Задача с Id={id} не найдена." });

        if (!string.IsNullOrWhiteSpace(request.Title))
            task.Rename(request.Title);

        if (request.Description is not null)
            task.ChangeDescription(request.Description);

        if (request.Priority.HasValue)
            task.Priority = request.Priority.Value;

        if (!string.IsNullOrWhiteSpace(request.Assignee))
            task.Assign(request.Assignee);

        await _db.SaveChangesAsync();
        return Ok(task.ToResponse());
    }

    /// <summary>
    /// DELETE api/tasks/{id} — удаление задачи.
    /// Бизнес-правило модели Project: задачу в работе удалять нельзя.
    /// </summary>
    [HttpDelete("{id:int}")]
    [ProducesResponseType(StatusCodes.Status204NoContent)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public async Task<IActionResult> Delete(int id)
    {
        var task = await _db.Tasks
            .Include(t => t.Project)
                .ThenInclude(p => p!.Tasks)
            .Include(t => t.Comments)
            .FirstOrDefaultAsync(t => t.Id == id);

        if (task is null)
            return NotFound(new { message = $"Задача с Id={id} не найдена." });

        task.Project?.RemoveTask(task);
        _db.Tasks.Remove(task);
        await _db.SaveChangesAsync();

        return NoContent();
    }

    // ---------------- Команды бизнес-логики ----------------

    /// <summary>PUT api/tasks/{id}/status — перевод задачи в новый статус (с проверкой переходов).</summary>
    [HttpPut("{id:int}/status")]
    public async Task<ActionResult<TaskResponse>> ChangeStatus(int id, [FromBody] ChangeStatusRequest request)
    {
        var task = await _db.Tasks
            .Include(t => t.Project)
            .Include(t => t.Comments)
            .FirstOrDefaultAsync(t => t.Id == id);

        if (task is null)
            return NotFound(new { message = $"Задача с Id={id} не найдена." });

        task.ChangeStatus(request.Status);
        await _db.SaveChangesAsync();
        return Ok(task.ToResponse());
    }

    /// <summary>PUT api/tasks/{id}/assignee — назначение исполнителя.</summary>
    [HttpPut("{id:int}/assignee")]
    public async Task<ActionResult<TaskResponse>> Assign(int id, [FromQuery] string assignee)
    {
        var task = await _db.Tasks
            .Include(t => t.Project)
            .Include(t => t.Comments)
            .FirstOrDefaultAsync(t => t.Id == id);

        if (task is null)
            return NotFound(new { message = $"Задача с Id={id} не найдена." });

        task.Assign(assignee);
        await _db.SaveChangesAsync();
        return Ok(task.ToResponse());
    }

    /// <summary>POST api/tasks/{id}/work — списание трудозатрат (контроль перерасхода).</summary>
    [HttpPost("{id:int}/work")]
    public async Task<ActionResult<TaskResponse>> LogWork(int id, [FromBody] LogWorkRequest request)
    {
        var task = await _db.Tasks
            .Include(t => t.Project)
            .Include(t => t.Comments)
            .FirstOrDefaultAsync(t => t.Id == id);

        if (task is null)
            return NotFound(new { message = $"Задача с Id={id} не найдена." });

        task.LogWork(request.Hours, request.Note);
        await _db.SaveChangesAsync();
        return Ok(task.ToResponse());
    }

    /// <summary>PUT api/tasks/{id}/estimate — установка оценки трудоёмкости.</summary>
    [HttpPut("{id:int}/estimate")]
    public async Task<ActionResult<TaskResponse>> SetEstimate(int id, [FromBody] EstimateRequest request)
    {
        var task = await _db.Tasks
            .Include(t => t.Project)
            .Include(t => t.Comments)
            .FirstOrDefaultAsync(t => t.Id == id);

        if (task is null)
            return NotFound(new { message = $"Задача с Id={id} не найдена." });

        task.SetEstimate(request.Hours);
        await _db.SaveChangesAsync();
        return Ok(task.ToResponse());
    }

    /// <summary>PUT api/tasks/{id}/reschedule — перенос срока задачи.</summary>
    [HttpPut("{id:int}/reschedule")]
    public async Task<ActionResult<TaskResponse>> Reschedule(int id, [FromBody] RescheduleRequest request)
    {
        var task = await _db.Tasks
            .Include(t => t.Project)
            .Include(t => t.Comments)
            .FirstOrDefaultAsync(t => t.Id == id);

        if (task is null)
            return NotFound(new { message = $"Задача с Id={id} не найдена." });

        task.Reschedule(request.DueDateUtc, request.Reason);
        await _db.SaveChangesAsync();
        return Ok(task.ToResponse());
    }

    /// <summary>POST api/tasks/{id}/comments — добавить комментарий к задаче.</summary>
    [HttpPost("{id:int}/comments")]
    public async Task<ActionResult<CommentResponse>> AddComment(int id, [FromBody] CommentRequest request)
    {
        var task = await _db.Tasks
            .Include(t => t.Project)
            .Include(t => t.Comments)
            .FirstOrDefaultAsync(t => t.Id == id);

        if (task is null)
            return NotFound(new { message = $"Задача с Id={id} не найдена." });

        var comment = task.AddComment(request.Author, request.Text);
        _db.Comments.Add(comment);
        await _db.SaveChangesAsync();

        comment.Task = task;
        return CreatedAtAction(nameof(GetById), new { id = task.Id }, comment.ToResponse());
    }

    /// <summary>
    /// GET api/tasks/my-board — задачи исполнителя по всем проектам.
    /// Пример запроса на объединение данных в синтаксисе LINQ (from ... join ... select).
    /// </summary>
    [HttpGet("my-board")]
    public async Task<ActionResult<IEnumerable<TaskResponse>>> GetMyBoard([FromQuery] string assignee)
    {
        if (string.IsNullOrWhiteSpace(assignee))
            return BadRequest(new { message = "Укажите исполнителя в параметре assignee." });

        var projects = await _db.Projects.Include(p => p.Tasks).ThenInclude(t => t.Comments).ToListAsync();

        // синтаксис запросов LINQ: join задач с их проектами + фильтрация
        var board = from project in projects
                    join task in projects.SelectMany(p => p.Tasks) on project.Id equals task.ProjectId
                    where task.Assignee != null
                          && task.Assignee.Contains(assignee, StringComparison.OrdinalIgnoreCase)
                          && !task.IsClosed
                    orderby task.Priority descending, task.DueDateUtc
                    select task.ToResponse();

        return Ok(board.ToList());
    }
}
