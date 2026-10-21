using System.ComponentModel.DataAnnotations;

namespace TaskTrackerApi.Models;

/// <summary>
/// Задача проекта. Содержит бизнес-логику жизненного цикла (канбан),
/// учёт трудозатрат, планирование срока и работу с комментариями.
/// Имя класса — ProjectTask, чтобы не конфликтовать с System.Threading.Tasks.Task.
/// </summary>
public class ProjectTask : IHasDeadline
{
    public int Id { get; set; }

    public int ProjectId { get; set; }

    /// <summary>Проект-владелец задачи (навигационное свойство).</summary>
    public Project? Project { get; set; }

    [Required]
    [StringLength(150, MinimumLength = 3)]
    public string Title { get; set; } = string.Empty;

    [StringLength(4000)]
    public string Description { get; set; } = string.Empty;

    public TaskStatus Status { get; set; } = TaskStatus.Backlog;

    public Priority Priority { get; set; } = Priority.Medium;

    /// <summary>Исполнитель. Может быть не назначен, пока задача в бэклоге.</summary>
    [StringLength(100)]
    public string? Assignee { get; set; }

    public DateTime CreatedAtUtc { get; set; } = DateTime.UtcNow;

    public DateTime UpdatedAtUtc { get; set; } = DateTime.UtcNow;

    public DateTime? DueDateUtc { get; set; }

    /// <summary>Оценка трудоёмкости, часы.</summary>
    public double? EstimatedHours { get; set; }

    /// <summary>Фактически затрачено, часы.</summary>
    public double SpentHours { get; set; }

    /// <summary>Комментарии к задаче (навигационное свойство).</summary>
    public ICollection<Comment> Comments { get; set; } = new List<Comment>();

    // ---------------- Бизнес-логика ----------------

    /// <summary>Задача закрыта, если выполнена или отменена.</summary>
    public bool IsClosed => Status is TaskStatus.Done or TaskStatus.Cancelled;

    /// <summary>Просрочена: срок задан, наступил и задача ещё не закрыта.</summary>
    public bool IsOverdue =>
        DueDateUtc.HasValue &&
        DueDateUtc.Value < DateTime.UtcNow &&
        !IsClosed;

    /// <summary>Явная реализация IHasDeadline: сроком задачи является DueDateUtc.</summary>
    DateTime? IHasDeadline.DeadlineUtc => DueDateUtc;

    /// <summary>Условный прогресс задачи в процентах (для отчётов и дашбордов).</summary>
    public int Progress => Status switch
    {
        TaskStatus.Done => 100,
        TaskStatus.Review => 90,
        TaskStatus.InProgress => 50,
        TaskStatus.ToDo => 10,
        _ => 0
    };

    /// <summary>Сколько дней осталось до срока (отрицательное значение — просрочка).</summary>
    public int? DaysLeft =>
        DueDateUtc.HasValue ? (int)Math.Ceiling((DueDateUtc.Value - DateTime.UtcNow).TotalDays) : null;

    public static ProjectTask Create(string title, Priority priority, string? assignee, DateTime? dueDateUtc)
    {
        if (string.IsNullOrWhiteSpace(title) || title.Trim().Length < 3)
            throw new DomainException("Название задачи должно содержать не менее 3 символов.");

        return new ProjectTask
        {
            Title = title.Trim(),
            Priority = priority,
            Assignee = string.IsNullOrWhiteSpace(assignee) ? null : assignee.Trim(),
            DueDateUtc = dueDateUtc,
            Status = TaskStatus.Backlog,
            CreatedAtUtc = DateTime.UtcNow,
            UpdatedAtUtc = DateTime.UtcNow
        };
    }

    public void Rename(string newTitle)
    {
        if (string.IsNullOrWhiteSpace(newTitle) || newTitle.Trim().Length < 3)
            throw new DomainException("Название задачи должно содержать не менее 3 символов.");
        if (IsClosed)
            throw new DomainException($"Задача '{Title}' закрыта ({Status}) — переименование запрещено.");

        Touch(newTitle.Trim());
    }

    public void ChangeDescription(string newDescription) =>
        Touch(newDescription?.Trim() ?? string.Empty, descriptionChanged: true);

    /// <summary>Назначение исполнителя.</summary>
    public void Assign(string assignee)
    {
        if (string.IsNullOrWhiteSpace(assignee))
            throw new DomainException("Имя исполнителя не может быть пустым.");
        if (Status == TaskStatus.Cancelled)
            throw new DomainException($"Нельзя назначить исполнителя на отменённую задачу '{Title}'.");

        Assignee = assignee.Trim();
        Touch();
    }

    /// <summary>Снятие исполнителя. Задачу в работе нельзя оставить без исполнителя.</summary>
    public void Unassign()
    {
        if (Status == TaskStatus.InProgress || Status == TaskStatus.Review)
            throw new DomainException(
                $"Задача '{Title}' в статусе {Status}: сначала верните её в ToDo или Backlog.");

        Assignee = null;
        Touch();
    }

    /// <summary>
    /// Перевод задачи в работу. Бизнес-правило: обязателен исполнитель.
    /// </summary>
    public void Start()
    {
        if (string.IsNullOrWhiteSpace(Assignee))
            throw new DomainException($"Нельзя начать задачу '{Title}' без исполнителя.");
        if (IsClosed)
            throw new DomainException($"Задача '{Title}' закрыта ({Status}) — сначала переоткройте её.");

        ChangeStatus(TaskStatus.InProgress);
    }

    /// <summary>
    /// Смена статуса с проверкой допустимых переходов.
    /// Backlog → ToDo → InProgress → Review → Done; любую незакрытую задачу можно отменить.
    /// </summary>
    public void ChangeStatus(TaskStatus newStatus)
    {
        if (newStatus == Status)
            throw new DomainException($"Задача '{Title}' уже находится в статусе {Status}.");

        if (Status is TaskStatus.Done or TaskStatus.Cancelled && newStatus != TaskStatus.ToDo)
            throw new DomainException(
                $"Из статуса {Status} задачу '{Title}' можно только переоткрыть (ToDo).");

        if (newStatus == TaskStatus.InProgress && string.IsNullOrWhiteSpace(Assignee))
            throw new DomainException($"Нельзя перевести задачу '{Title}' в работу без исполнителя.");

        if (newStatus == TaskStatus.Done)
        {
            if (string.IsNullOrWhiteSpace(Assignee))
                throw new DomainException($"Нельзя закрыть задачу '{Title}' без исполнителя.");
            if (Status != TaskStatus.Review)
                throw new DomainException(
                    $"Задачу '{Title}' можно закрыть только из статуса Review (текущий: {Status}).");
        }

        Status = newStatus;
        Touch();
    }

    /// <summary>Переоткрытие закрытой задачи.</summary>
    public void Reopen()
    {
        if (!IsClosed)
            throw new DomainException($"Задача '{Title}' не закрыта (текущий статус: {Status}).");

        Status = TaskStatus.ToDo;
        Touch();
    }

    /// <summary>
    /// Перенос срока задачи. Бизнес-правила: срок не в прошлом; срок не позже срока проекта.
    /// </summary>
    public void Reschedule(DateTime newDueDate, string? reason = null)
    {
        if (IsClosed)
            throw new DomainException($"Срок закрытой задачи '{Title}' ({Status}) менять нельзя.");
        if (newDueDate < DateTime.UtcNow)
            throw new DomainException("Новый срок задачи не может быть в прошлом.");
        if (Project?.DeadlineUtc is { } projectDeadline && newDueDate > projectDeadline)
            throw new DomainException(
                $"Новый срок задачи ({newDueDate:yyyy-MM-dd}) позже срока проекта ({projectDeadline:yyyy-MM-dd}).");

        DueDateUtc = newDueDate;
        Touch(reason is null ? null : $"Срок перенесён: {reason}");
    }

    /// <summary>Установка оценки трудоёмкости (0.5..1000 часов).</summary>
    public void SetEstimate(double hours)
    {
        if (hours is <= 0 or > 1000)
            throw new DomainException("Оценка трудоёмкости должна быть в диапазоне от 0.5 до 1000 часов.");
        if (IsClosed)
            throw new DomainException($"Оценку закрытой задачи '{Title}' менять нельзя.");

        EstimatedHours = Math.Round(hours, 1);
        Touch();
    }

    /// <summary>
    /// Списание трудозатрат. Бизнес-правила: шаг 0.25..24 часа;
    /// суммарно не более оценки (если оценка задана) и не более 1000 часов.
    /// </summary>
    public void LogWork(double hours, string? note = null)
    {
        if (hours is < 0.25 or > 24)
            throw new DomainException("За один раз можно списать от 0.25 до 24 часов.");
        if (Status == TaskStatus.Cancelled)
            throw new DomainException($"Нельзя списывать время на отменённую задачу '{Title}'.");
        if (Status == TaskStatus.Done)
            throw new DomainException(
                $"Задача '{Title}' закрыта — списать время нельзя. Сначала переоткройте задачу (Reopen).");

        var newTotal = Math.Round(SpentHours + hours, 2);
        if (newTotal > 1000)
            throw new DomainException("Суммарные трудозатраты по задаче не могут превышать 1000 часов.");
        if (EstimatedHours.HasValue && newTotal > EstimatedHours.Value * 2)
            throw new DomainException(
                $"Перерасход по задаче '{Title}': списано {newTotal} ч при оценке {EstimatedHours} ч (лимит — двойная оценка).");

        SpentHours = newTotal;
        Touch(note is null ? null : $"Списано {hours} ч: {note}");
    }

    /// <summary>Добавление комментария с валидацией автора и текста.</summary>
    public Comment AddComment(string author, string text)
    {
        if (Status == TaskStatus.Cancelled)
            throw new DomainException($"Нельзя комментировать отменённую задачу '{Title}'.");

        var comment = Comment.Create(author, text);
        Comments.Add(comment);
        Touch();
        return comment;
    }

    /// <summary>Удаление комментария из задачи.</summary>
    public void RemoveComment(Comment comment)
    {
        Comments.Remove(comment);
        Touch();
    }

    /// <summary>Отставание от оценки в часах (положительное — перерасход).</summary>
    public double? EstimateDeviation =>
        EstimatedHours.HasValue ? Math.Round(SpentHours - EstimatedHours.Value, 2) : null;

    private void Touch(string? note = null, bool descriptionChanged = false)
    {
        if (descriptionChanged)
            Description = note ?? string.Empty;

        UpdatedAtUtc = DateTime.UtcNow;
    }
}
