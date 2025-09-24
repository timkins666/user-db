using Api.Models;

namespace api_tests.Models;

public class PostgresDbContextTests : IDisposable
{
    private readonly PostgresDbContext _context;

    public PostgresDbContextTests()
    {
        _context = TestDbContext.CreateInMemoryContext();
    }

    [Fact]
    public void DbContext_ShouldAddAndRetrieveUser()
    {
        var user = new User(Guid.NewGuid(), "Test", "User", new DateOnly(1990, 1, 1), DateTime.UtcNow);

        _context.Users.Add(user);
        _context.SaveChanges();

        var retrievedUser = _context.Users.Find(user.Id);
        Assert.NotNull(retrievedUser);
        Assert.Equal(user.FirstName, retrievedUser.FirstName);
    }

    [Fact]
    public void DbContext_ShouldFilterDeletedUsers()
    {
        var user1 = new User(Guid.NewGuid(), "Active", "User", new DateOnly(1990, 1, 1), DateTime.UtcNow);
        var user2 = new User(Guid.NewGuid(), "Deleted", "User", new DateOnly(1990, 1, 1), DateTime.UtcNow) { Deleted = true };

        _context.Users.AddRange(user1, user2);
        _context.SaveChanges();

        var activeUsers = _context.Users.Where(u => !u.Deleted).ToList();
        Assert.Single(activeUsers);
        Assert.Equal("Active", activeUsers[0].FirstName);
    }

    public void Dispose()
    {
        _context.Dispose();
        GC.SuppressFinalize(this);
    }
}