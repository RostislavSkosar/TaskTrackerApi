using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using TaskTrackerApi.Data;
using TaskTrackerApi.DTOs;
using TaskTrackerApi.Models;

namespace TaskTrackerApi.Controllers;

/// <summary>CRUD-операции над проектами + полная карточка проекта (проект → задачи → комментарии).</summary>
[ApiController]
[Route("api/[controller]")]
[Produces("application/json")]
public class ProjectsController : ControllerBase
{
    private readonly AppDbContext _db;

    public ProjectsController(AppDbContext db) => _db = db;

    /// <summary>GET api/projects — список проектов (LINQ: Where + Select + OrderBy).</summary>
    /// <param name="status">Фильтр по статусу проекта.</param>
    /// <param name="search">Поиск по названию или коду.</param>
    [HttpGet]
    [ProducesResponseType(typeof(IEnumerable<ProjectResponse>), StatusCodes.Status200OK)]
    public async Task<ActionResult<IEnumerable<ProjectResponse>>> GetAll(
        [FromQuery] ProjectStatus? status,
        [FromQuery] string? search)
    {
        var projects = await _db.Projects
            .Include(p => p.Tasks)
            .ToListAsync();

        // LINQ: Where (фильтрация) и Select (проекция в DTO)
        var result = projects
            .AsQueryable()
            .Where(p => status == null || p.Status == status)
            .Where(p => string.IsNullOrWhiteSpace(search)
                        || p.Name.Contains(search, StringComparison.OrdinalIgnoreCase)
                        || p.Code.Contains(search, StringComparison.OrdinalIgnoreCase))
            .OrderBy(p => p.Name)
            .Select(p => p.ToResponse())
            .ToList();

        return Ok(result);
    }

    /// <summary>GET api/projects/{id} — проект с расчётными показателями.</summary>
    [HttpGet("{id:int}")]
    [ProducesResponseType(typeof(ProjectResponse), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<ProjectResponse>> GetById(int id)
    {
        var project = await _db.Projects
            .Include(p => p.Tasks)
            .FirstOrDefaultAsync(p => p.Id == id);

        if (project is null)
            return NotFound(new { message = $"Проект с Id={id} не найден." });

        return Ok(project.ToResponse());
    }

    /// <summary>POST api/projects — создание проекта (валидация выполняется в модели).</summary>
    [HttpPost]
    [ProducesResponseType(typeof(ProjectResponse), StatusCodes.Status201Created)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public async Task<ActionResult<ProjectResponse>> Create([FromBody] ProjectRequest request)
    {
        if (await _db.Projects.AnyAsync(p => p.Code == request.Code.Trim().ToUpperInvariant()))
            return BadRequest(new { message = $"Проект с кодом '{request.Code}' уже существует." });

        var project = Project.Create(
            request.Name, request.Code, request.Description ?? string.Empty,
            request.Priority, request.DeadlineUtc);

        _db.Projects.Add(project);
        await _db.SaveChangesAsync();

        return CreatedAtAction(nameof(GetById), new { id = project.Id }, project.ToResponse());
    }

    /// <summary>PUT api/projects/{id} — обновление данных проекта.</summary>
    [HttpPut("{id:int}")]
    [ProducesResponseType(typeof(ProjectResponse), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public async Task<ActionResult<ProjectResponse>> Update(int id, [FromBody] UpdateProjectRequest request)
    {
        var project = await _db.Projects
            .Include(p => p.Tasks)
            .FirstOrDefaultAsync(p => p.Id == id);

        if (project is null)
            return NotFound(new { message = $"Проект с Id={id} не найден." });

        if (!string.IsNullOrWhiteSpace(request.Name))
            project.Rename(request.Name);

        if (!string.IsNullOrWhiteSpace(request.Code))
        {
            var newCode = request.Code.Trim().ToUpperInvariant();
            if (await _db.Projects.AnyAsync(p => p.Code == newCode && p.Id != id))
                return BadRequest(new { message = $"Проект с кодом '{newCode}' уже существует." });

            project.ChangeCode(newCode);
        }

        if (request.Description is not null)
            project.ChangeDescription(request.Description);

        if (request.Priority.HasValue)
            project.Priority = request.Priority.Value;

        await _db.SaveChangesAsync();
        return Ok(project.ToResponse());
    }

    /// <summary>
    /// DELETE api/projects/{id} — удаление проекта.
    /// Бизнес-правило: удалять можно только архивированный проект либо проект без задач.
    /// </summary>
    [HttpDelete("{id:int}")]
    [ProducesResponseType(StatusCodes.Status204NoContent)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public async Task<IActionResult> Delete(int id)
    {
        var project = await _db.Projects
            .Include(p => p.Tasks)
            .FirstOrDefaultAsync(p => p.Id == id);

        if (project is null)
            return NotFound(new { message = $"Проект с Id={id} не найден." });

        if (project.Tasks.Count > 0 && project.Status != ProjectStatus.Archived)
            return BadRequest(new
            {
                message = $"Проект '{project.Name}' содержит задач: {project.Tasks.Count}. " +
                          "Удалить можно только архивированный проект (POST api/projects/{id}/archive) или пустой проект."
            });

        _db.Projects.Remove(project);
        await _db.SaveChangesAsync();
        return NoContent();
    }

    // ---------------- Команды, реализующие бизнес-логику модели ----------------

    /// <summary>POST api/projects/{id}/hold — поставить проект на паузу.</summary>
    [HttpPost("{id:int}/hold")]
    public async Task<ActionResult<ProjectResponse>> Hold(int id, [FromQuery] string reason)
    {
        var project = await _db.Projects.Include(p => p.Tasks).FirstOrDefaultAsync(p => p.Id == id);
        if (project is null)
            return NotFound(new { message = $"Проект с Id={id} не найден." });

        project.Hold(reason);
        await _db.SaveChangesAsync();
        return Ok(project.ToResponse());
    }

    /// <summary>POST api/projects/{id}/resume — снять проект с паузы.</summary>
    [HttpPost("{id:int}/resume")]
    public async Task<ActionResult<ProjectResponse>> Resume(int id)
    {
        var project = await _db.Projects.Include(p => p.Tasks).FirstOrDefaultAsync(p => p.Id == id);
        if (project is null)
            return NotFound(new { message = $"Проект с Id={id} не найден." });

        project.Resume();
        await _db.SaveChangesAsync();
        return Ok(project.ToResponse());
    }

    /// <summary>POST api/projects/{id}/complete — завершить проект (все задачи должны быть закрыты).</summary>
    [HttpPost("{id:int}/complete")]
    public async Task<ActionResult<ProjectResponse>> Complete(int id)
    {
        var project = await _db.Projects.Include(p => p.Tasks).FirstOrDefaultAsync(p => p.Id == id);
        if (project is null)
            return NotFound(new { message = $"Проект с Id={id} не найден." });

        project.Complete();
        await _db.SaveChangesAsync();
        return Ok(project.ToResponse());
    }

    /// <summary>POST api/projects/{id}/archive — архивировать завершённый проект.</summary>
    [HttpPost("{id:int}/archive")]
    public async Task<ActionResult<ProjectResponse>> Archive(int id)
    {
        var project = await _db.Projects.Include(p => p.Tasks).FirstOrDefaultAsync(p => p.Id == id);
        if (project is null)
            return NotFound(new { message = $"Проект с Id={id} не найден." });

        project.Archive();
        await _db.SaveChangesAsync();
        return Ok(project.ToResponse());
    }

    /// <summary>PUT api/projects/{id}/deadline — изменить срок проекта.</summary>
    [HttpPut("{id:int}/deadline")]
    public async Task<ActionResult<ProjectResponse>> SetDeadline(int id, [FromBody] DateTime deadlineUtc)
    {
        var project = await _db.Projects.Include(p => p.Tasks).FirstOrDefaultAsync(p => p.Id == id);
        if (project is null)
            return NotFound(new { message = $"Проект с Id={id} не найден." });

        project.SetDeadline(deadlineUtc);
        await _db.SaveChangesAsync();
        return Ok(project.ToResponse());
    }

    /// <summary>
    /// GET api/projects/{id}/details — объединение данных: проект + его задачи + комментарии к задачам.
    /// </summary>
    [HttpGet("{id:int}/details")]
    [ProducesResponseType(typeof(ProjectDetailsResponse), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<ProjectDetailsResponse>> GetDetails(int id)
    {
        var project = await _db.Projects
            .Include(p => p.Tasks)
                .ThenInclude(t => t.Comments)
            .FirstOrDefaultAsync(p => p.Id == id);

        if (project is null)
            return NotFound(new { message = $"Проект с Id={id} не найден." });

        // LINQ: Select — сборка сложного DTO из связанных сущностей
        var details = new ProjectDetailsResponse(
            project.Id, project.Name, project.Code, project.Status, project.Priority,
            project.DeadlineUtc, project.IsOverdue, project.CompletionPercent,
            project.Tasks
                .OrderByDescending(t => t.Priority)
                .ThenBy(t => t.DueDateUtc ?? DateTime.MaxValue)
                .Select(t => new TaskWithComments(
                    t.Id, t.Title, t.Status, t.Priority, t.Assignee, t.DueDateUtc,
                    t.IsOverdue, t.SpentHours,
                    t.Comments
                        .OrderBy(c => c.CreatedAtUtc)
                        .Select(c => c.ToResponse())
                        .ToList()))
                .ToList());

        return Ok(details);
    }
}
