using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using TaskTrackerApi.Data;
using TaskTrackerApi.DTOs;
using TaskTrackerApi.Models;

namespace TaskTrackerApi.Controllers;

/// <summary>CRUD-операции над комментариями к задачам.</summary>
[ApiController]
[Route("api/comments")]
[Produces("application/json")]
public class CommentsController : ControllerBase
{
    private readonly AppDbContext _db;

    public CommentsController(AppDbContext db) => _db = db;

    /// <summary>
    /// GET api/comments — все комментарии с данными задачи и проекта (объединение трёх сущностей).
    /// </summary>
    /// <param name="taskId">Фильтр по задаче.</param>
    /// <param name="projectId">Фильтр по проекту.</param>
    /// <param name="author">Фильтр по автору (частичное совпадение).</param>
    [HttpGet]
    [ProducesResponseType(typeof(IEnumerable<CommentResponse>), StatusCodes.Status200OK)]
    public async Task<ActionResult<IEnumerable<CommentResponse>>> GetAll(
        [FromQuery] int? taskId,
        [FromQuery] int? projectId,
        [FromQuery] string? author)
    {
        var comments = await _db.Comments
            .Include(c => c.Task)
                .ThenInclude(t => t!.Project)
            .ToListAsync();

        // LINQ: Where + Select
        var result = comments.AsQueryable()
            .Where(c => taskId == null || c.ProjectTaskId == taskId)
            .Where(c => projectId == null || c.Task!.ProjectId == projectId)
            .Where(c => string.IsNullOrWhiteSpace(author)
                        || c.Author.Contains(author, StringComparison.OrdinalIgnoreCase))
            .OrderByDescending(c => c.CreatedAtUtc)
            .Select(c => c.ToResponse())
            .ToList();

        return Ok(result);
    }

    /// <summary>GET api/comments/{id} — комментарий по идентификатору.</summary>
    [HttpGet("{id:int}")]
    [ProducesResponseType(typeof(CommentResponse), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<CommentResponse>> GetById(int id)
    {
        var comment = await _db.Comments
            .Include(c => c.Task)
                .ThenInclude(t => t!.Project)
            .FirstOrDefaultAsync(c => c.Id == id);

        if (comment is null)
            return NotFound(new { message = $"Комментарий с Id={id} не найден." });

        return Ok(comment.ToResponse());
    }

    /// <summary>POST api/comments — создать комментарий (taskId — в теле запроса).</summary>
    [HttpPost]
    [ProducesResponseType(typeof(CommentResponse), StatusCodes.Status201Created)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public async Task<ActionResult<CommentResponse>> Create(
        [FromQuery] int taskId, [FromBody] CommentRequest request)
    {
        var task = await _db.Tasks
            .Include(t => t.Project)
            .Include(t => t.Comments)
            .FirstOrDefaultAsync(t => t.Id == taskId);

        if (task is null)
            return NotFound(new { message = $"Задача с Id={taskId} не найдена." });

        var comment = task.AddComment(request.Author, request.Text);
        comment.ProjectTaskId = task.Id;
        _db.Comments.Add(comment);
        await _db.SaveChangesAsync();

        comment.Task = task;
        return CreatedAtAction(nameof(GetById), new { id = comment.Id }, comment.ToResponse());
    }

    /// <summary>
    /// PUT api/comments/{id} — редактирование комментария.
    /// Бизнес-правила модели Comment: правит только автор и только в течение 24 часов.
    /// </summary>
    [HttpPut("{id:int}")]
    [ProducesResponseType(typeof(CommentResponse), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public async Task<ActionResult<CommentResponse>> Update(int id, [FromBody] UpdateCommentRequest request)
    {
        var comment = await _db.Comments
            .Include(c => c.Task)
                .ThenInclude(t => t!.Project)
            .FirstOrDefaultAsync(c => c.Id == id);

        if (comment is null)
            return NotFound(new { message = $"Комментарий с Id={id} не найден." });

        comment.Edit(request.Text, request.Editor);
        await _db.SaveChangesAsync();
        return Ok(comment.ToResponse());
    }

    /// <summary>DELETE api/comments/{id} — удаление комментария.</summary>
    [HttpDelete("{id:int}")]
    [ProducesResponseType(StatusCodes.Status204NoContent)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> Delete(int id)
    {
        var comment = await _db.Comments
            .Include(c => c.Task)
            .FirstOrDefaultAsync(c => c.Id == id);

        if (comment is null)
            return NotFound(new { message = $"Комментарий с Id={id} не найден." });

        comment.Task?.RemoveComment(comment);
        _db.Comments.Remove(comment);
        await _db.SaveChangesAsync();

        return NoContent();
    }
}
