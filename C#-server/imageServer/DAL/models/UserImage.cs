using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

using System;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace Acuity.DAL.Models
{
    [Table("UserImages")] // מקשר לטבלת UserImages
    public class UserImage
    {
        [Key]
        public int ImageId { get; set; }

        [Required]
        public int UserId { get; set; }

        [Required]
        [StringLength(500)]
        public string OriginalImagePath { get; set; } = string.Empty;

        [StringLength(500)]
        public string? EnhancedImagePath { get; set; }

        [StringLength(20)]
        public string ProcessingStatus { get; set; } = "Pending";

        public DateTime UploadDate { get; set; } = DateTime.Now;

        // מפתח זר שמצביע למשתמש הרלוונטי
        [ForeignKey("UserId")]
        public User User { get; set; } = null!;
    }
}