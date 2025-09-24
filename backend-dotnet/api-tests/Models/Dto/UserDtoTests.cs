using Api.Models.Dto;

namespace api_tests.Models.Dto;

public class UserDtoTests
{
    [Fact]
    public void UserDto_ShouldCreateCorrectly()
    {
        var id = Guid.NewGuid();
        var userDto = new UserDto(id, "Miriam", "Margolyes", new DateOnly(1995, 5, 15));
        
        Assert.Equal(id, userDto.Id);
        Assert.Equal("Miriam", userDto.FirstName);
        Assert.Equal("Margolyes", userDto.LastName);
        Assert.Equal(new DateOnly(1995, 5, 15), userDto.DateOfBirth);
    }

    [Fact]
    public void CreateUserDto_ShouldCreateCorrectly()
    {
        var createUser = new CreateUserDto("Christopher", "Lee", new DateOnly(2000, 1, 1));
        
        Assert.Equal("Christopher", createUser.FirstName);
        Assert.Equal("Lee", createUser.LastName);
        Assert.Equal(new DateOnly(2000, 1, 1), createUser.DateOfBirth);
    }
}