# -*- coding: utf-8 -*-
"""Генератор коллекции Bruno для проверки TaskTrackerApi (report/make_bruno.py)."""
import json
import os
from urllib.parse import quote

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(BASE, "..", "bruno"))

COLLECTION_NAME = "TaskTrackerApi - лабораторная (Скосарь Р.А., АС-23-04)"


def esc(s):
    return s


# ------------------------------------------------------------------ данные
# (папка, файл, имя, метод, url, params, body, after_response, tests)
# tests: список кортежей (название теста, js-строка тела)
R = []


def add(folder, fname, name, method, url, params=None, body=None, after=None, tests=None):
    R.append(dict(folder=folder, fname=fname, name=name, method=method, url=url,
                  params=params or {}, body=body, after=after, tests=tests or []))


def st(code):
    return (f"HTTP {code}", f"expect(res.getStatus()).to.equal({code});")


P = "01 Projects"
add(P, "01-get-projects", "Список проектов (LINQ Where+Select)", "get", "{{baseUrl}}/api/projects",
    tests=[st(200), ("проектов не меньше трёх", "expect(res.getBody().length).to.be.at.least(3);"),
           ("у каждого проекта есть код", "res.getBody().forEach(p => expect(p.code).to.be.a('string'));")])
add(P, "02-get-project-1", "Проект по Id (SHOP)", "get", "{{baseUrl}}/api/projects/1",
    tests=[st(200), ("код проекта SHOP", "expect(res.getBody().code).to.equal('SHOP');"),
           ("есть расчётный процент выполнения", "expect(res.getBody().completionPercent).to.be.a('number');")])
add(P, "03-create-project", "Создать проект (201)", "post", "{{baseUrl}}/api/projects",
    body={"name": "Портал университета", "code": "UNI", "description": "Личный кабинет студента",
          "priority": "Medium", "deadlineUtc": "2027-01-16T00:00:00Z"},
    after="bru.setVar('createdProjectId', res.getBody().id);",
    tests=[st(201), ("код UNI", "expect(res.getBody().code).to.equal('UNI');"),
           ("Id сохранён в переменную коллекции", "expect(res.getBody().id).to.be.a('number');")])
add(P, "04-update-project", "Обновить созданный проект", "put", "{{baseUrl}}/api/projects/{{createdProjectId}}",
    body={"name": "Портал университета v2", "priority": "High"},
    tests=[st(200), ("имя обновлено", "expect(res.getBody().name).to.equal('Портал университета v2');"),
           ("приоритет High", "expect(res.getBody().priority).to.equal('High');")])
add(P, "05-set-deadline", "Изменить срок проекта", "put", "{{baseUrl}}/api/projects/{{createdProjectId}}/deadline",
    body="2027-02-01T00:00:00Z",
    tests=[st(200), ("срок обновлён", "expect(res.getBody().deadlineUtc).to.be.a('string');")])
add(P, "06-hold-project-1", "Поставить проект 1 на паузу", "post", "{{baseUrl}}/api/projects/1/hold",
    params={"reason": "ожидание макетов"},
    tests=[st(200), ("статус OnHold", "expect(res.getBody().status).to.equal('OnHold');")])
add(P, "07-resume-project-1", "Снять проект 1 с паузы", "post", "{{baseUrl}}/api/projects/1/resume",
    tests=[st(200), ("статус Active", "expect(res.getBody().status).to.equal('Active');")])
add(P, "08-project-details", "Карточка проекта: проект+задачи+комментарии", "get", "{{baseUrl}}/api/projects/1/details",
    tests=[st(200), ("есть задачи", "expect(res.getBody().tasks.length).to.be.at.least(1);"),
           ("у задач есть комментарии-массив", "expect(res.getBody().tasks[0].comments).to.be.an('array');")])

T = "02 Tasks"
add(T, "01-get-tasks-project", "Задачи проекта 1", "get", "{{baseUrl}}/api/tasks",
    params={"projectId": "1"},
    tests=[st(200), ("задач не меньше пяти", "expect(res.getBody().length).to.be.at.least(5);"),
           ("все задачи проекта 1", "res.getBody().forEach(t => expect(t.projectId).to.equal(1));")])
add(T, "02-get-overdue", "Только просроченные задачи", "get", "{{baseUrl}}/api/tasks",
    params={"overdueOnly": "true"},
    tests=[st(200), ("все просроченные", "res.getBody().forEach(t => expect(t.isOverdue).to.equal(true));")])
add(T, "03-get-task-1", "Задача по Id", "get", "{{baseUrl}}/api/tasks/1",
    tests=[st(200), ("название задачи", "expect(res.getBody().title).to.equal('REST API каталога товаров');"),
           ("проект подтянут (объединение)", "expect(res.getBody().projectCode).to.equal('SHOP');")])
add(T, "04-create-task", "Создать задачу в проекте 1 (201)", "post", "{{baseUrl}}/api/tasks",
    params={"projectId": "1"},
    body={"title": "Кеширование каталога", "description": "Redis", "priority": "Medium",
          "assignee": "Скосарь Р.А.", "dueDateUtc": "2026-10-30T00:00:00Z"},
    after="bru.setVar('createdTaskId', res.getBody().id);",
    tests=[st(201), ("статус Backlog", "expect(res.getBody().status).to.equal('Backlog');")])
add(T, "05-update-task", "Обновить созданную задачу", "put", "{{baseUrl}}/api/tasks/{{createdTaskId}}",
    body={"description": "Redis cluster + TTL", "priority": "High"},
    tests=[st(200), ("описание обновлено", "expect(res.getBody().description).to.equal('Redis cluster + TTL');")])
add(T, "06-assign-task-4", "Назначить исполнителя задаче 4", "put", "{{baseUrl}}/api/tasks/4/assignee",
    params={"assignee": "Игорь П."},
    tests=[st(200), ("исполнитель назначен", "expect(res.getBody().assignee).to.equal('Игорь П.');")])
add(T, "07-status-inprogress", "Задача 4: в работу", "put", "{{baseUrl}}/api/tasks/4/status",
    body={"status": "InProgress"},
    tests=[st(200), ("статус InProgress", "expect(res.getBody().status).to.equal('InProgress');"),
           ("прогресс 50", "expect(res.getBody().progress).to.equal(50);")])
add(T, "08-status-review", "Задача 4: на проверку", "put", "{{baseUrl}}/api/tasks/4/status",
    body={"status": "Review"},
    tests=[st(200), ("статус Review", "expect(res.getBody().status).to.equal('Review');")])
add(T, "09-status-done", "Задача 4: закрыть", "put", "{{baseUrl}}/api/tasks/4/status",
    body={"status": "Done"},
    tests=[st(200), ("статус Done", "expect(res.getBody().status).to.equal('Done');"),
           ("прогресс 100", "expect(res.getBody().progress).to.equal(100);")])
add(T, "10-estimate-task-3", "Оценка трудоёмкости задачи 3", "put", "{{baseUrl}}/api/tasks/3/estimate",
    body={"hours": 20},
    tests=[st(200), ("оценка 20", "expect(res.getBody().estimatedHours).to.equal(20);")])
add(T, "11-log-work-task-3", "Списать 2.5 ч на задачу 3", "post", "{{baseUrl}}/api/tasks/3/work",
    body={"hours": 2.5, "note": "вёрстка"},
    tests=[st(200), ("списано 2.5", "expect(res.getBody().spentHours).to.equal(2.5);")])
add(T, "12-reschedule-task-3", "Перенести срок задачи 3", "put", "{{baseUrl}}/api/tasks/3/reschedule",
    body={"dueDateUtc": "2026-11-20T00:00:00Z", "reason": "перенос спринта"},
    tests=[st(200), ("срок обновлён", "expect(res.getBody().dueDateUtc).to.be.a('string');")])
add(T, "13-my-board", "Доска исполнителя (join, синтаксис запросов LINQ)", "get", "{{baseUrl}}/api/tasks/my-board",
    params={"assignee": "Скосарь"},
    tests=[st(200), ("есть задачи", "expect(res.getBody().length).to.be.at.least(1);"),
           ("все задачи незакрытые", "res.getBody().forEach(t => expect(['Done','Cancelled']).to.not.include(t.status));")])
add(T, "14-add-comment-via-task", "Комментарий через задачу 1 (201)", "post", "{{baseUrl}}/api/tasks/1/comments",
    body={"author": "Скосарь Р.А.", "text": "@Игорь П. проверь интеграцию с оплатой"},
    after="bru.setVar('createdCommentId', res.getBody().id);",
    tests=[st(201), ("упоминание распознано", "expect(res.getBody().mentionedUsers.length).to.be.at.least(1);")])

C = "03 Comments"
add(C, "01-get-comments-task", "Комментарии задачи 1", "get", "{{baseUrl}}/api/comments",
    params={"taskId": "1"},
    tests=[st(200), ("комментариев не меньше двух", "expect(res.getBody().length).to.be.at.least(2);")])
add(C, "02-get-comments-project", "Комментарии проекта 1 (объединение 3 сущностей)", "get", "{{baseUrl}}/api/comments",
    params={"projectId": "1"},
    tests=[st(200), ("у каждого комментария есть код проекта",
                     "res.getBody().forEach(c => expect(c.projectCode).to.equal('SHOP'));")])
add(C, "03-get-comment-created", "Созданный комментарий по Id", "get", "{{baseUrl}}/api/comments/{{createdCommentId}}",
    tests=[st(200), ("автор совпадает", "expect(res.getBody().author).to.equal('Скосарь Р.А.');")])
add(C, "04-create-comment", "Создать комментарий к задаче 2", "post", "{{baseUrl}}/api/comments",
    params={"taskId": "2"},
    body={"author": "Мария Д.", "text": "Добавила макеты экрана корзины"},
    tests=[st(201)])
add(C, "05-edit-comment", "Автор правит свой комментарий", "put", "{{baseUrl}}/api/comments/{{createdCommentId}}",
    body={"editor": "Скосарь Р.А.", "text": "@Игорь П. проверь интеграцию с оплатой (срочно)"},
    tests=[st(200), ("помечен как изменённый", "expect(res.getBody().editedAtUtc).to.not.equal(null);")])

A = "04 Analytics (LINQ-объединения)"
add(A, "01-projects-statistics", "Запрос 1: статистика проектов (GroupBy)", "get",
    "{{baseUrl}}/api/analytics/projects-statistics",
    tests=[st(200), ("проектов не меньше трёх", "expect(res.getBody().length).to.be.at.least(3);"),
           ("есть разбивка по статусам", "expect(res.getBody()[0].byStatus).to.be.an('array');")])
add(A, "02-projects-statistics-active", "Запрос 1б: только активные проекты", "get",
    "{{baseUrl}}/api/analytics/projects-statistics", params={"onlyActive": "true"},
    tests=[st(200), ("все активные", "res.getBody().forEach(p => expect(p.status).to.equal('Active'));")])
add(A, "03-overdue-tasks", "Запрос 2: просроченные задачи + проект + комментарии", "get",
    "{{baseUrl}}/api/analytics/overdue-tasks",
    tests=[st(200), ("есть код проекта", "res.getBody().forEach(t => expect(t.projectCode).to.be.a('string'));"),
           ("есть число комментариев", "res.getBody().forEach(t => expect(t.commentsCount).to.be.a('number'));")])
add(A, "04-assignees-summary", "Запрос 3: сводка по исполнителям", "get",
    "{{baseUrl}}/api/analytics/assignees-summary",
    tests=[st(200), ("исполнителей не меньше трёх", "expect(res.getBody().length).to.be.at.least(3);"),
           ("список проектов исполнителя", "res.getBody().forEach(a => expect(a.projects).to.be.an('array'));")])
add(A, "05-task-discussions", "Запрос 4: самые обсуждаемые задачи", "get",
    "{{baseUrl}}/api/analytics/task-discussions", params={"take": "3"},
    tests=[st(200), ("не больше трёх", "expect(res.getBody().length).to.be.at.most(3);"),
           ("есть участники", "res.getBody().forEach(t => expect(t.participants.length).to.be.at.least(1));")])
add(A, "06-projects-activity", "Запрос 5: активность обсуждения проектов", "get",
    "{{baseUrl}}/api/analytics/projects-activity",
    tests=[st(200), ("есть дата последней активности",
                     "res.getBody().forEach(p => expect(p.lastActivityUtc).to.be.a('string'));")])

E = "05 Бизнес-правила (ошибки 400/404)"
add(E, "01-duplicate-project-code", "Дубликат кода проекта -> 400", "post", "{{baseUrl}}/api/projects",
    body={"name": "Портал университета", "code": "uni", "priority": "Medium"},
    tests=[st(400), ("текст причины в ответе", "expect(res.getBody().message).to.include('уже существует');")])
add(E, "02-long-project-code", "Код длиннее 8 символов -> 400 (валидация DTO)", "post", "{{baseUrl}}/api/projects",
    body={"name": "Портал университета", "code": "PORTALDEV", "priority": "Medium"},
    tests=[st(400), ("ошибка валидации поля Code", "expect(JSON.stringify(res.getBody())).to.include('Code');")])
add(E, "03-deadline-in-past", "Срок проекта в прошлом -> 400", "post", "{{baseUrl}}/api/projects",
    body={"name": "Проект с прошлым сроком", "code": "OLD", "priority": "Low",
          "deadlineUtc": "2020-01-01T00:00:00Z"},
    tests=[st(400), ("причина: срок раньше создания", "expect(res.getBody().detail).to.include('раньше даты его создания');")])
add(E, "04-duplicate-task-title", "Дубликат названия задачи в проекте -> 400", "post", "{{baseUrl}}/api/tasks",
    params={"projectId": "1"},
    body={"title": "REST API каталога товаров", "priority": "Low"},
    tests=[st(400), ("причина: задача уже есть", "expect(res.getBody().detail).to.include('уже есть в проекте');")])
add(E, "05-start-without-assignee", "Старт задачи без исполнителя -> 400", "put", "{{baseUrl}}/api/tasks/11/status",
    body={"status": "InProgress"},
    tests=[st(400), ("причина: нет исполнителя", "expect(res.getBody().detail).to.include('без исполнителя');")])
add(E, "06-done-not-from-review", "Закрытие минуя Review -> 400", "put", "{{baseUrl}}/api/tasks/1/status",
    body={"status": "Done"},
    tests=[st(400), ("причина: только из Review", "expect(res.getBody().detail).to.include('только из статуса Review');")])
add(E, "07-work-on-closed-task", "Списание времени на закрытую задачу -> 400", "post", "{{baseUrl}}/api/tasks/4/work",
    body={"hours": 3, "note": "реализация"},
    tests=[st(400), ("причина: задача закрыта", "expect(res.getBody().detail).to.include('закрыта');")])
add(E, "08-work-too-many-hours", "Списание 60 ч за раз -> 400 (Range)", "post", "{{baseUrl}}/api/tasks/3/work",
    body={"hours": 60, "note": "слишком много"},
    tests=[st(400), ("ошибка валидации Hours", "expect(JSON.stringify(res.getBody())).to.include('Hours');")])
add(E, "09-edit-foreign-comment", "Правка чужого комментария -> 400", "put", "{{baseUrl}}/api/comments/1",
    body={"editor": "Игорь П.", "text": "Чужой комментарий"},
    tests=[st(400), ("причина: только автор", "expect(res.getBody().detail).to.include('только его автор');")])
add(E, "10-reschedule-to-past", "Перенос срока в прошлое -> 400", "put", "{{baseUrl}}/api/tasks/1/reschedule",
    body={"dueDateUtc": "2020-05-05T00:00:00Z"},
    tests=[st(400), ("причина: срок в прошлом", "expect(res.getBody().detail).to.include('не может быть в прошлом');")])
add(E, "11-delete-project-with-tasks", "Удаление проекта с задачами -> 400", "delete", "{{baseUrl}}/api/projects/1",
    tests=[st(400), ("причина: содержит задачи", "expect(res.getBody().message).to.include('содержит задач');")])
add(E, "12-project-not-found", "Несуществующий проект -> 404", "get", "{{baseUrl}}/api/projects/99",
    tests=[st(404)])

CL = "06 Очистка"
add(CL, "01-archive-project-2", "Архивировать завершённый проект 2", "post", "{{baseUrl}}/api/projects/2/archive",
    tests=[st(200), ("статус Archived", "expect(res.getBody().status).to.equal('Archived');")])
add(CL, "02-delete-project-2", "Удалить архивированный проект 2 -> 204", "delete", "{{baseUrl}}/api/projects/2",
    tests=[("HTTP 204", "expect(res.getStatus()).to.equal(204);")])
add(CL, "03-delete-task-4", "Удалить закрытую задачу 4 -> 204", "delete", "{{baseUrl}}/api/tasks/4",
    tests=[("HTTP 204", "expect(res.getStatus()).to.equal(204);")])
add(CL, "04-projects-after-cleanup", "Список проектов после очистки", "get", "{{baseUrl}}/api/projects",
    tests=[st(200), ("CRM удалён", "expect(res.getBody().map(p => p.code)).to.not.include('CRM');")])


# ------------------------------------------------------------------ генерация
def build_url(r):
    url = r["url"]
    if r["params"]:
        qs = "&".join(f"{k}={quote(str(v))}" for k, v in r["params"].items())
        url = f"{url}{'&' if '?' in url else '?'}{qs}"
    return url


def bru_file(r, seq):
    lines = []
    lines.append("meta {")
    lines.append(f"  name: {r['name']}")
    lines.append("  type: http")
    lines.append(f"  seq: {seq}")
    lines.append("}")
    lines.append("")
    lines.append(f"{r['method']} {{")
    lines.append(f"  url: {build_url(r)}")
    lines.append(f"  body: {'json' if r['body'] is not None else 'none'}")
    lines.append("  auth: inherit")
    lines.append("}")
    if r["body"] is not None:
        lines.append("")
        lines.append("body:json {")
        if isinstance(r["body"], str):
            lines.append(f'  "{r["body"]}"' if not r["body"].startswith('"') else f"  {r['body']}")
        else:
            body_json = json.dumps(r["body"], ensure_ascii=False, indent=2)
            for bl in body_json.split("\n"):
                lines.append(f"  {bl}")
        lines.append("}")
    if r["after"]:
        lines.append("")
        lines.append("script:post-response {")
        lines.append(f"  {r['after']}")
        lines.append("}")
    if r["tests"]:
        lines.append("")
        lines.append("tests {")
        for label, js in r["tests"]:
            lines.append(f'  test("{label}", function() {{')
            lines.append(f"    {js}")
            lines.append("  });")
        lines.append("}")
    return "\n".join(lines) + "\n"


def main():
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(os.path.join(OUT, "environments"), exist_ok=True)

    with open(os.path.join(OUT, "bruno.json"), "w", encoding="utf-8") as f:
        json.dump({
            "version": "1",
            "name": COLLECTION_NAME,
            "type": "collection",
            "ignore": ["node_modules", ".git"],
        }, f, ensure_ascii=False, indent=2)

    with open(os.path.join(OUT, "collection.bru"), "w", encoding="utf-8") as f:
        f.write("""headers {
  Accept: application/json
}
""")

    with open(os.path.join(OUT, "environments", "localhost.bru"), "w", encoding="utf-8") as f:
        f.write("""vars {
  baseUrl: http://localhost:5080
}
""")

    folders = {}
    for r in R:
        folders.setdefault(r["folder"], []).append(r)

    for fi, (folder, items) in enumerate(folders.items(), 1):
        fdir = os.path.join(OUT, folder)
        os.makedirs(fdir, exist_ok=True)
        with open(os.path.join(fdir, "folder.bru"), "w", encoding="utf-8") as f:
            f.write(f"meta {{\n  name: {folder}\n  seq: {fi}\n}}\n")
        for seq, r in enumerate(items, 1):
            with open(os.path.join(fdir, r["fname"] + ".bru"), "w", encoding="utf-8") as f:
                f.write(bru_file(r, seq))

    print("bruno collection generated:", OUT)
    print("folders:", len(folders), "requests:", len(R))


if __name__ == "__main__":
    main()
