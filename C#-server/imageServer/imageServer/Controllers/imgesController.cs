using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.RateLimiting;
using Acuity.BLL.Services;
using System;
using System.Threading.Tasks;

namespace imageServer.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    public class ImagesController : ControllerBase
    {
        private readonly ImageService _imageService;

        public ImagesController(ImageService imageService)
        {
            _imageService = imageService;
        }

        [HttpGet("history/{userId}")]
        public async Task<IActionResult> GetHistory(int userId)
        {
            var history = await _imageService.GetUserHistoryAsync(userId);
            return Ok(history);
        }

        [HttpPost("enhance/{userId}")]
        [EnableRateLimiting("ImageEnhanceLimit")]
        [RequestSizeLimit(5 * 1024 * 1024)] // <-- הגבלת גודל הקובץ
        public async Task<IActionResult> EnhanceImage(int userId, IFormFile image)
        {
            if (image == null || image.Length == 0)
            {
                return BadRequest("לא נבחרה תמונה. אנא העלה קובץ.");
            }

            try
            {
                using var stream = image.OpenReadStream();
                var enhancedImageBytes = await _imageService.EnhanceImageAsync(userId, stream, image.FileName);

                return File(enhancedImageBytes, "image/jpeg");
            }
            catch (Exception ex)
            {
                // במקרה ששרת הפייתון קרס או החזיר שגיאה
                return StatusCode(500, $"שגיאה בעיבוד התמונה: {ex.Message}");
            }
        }
        [HttpDelete("{imageId}")]
        public async Task<IActionResult> DeleteImage(int imageId)
        {
            try
            {
                await _imageService.DeleteImageAsync(imageId);
                return Ok(new { message = "התמונה והקבצים נמחקו בהצלחה מההיסטוריה" });
            }
            catch (Exception ex)
            {
                return BadRequest($"שגיאה במחיקה: {ex.Message}");
            }
        }
    }
}