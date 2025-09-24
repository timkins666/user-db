using System.Runtime.CompilerServices;
using Microsoft.EntityFrameworkCore;

namespace Api.Models
{
    public class PostgresDbContext : DbContext
    {
        public PostgresDbContext(DbContextOptions<PostgresDbContext> options) : base(options) { }

        public DbSet<User> Users { get; set; }

        protected override void OnModelCreating(ModelBuilder modelBuilder)
        {
            base.OnModelCreating(modelBuilder);

            modelBuilder.Entity<User>(entity =>
            {
                entity.ToTable("user");
                entity.HasKey(u => u.Id);
                entity.Property(u => u.Id).HasColumnName("id");
                entity.Property(u => u.FirstName).HasColumnName("firstname");
                entity.Property(u => u.LastName).HasColumnName("lastname");
                entity.Property(u => u.DateOfBirth).HasColumnName("date_of_birth");
                entity.Property(u => u.Deleted).HasColumnName("deleted");
                entity.Property(u => u.CreatedAt).HasColumnName("created_at");
            });
        }
    }

    public record User(
        Guid Id,
        string FirstName,
        string LastName,
        DateOnly DateOfBirth,
        DateTime CreatedAt
    )
    {
        public bool Deleted { get; set; }
    }
}
