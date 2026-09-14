
using Acuity.DAL.Models;
using Acuity.DAL.DTO;
using Microsoft.EntityFrameworkCore;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace Acuity.DAL.DataServices
{
    
    public class ImagesData : IImagesData
    {
        private readonly AcuityDbContext _context;

     
        public ImagesData(AcuityDbContext context)
        {
            _context = context;
        }

        public async Task<int> AddNewImageAsync(UserImage image)
        {
            _context.UserImages.Add(image);
            await _context.SaveChangesAsync();
            return image.ImageId; // מחזיר את ה-ID החדש שנוצר במסד הנתונים
        }

        public async Task UpdateImageStatusAsync(UserImage image)
        {
            _context.UserImages.Update(image);
            await _context.SaveChangesAsync();
        }

        public async Task<List<ImageHistoryDto>> GetUserImagesHistoryAsync(int userId)
        {
            return await _context.UserImages
                .Where(img => img.UserId == userId)
                .OrderByDescending(img => img.UploadDate)
                .Select(img => new ImageHistoryDto
                {
                    ImageId = img.ImageId,
                    OriginalUrl = img.OriginalImagePath,
                    EnhancedUrl = img.EnhancedImagePath,
                    Status = img.ProcessingStatus,
                    UploadDate = img.UploadDate
                })
                .ToListAsync();
        }
        public async Task<UserImage> GetImageByIdAsync(int imageId)
        {
            return await _context.UserImages.FindAsync(imageId);
        }

        public async Task DeleteImageAsync(int imageId)
        {
            var image = await _context.UserImages.FindAsync(imageId);
            if (image != null)
            {
                _context.UserImages.Remove(image);
                await _context.SaveChangesAsync();
            }
        }
    }
}