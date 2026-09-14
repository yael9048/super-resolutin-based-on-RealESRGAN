import torch
import torch.nn as nn
from torch.nn import functional as F

# הבלוק הבסיסי: Residual Dense Block
class ResidualDenseBlock(nn.Module):
    def __init__(self,num_feat=64, num_grow_ch=32):
        super(ResidualDenseBlock, self).__init__()
        self.conv1 = nn.Conv2d(num_feat, num_grow_ch, 3, 1, 1)
        self.conv2 = nn.Conv2d(num_feat + num_grow_ch, num_grow_ch, 3, 1, 1)
        self.conv3 = nn.Conv2d(num_feat + 2 * num_grow_ch, num_grow_ch, 3, 1, 1)
        self.conv4 = nn.Conv2d(num_feat + 3 * num_grow_ch, num_grow_ch, 3, 1, 1)
        self.conv5 = nn.Conv2d(num_feat + 4 * num_grow_ch, num_feat, 3, 1, 1)

        #LeakyReLU:  מספר שלילי מוכפל ב 0.2 וחיובי נשאר כמו שהוא
        self.lrelu = nn.LeakyReLU(negative_slope=0.2, inplace=True)

    def forward(self, x):
        x1 = self.lrelu(self.conv1(x))
        x2 = self.lrelu(self.conv2(torch.cat((x, x1), 1)))
        x3 = self.lrelu(self.conv3(torch.cat((x, x1, x2), 1)))
        x4 = self.lrelu(self.conv4(torch.cat((x, x1, x2, x3), 1)))
        x5 = self.conv5(torch.cat((x, x1, x2, x3, x4), 1))
        # הכפלה ב-0.2 לנרמול הערכים באימון
        return x5 * 0.2 + x

# Residual in Residual Dense Block (RRDB)
class RRDB(nn.Module):
    def __init__(self, num_feat, num_grow_ch=32):
        super(RRDB, self).__init__()
        self.rdb1 = ResidualDenseBlock(num_feat, num_grow_ch)
        self.rdb2 = ResidualDenseBlock(num_feat, num_grow_ch)
        self.rdb3 = ResidualDenseBlock(num_feat, num_grow_ch)

    def forward(self, x):
        out = self.rdb1(x)
        out = self.rdb2(out)
        out = self.rdb3(out)
        #הכפלה ב-0.2 לנרמול הערכים באימון
        return out * 0.2 + x

# פונקציה זו מקבלת את המחלקה הבסיסית וכמות אובייקטים ובונה אותם בפועל
def make_layer(class_RRDB, n_layers, **kwargs):
    layers = []
    for i in range(n_layers):
        layers.append(class_RRDB(**kwargs))
    return nn.Sequential(*layers)

# רשת הגנרטור הכוללת : RRDBNet
class RRDBNet(nn.Module):
    def __init__(self, num_in_ch, num_out_ch, scale=4, num_feat=64, num_block=23, num_grow_ch=32):
        super(RRDBNet, self).__init__()
        self.scale = scale
        #
        self.conv_first = nn.Conv2d(num_in_ch, num_feat, 3, 1, 1)
        #
        self.body = make_layer(RRDB, num_block, num_feat=num_feat, num_grow_ch=num_grow_ch)
        # שכבת חיבור
        self.conv_body = nn.Conv2d(num_feat, num_feat, 3, 1, 1)
        # שכבות הגדלה
        # כל שלב מכפיל את הגודל פי 2. סה"כ שתי שכבות נותנות הגדלה פי 4.
        self.conv_up1 = nn.Conv2d(num_feat, num_feat, 3, 1, 1)
        self.conv_up2 = nn.Conv2d(num_feat, num_feat, 3, 1, 1)
        #   חידוד לאחר ההגדלה והמרה חזרה לצבע
        self.conv_hr = nn.Conv2d(num_feat, num_feat, 3, 1, 1)
        self.conv_last = nn.Conv2d(num_feat, num_out_ch, 3, 1, 1)
        self.lrelu = nn.LeakyReLU(negative_slope=0.2, inplace=True)

    def forward(self, x):
        feat = x
        #המרה מ-3 ערוצים ל64 ערוצים
        feat = self.conv_first(feat)
        # 23 הבלוקים
        body_feat = self.conv_body(self.body(feat))

        # חיבור רזידואלי (הקלט + התוצאה של גוף העיבוד)
        feat = feat + body_feat

        # הגדלת התמונה
        feat = self.lrelu(self.conv_up1(F.interpolate(feat, scale_factor=2, mode='nearest')))
        feat = self.lrelu(self.conv_up2(F.interpolate(feat, scale_factor=2, mode='nearest')))
        # שחזור סופי והמרה לצבע
        out = self.conv_last(self.lrelu(self.conv_hr(feat)))

        return out