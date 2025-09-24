using System.ComponentModel.DataAnnotations;

namespace Api.Models.Dto
{
    public record UserDto(
        Guid Id,
        string FirstName,
        string LastName,
        DateOnly DateOfBirth
    );

    public record CreateUserDto(
        [Required, StringLength(100, MinimumLength = 1)]
        string FirstName,
        [Required, StringLength(100, MinimumLength = 1)]
        string LastName,
        DateOnly DateOfBirth
    );
}