using Acuity.BLL.Services;
using Acuity.DAL.DataServices;
using Acuity.DAL.Models;
using Microsoft.AspNetCore.RateLimiting;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.FileProviders;
var builder = WebApplication.CreateBuilder(args);

// --- תוספת 1: הגדרת ה-CORS כדי שהאנגולר יוכל לגשת ---
builder.Services.AddCors(options =>
{
    options.AddPolicy("AllowAngular", policy =>
    {
        policy.AllowAnyOrigin()// הכתובת של האנגולר שלך
              .AllowAnyHeader()
              .AllowAnyMethod();
    });
});


// --------------------------------------------------
// --- הגנה מעומס קריסות ---
builder.Services.AddRateLimiter(options =>
{
    options.AddFixedWindowLimiter("ImageEnhanceLimit", opt =>
    {
        opt.Window = TimeSpan.FromMinutes(1); // חלון של דקה
        opt.PermitLimit = 3; // מקסימום 3 בקשות בדקה לאדם
        opt.QueueLimit = 0; // בקשות מעבר ל-3 הראשונות יידחו ולא ישמרו בתור
    });
});

// הוספת שירותים נדרשים
builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer(); // נדרש עבור Minimal APIs ו-Swagger
builder.Services.AddSwaggerGen(); // רישום Swagger




// 1. חיבור למסד הנתונים
builder.Services.AddDbContext<AcuityDbContext>(options =>
    options.UseSqlServer(builder.Configuration.GetConnectionString("DefaultConnection"),
    sqlServerOptionsAction: sqlOptions =>
    {
        sqlOptions.EnableRetryOnFailure(); 
    }));

// 2. רישום השירותים של ה-DAL וה-BLL
builder.Services.AddScoped<IImagesData, ImagesData>();
builder.Services.AddScoped<ImageService>();
// הוספת השירותים של ההזדהות
builder.Services.AddScoped<IAuthData, AuthData>();
builder.Services.AddScoped<IAuthService, AuthService>();

// הוספת היכולת לתקשר עם השרת פייתון
builder.Services.AddHttpClient();
var app = builder.Build();

// הגדרת צינור הבקשות
if (app.Environment.IsDevelopment())
{
    app.UseSwagger(); // ייצור קובץ ה-JSON של ה-OpenAPI
    app.UseSwaggerUI(); // הפעלת ממשק ה-UI של Swagger
}

app.UseHttpsRedirection();

app.UseCors("AllowAngular");

// יצירת תיקיית התמונות אם היא לא קיימת
var uploadsFolder = Path.Combine(Directory.GetCurrentDirectory(), "uploads");
if (!Directory.Exists(uploadsFolder))
{
    Directory.CreateDirectory(uploadsFolder);
}

// פתיחת התיקייה לגישה מהאינטרנט
app.UseStaticFiles(new StaticFileOptions
{
    FileProvider = new PhysicalFileProvider(uploadsFolder),
    RequestPath = "/uploads"
});
// ----------------------------------------------------------------------

app.UseAuthorization();
app.UseRateLimiter(); 
app.MapControllers();

app.Run();