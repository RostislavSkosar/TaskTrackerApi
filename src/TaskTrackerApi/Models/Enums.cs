namespace TaskTrackerApi.Models;

/// <summary>Приоритет проекта или задачи.</summary>
public enum Priority
{
    Low = 0,
    Medium = 1,
    High = 2,
    Critical = 3
}

/// <summary>Жизненный цикл проекта.</summary>
public enum ProjectStatus
{
    Active = 0,
    OnHold = 1,
    Completed = 2,
    Archived = 3
}

/// <summary>Жизненный цикл задачи (канбан-доска).</summary>
public enum TaskStatus
{
    Backlog = 0,
    ToDo = 1,
    InProgress = 2,
    Review = 3,
    Done = 4,
    Cancelled = 5
}
