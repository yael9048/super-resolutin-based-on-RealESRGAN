// DAL/DTO/LoginDto.cs
using System.ComponentModel.DataAnnotations;

namespace Acuity.DAL.DTO
{
    public class LoginDto
    {
        [Required(ErrorMessage = "יש להזין כתובת מייל.")]
        [EmailAddress(ErrorMessage = "כתובת המייל אינה תקינה.")]
        public string Email { get; set; } = string.Empty;

        [Required(ErrorMessage = "יש להזין סיסמה.")]
        [RegularExpression(@".*[a-zA-Zא-ת].*", ErrorMessage = "הסיסמה חייבת להכיל לפחות אות אחת.")]
        public string Password { get; set; } = string.Empty;
    }
}