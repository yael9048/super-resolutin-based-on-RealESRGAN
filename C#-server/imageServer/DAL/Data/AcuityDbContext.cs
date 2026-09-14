using Acuity.DAL.Models;
using Microsoft.EntityFrameworkCore;
using System.Reflection.Emit;
using Acuity.DAL.Models;
namespace Acuity.DAL.Models
{
    public class AcuityDbContext : DbContext
    {
        public AcuityDbContext(DbContextOptions<AcuityDbContext> options) : base(options) { }

        // אלו הטבלאות שיהיו זמינות לשליפות מהקוד
        public DbSet<User> Users { get; set; }
        public DbSet<UserImage> UserImages { get; set; }

        protected override void OnModelCreating(ModelBuilder modelBuilder)
        {
            base.OnModelCreating(modelBuilder);

            // מגדיר את הקשר של One-to-Many ואת מחיקת הקסקדה
            modelBuilder.Entity<UserImage>()
                .HasOne(img => img.User)
                .WithMany(u => u.UserImages)
                .HasForeignKey(img => img.UserId)
                .OnDelete(DeleteBehavior.Cascade);
        }
    }
}