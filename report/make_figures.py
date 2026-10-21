"""Генерация иллюстраций к лабораторной работе (диаграмма классов и жизненный цикл задачи)."""
from PIL import Image, ImageDraw, ImageFont

import os as _os
_BASE = _os.path.dirname(_os.path.abspath(__file__))
_CAND = _os.path.join(_BASE, "..", "assets", "fonts")
_TMP = "/tmp/fonts"
_DIR = _CAND if _os.path.isdir(_CAND) else _TMP
F = _os.path.join(_DIR, "DVSans.ttf")
FB = _os.path.join(_DIR, "DVSans-Bold.ttf")
FM = _os.path.join(_DIR, "DVSansMono.ttf")

def font(path, size):
    return ImageFont.truetype(path, size)

# ---------------------------------------------------------------- Диаграмма классов
def class_diagram(out_path):
    W, H = 1700, 1110
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)

    f_title = font(FB, 30)
    f_head = font(FB, 24)
    f_body = font(F, 20)
    f_meth = font(FM, 18)
    f_small = font(F, 17)

    d.text((W / 2, 34), "Модель предметной области «Трекер задач»", font=f_title, fill="black", anchor="mt")

    connectors = []

    def box(x, y, w, title, fields, methods, fill="#EAF2FB", border="#1F4E79"):
        h_fields = 40 + len(fields) * 27
        h_meth = 34 + len(methods) * 25
        d.rectangle([x, y, x + w, y + 44], fill=border, outline=border)
        d.text((x + w / 2, y + 22), title, font=f_head, fill="white", anchor="mm")
        d.rectangle([x, y + 44, x + w, y + 44 + h_fields], fill=fill, outline=border)
        yy = y + 54
        for fl in fields:
            d.text((x + 14, yy), fl, font=f_body, fill="#123")
            yy += 27
        d.rectangle([x, y + 44 + h_fields, x + w, y + 44 + h_fields + h_meth], fill="white", outline=border)
        yy = y + 44 + h_fields + 8
        for m in methods:
            d.text((x + 14, yy), m, font=f_meth, fill="#1F4E79")
            yy += 25
        return (x, y, x + w, y + 44 + h_fields + h_meth)

    p = box(60, 110, 470, "Project  (проект)",
            ["Id : int", "Name : string", "Code : string (unique)", "Status : ProjectStatus",
             "Priority : Priority", "DeadlineUtc : DateTime?", "Tasks : ICollection<ProjectTask>"],
            ["+ Create(name, code, ...) : Project",
             "+ Rename(newName) : void",
             "+ SetDeadline(date) : void",
             "+ AddTask(title, ...) : ProjectTask",
             "+ RemoveTask(task) : void",
             "+ Hold(reason) / Resume() : void",
             "+ Complete() / Archive() : void",
             "+ IsOverdue : bool",
             "+ CompletionPercent : double",
             "+ GetTaskBreakdownByStatus()"])

    t = box(650, 110, 520, "ProjectTask  (задача)",
            ["Id : int", "ProjectId : int", "Title : string", "Status : TaskStatus",
             "Priority : Priority", "Assignee : string?", "DueDateUtc : DateTime?",
             "EstimatedHours : double?", "SpentHours : double", "Comments : ICollection<Comment>"],
            ["+ Create(title, priority, ...) : ProjectTask",
             "+ Start() / Reopen() : void",
             "+ ChangeStatus(newStatus) : void",
             "+ Assign(user) / Unassign() : void",
             "+ Reschedule(date, reason) : void",
             "+ SetEstimate(hours) : void",
             "+ LogWork(hours, note) : void",
             "+ AddComment(author, text) : Comment",
             "+ IsOverdue / Progress / DaysLeft"])

    c = box(1290, 260, 370, "Comment  (комментарий)",
            ["Id : int", "ProjectTaskId : int", "Author : string", "Text : string",
             "CreatedAtUtc : DateTime", "EditedAtUtc : DateTime?"],
            ["+ Create(author, text) : Comment",
             "+ Edit(newText, editor) : void",
             "+ CanBeEdited : bool",
             "+ Excerpt(max) : string",
             "+ GetMentionedUsers() : list"])

    connectors.append(((p[2], 330), (t[0], 330), "содержит", "1", "*"))
    connectors.append(((t[2], 430), (c[0], 430), "обсуждается", "1", "*"))

    for (x1, y1), (x2, y2), label, m1, m2 in connectors:
        d.line([(x1, y1), (x2, y2)], fill="#444", width=3)
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        tw = d.textlength(label, font=f_small) + 16
        d.rectangle([mx - tw / 2, my - 15, mx + tw / 2, my + 15], fill="white", outline="#444")
        d.text((mx, my), label, font=f_small, fill="black", anchor="mm")
        d.text((x1 + 14, y1 - 12), m1, font=f_small, fill="#444", anchor="mm")
        d.text((x2 - 14, y2 - 12), m2, font=f_small, fill="#444", anchor="mm")

    ly = 830
    d.rectangle([60, ly, W - 60, H - 40], fill="#FBFBF3", outline="#999")
    d.text((80, ly + 16), "Бизнес-правила, реализованные в модели:", font=f_head, fill="black")
    rules = [
        "1. Задачу нельзя взять в работу (InProgress) и закрыть (Done) без исполнителя; Done возможен только из Review.",
        "2. Суммарное списание времени ограничено двойной оценкой; за один раз - не более 24 ч; на закрытую задачу время не списывается.",
        "3. Срок задачи не может быть позже срока проекта; срок проекта - раньше даты его создания.",
        "4. Проект можно завершить только при всех закрытых задачах, а архивировать - только завершённый и без просрочек.",
        "5. В закрытый проект нельзя добавлять задачи; названия задач в пределах проекта уникальны.",
        "6. Комментарий редактирует только автор и только в течение 24 часов после создания.",
    ]
    yy = ly + 58
    for r in rules:
        d.text((80, yy), r, font=f_body, fill="#222")
        yy += 30

    img.save(out_path)
    print("saved", out_path)


# ---------------------------------------------------------------- Жизненный цикл задачи
def state_diagram(out_path):
    import math
    W, H = 1700, 700
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    f_title = font(FB, 28)
    f_st = font(FB, 24)
    f_sm = font(F, 17)

    d.text((W / 2, 26), "Жизненный цикл задачи: допустимые переходы статусов (метод ChangeStatus)",
           font=f_title, fill="black", anchor="mt")

    def arrowhead(p2, ang, color, L=13):
        d.polygon([p2,
                   (p2[0] - L * math.cos(ang - 0.4), p2[1] - L * math.sin(ang - 0.4)),
                   (p2[0] - L * math.cos(ang + 0.4), p2[1] - L * math.sin(ang + 0.4))], fill=color)

    names = ["Backlog", "ToDo", "InProgress", "Review", "Done"]
    xs = [90, 400, 710, 1060, 1370]
    bw, bh, y0 = 230, 80, 170
    coords = {}
    for name, x in zip(names, xs):
        col = "#1E7B34" if name == "Done" else "#1F4E79"
        d.rounded_rectangle([x, y0, x + bw, y0 + bh], radius=16, fill=col, outline=col)
        d.text((x + bw / 2, y0 + bh / 2), name, font=f_st, fill="white", anchor="mm")
        coords[name] = (x, y0, x + bw, y0 + bh)

    labs = ["планирование", "Start(): нужен исполнитель", "на проверку", "закрытие"]
    for (a, b), lab in zip([("Backlog", "ToDo"), ("ToDo", "InProgress"),
                            ("InProgress", "Review"), ("Review", "Done")], labs):
        x1, x2 = coords[a][2], coords[b][0]
        y = y0 + bh / 2
        d.line([(x1, y), (x2 - 3, y)], fill="#333", width=3)
        arrowhead((x2 - 1, y), 0, "#333")
        d.text(((x1 + x2) / 2, y0 - 22), lab, font=f_sm, fill="#333", anchor="mm")
        d.line([((x1 + x2) / 2, y0 - 12), ((x1 + x2) / 2, y - 4)], fill="#999", width=1)

    # Отмена: пунктир от незакрытых статусов к Cancelled
    ydash = 380
    centers = [(coords[n][0] + coords[n][2]) / 2 for n in names[:4]]
    for x in centers:
        yy = y0 + bh + 4
        while yy < ydash:
            d.line([(x, yy), (x, min(yy + 9, ydash))], fill="#7B241C", width=2)
            yy += 18
    d.line([(centers[0], ydash), (centers[-1], ydash)], fill="#7B241C", width=2)
    cx = 667
    d.line([(cx, ydash), (cx, 428)], fill="#7B241C", width=3)
    arrowhead((cx, 430), math.pi / 2, "#7B241C")
    d.rounded_rectangle([cx - 110, 430, cx + 110, 494], radius=16, fill="#7B241C", outline="#7B241C")
    d.text((cx, 462), "Cancelled", font=f_st, fill="white", anchor="mm")
    d.text((centers[-1] + 40, ydash), "отмена из любого незакрытого статуса", font=f_sm,
           fill="#7B241C", anchor="lm")

    # Reopen: Done -> ToDo ортогонально снизу
    dx = (coords["Done"][0] + coords["Done"][2]) / 2
    tx = (coords["ToDo"][0] + coords["ToDo"][2]) / 2
    yr = 600
    d.line([(dx, y0 + bh), (dx, yr)], fill="#B03A2E", width=3)
    d.line([(dx, yr), (tx, yr)], fill="#B03A2E", width=3)
    d.line([(tx, yr), (tx, y0 + bh + 3)], fill="#B03A2E", width=3)
    arrowhead((tx, y0 + bh + 1), -math.pi / 2, "#B03A2E")
    d.text(((dx + tx) / 2, yr + 24), "Reopen(): переоткрытие закрытой задачи (Done / Cancelled -> ToDo)",
           font=f_sm, fill="#B03A2E", anchor="mm")
    d.text((90, 110), "Нарушение правил перехода -> DomainException -> ответ HTTP 400 с описанием причины",
           font=f_sm, fill="#555")

    img.save(out_path)
    print("saved", out_path)


# ---------------------------------------------------------------- Архитектура приложения
def arch_diagram(out_path):
    W, H = 1700, 780
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    f_title = font(FB, 30)
    f_head = font(FB, 22)
    f_body = font(F, 19)
    f_m = font(FM, 18)

    d.text((W / 2, 30), "Архитектура приложения TaskTrackerApi", font=f_title, fill="black", anchor="mt")

    def panel(x, y, w, h, title, lines, fill="#F4F8FC", border="#1F4E79", mono=False):
        d.rectangle([x, y, x + w, y + 40], fill=border, outline=border)
        d.text((x + w / 2, y + 20), title, font=f_head, fill="white", anchor="mm")
        d.rectangle([x, y + 40, x + w, y + h], fill=fill, outline=border)
        yy = y + 52
        for ln in lines:
            d.text((x + 14, yy), ln, font=(f_m if mono else f_body), fill="#123")
            yy += 27

    panel(50, 100, 380, 300, "Клиент",
          ["Swagger UI (/swagger)", "HTTP-запросы (curl, Postman)", "Мобильное / веб-приложение",
           "", "Формат обмена: JSON", "(перечисления — строками)"], border="#5B7FA6")

    panel(480, 100, 480, 300, "ASP.NET Core Web API (.NET 8)",
          ["Controllers:", "  ProjectsController — CRUD + команды", "  TasksController — CRUD + статусы/время",
           "  CommentsController — CRUD", "  AnalyticsController — 5 объединяющих запросов",
           "Infrastructure: DomainExceptionHandler", "  DomainException → 400 ProblemDetails"])

    panel(1010, 100, 330, 300, "Модель (бизнес-логика)",
          ["Project", "ProjectTask", "Comment", "", "валидация данных,", "правила переходов,",
           "расчётные свойства"], border="#1E7B34", fill="#F1F9F2")

    panel(1380, 100, 270, 300, "Доступ к данным",
          ["AppDbContext", "(EF Core 8)", "", "InMemory-провайдер:", "данные живут",
           "в процессе приложения", "", "DbInitializer.Seed()"], border="#8E6C1F", fill="#FDF8EC")

    def arrow(x1, x2, y, label=""):
        d.line([(x1, y), (x2, y)], fill="#333", width=3)
        d.polygon([(x2, y), (x2 - 12, y - 7), (x2 - 12, y + 7)], fill="#333")
        if label:
            d.text(((x1 + x2) / 2, y - 16), label, font=f_body, fill="#333", anchor="mm")

    arrow(430, 480, 250, "HTTP/JSON")
    arrow(960, 1010, 250)
    arrow(1340, 1380, 250)

    panel(50, 450, 1600, 280, "Конвейер обработки запроса",
          ["1. Маршрутизация: [ApiController] + [Route(\"api/[controller]\")] → выбор действия контроллера.",
           "2. Привязка модели: JSON-тело → record-DTO; атрибуты [Required], [StringLength], [Range] → автоответ 400 при ошибке валидации.",
           "3. Загрузка данных: EF Core Include(...) — подгрузка связанных сущностей (проект → задачи → комментарии).",
           "4. Бизнес-логика: вызов методов модели (Project.AddTask, ProjectTask.ChangeStatus, Comment.Edit).",
           "   Нарушение правила → DomainException → DomainExceptionHandler → 400 + ProblemDetails с текстом причины.",
           "5. Сохранение: SaveChangesAsync() → ответ 200/201/204 с DTO, собранным LINQ-проекцией Select(...)."],
          fill="#FFFFFF", border="#444")

    img.save(out_path)
    print("saved", out_path)


if __name__ == "__main__":
    import os, sys
    outdir = sys.argv[1] if len(sys.argv) > 1 else "."
    os.makedirs(outdir, exist_ok=True)
    class_diagram(os.path.join(outdir, "fig1_classes.png"))
    state_diagram(os.path.join(outdir, "fig2_lifecycle.png"))
    arch_diagram(os.path.join(outdir, "fig3_arch.png"))
