# -*- coding: utf-8 -*-
"""Сборка отчёта по лабораторной работе (python-docx)."""
import json
import os
import re

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BASE, "..", "src", "TaskTrackerApi")
IMG = os.path.join(BASE, "img")
OUT = os.path.join(BASE, "..", "Отчет_Скосарь_АС-23-04_Технологии_кроссплатформенной_разработки.docx")

RESP = json.load(open(os.path.join(BASE, "test_results", "responses.json"), encoding="utf-8"))


def read(*parts):
    with open(os.path.join(SRC, *parts), encoding="utf-8-sig") as f:
        return f.read()


# ------------------------------------------------------------------ helpers
def setup(doc):
    st = doc.styles["Normal"]
    st.font.name = "Times New Roman"
    st.font.size = Pt(14)
    st.element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    pf = st.paragraph_format
    pf.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    pf.first_line_indent = Cm(1.25)
    pf.space_after = Pt(0)
    pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    sec = doc.sections[0]
    sec.left_margin, sec.right_margin = Cm(3.0), Cm(1.5)
    sec.top_margin, sec.bottom_margin = Cm(2.0), Cm(2.0)

    # нумерация страниц в колонтитуле
    footer = sec.footer
    p = footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    fld1, instr, fld2 = OxmlElement("w:fldChar"), OxmlElement("w:instrText"), OxmlElement("w:fldChar")
    fld1.set(qn("w:fldCharType"), "begin")
    instr.set(qn("xml:space"), "preserve")
    instr.text = "PAGE"
    fld2.set(qn("w:fldCharType"), "end")
    run._r.append(fld1)
    run._r.append(instr)
    run._r.append(fld2)
    run.font.size = Pt(12)


def para(doc, text="", *, size=14, bold=False, italic=False, align=WD_ALIGN_PARAGRAPH.JUSTIFY,
         indent=Cm(1.25), space_after=0, color=None):
    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = indent
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    p.alignment = align
    r = p.add_run(text)
    r.font.size = Pt(size)
    r.bold = bold
    r.italic = italic
    if color:
        r.font.color.rgb = RGBColor(*color)
    return p


def heading(doc, text, level=1):
    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(8)
    p.paragraph_format.keep_with_next = True
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT if level > 1 else WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(text)
    r.bold = True
    r.font.size = Pt(14 if level > 1 else 15)
    return p


def shade(paragraph, fill="F2F2F2"):
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:fill"), fill)
    paragraph._p.get_or_add_pPr().append(shd)


def code(doc, text, size=9):
    for i, line in enumerate(text.rstrip("\n").split("\n")):
        p = doc.add_paragraph()
        p.paragraph_format.first_line_indent = Cm(0)
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
        p.paragraph_format.left_indent = Cm(0.6)
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        r = p.add_run(line if line else " ")
        r.font.name = "Consolas"
        r._element.rPr.rFonts.set(qn("w:eastAsia"), "Consolas")
        r.font.size = Pt(size)
        if i == 0:
            shade(p)
        else:
            shade(p)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def caption(doc, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(10)
    r = p.add_run(text)
    r.font.size = Pt(12)
    r.italic = True
    return p


def figure(doc, fname, text, width=16.5):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Cm(0)
    p.add_run().add_picture(os.path.join(IMG, fname), width=Cm(width))
    caption(doc, text)


def table(doc, header, rows, widths=None, size=10, header_fill="1F4E79"):
    t = doc.add_table(rows=1, cols=len(header))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    for j, h in enumerate(header):
        c = t.rows[0].cells[j]
        c.text = ""
        p = c.paragraphs[0]
        p.paragraph_format.first_line_indent = Cm(0)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h)
        r.bold = True
        r.font.size = Pt(size)
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        shd = OxmlElement("w:shd")
        shd.set(qn("w:val"), "clear")
        shd.set(qn("w:fill"), header_fill)
        c._tc.get_or_add_tcPr().append(shd)
    for row in rows:
        cells = t.add_row().cells
        for j, val in enumerate(row):
            p = cells[j].paragraphs[0]
            p.paragraph_format.first_line_indent = Cm(0)
            p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
            r = p.add_run(str(val))
            r.font.size = Pt(size)
    if widths:
        for j, w in enumerate(widths):
            for row in t.rows:
                row.cells[j].width = Cm(w)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


def extract(path, start_marker, end_marker=None, indent_strip=0):
    """Вырезать фрагмент исходника между маркерами."""
    src = read(*path)
    i = src.index(start_marker)
    if end_marker:
        j = src.index(end_marker, i)
    else:
        j = len(src)
    return src[i:j].rstrip()


def trim_json(text, max_items=2, max_lines=60):
    """Сократить JSON-ответ для печати: первые max_items элементов массива/объекта."""
    try:
        data = json.loads(text)
    except Exception:
        return text
    if isinstance(data, list):
        out = json.dumps(data[:max_items], ensure_ascii=False, indent=2)
        if len(data) > max_items:
            out = out.rsplit("]", 1)[0] + f",\n  ... ещё элементов: {len(data) - max_items}\n]"
    else:
        out = json.dumps(data, ensure_ascii=False, indent=2)
    lines = out.split("\n")
    if len(lines) > max_lines:
        lines = lines[:max_lines] + ["  ..."]
    return "\n".join(lines)


def resp(note_sub, prefer_method=None):
    for r in RESP:
        if note_sub in r["note"]:
            return r
    raise KeyError(note_sub)


# ------------------------------------------------------------------ документ
doc = Document()
setup(doc)

# =============================== ТИТУЛЬНЫЙ ЛИСТ ===============================
tp = doc.add_paragraph()
tp.paragraph_format.first_line_indent = Cm(0)
tp.alignment = WD_ALIGN_PARAGRAPH.CENTER
for line in [
    "МИНИСТЕРСТВО НАУКИ И ВЫСШЕГО ОБРАЗОВАНИЯ РОССИЙСКОЙ ФЕДЕРАЦИИ",
    "[полное наименование образовательной организации]",
    "[наименование факультета / института]",
    "Кафедра [наименование кафедры]",
]:
    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.space_after = Pt(0)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(line)
    r.font.size = Pt(12)
    r.bold = line.startswith("МИНИСТЕРСТВО")

doc.add_paragraph()
doc.add_paragraph()

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.first_line_indent = Cm(0)
r = p.add_run("ЛАБОРАТОРНАЯ РАБОТА")
r.bold = True
r.font.size = Pt(22)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.first_line_indent = Cm(0)
r = p.add_run("по дисциплине «Технологии кроссплатформенной разработки»")
r.font.size = Pt(14)

doc.add_paragraph()

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.first_line_indent = Cm(0)
r = p.add_run("Тема: «Разработка Web API приложения «Трекер задач» с бизнес-логикой")
r.bold = True
r.font.size = Pt(15)
r = p.add_run()
r.add_break()
r = p.add_run("и объединяющими запросами LINQ (ASP.NET Core, .NET 8)»")
r.bold = True
r.font.size = Pt(15)

for _ in range(4):
    doc.add_paragraph()

# блок исполнителя
sign = [
    ("Выполнил:", "студент группы АС-23-04 Скосарь Р.А."),
    ("Проверил:", "[уч. степень, должность] ____________________"),
    ("Дата защиты:", "«____» ______________ 2026 г."),
    ("Оценка:", "____________________"),
]
for left, right in sign:
    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.left_indent = Cm(8.5)
    p.paragraph_format.space_after = Pt(4)
    r = p.add_run(left + "  ")
    r.bold = True
    r.font.size = Pt(13)
    r = p.add_run(right)
    r.font.size = Pt(13)

for _ in range(3):
    doc.add_paragraph()

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.first_line_indent = Cm(0)
r = p.add_run("2026")
r.font.size = Pt(14)

doc.add_page_break()

# =============================== СОДЕРЖАНИЕ ===============================
heading(doc, "СОДЕРЖАНИЕ")
toc = [
    ("1 Цель работы", ""),
    ("2 Задание", ""),
    ("3 Среда разработки и стек технологий", ""),
    ("4 Модель предметной области", ""),
    ("4.1 Классы модели и их бизнес-логика", ""),
    ("4.2 Жизненный цикл задачи", ""),
    ("5 Архитектура Web API приложения", ""),
    ("6 Спецификация эндпоинтов API", ""),
    ("7 Запросы на объединение данных (LINQ)", ""),
    ("8 Тестирование приложения", ""),
    ("9 Выводы", ""),
    ("Список использованных источников", ""),
    ("Приложение А. Листинг классов модели", ""),
    ("Приложение Б. Листинг слоя данных и точки входа", ""),
    ("Приложение В. Листинг DTO и маппинга", ""),
    ("Приложение Г. Листинг контроллеров", ""),
]
for t, _ in toc:
    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.space_after = Pt(2)
    r = p.add_run(t)
    r.font.size = Pt(13)
doc.add_page_break()

# =============================== 1 ЦЕЛЬ ===============================
heading(doc, "1 ЦЕЛЬ РАБОТЫ")
para(doc, "Цель работы — освоить разработку серверной части кроссплатформенного приложения в виде "
          "Web API на платформе .NET: спроектировать модель предметной области с бизнес-логикой, "
          "реализовать контроллеры с CRUD-операциями и запросами, объединяющими данные разных классов, "
          "с использованием технологии LINQ, а также проверить работоспособность API посредством "
          "HTTP-запросов.")
para(doc, "Задачи работы:")
for t in [
    "изучить архитектуру ASP.NET Core Web API (контроллеры, маршрутизация, привязка модели, обработка ошибок);",
    "спроектировать и реализовать модель предметной области из трёх классов, методы которых инкапсулируют "
    "бизнес-правила, а не только хранение данных;",
    "реализовать CRUD-операции для каждого класса модели;",
    "реализовать не менее пяти запросов, объединяющих данные разных классов, с применением операторов LINQ "
    "(Where, Select, GroupBy, Join, OrderBy, агрегатные функции);",
    "выполнить автоматизированное тестирование всех эндпоинтов и зафиксировать результаты.",
]:
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.left_indent = Cm(1.25)
    r = p.add_run(t)
    r.font.size = Pt(14)

# =============================== 2 ЗАДАНИЕ ===============================
heading(doc, "2 ЗАДАНИЕ")
para(doc, "Разработать приложение Web API (ASP.NET Core, .NET 8). Требования задания:")
for t in [
    "описать модель: 2–3 класса с бизнес-логикой, т.е. классы содержат не только данные, но и методы для работы с ними;",
    "добавить в API контроллеры для работы с моделью: CRUD-операции;",
    "добавить 2–5 запросов на объединение данных из разных классов;",
    "для работы с коллекциями пользоваться LINQ (программа минимум — Where и Select).",
]:
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.left_indent = Cm(1.25)
    r = p.add_run(t)
    r.font.size = Pt(14)
para(doc, "Предметная область — «Трекер задач» (аналог Jira/Trello): проекты, задачи внутри проектов "
          "и комментарии к задачам. Выбор области обусловлен наличием выраженных бизнес-правил "
          "(жизненный цикл задачи, контроль сроков и трудозатрат, права редактирования комментариев), "
          "которые естественно ложятся на методы классов модели.")

# =============================== 3 СРЕДА ===============================
heading(doc, "3 СРЕДА РАЗРАБОТКИ И СТЕК ТЕХНОЛОГИЙ")
table(doc,
      ["Компонент", "Версия / значение", "Назначение"],
      [
          [".NET SDK", "8.0.404", "кроссплатформенная платформа выполнения и сборки"],
          ["ASP.NET Core Web API", "в составе .NET 8", "HTTP-каркас: контроллеры, маршрутизация, JSON"],
          ["Entity Framework Core (InMemory)", "8.0.11", "ORM и хранилище данных (не требует установки СУБД)"],
          ["Swashbuckle (Swagger UI)", "6.6.2", "интерактивная документация API по адресу /swagger"],
          ["C# 12", "—", "язык реализации (record, первичные конструкторы, switch-выражения)"],
          ["Редактор / IDE", "VS Code / Visual Studio / Rider", "разработка и отладка"],
          ["Тестирование", "curl / Python urllib, Swagger UI", "проверка эндпоинтов HTTP-запросами"],
      ],
      widths=[5.5, 4.5, 7.0])
para(doc, "Проект собирается и запускается одинаково на Windows, Linux и macOS, что соответствует "
          "дисциплине «Технологии кроссплатформенной разработки»:")
code(doc, """dotnet run --project src/TaskTrackerApi      # запуск API на http://localhost:5080
# документация Swagger UI:  http://localhost:5080/swagger""")

doc.add_page_break()
# =============================== 4 МОДЕЛЬ ===============================
heading(doc, "4 МОДЕЛЬ ПРЕДМЕТНОЙ ОБЛАСТИ")
para(doc, "Модель состоит из трёх классов: Project (проект), ProjectTask (задача проекта) и "
          "Comment (комментарий к задаче). Связи: проект содержит задачи (1:*), задача содержит "
          "комментарии (1:*). Каждый класс, помимо свойств-данных, содержит методы и вычисляемые "
          "свойства, реализующие бизнес-логику: валидацию входных данных, правила переходов между "
          "состояниями, контроль сроков и трудозатрат, расчёт статистики.")
figure(doc, "fig1_classes.png", "Рисунок 1 — Классы модели предметной области и их бизнес-логика")

heading(doc, "4.1 Классы модели и их бизнес-логика", 2)
para(doc, "Класс Project. Инкапсулирует правила работы с проектом: создание с нормализацией кода, "
          "контроль срока (срок проекта не может быть раньше даты создания и раньше срока самой поздней "
          "задачи), управление составом задач (в закрытый проект задачи не добавляются, названия задач "
          "уникальны), жизненный цикл (пауза, завершение только при закрытых задачах, архивация только "
          "завершённого проекта без просрочек) и расчёт показателей (процент выполнения, трудозатраты, "
          "разбивка задач по статусам).")
code(doc, extract(("Models", "Project.cs"),
                  "    /// <summary>\n    /// Добавление задачи в проект.",
                  "    /// <summary>\n    /// Удаление задачи из проекта."))
code(doc, extract(("Models", "Project.cs"),
                  "    /// <summary>\n    /// Завершение проекта.",
                  "    /// <summary>\n    /// Архивация проекта."))
para(doc, "Класс ProjectTask. Имя выбрано, чтобы не конфликтовать с типом System.Threading.Tasks.Task. "
          "Класс реализует канбан-жизненный цикл задачи с проверкой допустимых переходов, учёт "
          "трудозатрат с контролем перерасхода, планирование срока и работу с комментариями.")
code(doc, extract(("Models", "ProjectTask.cs"),
                  "    /// <summary>\n    /// Перевод задачи в работу.",
                  "    /// <summary>Переоткрытие закрытой задачи."))
code(doc, extract(("Models", "ProjectTask.cs"),
                  "    /// <summary>\n    /// Списание трудозатрат.",
                  "    /// <summary>Добавление комментария"))
para(doc, "Класс Comment. Валидация автора и текста при создании, правило редактирования "
          "(править может только автор и только в течение 24 часов), вспомогательные методы "
          "(выдержка текста, поиск упоминаний @пользователь).")
code(doc, extract(("Models", "Comment.cs"),
                  "    /// <summary>\n    /// Редактирование комментария.",
                  "    /// <summary>Краткая выдержка текста"))

heading(doc, "4.2 Жизненный цикл задачи", 2)
para(doc, "Допустимые переходы статусов задачи задаются методом ProjectTask.ChangeStatus и приведены "
          "на рисунке 2. Нарушение любого правила приводит к исключению DomainException, которое "
          "глобальный обработчик преобразует в ответ HTTP 400 с текстом причины, — таким образом "
          "бизнес-логика модели напрямую определяет контракт API.")
figure(doc, "fig2_lifecycle.png", "Рисунок 2 — Допустимые переходы статусов задачи")

doc.add_page_break()
# =============================== 5 АРХИТЕКТУРА ===============================
heading(doc, "5 АРХИТЕКТУРА WEB API ПРИЛОЖЕНИЯ")
para(doc, "Приложение построено по классической схеме ASP.NET Core Web API: контроллеры принимают "
          "HTTP-запросы, загружают сущности через контекст EF Core, вызывают методы бизнес-логики "
          "модели и возвращают DTO, собранные LINQ-проекциями. Хранилище — InMemory-провайдер EF Core: "
          "база данных живёт в процессе приложения и заполняется демонстрационными данными при старте "
          "(DbInitializer.Seed), поэтому для выполнения работы не требуется установка СУБД.")
figure(doc, "fig3_arch.png", "Рисунок 3 — Архитектура приложения и конвейер обработки запроса")
para(doc, "Фрагмент точки входа Program.cs (регистрация сервисов и конвейера):")
code(doc, extract(("Program.cs",), "var builder = WebApplication.CreateBuilder", None))
para(doc, "Ошибки бизнес-логики обрабатываются централизованно: класс DomainExceptionHandler "
          "реализует IExceptionHandler и возвращает ProblemDetails с кодом 400 для DomainException, "
          "404 для KeyNotFoundException и 500 для прочих исключений. Ошибки валидации DTO "
          "([Required], [StringLength], [Range]) обрабатываются каркасом автоматически (также 400).")

doc.add_page_break()
# =============================== 6 СПЕЦИФИКАЦИЯ ===============================
heading(doc, "6 СПЕЦИФИКАЦИЯ ЭНДПОИНТОВ API")
para(doc, "Полная интерактивная документация доступна в Swagger UI. Ниже приведена сводная таблица "
          "эндпоинтов; CRUD-операции выделены для каждого из трёх классов модели.")
rows = [
    ["GET", "/api/projects", "R", "список проектов (фильтры status, search) — Where + Select"],
    ["GET", "/api/projects/{id}", "R", "проект с расчётными показателями"],
    ["POST", "/api/projects", "C", "создание проекта (Project.Create)"],
    ["PUT", "/api/projects/{id}", "U", "обновление (Rename, ChangeCode, ChangeDescription)"],
    ["DELETE", "/api/projects/{id}", "D", "удаление (только архивированный или пустой)"],
    ["POST", "/api/projects/{id}/hold | /resume", "—", "пауза / снятие с паузы (бизнес-команды)"],
    ["POST", "/api/projects/{id}/complete | /archive", "—", "завершение / архивация (бизнес-команды)"],
    ["PUT", "/api/projects/{id}/deadline", "U", "изменение срока проекта (SetDeadline)"],
    ["GET", "/api/projects/{id}/details", "R+", "проект + задачи + комментарии (объединение, запрос 6)"],
    ["GET", "/api/tasks", "R", "список задач с данными проекта (фильтры projectId, status, priority, assignee, overdueOnly)"],
    ["GET", "/api/tasks/{id}", "R", "задача с названием и кодом проекта"],
    ["POST", "/api/tasks?projectId={id}", "C", "создание задачи (Project.AddTask)"],
    ["PUT", "/api/tasks/{id}", "U", "обновление (Rename, ChangeDescription, Assign)"],
    ["DELETE", "/api/tasks/{id}", "D", "удаление (Project.RemoveTask: задачу в работе удалять нельзя)"],
    ["PUT", "/api/tasks/{id}/status", "U", "смена статуса (ChangeStatus с проверкой переходов)"],
    ["PUT", "/api/tasks/{id}/assignee", "U", "назначение исполнителя (Assign)"],
    ["PUT", "/api/tasks/{id}/estimate", "U", "оценка трудоёмкости (SetEstimate)"],
    ["PUT", "/api/tasks/{id}/reschedule", "U", "перенос срока (Reschedule)"],
    ["POST", "/api/tasks/{id}/work", "C", "списание трудозатрат (LogWork)"],
    ["POST", "/api/tasks/{id}/comments", "C", "добавление комментария (AddComment)"],
    ["GET", "/api/tasks/my-board?assignee=...", "R+", "доска исполнителя по всем проектам (join, синтаксис запросов LINQ)"],
    ["GET", "/api/comments", "R", "комментарии с данными задачи и проекта (фильтры taskId, projectId, author)"],
    ["GET", "/api/comments/{id}", "R", "комментарий по идентификатору"],
    ["POST", "/api/comments?taskId={id}", "C", "создание комментария (Comment.Create)"],
    ["PUT", "/api/comments/{id}", "U", "редактирование (Comment.Edit: только автор, окно 24 ч)"],
    ["DELETE", "/api/comments/{id}", "D", "удаление комментария"],
    ["GET", "/api/analytics/projects-statistics", "R+", "запрос 1: статистика проектов (GroupBy по статусам задач)"],
    ["GET", "/api/analytics/overdue-tasks", "R+", "запрос 2: просроченные задачи + проект + число комментариев"],
    ["GET", "/api/analytics/assignees-summary", "R+", "запрос 3: сводка по исполнителям поверх всех проектов"],
    ["GET", "/api/analytics/task-discussions", "R+", "запрос 4: самые обсуждаемые задачи и участники"],
    ["GET", "/api/analytics/projects-activity", "R+", "запрос 5: активность обсуждения проектов"],
]
table(doc, ["Метод", "Маршрут", "CRUD", "Назначение"], rows, widths=[1.8, 6.2, 1.4, 7.6], size=9)
para(doc, "В таблице: C — создание, R — чтение, U — обновление, D — удаление, R+ — запрос, "
          "объединяющий данные нескольких классов.", size=12, italic=True)

doc.add_page_break()
# =============================== 7 LINQ ===============================
heading(doc, "7 ЗАПРОСЫ НА ОБЪЕДИНЕНИЕ ДАННЫХ (LINQ)")
para(doc, "Программа минимум по заданию — использование операторов Where и Select — выполнена во всех "
          "выборках контроллеров. Пример базовой выборки с фильтрацией и проекцией в DTO "
          "(ProjectsController.GetAll):")
code(doc, extract(("Controllers", "ProjectsController.cs"),
                  "        // LINQ: Where (фильтрация) и Select (проекция в DTO)",
                  "        return Ok(result);"))
para(doc, "Ниже приведены пять запросов, объединяющих данные разных классов модели "
          "(Project + ProjectTask + Comment), и один вложенный запрос-карточка. Все они реализованы "
          "в AnalyticsController (и ProjectsController.GetDetails) средствами LINQ: Where, Select, "
          "GroupBy, Join (в синтаксисе запросов), OrderBy, Take, агрегатные функции Count/Sum/Average/Max.")

queries = [
    ("Запрос 1. Статистика по проектам", "GET /api/analytics/projects-statistics",
     "Данные проекта объединяются с агрегатами по его задачам и комментариям: число задач, выполненных "
     "и просроченных, процент выполнения, суммарные трудозатраты, средняя оценка, число комментариев "
     "и разбивка задач по статусам (GroupBy).",
     "projects-statistics"),
    ("Запрос 2. Просроченные задачи с контекстом проекта", "GET /api/analytics/overdue-tasks",
     "Объединение ProjectTask + Project + Comment: для каждой просроченной задачи (бизнес-свойство "
     "IsOverdue) выдаются код и название проекта, число дней просрочки и количество комментариев.",
     "overdue-tasks"),
    ("Запрос 3. Сводка по исполнителям", "GET /api/analytics/assignees-summary",
     "Задачи всех проектов группируются по исполнителю (GroupBy): число назначенных и выполненных задач, "
     "процент выполнения, просрочки, суммарные трудозатраты и список кодов проектов исполнителя (Distinct).",
     "assignees-summary"),
    ("Запрос 4. Самые обсуждаемые задачи", "GET /api/analytics/task-discussions",
     "Задача + проект + комментарии: число комментариев, дата последнего комментария (Max) и список "
     "участников обсуждения (Distinct по авторам); выдача упорядочена по убыванию числа комментариев.",
     "task-discussions"),
    ("Запрос 5. Активность обсуждения проектов", "GET /api/analytics/projects-activity",
     "Проект + все его задачи + все комментарии (SelectMany): число комментариев по проекту, дата "
     "последней активности и список участников; фильтр по минимальному числу комментариев.",
     "projects-activity"),
]
def query_code(idx):
    src = read("Controllers", "AnalyticsController.cs")
    marks = ["ЗАПРОС 1.", "ЗАПРОС 2.", "ЗАПРОС 3.", "ЗАПРОС 4.", "ЗАПРОС 5."]
    i = src.index(marks[idx])
    i = src.rindex("/// <summary>", 0, i)
    k = src.index("{", src.index("public async Task", i))
    depth, j = 0, k
    while j < len(src):
        if src[j] == "{":
            depth += 1
        elif src[j] == "}":
            depth -= 1
            if depth == 0:
                break
        j += 1
    return src[i:j + 1].rstrip()


for n, (title, route, desc, key) in enumerate(queries):
    heading(doc, title, 2)
    para(doc, f"Маршрут: {route}. {desc}")
    code(doc, query_code(n))
    r = resp({"projects-statistics": "ЗАПРОС 1: статистика",
              "overdue-tasks": "ЗАПРОС 2",
              "assignees-summary": "ЗАПРОС 3",
              "task-discussions": "ЗАПРОС 4",
              "projects-activity": "ЗАПРОС 5"}[key])
    para(doc, f"Фрагмент фактического ответа сервера (HTTP {r['status']}):", size=12, italic=True)
    code(doc, trim_json(r["response"], max_items=2 if key != "overdue-tasks" else 3, max_lines=46))

heading(doc, "Запрос 6. Полная карточка проекта (вложенное объединение)", 2)
para(doc, "Эндпоинт GET /api/projects/{id}/details собирает иерархию проект → задачи → комментарии "
          "одним запросом с вложенными проекциями Select:")
code(doc, extract(("Controllers", "ProjectsController.cs"),
                  "        // LINQ: Select — сборка сложного DTO из связанных сущностей",
                  "        return Ok(details);"))
r = resp("Полная карточка проекта")
para(doc, f"Фрагмент фактического ответа сервера (HTTP {r['status']}):", size=12, italic=True)
code(doc, trim_json(r["response"], max_items=1, max_lines=40))

heading(doc, "Объединение в синтаксисе запросов LINQ (join)", 2)
para(doc, "Эндпоинт GET /api/tasks/my-board демонстрирует оператор join в синтаксисе запросов LINQ: "
          "задачи соединяются со своими проектами, фильтруются по исполнителю и упорядочиваются "
          "по приоритету и сроку:")
code(doc, extract(("Controllers", "TasksController.cs"),
                  "        // синтаксис запросов LINQ: join задач с их проектами",
                  "        return Ok(board.ToList());"))

doc.add_page_break()
# =============================== 8 ТЕСТИРОВАНИЕ ===============================
heading(doc, "8 ТЕСТИРОВАНИЕ ПРИЛОЖЕНИЯ")
para(doc, "Тестирование выполнено автоматизированным скриптом (43 HTTP-запроса) против запущенного "
          "приложения. Проверялись: успешные сценарии CRUD, срабатывание бизнес-правил (ответ 400 "
          "с текстом причины), валидация DTO, ответы 404 и 204. Все фактические коды состояния "
          "совпали с ожидаемыми.")
rows = []
for r in RESP:
    rows.append([r["method"], r["path"], r["status"], r["note"]])
table(doc, ["Метод", "Запрос", "Код", "Проверяемый сценарий"], rows,
      widths=[1.7, 6.6, 1.3, 7.4], size=8)

heading(doc, "Примеры запросов и ответов", 2)
para(doc, "1) Создание проекта (успех, 201 Created):")
code(doc, """curl -X POST http://localhost:5080/api/projects -H "Content-Type: application/json" -d \\
'{"name":"Портал университета","code":"UNI","description":"Личный кабинет студента",
  "priority":"Medium","deadlineUtc":"2027-01-16T00:00:00Z"}'""")
code(doc, trim_json(resp("Создание проекта")["response"]))
para(doc, "2) Нарушение бизнес-правила уникальности кода проекта (400):")
code(doc, trim_json(resp("Дубликат кода")["response"]))
para(doc, "3) Нарушение правила переходов статусов: закрытие задачи минуя Review (400):")
code(doc, trim_json(resp("Закрытие из InProgress")["response"]))
para(doc, "4) Списание времени на закрытую задачу запрещено моделью (400):")
code(doc, trim_json(resp("Списание времени на закрытую")["response"]))
para(doc, "5) Редактирование комментария посторонним пользователем запрещено (400):")
code(doc, trim_json(resp("Правка чужого")["response"]))
para(doc, "6) Успешная смена статуса с назначенным исполнителем (200):")
code(doc, trim_json(resp("Перевод в работу")["response"], max_lines=26))
para(doc, "7) Удаление проекта с задачами запрещено (400), а архивированного — разрешено (204):")
code(doc, trim_json(resp("Удаление проекта с задачами")["response"]))
para(doc, "8) Валидация DTO каркасом ASP.NET Core: код проекта длиннее 8 символов (400):")
code(doc, trim_json(resp("Код длиннее")["response"]))

doc.add_page_break()
# =============================== 9 ВЫВОДЫ ===============================
heading(doc, "9 ВЫВОДЫ")
para(doc, "В ходе лабораторной работы разработано кроссплатформенное серверное приложение Web API "
          "«Трекер задач» на ASP.NET Core (.NET 8). Модель предметной области реализована тремя "
          "классами (Project, ProjectTask, Comment), каждый из которых содержит не только данные, "
          "но и бизнес-логику: валидацию, правила жизненного цикла, контроль сроков и трудозатрат, "
          "расчёт статистических показателей.")
para(doc, "Для каждого класса модели реализованы CRUD-операции в соответствующих контроллерах "
          "(ProjectsController, TasksController, CommentsController), а также командные эндпоинты, "
          "вызывающие методы бизнес-логики (смена статуса, списание времени, перенос срока, пауза и "
          "архивация проекта, редактирование комментария).")
para(doc, "Реализовано шесть запросов, объединяющих данные разных классов модели, и доска исполнителя "
          "с оператором join; во всех выборках применены операторы LINQ Where и Select (программа "
          "минимум), дополнительно — GroupBy, Join, OrderBy, Take, Distinct и агрегатные функции. "
          "Ошибки бизнес-правил транслируются в ответы HTTP 400 с человекочитаемым описанием причины, "
          "что формирует понятный контракт API.")
para(doc, "Работоспособность подтверждена автоматизированным прогоном 43 HTTP-запросов: все фактические "
          "коды состояния совпали с ожидаемыми, включая сценарии нарушений бизнес-правил. Таким образом, "
          "цель работы достигнута, задания программы минимум и расширенной программы выполнены.")

# =============================== ИСТОЧНИКИ ===============================
heading(doc, "СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ")
srcs = [
    "Документация ASP.NET Core: Controller action methods, Routing, Model validation. — URL: https://learn.microsoft.com/aspnet/core/ (дата обращения: 18.10.2026).",
    "Документация LINQ: Standard query operators, синтаксис запросов и методов. — URL: https://learn.microsoft.com/dotnet/csharp/programming-guide/concepts/linq/ (дата обращения: 18.10.2026).",
    "Документация Entity Framework Core: InMemory provider, Include/ThenInclude. — URL: https://learn.microsoft.com/ef/core/ (дата обращения: 18.10.2026).",
    "Троелсен Э., Джелли М. Язык C# и платформа .NET. — 11-е изд. — СПб.: Питер, 2023. — 1120 с.",
    "Албахари Дж., Албахари Б. C# 12 in a Nutshell. — O'Reilly Media, 2024. — 900 p.",
]
for i, s in enumerate(srcs, 1):
    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.left_indent = Cm(0.7)
    p.paragraph_format.space_after = Pt(3)
    r = p.add_run(f"{i}. {s}")
    r.font.size = Pt(12)

# =============================== ПРИЛОЖЕНИЯ ===============================
def appendix(doc, title, files):
    doc.add_page_break()
    heading(doc, title)
    for label, parts in files:
        heading(doc, label, 2)
        code(doc, read(*parts), size=8)

appendix(doc, "ПРИЛОЖЕНИЕ А. ЛИСТИНГ КЛАССОВ МОДЕЛИ", [
    ("А.1 Enums.cs — перечисления модели", ("Models", "Enums.cs")),
    ("А.2 DomainException.cs и интерфейс IHasDeadline", ("Models", "DomainException.cs")),
    ("А.3 Project.cs", ("Models", "Project.cs")),
    ("А.4 ProjectTask.cs", ("Models", "ProjectTask.cs")),
    ("А.5 Comment.cs", ("Models", "Comment.cs")),
])
appendix(doc, "ПРИЛОЖЕНИЕ Б. СЛОЙ ДАННЫХ И ТОЧКА ВХОДА", [
    ("Б.1 AppDbContext.cs", ("Data", "AppDbContext.cs")),
    ("Б.2 DbInitializer.cs — демонстрационные данные", ("Data", "DbInitializer.cs")),
    ("Б.3 DomainExceptionHandler.cs", ("Infrastructure", "DomainExceptionHandler.cs")),
    ("Б.4 Program.cs", ("Program.cs",)),
])
appendix(doc, "ПРИЛОЖЕНИЕ В. DTO И МАППИНГ", [
    ("В.1 Dtos.cs", ("DTOs", "Dtos.cs")),
])
appendix(doc, "ПРИЛОЖЕНИЕ Г. ЛИСТИНГ КОНТРОЛЛЕРОВ", [
    ("Г.1 ProjectsController.cs", ("Controllers", "ProjectsController.cs")),
    ("Г.2 TasksController.cs", ("Controllers", "TasksController.cs")),
    ("Г.3 CommentsController.cs", ("Controllers", "CommentsController.cs")),
    ("Г.4 AnalyticsController.cs", ("Controllers", "AnalyticsController.cs")),
])

doc.save(OUT)
print("saved:", OUT)
