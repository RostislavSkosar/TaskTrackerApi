import json, os, sys, time, urllib.request, urllib.error, datetime

BASE = "http://127.0.0.1:5080"
out = []

def req(method, path, body=None, note=""):
    url = BASE + path
    data = None
    headers = {"Accept": "application/json"}
    if body is not None:
        if isinstance(body, str):
            data = body.encode()
            headers["Content-Type"] = "application/json"
        else:
            data = json.dumps(body, ensure_ascii=False).encode()
            headers["Content-Type"] = "application/json"
    r = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(r, timeout=30) as resp:
            code = resp.status
            text = resp.read().decode()
    except urllib.error.HTTPError as e:
        code = e.code
        text = e.read().decode()
    except Exception as e:
        code = -1
        text = str(e)
    out.append({"note": note, "method": method, "path": path, "body": body, "status": code, "response": text})
    print(f"[{code}] {method} {path}  {note}")
    try:
        return code, json.loads(text)
    except Exception:
        return code, text

future = lambda d: (datetime.datetime.utcnow() + datetime.timedelta(days=d)).strftime("%Y-%m-%dT%H:%M:%SZ")

req("GET", "/api/projects", note="Список проектов (Where + Select)")
req("GET", "/api/projects/1", note="Проект по Id с расчётными показателями")
req("POST", "/api/projects", {"name": "Портал университета", "code": "UNI", "description": "Личный кабинет студента", "priority": "Medium", "deadlineUtc": future(90)}, note="Создание проекта")
req("POST", "/api/projects", {"name": "Портал университета", "code": "uni", "priority": "Medium"}, note="Дубликат кода -> 400")
req("POST", "/api/projects", {"name": "Портал университета", "code": "PORTALDEV", "priority": "Medium"}, note="Код длиннее 8 символов -> 400 (валидация модели)")
req("PUT", "/api/projects/4", {"name": "Портал университета v2", "priority": "High"}, note="Обновление проекта")
req("GET", "/api/projects/2", note="Завершённый проект")
req("POST", "/api/projects/2/hold?reason=%D1%82%D0%B5%D1%81%D1%82", note="Пауза завершённого проекта -> 400")

req("GET", "/api/tasks?projectId=1", note="Задачи проекта 1")
req("GET", "/api/tasks?overdueOnly=true", note="Только просроченные задачи")
req("GET", "/api/tasks/1", note="Задача по Id")
req("POST", "/api/tasks?projectId=1", {"title": "Кеширование каталога", "description": "Redis", "priority": "Medium", "assignee": "Скосарь Р.А.", "dueDateUtc": future(12)}, note="Создание задачи")
req("POST", "/api/tasks?projectId=1", {"title": "REST API каталога товаров", "priority": "Low"}, note="Дубликат названия задачи в проекте -> 400")
req("PUT", "/api/tasks/4/status", {"status": "InProgress"}, note="Старт задачи без исполнителя -> 400")
req("PUT", "/api/tasks/4/assignee?assignee=%D0%98%D0%B3%D0%BE%D1%80%D1%8C%20%D0%9F.", note="Назначение исполнителя")
req("PUT", "/api/tasks/4/status", {"status": "InProgress"}, note="Перевод в работу")
req("PUT", "/api/tasks/4/status", {"status": "Done"}, note="Закрытие из InProgress -> 400 (только из Review)")
req("PUT", "/api/tasks/4/status", {"status": "Review"}, note="Перевод в Review")
req("PUT", "/api/tasks/4/status", {"status": "Done"}, note="Закрытие из Review -> 200")
req("POST", "/api/tasks/4/work", {"hours": 3, "note": "реализация"}, note="Списание времени на закрытую задачу -> 400")
req("PUT", "/api/tasks/3/estimate", {"hours": 20}, note="Установка оценки")
req("POST", "/api/tasks/3/work", {"hours": 2.5, "note": "вёрстка"}, note="Списание трудозатрат")
req("POST", "/api/tasks/3/work", {"hours": 60, "note": "слишком много"}, note="Списание > 24 ч -> 400")
req("PUT", "/api/tasks/3/reschedule", {"dueDateUtc": future(30), "reason": "перенос спринта"}, note="Перенос срока")
req("GET", "/api/tasks/my-board?assignee=%D0%A1%D0%BA%D0%BE%D1%81%D0%B0%D1%80%D1%8C", note="Доска исполнителя (join в синтаксисе запросов LINQ)")

req("GET", "/api/comments?taskId=1", note="Комментарии задачи 1")
req("POST", "/api/tasks/1/comments", {"author": "Скосарь Р.А.", "text": "@Игорь П. проверь интеграцию с оплатой"}, note="Создание комментария через задачу")
req("POST", "/api/comments?taskId=2", {"author": "Мария Д.", "text": "Добавила макеты экрана корзины"}, note="Создание комментария")
req("PUT", "/api/comments/1", {"editor": "Игорь П.", "text": "Чужой комментарий"}, note="Правка чужого комментария -> 400")
req("PUT", "/api/comments/1", {"editor": "Алёна К.", "text": "Уточнение: пагинация курсорная"}, note="Правка своим комментарием -> 200")
req("DELETE", "/api/comments/6", note="Удаление комментария")

req("GET", "/api/analytics/projects-statistics", note="ЗАПРОС 1: статистика проектов")
req("GET", "/api/analytics/projects-statistics?onlyActive=true", note="ЗАПРОС 1: только активные")
req("GET", "/api/analytics/overdue-tasks", note="ЗАПРОС 2: просроченные задачи + проекты + комментарии")
req("GET", "/api/analytics/assignees-summary", note="ЗАПРОС 3: сводка по исполнителям")
req("GET", "/api/analytics/task-discussions?take=3", note="ЗАПРОС 4: самые обсуждаемые задачи")
req("GET", "/api/analytics/projects-activity", note="ЗАПРОС 5: активность обсуждения проектов")
req("GET", "/api/projects/1/details", note="Полная карточка проекта (проект+задачи+комментарии)")

req("DELETE", "/api/tasks/4", note="Удаление закрытой задачи")
req("DELETE", "/api/projects/1", note="Удаление проекта с задачами -> 400")
req("POST", "/api/projects/2/archive", note="Архивация завершённого проекта")
req("DELETE", "/api/projects/2", note="Удаление архивированного проекта -> 204")
req("GET", "/api/projects/99", note="Несуществующий проект -> 404")

os.makedirs("test_results", exist_ok=True)
OUT = "test_results/responses.json"
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print("saved", len(out), "responses ->", os.path.abspath(OUT))
