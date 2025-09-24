using Api.Models;
using Microsoft.EntityFrameworkCore;

namespace api_tests;

public static class TestDbContext
{
    public static PostgresDbContext CreateInMemoryContext()
    {
        var options = new DbContextOptionsBuilder<PostgresDbContext>()
            .UseSqlite("DataSource=:memory:")
            .Options;

        var context = new PostgresDbContext(options);
        context.Database.OpenConnection();
        context.Database.EnsureCreated();
        return context;
    }
}