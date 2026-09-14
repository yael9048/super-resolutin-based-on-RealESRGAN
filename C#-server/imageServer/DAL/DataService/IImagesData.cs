using Acuity.DAL.Models;
using Acuity.DAL.DTO;
using System.Collections.Generic;
using System.Threading.Tasks;

namespace Acuity.DAL.DataServices
{
    public interface IImagesData
    {
        Task<int> AddNewImageAsync(UserImage image);
        Task UpdateImageStatusAsync(UserImage image);
        Task<List<ImageHistoryDto>> GetUserImagesHistoryAsync(int userId);
        Task<UserImage> GetImageByIdAsync(int imageId);
        Task DeleteImageAsync(int imageId);
    }
}