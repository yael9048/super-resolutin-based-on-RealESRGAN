// DAL/DTO/ImageHistoryDto.cs
using System;

namespace Acuity.DAL.DTO
{
    public class ImageHistoryDto
    {
        public int ImageId { get; set; }
        public string OriginalUrl { get; set; } = string.Empty;
        public string? EnhancedUrl { get; set; }
        public string Status { get; set; } = string.Empty;
        public DateTime UploadDate { get; set; }
    }
}