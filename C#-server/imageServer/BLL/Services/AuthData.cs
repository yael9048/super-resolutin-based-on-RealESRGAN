
using Acuity.DAL.Models;
using Microsoft.EntityFrameworkCore;
namespace Acuity.DAL.DataServices
{
    public class AuthData : IAuthData
    {
        private readonly AcuityDbContext _context;

        public AuthData(AcuityDbContext context)
        {
            _context = context;
        }

        public async Task<User?> GetUserByUsernameAsync(string username)
        {
            // מחפש במסד הנתונים משתמש עם השם הזה, אם אין מחזיר NULL
            return await _context.Users.FirstOrDefaultAsync(u => u.Username == username);
        }

        public async Task<User?> GetUserByEmailAsync(string email)
        {
            // מחפש לפי אימייל
            return await _context.Users.FirstOrDefaultAsync(u => u.Email == email);
        }

        public async Task<int> AddUserAsync(User user)
        {
            // שומר משתמש חדש
            _context.Users.Add(user);
            await _context.SaveChangesAsync();
            return user.Id;
        }
    }
}