using Acuity.DAL.DataServices;
using Acuity.DAL.DTO;
using Acuity.DAL.Models;

namespace Acuity.BLL.Services
{
    public class AuthService : IAuthService
    {
        private readonly IAuthData _authData;

        public AuthService(IAuthData authData)
        {
            _authData = authData;
        }

        public async Task<User?> RegisterAsync(RegisterDto dto)
        {
            // 1.נבדוק האם המייל קיים - כי זה המזהה הייחודי
            var existingUserByEmail = await _authData.GetUserByEmailAsync(dto.Email);

            if (existingUserByEmail != null)
            {
                throw new Exception("כתובת המייל הזו כבר רשומה במערכת.");
            }

            // 2.המרת הסיסמה
            string hashedPassword = BCrypt.Net.BCrypt.HashPassword(dto.Password);
           
            // 3. יצירת אובייקט משתמש חדש לשמירה 
            var newUser = new User
            {
                Username = dto.Username, // יכול לחזור על עצמו אצל כמה משתמשים
                Email = dto.Email,       // ייחודי 
                PasswordHash = hashedPassword,
                CreatedAt = DateTime.Now
            };

            // 4. שמירה במסד הנתונים דרך שכבת ה-DAL
            await _authData.AddUserAsync(newUser);

            return newUser;
        }

        public async Task<User?> LoginAsync(LoginDto dto)
        {
            var user = await _authData.GetUserByEmailAsync(dto.Email);

            // אם המייל לא נמצא במערכת
            if (user == null)
            {
                return null;
            }

            // 2. אימות הסיסמה שהוזנה מול ההאש ששמור במסד הנתונים
            bool isPasswordValid = BCrypt.Net.BCrypt.Verify(dto.Password, user.PasswordHash);

            if (!isPasswordValid)
            {
                return null; // סיסמה שגויה
            }

            return user;
        }
    }
}