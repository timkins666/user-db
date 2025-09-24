using System.Net;
using System.Text;
using System.Text.Json;
using Api.Models;
using Api.Models.Dto;
using Microsoft.EntityFrameworkCore;

namespace api_tests.Endpoints;

public class UserEndpointsTests : IClassFixture<CustomWebApplicationFactory>
{
    private readonly CustomWebApplicationFactory _factory;
    private readonly JsonSerializerOptions _jsonOptions;

    public UserEndpointsTests(CustomWebApplicationFactory factory)
    {
        _factory = factory;
        _jsonOptions = new JsonSerializerOptions { PropertyNamingPolicy = JsonNamingPolicy.CamelCase };
    }

    [Fact]
    public async Task GetUsers_ShouldReturnEmptyList_WhenNoUsers()
    {
        var client = _factory.CreateClient();

        var response = await client.GetAsync("/users");

        response.EnsureSuccessStatusCode();
        var content = await response.Content.ReadAsStringAsync();
        var users = JsonSerializer.Deserialize<List<UserDto>>(content, _jsonOptions);
        Assert.NotNull(users);
        Assert.Empty(users);
    }

    [Fact]
    public async Task GetUsers_ShouldReturnActiveUsers_WhenUsersExist()
    {
        var client = _factory.CreateClient();

        _factory.AddUsers(
            new User(Guid.NewGuid(), "Christopher", "Lee", new DateOnly(1990, 1, 1), DateTime.UtcNow),
            new User(Guid.NewGuid(), "Miriam", "Margolyes", new DateOnly(1995, 5, 15), DateTime.UtcNow) { Deleted = true }
        );

        var response = await client.GetAsync("/users");

        response.EnsureSuccessStatusCode();
        var content = await response.Content.ReadAsStringAsync();
        var users = JsonSerializer.Deserialize<List<UserDto>>(content, _jsonOptions);
        Assert.NotNull(users);
        Assert.Single(users);
        Assert.Equal("Christopher", users[0].FirstName);

        Assert.Contains("firstName", content);
        Assert.Contains("lastName", content);
        Assert.Contains("dateOfBirth", content);
    }

    [Fact]
    public async Task CreateUser_ShouldReturnCreated_WhenValidUser()
    {
        var createUser = new CreateUserDto("Christopher", "Lee", new DateOnly(2000, 1, 3));
        var json = JsonSerializer.Serialize(createUser, _jsonOptions);
        var content = new StringContent(json, Encoding.UTF8, "application/json");

        var client = _factory.CreateClient();
        var response = await client.PostAsync("/users/create", content);

        Assert.Equal(HttpStatusCode.Created, response.StatusCode);
        var responseContent = await response.Content.ReadAsStringAsync();
        var user = JsonSerializer.Deserialize<UserDto>(responseContent, _jsonOptions);

        Assert.Equal("Christopher", user?.FirstName);
        Assert.Equal("Lee", user?.LastName);
        Assert.Equal(new DateOnly(2000, 1, 3), user?.DateOfBirth);

        Assert.Contains("firstName", responseContent);
        Assert.Contains("lastName", responseContent);
        Assert.Contains("dateOfBirth", responseContent);

        var dbUser = await _factory.Db.Users.FindAsync(user?.Id);
        Assert.NotNull(dbUser);
    }

    [Fact]
    public async Task CreateUser_ShouldReturnBadRequest_WhenUserTooYoung()
    {
        var createUser = new CreateUserDto("Young", "User", DateOnly.FromDateTime(DateTime.Today.AddYears(-10)));
        var json = JsonSerializer.Serialize(createUser, _jsonOptions);
        var content = new StringContent(json, Encoding.UTF8, "application/json");

        var client = _factory.CreateClient();
        var response = await client.PostAsync("/users/create", content);

        Assert.Equal(HttpStatusCode.BadRequest, response.StatusCode);
    }

    [Theory]
    [InlineData("", "Lee")]
    [InlineData("Chris123", "Lee")]
    [InlineData("Chris", "")]
    [InlineData("Chris", "Lee!")]
    public async Task CreateUser_ShouldReturnBadRequest_WhenInvalidName(string firstName, string lastName)
    {
        var createUser = new CreateUserDto(firstName, lastName, new DateOnly(2000, 1, 1));
        var json = JsonSerializer.Serialize(createUser, _jsonOptions);
        var content = new StringContent(json, Encoding.UTF8, "application/json");

        var client = _factory.CreateClient();
        var response = await client.PostAsync("/users/create", content);

        Assert.Equal(HttpStatusCode.BadRequest, response.StatusCode);
    }

    [Fact]
    public async Task DeleteUser_ShouldReturnNoContent_WhenUserExists()
    {
        var client = _factory.CreateClient();

        var userId = Guid.NewGuid();
        _factory.AddUsers(new User(userId, "Christopher", "Lee", new DateOnly(1990, 1, 1), DateTime.UtcNow));

        var response = await client.DeleteAsync($"/user/{userId}");

        Assert.Equal(HttpStatusCode.NoContent, response.StatusCode);

        var deletedUser = await _factory.Db.Users.AsNoTracking().FirstOrDefaultAsync(u => u.Id == userId);
        Assert.True(deletedUser?.Deleted);
    }

    [Fact]
    public async Task DeleteUser_ShouldReturnNoContent_WhenUserDoesNotExist()
    {
        var client = _factory.CreateClient();
        var response = await client.DeleteAsync($"/user/{Guid.NewGuid()}");

        Assert.Equal(HttpStatusCode.NoContent, response.StatusCode);
    }
}