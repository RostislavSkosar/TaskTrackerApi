using Microsoft.EntityFrameworkCore;
using TaskTrackerApi.Models;

namespace TaskTrackerApi.Data;

/// <summary>Контекст БД. Используется EF Core InMemory provider (не требует установки СУБД).</summary>
public class AppDbContext : DbContext
{
    public AppDbContext(DbContextOptions<AppDbContext> options) : base(options)
    {
    }

    public DbSet<Project> Projects => Set<Project>();

    public DbSet<ProjectTask> Tasks => Set<ProjectTask>();

    public DbSet<Comment> Comments => Set<Comment>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.Entity<Project>(e =>
        {
            e.HasIndex(p => p.Code).IsUnique();
            e.Property(p => p.Name).IsRequired();
            e.Property(p => p.Status).HasConversion<string>();
            e.Property(p => p.Priority).HasConversion<string>();
        });

        modelBuilder.Entity<ProjectTask>(e =>
        {
            e.Property(t => t.Title).IsRequired();
            e.Property(t => t.Status).HasConversion<string>();
            e.Property(t => t.Priority).HasConversion<string>();

            e.HasOne(t => t.Project)
                .WithMany(p => p.Tasks)
                .HasForeignKey(t => t.ProjectId)
                .OnDelete(DeleteBehavior.Cascade);
        });

        modelBuilder.Entity<Comment>(e =>
        {
            e.HasOne(c => c.Task)
                .WithMany(t => t.Comments)
                .HasForeignKey(c => c.ProjectTaskId)
                .OnDelete(DeleteBehavior.Cascade);
        });
    }
}
