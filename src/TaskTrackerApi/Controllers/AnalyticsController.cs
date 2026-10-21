using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using TaskTrackerApi.Data;
using TaskTrackerApi.DTOs;
using TaskTrackerApi.Models;

namespace TaskTrackerApi.Controllers;

/// <summary>
/// Запросы на объединение данных из разных классов модели (проект + задача + комментарий).
/// Все выборки построены на LINQ: Where, Select, Join, GroupBy, OrderBy.
/// </summary>
[ApiController]
[Route("api/analytics")]
[Produces("application/json")]
public class AnalyticsController : ControllerBase
{
    private readonly AppDbContext _db;

    public AnalyticsController(AppDbContext db) => _db = db;

    /// <summary>
    /// ЗАПРОС 1. GET api/analytics/projects-statistics — статистика по каждому проекту:
    /// данные проекта объединяются с агрегатами по его задачам и комментариям.
    /// </summary>
    /// <param name="onlyActive">Показывать только активные проекты.</param>
    [HttpGet("projects-statistics")]
    [ProducesResponseType(typeof(IEnumerable<ProjectStatisticsResponse>), StatusCodes.Status200OK)]
    public async Task<ActionResult<IEnumerable<ProjectStatisticsResponse>>> GetProjectsStatistics(
        [FromQuery] bool onlyActive = false)
    {
        var projects = await _db.Projects
            .Include(p => p.Tasks)
                .ThenInclude(t => t.Comments)
            .ToListAsync();

        var statistics = projects.AsQueryable()
            .Where(p => !onlyActive || p.Status == ProjectStatus.Active)
            .OrderByDescending(p => p.CompletionPercent)
            .ThenBy(p => p.Name)
            .Select(p => new ProjectStatisticsResponse(
                p.Id,
                p.Code,
                p.Name,
                p.Status,
                p.Tasks.Count,
                p.Tasks.Count(t => t.Status == Models.TaskStatus.Done),
                p.Tasks.Count(t => t.IsOverdue),
                p.Tasks.Count == 0 ? 0 : Math.Round(100.0 * p.Tasks.Count(t => t.Status == Models.TaskStatus.Done) / p.Tasks.Count, 1),
                Math.Round(p.Tasks.Sum(t => t.SpentHours), 1),
                p.Tasks.Where(t => t.EstimatedHours.HasValue).Any()
                    ? Math.Round(p.Tasks.Where(t => t.EstimatedHours.HasValue).Average(t => t.EstimatedHours!.Value), 1)
                    : (double?)null,
                p.Tasks.SelectMany(t => t.Comments).Count(),
                p.Tasks
                    .GroupBy(t => t.Status)
                    .Select(g => new StatusCount(g.Key.ToString(), g.Count()))
                    .OrderBy(sc => sc.Status)
                    .ToList()))
            .ToList();

        return Ok(statistics);
    }

    /// <summary>
    /// ЗАПРОС 2. GET api/analytics/overdue-tasks — просроченные задачи вместе с данными
    /// их проектов и количеством комментариев (объединение Project + ProjectTask + Comment).
    /// </summary>
    /// <param name="projectId">Ограничить отчёт одним проектом.</param>
    [HttpGet("overdue-tasks")]
    [ProducesResponseType(typeof(IEnumerable<OverdueTaskResponse>), StatusCodes.Status200OK)]
    public async Task<ActionResult<IEnumerable<OverdueTaskResponse>>> GetOverdueTasks([FromQuery] int? projectId = null)
    {
        var tasks = await _db.Tasks
            .Include(t => t.Project)
            .Include(t => t.Comments)
            .ToListAsync();

        var now = DateTime.UtcNow;

        var overdue = tasks.AsQueryable()
            .Where(t => t.IsOverdue)                                   // бизнес-свойство модели
            .Where(t => projectId == null || t.ProjectId == projectId)
            .OrderByDescending(t => now - t.DueDateUtc!.Value)           // самые «старые» просрочки — первыми
            .Select(t => new OverdueTaskResponse(
                t.Id,
                t.Title,
                t.Assignee,
                t.Status,
                t.Priority,
                t.DueDateUtc!.Value,
                (int)Math.Ceiling((now - t.DueDateUtc!.Value).TotalDays),
                t.Project!.Code,
                t.Project.Name,
                t.Comments.Count))
            .ToList();

        return Ok(overdue);
    }

    /// <summary>
    /// ЗАПРОС 3. GET api/analytics/assignees-summary — сводка по исполнителям:
    /// задачи группируются по исполнителю поверх всех проектов.
    /// </summary>
    /// <param name="minTasks">Показывать исполнителей не менее чем с указанным числом задач.</param>
    [HttpGet("assignees-summary")]
    [ProducesResponseType(typeof(IEnumerable<AssigneeSummaryResponse>), StatusCodes.Status200OK)]
    public async Task<ActionResult<IEnumerable<AssigneeSummaryResponse>>> GetAssigneesSummary(
        [FromQuery] int minTasks = 1)
    {
        var tasks = await _db.Tasks
            .Include(t => t.Project)
            .ToListAsync();

        var summary = tasks.AsQueryable()
            .Where(t => t.Assignee != null && t.Assignee != string.Empty)   // только назначенные задачи
            .GroupBy(t => t.Assignee!)
            .Where(g => g.Count() >= minTasks)
            .OrderByDescending(g => g.Count(t => t.Status == Models.TaskStatus.Done))
            .ThenBy(g => g.Key)
            .Select(g => new AssigneeSummaryResponse(
                g.Key,
                g.Count(),
                g.Count(t => t.Status == Models.TaskStatus.Done),
                Math.Round(100.0 * g.Count(t => t.Status == Models.TaskStatus.Done) / g.Count(), 1),
                g.Count(t => t.IsOverdue),
                Math.Round(g.Sum(t => t.SpentHours), 1),
                g.Select(t => t.Project!.Code).Distinct().OrderBy(code => code).ToList()))
            .ToList();

        return Ok(summary);
    }

    /// <summary>
    /// ЗАПРОС 4. GET api/analytics/task-discussions — самые обсуждаемые задачи:
    /// задача + её проект + статистика комментариев и список участников обсуждения.
    /// </summary>
    /// <param name="take">Сколько задач вернуть (по умолчанию 5).</param>
    /// <param name="status">Фильтр по статусу задачи.</param>
    [HttpGet("task-discussions")]
    [ProducesResponseType(typeof(IEnumerable<TaskDiscussionResponse>), StatusCodes.Status200OK)]
    public async Task<ActionResult<IEnumerable<TaskDiscussionResponse>>> GetTaskDiscussions(
        [FromQuery] int take = 5,
        [FromQuery] Models.TaskStatus? status = null)
    {
        var tasks = await _db.Tasks
            .Include(t => t.Project)
            .Include(t => t.Comments)
            .ToListAsync();

        var discussions = tasks.AsQueryable()
            .Where(t => t.Comments.Count > 0)
            .Where(t => status == null || t.Status == status)
            .OrderByDescending(t => t.Comments.Count)
            .ThenByDescending(t => t.Priority)
            .Take(take)
            .Select(t => new TaskDiscussionResponse(
                t.Id,
                t.Title,
                t.Project!.Code,
                t.Project.Name,
                t.Status,
                t.Comments.Count,
                t.Comments.Max(c => (DateTime?)c.CreatedAtUtc),
                t.Comments.Select(c => c.Author).Distinct().OrderBy(a => a).ToList()))
            .ToList();

        return Ok(discussions);
    }

    /// <summary>
    /// ЗАПРОС 5. GET api/analytics/projects-activity — активность обсуждения проектов:
    /// проект + число комментариев по всем его задачам + участники и дата последней активности.
    /// </summary>
    /// <param name="minComments">Проекты с количеством комментариев не менее указанного.</param>
    [HttpGet("projects-activity")]
    [ProducesResponseType(StatusCodes.Status200OK)]
    public async Task<ActionResult> GetProjectsActivity([FromQuery] int minComments = 1)
    {
        var projects = await _db.Projects
            .Include(p => p.Tasks)
                .ThenInclude(t => t.Comments)
            .ToListAsync();

        var activity = projects.AsQueryable()
            .Select(p => new
            {
                ProjectId = p.Id,
                p.Code,
                p.Name,
                Status = p.Status.ToString(),
                TasksCount = p.Tasks.Count,
                CommentsCount = p.Tasks.SelectMany(t => t.Comments).Count(),
                LastActivityUtc = p.Tasks.SelectMany(t => t.Comments).Max(c => (DateTime?)c.CreatedAtUtc),
                Participants = p.Tasks.SelectMany(t => t.Comments)
                    .Select(c => c.Author)
                    .Distinct()
                    .OrderBy(a => a)
                    .ToList()
            })
            .Where(x => x.CommentsCount >= minComments)
            .OrderByDescending(x => x.LastActivityUtc)
            .ToList();

        return Ok(activity);
    }
}
