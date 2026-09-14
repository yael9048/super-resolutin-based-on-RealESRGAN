using Acuity.DAL.DTO;
using Acuity.DAL.Models;
using System.Threading.Tasks;

namespace Acuity.BLL.Services
{
    public interface IAuthService
    {
        Task<User?> RegisterAsync(RegisterDto dto);
        Task<User?> LoginAsync(LoginDto dto);
    }
}