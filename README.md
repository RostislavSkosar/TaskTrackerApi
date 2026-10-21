# Лабораторная работа. Web API «Трекер задач» (ASP.NET Core, .NET 8)

**Дисциплина:** Технологии кроссплатформенной разработки
**Выполнил:** Скосарь Р.А., группа АС-23-04

## Состав работы

```
Lab_WebAPI/
├── TaskTrackerApi.sln                     – решение Visual Studio / Rider
├── runtest.sh                             – сборка, запуск API и прогон 43 проверочных запросов
├── bruno/                                 – коллекция Bruno: 49 запросов, окружение, автотесты
├── src/TaskTrackerApi/                    – проект Web API
│   ├── Models/                            – модель предметной области (бизнес-логика)
│   │   ├── Enums.cs                       – Priority, ProjectStatus, TaskStatus
│   │   ├── DomainException.cs             – ошибка бизнес-правила + интерфейс IHasDeadline
│   │   ├── Project.cs                     – проект: валидация, сроки, жизненный цикл, статистика
│   │   ├── ProjectTask.cs                 – задача: канбан-переходы, трудозатраты, сроки
│   │   └── Comment.cs                     – комментарий: автор, окно редактирования 24 ч
│   ├── Data/
│   │   ├── AppDbContext.cs                – контекст EF Core (InMemory)
│   │   └── DbInitializer.cs               – демонстрационные данные
│   ├── DTOs/Dtos.cs                       – record-DTO запросов/ответов + маппинг
│   ├── Controllers/
│   │   ├── ProjectsController.cs          – CRUD проектов + команды + карточка проекта
│   │   ├── TasksController.cs             – CRUD задач + команды + my-board (join)
│   │   ├── CommentsController.cs          – CRUD комментариев
│   │   └── AnalyticsController.cs         – 5 запросов на объединение данных (LINQ)
│   ├── Infrastructure/DomainExceptionHandler.cs – DomainException → HTTP 400 (ProblemDetails)
│   ├── Program.cs                         – точка входа
│   └── Properties/launchSettings.json     – http://localhost:5080
└── report/                                – отчёт и материалы
    ├── build_report.py                    – генерация отчёта .docx (python-docx)
    ├── make_figures.py                    – генерация рисунков (Pillow)
    ├── make_bruno.py                      – генерация коллекции Bruno
    ├── make_zip.py                        – упаковка работы в zip
    ├── test_requests.py                   – автотест 43 HTTP-запросов
    ├── test_results/responses.json     – фактические ответы сервера
    └── img/                               – рисунки отчёта
```

Отчёт: `Отчет_Скосарь_АС-23-04_Технологии_кроссплатформенной_разработки.docx` (в корне Lab_WebAPI).

## Запуск

Требуется .NET SDK 8.0+.

```bash
dotnet run --project src/TaskTrackerApi
# API:        http://localhost:5080
# Swagger UI: http://localhost:5080/swagger
```

Хранилище — EF Core InMemory: база живёт в процессе и заполняется данными
(`DbInitializer.Seed`) при каждом старте, СУБД устанавливать не нужно.

## Проверочные запросы (примеры)

```bash
# CRUD
curl http://localhost:5080/api/projects
curl -X POST http://localhost:5080/api/projects -H "Content-Type: application/json" \
     -d '{"name":"Портал университета","code":"UNI","priority":"Medium"}'
curl -X PUT  http://localhost:5080/api/projects/1 -H "Content-Type: application/json" \
     -d '{"name":"Интернет-магазин «Вектор» (v2)"}'
curl -X DELETE http://localhost:5080/api/projects/3

curl "http://localhost:5080/api/tasks?projectId=1&overdueOnly=true"
curl -X POST "http://localhost:5080/api/tasks?projectId=1" -H "Content-Type: application/json" \
     -d '{"title":"Кеширование каталога","priority":"Medium","assignee":"Скосарь Р.А."}'
curl -X PUT  http://localhost:5080/api/tasks/4/status -H "Content-Type: application/json" \
     -d '{"status":"InProgress"}'
curl -X POST http://localhost:5080/api/tasks/3/work -H "Content-Type: application/json" \
     -d '{"hours":2.5,"note":"вёрстка"}'

curl "http://localhost:5080/api/comments?taskId=1"
curl -X POST "http://localhost:5080/api/comments?taskId=2" -H "Content-Type: application/json" \
     -d '{"author":"Мария Д.","text":"Добавила макеты экрана корзины"}'

# Запросы на объединение данных (LINQ)
curl http://localhost:5080/api/analytics/projects-statistics
curl http://localhost:5080/api/analytics/overdue-tasks
curl http://localhost:5080/api/analytics/assignees-summary
curl http://localhost:5080/api/analytics/task-discussions?take=3
curl http://localhost:5080/api/analytics/projects-activity
curl http://localhost:5080/api/projects/1/details
curl "http://localhost:5080/api/tasks/my-board?assignee=Скосарь"
```

## Проверка запросов в Bruno

В папке `bruno/` лежит готовая коллекция Bruno (49 запросов, 6 папок, окружение `localhost`,
автотесты в каждом запросе).

1. Установите Bruno: Windows — `winget install Bruno.Bruno` (или установщик с usebruno.com),
   macOS — `brew install bruno`, Linux — AppImage/deb с сайта.
2. Запустите API: `dotnet run --project src/TaskTrackerApi` (или F5 в Visual Studio).
3. В Bruno: **Open Collection** → выберите папку `Lab_WebAPI/bruno`.
4. Справа сверху выберите окружение **localhost** (`baseUrl = http://localhost:5080`).
5. Открывайте запросы по папкам 01 → 06 и жмите **Send**; результаты проверок — вкладка **Tests**.
   Или запустите всё сразу: правый клик по коллекции → **Run Collection** → **Run**.
6. То же из командной строки (Node.js): `cd bruno && npx @usebruno/cli run --env localhost`
   (проверено: 49/49 запросов, 108/108 тестов — PASS).

Особенности коллекции: папки выполняются по порядку (06 «Очистка» меняет данные — для повтора
перезапустите API, InMemory-база снова заполнится демо-данными); запросы создания сохраняют Id
в переменные коллекции (`createdProjectId`, `createdTaskId`, `createdCommentId`) через
`script:post-response`, поэтому зависимые запросы работают без правки Id вручную.

## Автоматический прогон всех сценариев

```bash
bash runtest.sh          # сборка + запуск + 43 запроса, отчёт в report/test_results/responses.json
```

## Ключевые бизнес-правила модели

1. Задачу нельзя взять в работу и закрыть без исполнителя; `Done` — только из `Review`.
2. Списание времени: 0.25–24 ч за раз, суммарно не более двойной оценки, на закрытую задачу — нельзя.
3. Срок задачи не позже срока проекта; срок проекта не раньше даты создания.
4. Проект завершается только при закрытых задачах; архивируется только завершённый и без просрочек.
5. В закрытый проект задачи не добавляются; названия задач в проекте уникальны.
6. Комментарий правит только автор и только в течение 24 часов.

Нарушение правила → `DomainException` → HTTP 400 с текстом причины (ProblemDetails).
