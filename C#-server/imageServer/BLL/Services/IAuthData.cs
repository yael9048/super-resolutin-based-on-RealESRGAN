using Acuity.DAL.Models;
using System.Threading.Tasks;

namespace Acuity.DAL.DataServices
{
    public interface IAuthData
    {
        Task<User?> GetUserByUsernameAsync(string username);
        Task<User?> GetUserByEmailAsync(string email); // הפונקציה הזו כנראה חסרה לך!
        Task<int> AddUserAsync(User user);             // וגם הפונקציה הזו
    }
}