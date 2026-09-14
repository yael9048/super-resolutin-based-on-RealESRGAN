import os
import cv2
import numpy as np
import random
from torch.utils.data import Dataset
from torchvision import transforms
from PIL import Image

# ==============================================================================
# הכנת הדאטה לאימון
# ==============================================================================
class RealESRGANDataset(Dataset):
    def __init__(self, hr_paths, patch_size=128, scale=4):
        self.patch_size = patch_size
        self.scale = scale
        self.hr_images = []
        for path in hr_paths:
            if os.path.exists(path):
                self.hr_images.extend( [os.path.join(path, f) for f in os.listdir(path) if f.endswith(('.png', '.jpg', '.jpeg'))])

        print(f"Dataset loaded: {len(self.hr_images)} images found.")
        self.cropper = transforms.RandomCrop(patch_size)
        self.interpolations = [cv2.INTER_LINEAR, cv2.INTER_CUBIC, cv2.INTER_AREA]

    def __len__(self):
        return len(self.hr_images)
    #יצירת קרנל טשטוש כללי לתמונה
    #תוצאת הטשטוש היא טשטוש הדרגתי
    def get_blur_kernel(self, k_size):
        sigma = random.uniform(0.2, 3.0)
        kernel = cv2.getGaussianKernel(k_size, sigma)
        return np.outer(kernel, kernel)
    #יצירת קרנל להורדת החדות לגבולות האובייקטים
    # הפונקציה מדמה טשטוש דיגיטלי שנוצר בדפדפנים ובתוכנות עריכה
    def generate_sinc_kernel(self, kernel_size=21, omega_c=np.pi/3):
        x = np.arange(-(kernel_size//2), kernel_size//2 + 1)
        #יצירת 2 מטריצות - אחת לשורות ואחת לעמודות
        X, Y = np.meshgrid(x, x)
        #משפט פיתגורס
        dist = np.sqrt(X**2 + Y**2)
        #זו הנוסחא ליצירת קרנל הטשטוש
        sinc = np.sin(omega_c * dist) / (np.pi * dist + 1e-6)
        sinc[dist == 0] = omega_c / np.pi
        #מנרמלים את הערכים של הקרנל כדי לא לשנות צבעים
        return sinc / np.sum(sinc)

    def degradation_step(self, img_np, is_first_step=True):
        # נשמור את מימדי התמונה - הגובה והרוחב שלה
        h, w = img_np.shape[:2]
        #טשטוש
        # נגריל את ערכי גודל הקרנל כדי שכל תמונה תטושטש בצורה שונה
        k_size = random.choice([7, 9, 11, 13, 15, 17, 19, 21])
        kernel = self.get_blur_kernel(k_size)
        #נעביר את הקרנל על התמונה בפועל
        img_np = cv2.filter2D(img_np, -1, kernel)

        # הקטנה
        #נגריל שיטת הקטנה
        interp = random.choice(self.interpolations)
        if is_first_step:
            #אם זו הפעם הראשונה נקטין לגודל רנדומלי
            scale_factor = random.uniform(0.2, 1.0)
            new_h, new_w = int(h * scale_factor), int(w * scale_factor)
            img_np = cv2.resize(img_np, (new_w, new_h), interpolation=interp)
        else:
            #בסבב השני נשנה את הגודל לגודל שהמודל רוצה לקבל
            target_sz = self.patch_size // self.scale
            img_np = cv2.resize(img_np, (target_sz, target_sz), interpolation=interp)

        # הוספת רעש גאוסיאני
        if random.random() < 0.8:
            noise_level = random.uniform(1, 20)
            img_np = np.clip(img_np.astype(np.float32) + np.random.normal(0, noise_level, img_np.shape), 0, 255).astype(
                np.uint8)

        # 4. דחיסת JPEG
        if random.random() < 0.8:
            quality = random.randint(30, 95)
            _, encoded = cv2.imencode('.jpg', img_np, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
            img_np = cv2.imdecode(encoded, 1)

        return img_np

    def __getitem__(self, idx):
        try:

            hr_img = cv2.cvtColor(cv2.imread(self.hr_images[idx]), cv2.COLOR_BGR2RGB)
            hr_patch = np.array(self.cropper(Image.fromarray(hr_img)))
            out = cv2.cvtColor(hr_patch, cv2.COLOR_RGB2BGR)
            #סבב ראשון
            if random.random() < 0.1:
                out = cv2.filter2D(out, -1, self.generate_sinc_kernel(21, random.uniform(np.pi/3, np.pi)))
            out = self.degradation_step(self.degradation_step(out, True), False)
            if random.random() < 0.1:
                out = cv2.filter2D(out, -1, self.generate_sinc_kernel(11, random.uniform(np.pi/3, np.pi)))
            return {'LR': transforms.ToTensor()(Image.fromarray(cv2.cvtColor(out, cv2.COLOR_BGR2RGB))),
                    'HR': transforms.ToTensor()(Image.fromarray(hr_patch))}
        except: return self.__getitem__(random.randint(0, len(self.hr_images) - 1))
