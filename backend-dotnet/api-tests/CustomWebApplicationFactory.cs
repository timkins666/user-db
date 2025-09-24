using Api.Models;
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Mvc.Testing;
using Microsoft.Data.Sqlite;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.DependencyInjection.Extensions;

namespace api_tests;

public class CustomWebApplicationFactory : WebApplicationFactory<Program>
{
    private readonly SqliteConnection _connection;
    private PostgresDbContext? _db;

    public PostgresDbContext Db
    {
        get
        {
            if (_db is null)
            {
                var scope = Services.CreateScope();
                _db = scope.ServiceProvider.GetRequiredService<PostgresDbContext>();
            }
            return _db;
        }
    }

    public CustomWebApplicationFactory()
    {
        _connection = new SqliteConnection("DataSource=:memory:");
        _connection.Open();
    }

    protected override void ConfigureWebHost(IWebHostBuilder builder)
    {
        builder.ConfigureServices(services =>
            {
                services.RemoveAll<Microsoft.EntityFrameworkCore.Infrastructure.ServiceProviderAccessor>();
                services.RemoveAll<Microsoft.EntityFrameworkCore.Infrastructure.IDbContextOptionsConfiguration<PostgresDbContext>>();
                services.RemoveAll<DbContextOptions<PostgresDbContext>>();
                services.RemoveAll<DbContextOptions>();
                services.RemoveAll<PostgresDbContext>();

                services.AddDbContext<PostgresDbContext>(options => options.UseSqlite(_connection));
            });
    }

    public new HttpClient CreateClient()
    {
        ResetDb();
        return base.CreateClient();
    }

    public void ResetDb(Action<PostgresDbContext>? seeder = null)
    {
        Db.Database.OpenConnection();
        Db.Database.EnsureDeleted();
        Db.Database.EnsureCreated();

        seeder?.Invoke(Db);
        Db.SaveChanges();
    }

    public CustomWebApplicationFactory AddUsers(params User[] users)
    {
        Db.Users.AddRange(users);
        Db.SaveChanges();

        return this;
    }


    public new void Dispose()
    {
        base.Dispose();
        _connection.Dispose();
    }
}
