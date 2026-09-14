using Acuity.DAL.DataServices;
using Acuity.DAL.Models;
using Acuity.DAL.DTO;

namespace Acuity.BLL.Services
{
    public class ImageService
    {
        private readonly IImagesData _imagesData;
        private readonly HttpClient _httpClient;

        public ImageService(IImagesData imagesData, HttpClient httpClient)
        {
            _imagesData = imagesData;
            _httpClient = httpClient;
        }

        // --- בדיקת חתימת קובץ ---
        private bool IsValidImage(Stream stream)
        {
            //נציב במערך את הבתים הראשונים של כל קובצי התמונה האפשריים
            // בתים קבועים בכל הקבצים מאותו סוג
            byte[] jpegSignature = { 0xFF, 0xD8, 0xFF };
            byte[] pngSignature = { 0x89, 0x50, 0x4E, 0x47 };
            //נקרא את התמונה
            using var reader = new BinaryReader(stream, System.Text.Encoding.UTF8, true);
            //נציב במשתנה את הבתים הראשונים לצורך אימות
            var headerBytes = reader.ReadBytes(4);

            //נחזיר את הסמן בתמונה לבית ה0
            stream.Position = 0; 

            //אם הבתים הללו תואמים את המבנה של אחד מהתבניות המותרות - נחזיר תשובה חיובית
            if (headerBytes.Take(3).SequenceEqual(jpegSignature)) return true;
            if (headerBytes.Take(4).SequenceEqual(pngSignature)) return true;

            return false; // אם זו לא תמונה
        }

        public async Task<List<ImageHistoryDto>> GetUserHistoryAsync(int userId)
        {
            return await _imagesData.GetUserImagesHistoryAsync(userId);
        }




    public async Task<byte[]> EnhanceImageAsync(int userId, Stream imageStream, string fileName)
    {
        if (!IsValidImage(imageStream))
        {
            throw new Exception("Security Alert: הקובץ אינו תמונה תקינה.");
        }

        try
        {
            // הגדרת נתיב השמירה ושם קובץ ייחודי - כדי למנוע דריסת קבצים
            string uploadsFolder = Path.Combine(Directory.GetCurrentDirectory(), "uploads");
            if (!Directory.Exists(uploadsFolder)) Directory.CreateDirectory(uploadsFolder);
        
            string uniqueFileName = $"{userId}_{DateTime.Now.Ticks}_{fileName}";
            string originalFilePath = Path.Combine(uploadsFolder, uniqueFileName);

            // שמירת התמונה המקורית בכונן
            using (var fileStream = new FileStream(originalFilePath, FileMode.Create))
            {
                imageStream.Position = 0; // נוודא שקריאת הקובץ מתבצעת מהתחלה
                await imageStream.CopyToAsync(fileStream);
            }

            // שליחה לשרת פייתון לעיבוד
            imageStream.Position = 0; 
            var content = new MultipartFormDataContent();
            content.Add(new StreamContent(imageStream), "image", uniqueFileName);

            var response = await _httpClient.PostAsync("http://127.0.0.1:5000/enhance", content);
        
            if (!response.IsSuccessStatusCode)
            {
                var error = await response.Content.ReadAsStringAsync();
                // אם פייתון נכשל - נמחק את התמונה ששמרנו
                if (File.Exists(originalFilePath)) File.Delete(originalFilePath);
                throw new Exception($"התקבלה שגיאה מהflask: {error}");
            }

            var enhancedImageBytes = await response.Content.ReadAsByteArrayAsync();

            // 4. שמירת התמונה המשופרת בכונן
            string enhancedFileName = $"enhanced_{uniqueFileName}";
            string enhancedFilePath = Path.Combine(uploadsFolder, enhancedFileName);
            await File.WriteAllBytesAsync(enhancedFilePath, enhancedImageBytes);

            // 5.שמירת התמונה עם כל פרטי ההעלאה רק אחרי שהבקשה הצליחה
            var newImage = new UserImage
            {
                UserId = userId,
                OriginalImagePath = uniqueFileName,
                EnhancedImagePath = enhancedFileName,
                ProcessingStatus = "Completed",
                UploadDate = DateTime.Now
            };

            await _imagesData.AddNewImageAsync(newImage);

            return enhancedImageBytes;
        }
        catch (Exception ex)
        {
            throw new Exception($"תהליך שיפור התמונה נכשל: {ex.Message}");
        }
}
        public async Task DeleteImageAsync(int imageId)
        {
            // 1. נשלוף את פרטי התמונה כדי לדעת מהם שמות הקבצים
            var image = await _imagesData.GetImageByIdAsync(imageId);
            if (image == null)
            {
                throw new Exception("התמונה לא נמצאה במערכת.");
            }

            // 2. נגדיר את הנתיב לתיקיית ה-uploads
            string uploadsFolder = Path.Combine(Directory.GetCurrentDirectory(), "uploads");

            // 3. מחיקת הקובץ המקורי מהכונן
            if (!string.IsNullOrEmpty(image.OriginalImagePath))
            {
                string originalPath = Path.Combine(uploadsFolder, image.OriginalImagePath);
                if (File.Exists(originalPath)) File.Delete(originalPath);
            }

            // 4. מחיקת הקובץ המשופר מהכונן
            if (!string.IsNullOrEmpty(image.EnhancedImagePath))
            {
                string enhancedPath = Path.Combine(uploadsFolder, image.EnhancedImagePath);
                if (File.Exists(enhancedPath)) File.Delete(enhancedPath);
            }

            // 5. מחיקת הרשומה ממסד הנתונים
            await _imagesData.DeleteImageAsync(imageId);
        }

    }
}