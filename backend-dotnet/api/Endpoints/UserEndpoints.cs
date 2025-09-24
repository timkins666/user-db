using System.Net;
using System.Text.RegularExpressions;
using Api.Models;
using Api.Models.Dto;
using Microsoft.EntityFrameworkCore;

namespace Api.Endpoints
{
    public static partial class UserEndpoints
    {
        [GeneratedRegex(@"^[a-zA-Z\s\-]+$")]
        private static partial Regex NameRegex();
        private static readonly DateOnly MinBirthDate = new(1990, 1, 1);

        public static WebApplication MapUserEndpoints(this WebApplication app)
        {
            app.MapGet("/users", async (PostgresDbContext dbContext) =>
            {
                return await dbContext.Users
                                .Where(u => !u.Deleted)
                                .Select(u => new UserDto(u.Id, u.FirstName, u.LastName, u.DateOfBirth))
                                .ToListAsync();
            }).WithName("GetAllUsers");

            app.MapPost("/users/create", async (PostgresDbContext dbContext, CreateUserDto createUser) =>
            {
                var validationErrors = ValidateUser(createUser);
                if (validationErrors.Count > 0)
                {
                    return Results.BadRequest(new { errors = validationErrors });
                }

                var user = new User(
                    Guid.NewGuid(),
                    createUser.FirstName,
                    createUser.LastName,
                    createUser.DateOfBirth,
                    DateTime.UtcNow
                );

                dbContext.Users.Add(user);
                await dbContext.SaveChangesAsync();

                var userDto = new UserDto(user.Id, user.FirstName, user.LastName, user.DateOfBirth);
                return Results.Created($"/users/{user.Id}", userDto);
            }).WithName("CreateUser");

            app.MapDelete("/user/{userId}", async (PostgresDbContext dbContext, Guid userId) =>
            {
                var user = await dbContext.Users.FindAsync(userId);

                if (user is not null)
                {
                    user.Deleted = true;
                    await dbContext.SaveChangesAsync();
                }

                return Results.StatusCode((int)HttpStatusCode.NoContent);
            }).WithName("DeleteUser");

            return app;
        }

        private static List<string> ValidateUser(CreateUserDto user)
        {
            var errors = new List<string>();

            if (!NameRegex().IsMatch(user.FirstName))
                errors.Add("First name can only contain letters, spaces, and hyphens");

            if (!NameRegex().IsMatch(user.LastName))
                errors.Add("Last name can only contain letters, spaces, and hyphens");

            if (user.DateOfBirth < MinBirthDate)
                errors.Add("Date of birth must be on or after 01/01/1990");

            var age = CalculateAge(user.DateOfBirth);
            if (age < 16)
                errors.Add("User must be at least 16 years old");

            return errors;
        }

        private static int CalculateAge(DateOnly birthDate)
        {
            var today = DateOnly.FromDateTime(DateTime.Today);
            var age = today.Year - birthDate.Year;
            if (birthDate > today.AddYears(-age)) age--;
            return age;
        }
    }
}