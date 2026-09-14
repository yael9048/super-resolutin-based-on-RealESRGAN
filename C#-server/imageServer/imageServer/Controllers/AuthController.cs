using Acuity.BLL.Services;
using Acuity.DAL.DTO;
using Microsoft.AspNetCore.Mvc;
using System;
using System.Threading.Tasks;

namespace imageServer.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    public class AuthController : ControllerBase
    {
        private readonly IAuthService _authService;

        
        public AuthController(IAuthService authService)
        {
            _authService = authService;
        }

        [HttpPost("register")]
        public async Task<IActionResult> Register([FromBody] RegisterDto dto)
        {
            try
            {
                var newUser = await _authService.RegisterAsync(dto);
                // אנחנו לא רוצים להחזיר את הסיסמה המוצפנת ללקוח, אז נחזיר רק הודעת הצלחה או אובייקט חלקי
                return Ok(new { message = "ההרשמה בוצעה בהצלחה!", userId = newUser.Id, username = newUser.Username });
            }
            catch (Exception ex)
            {
                // מחזיר את השגיאה שזרקנו מה-BLL (למשל: "כתובת המייל הזו כבר רשומה במערכת")
                return BadRequest(new { message = ex.Message });
            }
        }

        [HttpPost("login")]
        public async Task<IActionResult> Login([FromBody] LoginDto dto)
        {
            var user = await _authService.LoginAsync(dto);

            if (user == null)
            {
                return Unauthorized(new { message = "אימייל או סיסמה שגויים." });
            }

            return Ok(new { message = "התחברת בהצלחה!", userId = user.Id, username = user.Username });
        }
    }
}