using System.ComponentModel.DataAnnotations;

namespace TaskTrackerApi.Models;

/// <summary>
/// Проект — контейнер задач. Класс содержит не только данные,
/// но и бизнес-логику: валидацию, управление жизненным циклом,
/// контроль состава задач и расчёт статистики.
/// </summary>
public class Project : IHasDeadline
{
    public int Id { get; set; }

    /// <summary>Название проекта (3..100 символов).</summary>
    [Required]
    [StringLength(100, MinimumLength = 3)]
    public string Name { get; set; } = string.Empty;

    /// <summary>Короткий уникальный код проекта (2..8 символов, хранится в верхнем регистре).</summary>
    [Required]
    [StringLength(8, MinimumLength = 2)]
    public string Code { get; set; } = string.Empty;

    [StringLength(2000)]
    public string Description { get; set; } = string.Empty;

    public ProjectStatus Status { get; set; } = ProjectStatus.Active;

    public Priority Priority { get; set; } = Priority.Medium;

    public DateTime CreatedAtUtc { get; set; } = DateTime.UtcNow;

    /// <summary>Крайний срок проекта. Может быть не задан.</summary>
    public DateTime? DeadlineUtc { get; set; }

    /// <summary>Задачи проекта (навигационное свойство).</summary>
    public ICollection<ProjectTask> Tasks { get; set; } = new List<ProjectTask>();

    // ---------------- Бизнес-логика ----------------

    /// <summary>Проект считается просроченным, если срок задан, уже наступил и проект не закрыт.</summary>
    public bool IsOverdue =>
        DeadlineUtc.HasValue &&
        DeadlineUtc.Value < DateTime.UtcNow &&
        Status is not (ProjectStatus.Completed or ProjectStatus.Archived);

    /// <summary>Проект закрыт, если завершён или архивирован.</summary>
    public bool IsClosed => Status is ProjectStatus.Completed or ProjectStatus.Archived;

    /// <summary>
    /// Создание проекта с проверкой кода и срока.
    /// </summary>
    public static Project Create(string name, string code, string description,
        Priority priority, DateTime? deadlineUtc)
    {
        if (string.IsNullOrWhiteSpace(name) || name.Trim().Length < 3)
            throw new DomainException("Название проекта должно содержать не менее 3 символов.");

        var project = new Project
        {
            Name = name.Trim(),
            Code = NormalizeCode(code),
            Description = description?.Trim() ?? string.Empty,
            Priority = priority,
            CreatedAtUtc = DateTime.UtcNow
        };

        project.SetDeadline(deadlineUtc);
        return project;
    }

    /// <summary>Переименование проекта.</summary>
    public void Rename(string newName)
    {
        if (string.IsNullOrWhiteSpace(newName) || newName.Trim().Length < 3)
            throw new DomainException("Название проекта должно содержать не менее 3 символов.");
        if (IsClosed)
            throw new DomainException($"Проект '{Name}' закрыт ({Status}) — переименование запрещено.");

        Name = newName.Trim();
    }

    /// <summary>Смена кода проекта. Код приводится к верхнему регистру.</summary>
    public void ChangeCode(string newCode)
    {
        Code = NormalizeCode(newCode);
    }

    public void ChangeDescription(string newDescription) =>
        Description = newDescription?.Trim() ?? string.Empty;

    /// <summary>
    /// Установка/изменение срока проекта.
    /// Бизнес-правило: срок не может быть раньше даты создания и раньше максимального срока задач.
    /// </summary>
    public void SetDeadline(DateTime? deadlineUtc)
    {
        if (IsClosed)
            throw new DomainException($"Проект '{Name}' закрыт ({Status}) — срок изменять нельзя.");

        if (deadlineUtc.HasValue)
        {
            if (deadlineUtc.Value < CreatedAtUtc)
                throw new DomainException("Срок проекта не может быть раньше даты его создания.");

            var maxTaskDue = Tasks
                .Where(t => t.DueDateUtc.HasValue && t.Status != TaskStatus.Cancelled)
                .Select(t => t.DueDateUtc!.Value)
                .DefaultIfEmpty(DateTime.MinValue)
                .Max();

            if (deadlineUtc.Value < maxTaskDue)
                throw new DomainException(
                    $"Срок проекта не может быть раньше срока самой поздней активной задачи ({maxTaskDue:yyyy-MM-dd}).");
        }

        DeadlineUtc = deadlineUtc;
    }

    /// <summary>
    /// Добавление задачи в проект.
    /// Бизнес-правила: проект не закрыт; название задачи непустое;
    /// в рамках проекта нет задачи с таким же названием; срок задачи не позже срока проекта.
    /// </summary>
    public ProjectTask AddTask(string title, Priority priority, string? assignee, DateTime? dueDateUtc)
    {
        if (IsClosed)
            throw new DomainException($"В закрытый проект '{Name}' ({Status}) нельзя добавлять задачи.");

        if (string.IsNullOrWhiteSpace(title))
            throw new DomainException("Название задачи не может быть пустым.");

        var normalized = title.Trim();
        if (Tasks.Any(t => string.Equals(t.Title, normalized, StringComparison.OrdinalIgnoreCase)))
            throw new DomainException($"Задача '{normalized}' уже есть в проекте '{Name}'.");

        if (dueDateUtc.HasValue && DeadlineUtc.HasValue && dueDateUtc.Value > DeadlineUtc.Value)
            throw new DomainException(
                $"Срок задачи ({dueDateUtc:yyyy-MM-dd}) не может быть позже срока проекта ({DeadlineUtc:yyyy-MM-dd}).");

        var task = ProjectTask.Create(normalized, priority, assignee, dueDateUtc);
        task.ProjectId = Id;
        Tasks.Add(task);
        return task;
    }

    /// <summary>
    /// Удаление задачи из проекта.
    /// Бизнес-правило: нельзя удалить задачу, которая в работе.
    /// </summary>
    public void RemoveTask(ProjectTask task)
    {
        if (task.Status == TaskStatus.InProgress)
            throw new DomainException(
                $"Задачу '{task.Title}' нельзя удалить: она находится в работе. Сначала снимите исполнителя или отмените задачу.");

        Tasks.Remove(task);
    }

    /// <summary>Перевод проекта на паузу.</summary>
    public void Hold(string reason)
    {
        if (IsClosed)
            throw new DomainException($"Проект '{Name}' закрыт ({Status}) — поставить на паузу нельзя.");
        if (string.IsNullOrWhiteSpace(reason))
            throw new DomainException("Причина приостановки проекта обязательна.");

        Status = ProjectStatus.OnHold;
    }

    /// <summary>Снятие проекта с паузы.</summary>
    public void Resume()
    {
        if (Status != ProjectStatus.OnHold)
            throw new DomainException($"Проект '{Name}' не на паузе (текущий статус: {Status}).");

        Status = ProjectStatus.Active;
    }

    /// <summary>
    /// Завершение проекта. Бизнес-правило: все задачи должны быть закрыты (Done/Cancelled).
    /// </summary>
    public void Complete()
    {
        if (Status == ProjectStatus.Archived)
            throw new DomainException($"Проект '{Name}' архивирован — завершение невозможно.");

        var openTasks = Tasks
            .Where(t => !t.IsClosed)
            .Select(t => t.Title)
            .ToList();

        if (openTasks.Count > 0)
            throw new DomainException(
                $"Проект '{Name}' нельзя завершить: открыто задач — {openTasks.Count} ({string.Join(", ", openTasks.Take(3))}).");

        Status = ProjectStatus.Completed;
    }

    /// <summary>
    /// Архивация проекта. Бизнес-правило: архивировать можно только завершённый проект
    /// без просроченных задач.
    /// </summary>
    public void Archive()
    {
        if (Status != ProjectStatus.Completed)
            throw new DomainException($"Архивировать можно только завершённый проект. Текущий статус '{Name}': {Status}.");

        var overdue = Tasks.Count(t => t.IsOverdue);
        if (overdue > 0)
            throw new DomainException($"В проекте '{Name}' осталось просроченных задач: {overdue}.");

        Status = ProjectStatus.Archived;
    }

    // ---------------- Расчётные показатели ----------------

    public int TotalTasks => Tasks.Count;

    public int CompletedTasks => Tasks.Count(t => t.Status == TaskStatus.Done);

    public int CancelledTasks => Tasks.Count(t => t.Status == TaskStatus.Cancelled);

    public int OverdueTasks => Tasks.Count(t => t.IsOverdue);

    /// <summary>Процент выполнения проекта (завершённые задачи от общего числа).</summary>
    public double CompletionPercent =>
        TotalTasks == 0 ? 0d : Math.Round(100d * CompletedTasks / TotalTasks, 1);

    /// <summary>Суммарные трудозатраты по всем задачам проекта, часы.</summary>
    public double TotalSpentHours => Math.Round(Tasks.Sum(t => t.SpentHours), 1);

    /// <summary>Средняя оценка трудоёмкости задач проекта, часы.</summary>
    public double AverageEstimateHours
    {
        get
        {
            var estimated = Tasks.Where(t => t.EstimatedHours.HasValue).Select(t => t.EstimatedHours!.Value).ToList();
            return estimated.Count == 0 ? 0d : Math.Round(estimated.Average(), 1);
        }
    }

    /// <summary>Разбивка задач проекта по статусам (для отчётов и диаграмм).</summary>
    public Dictionary<string, int> GetTaskBreakdownByStatus() =>
        Tasks
            .GroupBy(t => t.Status)
            .ToDictionary(g => g.Key.ToString(), g => g.Count());

    /// <summary>Топ-N самых «обсуждаемых» задач проекта (по числу комментариев).</summary>
    public IEnumerable<ProjectTask> GetMostDiscussedTasks(int take = 3) =>
        Tasks
            .OrderByDescending(t => t.Comments.Count)
            .ThenByDescending(t => t.Priority)
            .Take(take);

    private static string NormalizeCode(string code)
    {
        if (string.IsNullOrWhiteSpace(code))
            throw new DomainException("Код проекта обязателен.");

        var normalized = code.Trim().ToUpperInvariant();
        if (normalized.Length < 2 || normalized.Length > 8)
            throw new DomainException("Код проекта должен содержать от 2 до 8 символов.");
        if (!normalized.All(char.IsLetterOrDigit))
            throw new DomainException("Код проекта может содержать только буквы и цифры.");

        return normalized;
    }
}
