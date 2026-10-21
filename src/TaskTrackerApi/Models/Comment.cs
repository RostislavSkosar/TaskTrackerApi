using System.ComponentModel.DataAnnotations;
using System.Text.RegularExpressions;

namespace TaskTrackerApi.Models;

/// <summary>
/// Комментарий к задаче. Бизнес-логика: валидация при создании,
/// редактирование только автором и только в течение 24 часов, поиск упоминаний.
/// </summary>
public class Comment
{
    /// <summary>Окно, в течение которого автору разрешено редактировать свой комментарий.</summary>
    public static readonly TimeSpan EditWindow = TimeSpan.FromHours(24);

    public int Id { get; set; }

    public int ProjectTaskId { get; set; }

    /// <summary>Задача, к которой оставлен комментарий (навигационное свойство).</summary>
    public ProjectTask? Task { get; set; }

    [Required]
    [StringLength(100, MinimumLength = 2)]
    public string Author { get; set; } = string.Empty;

    [Required]
    [StringLength(2000, MinimumLength = 3)]
    public string Text { get; set; } = string.Empty;

    public DateTime CreatedAtUtc { get; set; } = DateTime.UtcNow;

    public DateTime? EditedAtUtc { get; set; }

    // ---------------- Бизнес-логика ----------------

    public bool IsEdited => EditedAtUtc.HasValue;

    /// <summary>Можно ли ещё редактировать комментарий (не прошло окно редактирования).</summary>
    public bool CanBeEdited => DateTime.UtcNow - CreatedAtUtc <= EditWindow;

    public static Comment Create(string author, string text)
    {
        if (string.IsNullOrWhiteSpace(author) || author.Trim().Length < 2)
            throw new DomainException("Имя автора комментария должно содержать не менее 2 символов.");
        if (string.IsNullOrWhiteSpace(text) || text.Trim().Length < 3)
            throw new DomainException("Текст комментария должен содержать не менее 3 символов.");
        if (text.Trim().Length > 2000)
            throw new DomainException("Текст комментария не должен превышать 2000 символов.");

        return new Comment
        {
            Author = author.Trim(),
            Text = text.Trim(),
            CreatedAtUtc = DateTime.UtcNow
        };
    }

    /// <summary>
    /// Редактирование комментария.
    /// Бизнес-правила: править может только автор и только пока не истекло окно редактирования.
    /// </summary>
    public void Edit(string newText, string editor)
    {
        if (!string.Equals(editor?.Trim(), Author, StringComparison.OrdinalIgnoreCase))
            throw new DomainException(
                $"Комментарий может редактировать только его автор ({Author}).");

        if (!CanBeEdited)
            throw new DomainException(
                $"Окно редактирования комментария ({EditWindow.TotalHours:0} ч) истекло — текст изменить нельзя.");

        if (string.IsNullOrWhiteSpace(newText) || newText.Trim().Length < 3)
            throw new DomainException("Текст комментария должен содержать не менее 3 символов.");

        Text = newText.Trim();
        EditedAtUtc = DateTime.UtcNow;
    }

    /// <summary>Краткая выдержка текста (для списков и отчётов).</summary>
    public string Excerpt(int max = 60) =>
        Text.Length <= max ? Text : string.Concat(Text.AsSpan(0, max), "...");

    /// <summary>Пользователи, упомянутые в комментарии через @ (без дублей).</summary>
    public IReadOnlyList<string> GetMentionedUsers() =>
        Regex.Matches(Text, @"@([A-Za-zА-Яа-я0-9_.\-]+)")
            .Select(m => m.Groups[1].Value)
            .Distinct(StringComparer.OrdinalIgnoreCase)
            .ToList();
}
