using System.ComponentModel.DataAnnotations;
using TaskTrackerApi.Models;

namespace TaskTrackerApi.DTOs;

// ============================== ПРОЕКТЫ ==============================

public record ProjectRequest(
    [Required, StringLength(100, MinimumLength = 3)] string Name,
    [Required, StringLength(8, MinimumLength = 2)] string Code,
    string? Description,
    Priority Priority,
    DateTime? DeadlineUtc);

public record UpdateProjectRequest(
    [StringLength(100, MinimumLength = 3)] string? Name,
    [StringLength(8, MinimumLength = 2)] string? Code,
    string? Description,
    Priority? Priority);

public record ProjectResponse(
    int Id,
    string Name,
    string Code,
    string Description,
    ProjectStatus Status,
    Priority Priority,
    DateTime CreatedAtUtc,
    DateTime? DeadlineUtc,
    bool IsOverdue,
    int TotalTasks,
    int CompletedTasks,
    double CompletionPercent,
    double TotalSpentHours);

// ============================== ЗАДАЧИ ==============================

public record TaskRequest(
    [Required, StringLength(150, MinimumLength = 3)] string Title,
    string? Description,
    Priority Priority,
    string? Assignee,
    DateTime? DueDateUtc);

public record UpdateTaskRequest(
    [StringLength(150, MinimumLength = 3)] string? Title,
    string? Description,
    Priority? Priority,
    string? Assignee);

public record ChangeStatusRequest(
    [Required] Models.TaskStatus Status);

public record LogWorkRequest(
    [Range(0.25, 24)] double Hours,
    string? Note);

public record EstimateRequest(
    [Range(0.5, 1000)] double Hours);

public record RescheduleRequest(
    [Required] DateTime DueDateUtc,
    string? Reason);

public record TaskResponse(
    int Id,
    int ProjectId,
    string ProjectName,
    string ProjectCode,
    string Title,
    string Description,
    Models.TaskStatus Status,
    Priority Priority,
    string? Assignee,
    DateTime CreatedAtUtc,
    DateTime UpdatedAtUtc,
    DateTime? DueDateUtc,
    bool IsOverdue,
    int Progress,
    int? DaysLeft,
    double? EstimatedHours,
    double SpentHours,
    double? EstimateDeviation,
    int CommentsCount);

// ============================== КОММЕНТАРИИ ==============================

public record CommentRequest(
    [Required, StringLength(100, MinimumLength = 2)] string Author,
    [Required, StringLength(2000, MinimumLength = 3)] string Text);

public record UpdateCommentRequest(
    [Required, StringLength(100, MinimumLength = 2)] string Editor,
    [Required, StringLength(2000, MinimumLength = 3)] string Text);

public record CommentResponse(
    int Id,
    int ProjectTaskId,
    string TaskTitle,
    string ProjectCode,
    string Author,
    string Text,
    DateTime CreatedAtUtc,
    DateTime? EditedAtUtc,
    IReadOnlyList<string> MentionedUsers);

// ============ РЕЗУЛЬТАТЫ ЗАПРОСОВ НА ОБЪЕДИНЕНИЕ ДАННЫХ ============

/// <summary>Статистика по проекту: данные проекта + агрегаты по его задачам.</summary>
public record ProjectStatisticsResponse(
    int ProjectId,
    string ProjectCode,
    string ProjectName,
    ProjectStatus Status,
    int TotalTasks,
    int CompletedTasks,
    int OverdueTasks,
    double CompletionPercent,
    double TotalSpentHours,
    double? AverageEstimateHours,
    int TotalComments,
    IReadOnlyList<StatusCount> ByStatus);

public record StatusCount(string Status, int Count);

/// <summary>Просроченная задача вместе с данными её проекта и числом комментариев.</summary>
public record OverdueTaskResponse(
    int TaskId,
    string Title,
    string? Assignee,
    Models.TaskStatus Status,
    Priority Priority,
    DateTime DueDateUtc,
    int DaysOverdue,
    string ProjectCode,
    string ProjectName,
    int CommentsCount);

/// <summary>Сводка по исполнителю: задачи из разных проектов + трудозатраты.</summary>
public record AssigneeSummaryResponse(
    string Assignee,
    int TotalAssigned,
    int Completed,
    double CompletionPercent,
    int Overdue,
    double TotalSpentHours,
    IReadOnlyList<string> Projects);

/// <summary>Активность обсуждения задач: задача + проект + статистика комментариев.</summary>
public record TaskDiscussionResponse(
    int TaskId,
    string Title,
    string ProjectCode,
    string ProjectName,
    Models.TaskStatus Status,
    int CommentsCount,
    DateTime? LastCommentUtc,
    IReadOnlyList<string> Participants);

/// <summary>Полная карточка проекта: проект + его задачи + комментарии к ним.</summary>
public record ProjectDetailsResponse(
    int Id,
    string Name,
    string Code,
    ProjectStatus Status,
    Priority Priority,
    DateTime? DeadlineUtc,
    bool IsOverdue,
    double CompletionPercent,
    IReadOnlyList<TaskWithComments> Tasks);

public record TaskWithComments(
    int Id,
    string Title,
    Models.TaskStatus Status,
    Priority Priority,
    string? Assignee,
    DateTime? DueDateUtc,
    bool IsOverdue,
    double SpentHours,
    IReadOnlyList<CommentResponse> Comments);

// ============================== МАППИНГ ==============================

public static class Mapping
{
    public static ProjectResponse ToResponse(this Project p) => new(
        p.Id, p.Name, p.Code, p.Description, p.Status, p.Priority,
        p.CreatedAtUtc, p.DeadlineUtc, p.IsOverdue,
        p.TotalTasks, p.CompletedTasks, p.CompletionPercent, p.TotalSpentHours);

    public static TaskResponse ToResponse(this Models.ProjectTask t) => new(
        t.Id, t.ProjectId, t.Project?.Name ?? string.Empty, t.Project?.Code ?? string.Empty,
        t.Title, t.Description, t.Status, t.Priority, t.Assignee,
        t.CreatedAtUtc, t.UpdatedAtUtc, t.DueDateUtc, t.IsOverdue, t.Progress, t.DaysLeft,
        t.EstimatedHours, t.SpentHours, t.EstimateDeviation, t.Comments.Count);

    public static CommentResponse ToResponse(this Comment c) => new(
        c.Id, c.ProjectTaskId, c.Task?.Title ?? string.Empty, c.Task?.Project?.Code ?? string.Empty,
        c.Author, c.Text, c.CreatedAtUtc, c.EditedAtUtc, c.GetMentionedUsers());
}
