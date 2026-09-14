import torch
from torch import nn as nn
from torch.nn import functional as F
from torch.nn.utils import spectral_norm

#פונקציית עזר שמטרתה לנרמל את ערכי המשקולות במהלך האימון
def sn_conv2d(in_channels, out_channels, kernel_size, stride=1, padding=0, bias=True):
    # יצירת השכבה
    layer = nn.Conv2d(in_channels, out_channels, kernel_size, stride, padding, bias=bias)
    # נרמול הנתונים מהשכבה למעלה
    return spectral_norm(layer)

class UNetDiscriminatorSN(nn.Module):
  def __init__(self,num_in_ch, num_feat=64, skip_connection=True):
    super(UNetDiscriminatorSN, self).__init__()
    # נגדיר לו לשמור את כל המאפיינים בשלבי ההקטנה
    self.skip_connection = skip_connection
    norm = spectral_norm
    #נבנה עשר שכבות קונבולציה :
    #שכבה ראשונה משאירה את התמונה כמו שהיא בגודל
    #אבל מוסיפה לה ערוצים למאפיינים נוספים שהיא מוצאת באמצעות הקרנלים שהיא מגדירה
    #היא מגדירה (num_feat) קרנלים - כל אחד מזהה משהו אחר בתמונה
    self.conv0 = nn.Conv2d(num_in_ch, num_feat, kernel_size=3, stride=1, padding=1)
    #שלושת השכבות הראשונות מבצעות הקטנה לתמונה
    #הקטנה זו מתבצעת במטרה לאפשר לרשת לראות אובייקטים מרכזיים בתמונה
    #בלי להתמקד בכל פיקסל בודד אלא לקלוט קווים כלליים
    #ההקטנה מתבצעת ב-3 שכבות כדי לאפשר למידה של המאפיינים בצורה הדרגתית
    #קודם כל מאפיינים עדינים ובהמשך יותר ויותר כלליים
    #במהלך ההקטנה שומרים את כל הנתונים מהתמונה המקורית כדי להשתמש בזה בשלב ההגדלה
    self.conv1 = norm(nn.Conv2d(num_feat, num_feat * 2, 4, 2, 1, bias=False)) #נבטל את הbias כדי לא לפגוע בנרמול
    self.conv2 = norm(nn.Conv2d(num_feat * 2, num_feat * 4, 4, 2, 1, bias=False))#
    self.conv3 = norm(nn.Conv2d(num_feat * 4, num_feat * 8, 4, 2, 1, bias=False))
    #שלב ההגדלה:
    #ההגדלה מתבצעת בצורה סימטרית לשלב ההקטנה
    #בשלב ההגדלה הראשון נחזיר את התמונה לגודל המקורי שלה
    #המטרה:לקבוע אילו איזורים בתמונה אמיתיים ואילו מזוייפים
    self.conv4 = norm(nn.Conv2d(num_feat * 8, num_feat * 4, 3, 1, 1, bias=False))
    self.conv5 = norm(nn.Conv2d(num_feat * 4, num_feat * 2, 3, 1, 1, bias=False))
    self.conv6 = norm(nn.Conv2d(num_feat * 2, num_feat, 3, 1, 1, bias=False))
    #הגדלה נוספת - שיפור הרזולציה!
    self.conv7 = norm(nn.Conv2d(num_feat, num_feat, 3, 1, 1, bias=False))
    self.conv8 = norm(nn.Conv2d(num_feat, num_feat, 3, 1, 1, bias=False))
    self.conv9 = nn.Conv2d(num_feat, 1, 3, 1, 1)
  def forward(self,x):
   #נבצע הקטנה
    x0 = F.leaky_relu(self.conv0(x), negative_slope=0.2, inplace=True)
    x1 = F.leaky_relu(self.conv1(x0), negative_slope=0.2, inplace=True)
    x2 = F.leaky_relu(self.conv2(x1), negative_slope=0.2, inplace=True)
    x3 = F.leaky_relu(self.conv3(x2), negative_slope=0.2, inplace=True)
    #הגדלה
    #הפונקציה interpolate מגדילה את ערוצי הגובה והרוחב פי 2
    #הערכים שהיא מקבלת
    #את התמונה המוקטנת
    #פי כמה להגדיל
    #mode='bilinear': הערך בכל פיקסל שנוסף יחושב מארבעת הפיקסלים הסמוכים אליו
    #align_corners: איך למקם את הפיקסלים החדשים
    # align_corners=False הכוונה שלא משאירים את הפיקסלים המקוריים בפינות אלא מחשבים את היחס שלהם בתמונה השלימה
    x3 = F.interpolate(x3, scale_factor=2, mode='bilinear', align_corners=False)
    #עכשיו יש לנו תמונה גדולה אך מטושטשת
    #לכן נעביר את התמונה בשכבת הקונבולוציה ואחר כך בפונקצית האקציבציה ש
    x4 = F.leaky_relu(self.conv4(x3), negative_slope=0.2, inplace=True)

    if self.skip_connection:
        x4 = x4 + x2

    x4 = F.interpolate(x4, scale_factor=2, mode='bilinear', align_corners=False)
    x5 = F.leaky_relu(self.conv5(x4), negative_slope=0.2, inplace=True)


    if self.skip_connection:
        x5 = x5 + x1
    x5 = F.interpolate(x5, scale_factor=2, mode='bilinear', align_corners=False)
    x6 = F.leaky_relu(self.conv6(x5), negative_slope=0.2, inplace=True)

    if self.skip_connection:
        x6 = x6 + x0

    # extra convolutions
    out = F.leaky_relu(self.conv7(x6), negative_slope=0.2, inplace=True)
    out = F.leaky_relu(self.conv8(out), negative_slope=0.2, inplace=True)
    #לא מבצעים נרמול בשכבה האחרונה כדי לשמור על המידע גולמי שייכנס לLOSS
    out = self.conv9(out)

    return out