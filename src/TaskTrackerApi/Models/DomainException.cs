namespace TaskTrackerApi.Models;

/// <summary>
/// Исключение предметной области: нарушение бизнес-правила.
/// Перехватывается глобальным обработчиком и возвращается клиенту как 400 Bad Request.
/// </summary>
public class DomainException : Exception
{
    public DomainException(string message) : base(message)
    {
    }
}

/// <summary>Общий контракт для сущностей, у которых есть срок выполнения.</summary>
public interface IHasDeadline
{
    DateTime? DeadlineUtc { get; }

    /// <summary>Просрочен ли объект на текущий момент.</summary>
    bool IsOverdue { get; }
}
