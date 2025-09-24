using Api.Models;

namespace api_tests.Models;

public class UserTests
{
    [Fact]
    public void User_ShouldCreateWithCorrectProperties()
    {
        var id = Guid.NewGuid();
        var createdAt = DateTime.UtcNow;
        var dateOfBirth = new DateOnly(1990, 1, 1);

        var user = new User(id, "Christopher", "Lee", dateOfBirth, createdAt);

        Assert.Equal(id, user.Id);
        Assert.Equal("Christopher", user.FirstName);
        Assert.Equal("Lee", user.LastName);
        Assert.Equal(dateOfBirth, user.DateOfBirth);
        Assert.Equal(createdAt, user.CreatedAt);
        Assert.False(user.Deleted);
    }

    [Fact]
    public void User_ShouldAllowSettingDeleted()
    {
        var user = new User(Guid.NewGuid(), "Miriam", "Margolyes", new DateOnly(1995, 5, 15), DateTime.UtcNow)
        {
            Deleted = true
        };

        Assert.True(user.Deleted);
    }
}