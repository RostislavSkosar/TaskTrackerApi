using Microsoft.EntityFrameworkCore;
using TaskTrackerApi.Models;

namespace TaskTrackerApi.Data;

/// <summary>Заполнение in-memory базы демонстрационными данными при старте приложения.</summary>
public static class DbInitializer
{
    public static void Seed(AppDbContext db)
    {
        if (db.Projects.Any())
            return;

        var now = DateTime.UtcNow;

        // ---------- Проект 1: активный, есть просроченные задачи ----------
        var shop = Project.Create(
            "Интернет-магазин «Вектор»", "SHOP",
            "Развитие каталога, корзины и личного кабинета покупателя.",
            Priority.High, now.AddDays(45));
        shop.Status = ProjectStatus.Active;

        var t1 = shop.AddTask("REST API каталога товаров", Priority.High, "Скосарь Р.А.", now.AddDays(-2));
        t1.ChangeStatus(Models.TaskStatus.ToDo);
        t1.ChangeStatus(Models.TaskStatus.InProgress);
        t1.SetEstimate(16);
        t1.LogWork(6.5, "спроектированы эндпоинты");
        t1.AddComment("Алёна К.", "Не забудьте пагинацию и фильтр по категориям.");
        t1.AddComment("Скосарь Р.А.", "@Алёна К. пагинацию добавил, фильтр будет в следующем спринте.");

        var t2 = shop.AddTask("Корзина и оформление заказа", Priority.Critical, "Игорь П.", now.AddDays(5));
        t2.ChangeStatus(Models.TaskStatus.ToDo);
        t2.SetEstimate(24);
        t2.AddComment("Игорь П.", "Нужен расчёт доставки по региону.");

        var t3 = shop.AddTask("Личный кабинет покупателя", Priority.Medium, "Мария Д.", now.AddDays(20));
        t3.ChangeStatus(Models.TaskStatus.ToDo);
        t3.SetEstimate(20);

        var t4 = shop.AddTask("Интеграция с платёжным шлюзом", Priority.High, null, now.AddDays(30));

        var t5 = shop.AddTask("Нагрузочное тестирование каталога", Priority.Low, "Игорь П.", now.AddDays(40));
        t5.ChangeStatus(Models.TaskStatus.ToDo);
        t5.ChangeStatus(Models.TaskStatus.InProgress);
        t5.ChangeStatus(Models.TaskStatus.Review);
        t5.SetEstimate(8);
        t5.LogWork(7.25, "профилирование");

        // ---------- Проект 2: все задачи закрыты → проект завершён ----------
        var crm = Project.Create(
            "CRM отдела продаж", "CRM",
            "Воронка сделок, карточки клиентов, отчёты по менеджерам.",
            Priority.Medium, now.AddDays(12));
        crm.Status = ProjectStatus.Active;

        var c1 = crm.AddTask("Миграция базы клиентов", Priority.High, "Мария Д.", now.AddDays(5));
        c1.SetEstimate(12);
        c1.ChangeStatus(Models.TaskStatus.ToDo);
        c1.ChangeStatus(Models.TaskStatus.InProgress);
        c1.LogWork(14, "с расхождением схемы");
        c1.ChangeStatus(Models.TaskStatus.Review);
        c1.ChangeStatus(Models.TaskStatus.Done);
        c1.AddComment("Мария Д.", "Миграция выполнена, 12 480 карточек перенесено.");

        var c2 = crm.AddTask("Воронка сделок", Priority.Medium, "Скосарь Р.А.", now.AddDays(-15));
        c2.SetEstimate(16);
        c2.ChangeStatus(Models.TaskStatus.ToDo);
        c2.ChangeStatus(Models.TaskStatus.InProgress);
        c2.LogWork(11.5, "быстрее оценки");
        c2.ChangeStatus(Models.TaskStatus.Review);
        c2.ChangeStatus(Models.TaskStatus.Done);
        c2.AddComment("Пётр С.", "Отлично, этап «Переговоры» теперь виден в отчёте.");

        var c3 = crm.AddTask("Экспорт отчётов в Excel", Priority.Low, null, now.AddDays(-5));
        c3.AddComment("Пётр С.", "Заказчик перешёл на встроенные дашборды, обсуждаем отмену.");
        c3.ChangeStatus(Models.TaskStatus.Cancelled);

        crm.Complete();

        // ---------- Проект 3: на паузе ----------
        var mobile = Project.Create(
            "Мобильное приложение курьера", "MOB",
            "Кроссплатформенное приложение на .NET MAUI: маршруты, сканер штрих-кодов.",
            Priority.High, now.AddDays(60));
        mobile.Hold("ожидание макетов от дизайнера");

        var m1 = mobile.AddTask("Каркас приложения на MAUI", Priority.High, "Скосарь Р.А.", now.AddDays(10));
        m1.ChangeStatus(Models.TaskStatus.ToDo);
        m1.SetEstimate(20);
        m1.AddComment("Скосарь Р.А.", "Собрал каркас, работает на Android и Windows.");

        var m2 = mobile.AddTask("Сканер штрих-кодов", Priority.Medium, null, now.AddDays(25));
        m2.AddComment("Алёна К.", "@Скосарь Р.А. проверьте библиотеку ZXing на iOS.");

        var m3 = mobile.AddTask("Офлайн-режим и синхронизация", Priority.Critical, null, now.AddDays(50));

        db.Projects.AddRange(shop, crm, mobile);
        db.SaveChanges();
    }
}
