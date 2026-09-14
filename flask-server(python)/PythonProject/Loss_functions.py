import torch
import torch.nn as nn
import torchvision.models as models

# ==============================================================================
# פונקציות הפסד
# ==============================================================================

class GANLoss(nn.Module):
#בין הגנרטור לדיסקרימינטור
    def __init__(self):
        super(GANLoss, self).__init__()
        # משתמשים ב-BCEWithLogitsLoss כי הוא כולל Sigmoid בפנים
        # זה מונע התפוצצות ערכים
        self.oss_fcn = nn.BCEWithLogitsLoss()

    def forward(self, input_tensor, target_is_real):
        # יצירת מפת מטרה (Target Map) דינמית באותו גודל כמו הקלט
        # אנחנו רוצים שהגנרטור ינסה לקבל 1 (אמיתי)
        # והדיסקרימינטור ינסה לתת לזה 0 (מזויף)
        if target_is_real:
            target_tensor = torch.ones_like(input_tensor)  # הכל 1.0
        else:
            target_tensor = torch.zeros_like(input_tensor) # הכל 0.0

        return self.loss_fcn(input_tensor, target_tensor)

class PerceptualLoss(nn.Module):
    """
    מחשבת את הדמיון בתוכן (Content) בין התמונה המקורית למזויפת.
    משתמשת ברשת VGG19 מאומנת כדי לחלץ מאפיינים.
    """
    def __init__(self):
        super(PerceptualLoss, self).__init__()

        # 1. טעינת VGG19 (רק החלק שמחלץ מאפיינים - Features)
        # pretrained=True כולל משקלים מאומנים (ולא אקראיים)
        vgg = models.vgg19(pretrained=True).features

        #הקפאת המשקולות (כי לא מאמנים את VGG)
        for param in vgg.parameters():
            param.requires_grad = False

        # 3. בחירת השכבות
        # אנחנו לוקחים את כל השכבות עד שכבה 35 - לפני החלק של זיהוי האובייקטים
        self.vgg_layers = nn.Sequential(*list(vgg.children())[:35]).eval()

        # פונקציית המרחק בין המאפיינים (L1 Loss)
        self.criterion = nn.L1Loss()

    def forward(self, sr, hr):
        """
        sr: Super Resolution (התמונה מהגנרטור)
        hr: High Resolution (התמונה מהדאטה)
        """
        #  נרמול התמונות לפי הנרמול שדורשת  VGG
        sr = (sr - self.mean) / self.std
        hr = (hr - self.mean) / self.std

        #  חילוץ מאפיינים (העברה דרך הרשת)
        sr_features = self.vgg_layers(sr)
        hr_features = self.vgg_layers(hr)

        # ג. חישוב ההבדל בין המאפיינים
        return self.criterion(sr_features, hr_features)