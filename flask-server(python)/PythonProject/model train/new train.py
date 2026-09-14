import os
import glob
import cv2
import numpy as np
import random
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
import torchvision.utils as vutils
from PIL import Image

# ==============================================================================
# הכנת הדאטה לאימון - הגדרת פונקציות ההרס לאימון
# ==============================================================================
class RealESRGANDataset(Dataset):
    #hr_paths - פונקציית האיתחול של המחלקה מקבלת את מערך הניתובים לתמונות ברוזולוציה גבוהה
    #patch_size - גודל כל חתיכה מהתמונה
    #scale - פי כמה להגדיל
    def __init__(self, hr_paths, patch_size=128, scale=4):
        #הגדרת גודל כל חתיכה מהתמונה
        self.patch_size = patch_size
        #פי כמה להגדיל את התמונה
        self.scale = scale
        # נגדיר מערך שישמור את הנתיבים לתמונות ברזולוציה גבוהה
        self.hr_images = []
        #נעבור על המערך של התמונות החתוכות
        for path in hr_paths:
            #עבור כל אחת מהן -
            if os.path.exists(path):
                #נבדוק אם היא אכן תמונה נצרף אותה
                #path - הנתיב בו נמצאות התמונות
                #os.listdir - path-פונקציה זו מחזירה רשימה של שמות הקבצים שנמצאים ב
                #os.path.join -f את הגישה ל שם הקובץ ששמור ב path פונקציה זו מוסיפה לנתיב
                #imgs - בסוף הפעולה המערך הזה יכיל את הניתובים לכל התמונות
                imgs = [os.path.join(path, f) for f in os.listdir(path) if f.endswith(('.png', '.jpg', '.jpeg'))]
                #נעתיק את מערך הניתובים גם למערך הזה:
                self.hr_images.extend(imgs)
        print(f"Dataset loaded successfully: {len(self.hr_images)} images found.")
        #הספריה transforms מאפשרת לנו לעבוד עם התמונות בצורה אחידה ומסודרת בעזרת פונקציות רבות...
        # נחתוך ריבועים בגודל 128*128 מהתמונות ממיקום אקראי
        self.cropper = transforms.RandomCrop(patch_size)
        #בגלל שהמודל מאומן להגדיל תמונות פי 4 נאמן אותו על תמונות מוקטנות פי 4
        #נגדיר ליסט של סוגי ההקטנה
        # כדי להקטין את התמונה המחשב צריך למזג חלק מהפיקסלים
        #cv2.INTER_LINEAR - סוג המיזוג בהקטנה זו עושה ממוצע לכל 4 פיקסלים וממזג אותם לפיקסל אחד.
        #cv2.INTER_CUBIC - שיטה שמתחשבת ב-16 הפיקסלים השכנים כדי לחשב את הערך החדש
        #cv2.INTER_AREA - שיטה שמשתמשת ביחסי השטחים של הפיקסלים. זוהי השיטה הטובה ביותר כי היא שומרת שלא יהיו עיוותים
        self.interpolations = [cv2.INTER_LINEAR, cv2.INTER_CUBIC, cv2.INTER_AREA]

    def __len__(self):
        #פונקתיה זו מחזירה את כמות התמונות בדאטה
        return len(self.hr_images)

    #פונקציה זו מחזירה קרנל עם ערכים שמטשטשים את התמונה בצורה שונה
    #???????? מה זה הפונקציה getGaussianKernel
    def get_blur_kernel(self, k_size):
        #נגריל מספר בין 0 ל-1  ע"י הסיפריה random והפונקציה random
        prob = random.random()
        #נבחר את ערך הסיגמא באופן אקראי- שמייצג את עוצמת הטשטוש
        #עוצמת הטשטוש תהיה בטווח המספרים בין 0.2 ל3
        sigma = random.uniform(0.2, 3.0)
        if prob < 0.7:
            #k_size - משתנה זה קובע את כמות הפיקסלים עליהם יתבצע הטשטוש - לדוגמא ממוצע עם כל 4 פיקסלים או 16
            kernel = cv2.getGaussianKernel(k_size, sigma)
            #????????????????????????????
            return np.outer(kernel, kernel)
        #else:
            #kernel = cv2.getGaussianKernel(k_size, sigma)
            #return np.outer(kernel, kernel)

    def generate_sinc_kernel(self, kernel_size=21, omega_c=np.pi/3):
        #kernel_size -גודל הקרנל מוגדר להיות 21*21
        #omega_c - 3
        #הפקודה הבאה יוצרת מערך ממינוס 10 עד 10 בקפיצות של 1
        #המערך הזה משמש למילוי הערכים של הקרנל  באופן סימטרי כדי שהטשטוש בקרנל יהיה סימטרי ופעמוני
        x = np.arange(-(kernel_size//2), kernel_size//2 + 1)
        #[-10,-9,-8,-7,-6,-5,-4,-3,-2,-1,0,1,2,3,4,5,6,7,8,9,10]
        #כדי להפוך את הוקטור X להיות מטריצה סימטרית מכל הכיוונים
        #נשתמש בפקודה meshgrid
        #הפקודה הזו  מייצרת 2 מטריצות בגודל 21*21
        #מטריצה אחת מורכבת מ 21 שורות שהן שכפול של X
        #והמטריצה השנייה מורכבת מ21 עמודות שהן שכפול של X
        X, Y = np.meshgrid(x, x)
        #באמצעות 2 המטריצות X ו-Y נוכל להפעיל נוסחת מרחק
        #כי כל מיקום במטריצה הראשונה מייצג את הערך על ציר הX וכל מיקום במטריצה השניה מייצג את הערך על ציר הY
        #כלומר הנקודה הראשונה מורכבת מהערך שנמצא ב(0,0) במטריצת הX וה-Y שלה נמצא ב (0,0)במטריצה הY
        #מכל הנקודות שקיבלנו ניצור מטריצה חדשה  ונחשב בה נוסחת מרחק
        # עפ"י משפט פיתגורס.......
        dist = np.sqrt(X**2 + Y**2)
        sinc = np.sin(omega_c * dist) / (np.pi * dist + 1e-6)
        sinc[dist == 0] = omega_c / np.pi
        #המטריצה שמחזירים היא מנורמלת - סכום כל הערכים שלה חייב להיות 1 כדי שלא להרוס מדי הרבה את התמונה
        #מחלקים כל איבר בסכום כל האיברים
        return sinc / np.sum(sinc)


    #פונקציה זו מבצעת את הרס התמונה בפועל ותשלח לפונקציות הטשטוש המתאימות
    def degradation_step(self, img_np, is_first_step=True):
        #נשמור את מימדי התמונה - הגובה והרוחב שלה
        h, w = img_np.shape[:2]
        #נגריל את ערכי גודל הקרנל כדי שכל תמונה תטושטש בצורה שונה
        k_size = random.choice([7, 9, 11, 13, 15, 17, 19, 21])
        #נבנה את קרנל הטשטוש
        kernel = self.get_blur_kernel(k_size)
        #הפונקציה filter2D מעבירה בפועל את הקרנת על התמונה
        #שלחנו -1 כדי לציין שסוג הנתונים של  התמונה לא ישתנה
        #(שהערכים יהיו עדיין בין 0 ל255 כמו בפורמט שהם היו עד עכשיו - uint8)
        img_np = cv2.filter2D(img_np, -1, kernel)
        #נגדיר את שיטת ההקטנה - ע"י בחירה אקראית מהמערך
        interp = random.choice(self.interpolations)
        #אם זה הסבב הראשון של ההרס
        #נבצע הקטנה שתהרוס את התמונה
        if is_first_step:
            #נגריל מספר בין 0.2 ל1 שיגדיר בכמה להקטין את התמונה
            scale_factor = random.uniform(0.2, 1.0)
            #מימדי התמונה החדשה
            new_h, new_w = int(h * scale_factor), int(w * scale_factor)
            #נשנה את גודל התמונה ונשלח  את סוג ההקטנה המוגרל
            img_np = cv2.resize(img_np, (new_w, new_h), interpolation=interp)
        else:
            #בסבבים הבאים נדאג שגודל התמונה יהיה כגודל התמונה שהמודל רוצה לקבל
            target_sz = self.patch_size // self.scale
            img_np = cv2.resize(img_np, (target_sz, target_sz), interpolation=interp)


            #רעש
        if random.random() < 0.8:
            #נגריל את עוצמת הרעש
            noise_level = random.uniform(1, 20)
            #נוסיף אותו כך:
            #הפקודה הבאה תגדיל את טווח הערכים שהפיקסלים בתמונה יוכלו לקבל - ולא רק בין 0 ל255
            #כדי שנוכל להוסיף רעש גם  אם הוא יגלוש מעבר ל255
            #לבסוף נגביל את הערכים שיקבלו את הערך המקסימלי שאפשר - 255
            # (בגלל שuint8 מאפס ערכים שגולשים - אם הוא יקבל 260 הערך שייכנס יהיה 4 אז נגביל אותו שיהיה 255)

        if random.random() < 0.8:
            #נגריל את גודל הדחיסה - מספר גבוה ישאיר את התמונה גדולה יותר
            #בחרתי בטווח זה כדי שהדחיסה לא תהיה מדי חזקה - מתחת ל30
            # ושתהיה מורגשת - לפחות 95 כי 100 זה ללא דחיסה בכלל
            quality = random.randint(30, 95)
            #נדחוס את התמונה
            # הפונקציה  imencode ממירה תמונה לפורמט נתון
            # היא שומרת את התמונה בפורמט jpeg שדוחס את התמונה בזיכרון RAM
            #מערך הפרמטרים ששולחים מוגדר בופן הבא:
            #[פרמטר קבוע - הערך מספרי של שם_ההגדרה, הערך_שלה] - במערך הגדרנו את איכות התמונה שתתקבל
            #מה זה _, ??????????????????????????????????
            _, encoded = cv2.imencode('.jpg', img_np, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
            #לאחר הדחיסה נחזיר את את זה למטריצה רגילה של תמונה כי הפונקציה הקודת מחזירה תמונה מקודדת
            img_np = cv2.imdecode(encoded, 1)
        return img_np

    def __getitem__(self, idx):
        try:
            hr_img = cv2.cvtColor(cv2.imread(self.hr_images[idx]), cv2.COLOR_BGR2RGB)
            hr_patch = np.array(self.cropper(Image.fromarray(hr_img)))
            out = cv2.cvtColor(hr_patch, cv2.COLOR_RGB2BGR)
            if random.random() < 0.1: out = cv2.filter2D(out, -1, self.generate_sinc_kernel(21, random.uniform(np.pi/3, np.pi)))
            out = self.degradation_step(self.degradation_step(out, True), False)
            if random.random() < 0.1: out = cv2.filter2D(out, -1, self.generate_sinc_kernel(11, random.uniform(np.pi/3, np.pi)))
            return {'LR': transforms.ToTensor()(Image.fromarray(cv2.cvtColor(out, cv2.COLOR_BGR2RGB))), 'HR': transforms.ToTensor()(Image.fromarray(hr_patch))}
        except: return self.__getitem__(random.randint(0, len(self.hr_images) - 1))

# ==============================================================================
# לולאת האימון הראשית
# ==============================================================================

def train_gan_final_official_v2():
    # האם זה שומר את הגרדיאנטים בין השכבות????מה זה עושה?????????
    torch.set_grad_enabled(True)
    #נגדיר את המעבד עליו ירוץ הקוד
    DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    print("הורדת המשקלים של המודל real-ESRGAN")

   #הגדרת נתיבים
    PROJECT_DIR = '/content/drive/MyDrive/RealESRGAN_Project'
    EXPERIMENT_NAME = 'official_run_batch48'
    SAVE_DIR = os.path.join(PROJECT_DIR, EXPERIMENT_NAME, 'models')
    VISUAL_DIR = os.path.join(PROJECT_DIR, EXPERIMENT_NAME, 'visuals')
    PRETRAIN_DIR = os.path.join(PROJECT_DIR, 'pretrained_models')

    #ניצור תיקיות לשמירת הקבצים בדרייב
    os.makedirs(SAVE_DIR, exist_ok=True)
    os.makedirs(VISUAL_DIR, exist_ok=True)
    os.makedirs(PRETRAIN_DIR, exist_ok=True)

    official_model_path = os.path.join(PRETRAIN_DIR, 'RealESRNet_x4plus.pth')
    if not os.path.exists(official_model_path):
        os.system(f"wget https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.1/RealESRNet_x4plus.pth -O {official_model_path}")

    # פרמטרים
    PHYSICAL_BATCH_SIZE = 4
    ACCUMULATION_STEPS = 12
    TOTAL_ITERATIONS = 400000
    EMA_DECAY = 0.999 #  קצב עדכון EMA - למה 0.999????????????????

    # קצב התחלתי  - קצב הלמידה
    BASE_LR = 1e-4

    #הפונקציה globals מחזירה מילון של כל המשתנים בנמצאים בזיכרון
    #אם נמצא שם הניתוב לקובץ נגדיר אותו, אם לא נגדיר ניתוב ברירת מחדל
    if 'HR_PATHS' in globals(): train_paths = globals()['HR_PATHS']
    else: train_paths = ['/content/datasets/DF2K/DF2K_train_HR']


    #נגדיר את האובייקט שמייצג את הדאטה סט - שהוסבר לעיל
    #נשלח אליו את הניתוב לתיקיית התמונות ברזולוציה גבוהה
    # ונגדיר את המשתנה להיות בגודל 128
    dataset = RealESRGANDataset(train_paths, patch_size=128)
    #נטען את הדאטה סט ונמיר אותו לטנזורים כדי שנוכל להזין אותו לכרטיס המסך
    #הפרמטרים שהיא מקבלת:
    #האובייקט של הדאטה סט שיורש מהמחלקה torch.utils.data.Dataset
    #גודל ה-batch,כלומר, מס' התמונות בכל סבב אימון עליו יתבצע backpropagation
    #shuffle - באםון מעורבב GPU נגדיר לפנקציה להכניס את הנתונים ל
    #מס התהליכונים שירוצו על הCPU כדי לטעון את התמונות בזמן שהאימון מתבתע על הGPU
    #pin_memory -תהיה אסינכרונית, כדי למהר את העברת הנתונים שתתבצע תוך כדי פעילות האימון GPUמגדיר האם העברת הנתונים ל-
    dataloader = DataLoader(dataset, batch_size=PHYSICAL_BATCH_SIZE, shuffle=True, num_workers=2, pin_memory=True)


    #נגדיר את מבנה הגנרטור ונאחסן אותו בכרטיס מסך
    #num_in_ch - מס הערוצים בתמונת הקלט
    #num_out_ch - מס הערוצים בתמונת הפלט
    net_g = RRDBNet(num_in_ch=3, num_out_ch=3, scale=4).to(DEVICE)

  # כנ"ל נגדיר את מבנה הEMA כמו הגנרטור
    net_g_ema = RRDBNet(num_in_ch=3, num_out_ch=3, scale=4).to(DEVICE)
    #מבנה הEMA לא משמש לאימון אלא הוא רק מאחסן את המשקלים הממוצעים של אימון הגנרטור - כדי לשמור על תוצאה יציבה בסופו של האימון.
    for p in net_g_ema.parameters():
        #מכיוון שהוא לא לומד, אין צורך בשמירת הגרדיאנטים
        p.requires_grad = False



    # ===============================
    #נגדיר את מבנה הדיסקרימינטור
    #num_in_ch - מס הערוצים בתמונת הקלט
    #num_feat - (מס הערוצים בתמונת הפלט של השכבה הראשונה (מגדירים מס ערוצים התחלתי כי במהלך המעבר בשכבות הערוצים מכפילים או מחלקים את עצמם
    net_d = UNetDiscriminatorSN(num_in_ch=3, num_feat=64).to(DEVICE)

    # טעינת Checkpoint מהדרייב
    #מוצא אם יש קובץ מתאים בנתיב
    checkpoints = glob.glob(os.path.join(SAVE_DIR, 'net_g_iter_*.pth'))
    current_iter = 0

    if checkpoints:
        #נטען את קובץ המשקלים האחרון שנמצא בדרייב
        latest = max(checkpoints, key=lambda x: int(os.path.basename(x).split('_')[3].split('.')[0]))
        print(f" נמצא קובץ משקלים בדרייב. הקובץ: {os.path.basename(latest)}")
        try:
            #  כדי לדעת באיזה איטרציה אנחו נמצאים כרגע נחלק את שם קובץ המשקלים שנטען לפי התו "_" ונקבל את מס האיטרציה
            # שם קובצי המשקלים מהאימון מיוצג בתבנית הבאה - net_g_iter_*.pth
            current_iter = int(os.path.basename(latest).split('_')[3].split('.')[0])
            #state_dict - פונקציה זו שומרת מילון שבו עבור כל שכבה נשמר טנזור של כל המשקלים שלה
            #היא מקבלת את קובץ המשקלים של הגרסה האחרונה שנשמרה
            net_g.load_state_dict(torch.load(latest))
            #נחליף את שם הניתוב בכדי שנגיע לקובת המשקלים של הדיסקרימינטור
            d_path = latest.replace('net_g', 'net_d')
            #ונטען את קובת המשקלים אם הוא קיים
            if os.path.exists(d_path): net_d.load_state_dict(torch.load(d_path))

            # === תוספת 2: טעינת EMA אם קיים ===
            #נחליף אץ שם הקובץ כדי להגיע לקובץ המשקלים האחרון של הEMA
            ema_path = latest.replace('net_g', 'net_g_EMA')
            if os.path.exists(ema_path):
                #נטען אותם
                print(f"טוען EMA מהקובץ: {os.path.basename(ema_path)}")
                net_g_ema.load_state_dict(torch.load(ema_path))
            else:
                #אם זו הרצה ראשונה
                print("אין קובץ EMA קודם ")
                #נשכפל את  קובץ המשקלים net_g הנוכחי כהתחלה
                net_g_ema.load_state_dict(net_g.state_dict())
            # ==================================

        except:
            print("שגיאה בטעינה. טוען את net_g בלבד.")
            #אם יש שגיאה נטען רק את המשקלים של הגנרטור
            #ונשכפל אותם לEMA
            net_g.load_state_dict(torch.load(latest))
            net_g_ema.load_state_dict(net_g.state_dict())


    #אם לא מצאנו checkpoint:
    else:
        # זו הרצה ראשונה - נתחיל מקובץ המשקלים של הpre training
        print(f" מתחיל אימון חדש מהמשקלים של האימון המקדים ")
        state_dict = torch.load(official_model_path)

        if 'params_ema' in state_dict: state_dict = state_dict['params_ema']
        elif 'params' in state_dict: state_dict = state_dict['params']
        net_g.load_state_dict(state_dict, strict=True)
        # בהתחלה ה-EMA זהה בדיוק למודל של האימון המקדים
        net_g_ema.load_state_dict(state_dict, strict=True)

    # Losses
    #נטען את פונקציות ההפסד לGPU כדי שהקוד שלהם יהיה מוכן להרצה
    #אם לא היינו שמים אותו בGPU הוא היה רץ על המעבד הרגיל והקוד היה קורס כי הוא לא היה מוצא את המשקלים????
    criterion_pixel = nn.L1Loss().to(DEVICE)
    criterion_percep = PerceptualLoss().to(DEVICE)
    criterion_gan = GANLoss().to(DEVICE)

    #נטען את האופטימייזרים - שתפקידם לבצע את עידכון המשקלים בפועל לאחר החישוב של פונקציית ההפסד
    optimizer_g = optim.Adam(net_g.parameters(), lr=BASE_LR, betas=(0.9, 0.99))
    optimizer_d = optim.Adam(net_d.parameters(), lr=BASE_LR, betas=(0.9, 0.99))

    print(f"האימון מתחיל")

    #  הלולאה הראשית
    while current_iter < TOTAL_ITERATIONS:

        if current_iter < 200000:
            current_lr = 1e-4
        elif current_iter < 300000:
            current_lr = 5e-5  # חצי מהקצב
        else:
            current_lr = 2.5e-5 # רבע מהקצב

        # עדכון קצב הלמידה אצל האופטימייזרים
        for param_group in optimizer_g.param_groups:
            param_group['lr'] = current_lr
        for param_group in optimizer_d.param_groups:
            param_group['lr'] = current_lr
        # ---------------------------------------------

        #נעביר את המודלים למצב אימון
        #במצב זה ניתן לערוך עידכון למשקלים ופונקציות הנרמול בין השכבות יוכלו לפעול
        net_g.train()
        net_d.train()

        #נעבור על המערך של הדאטה שטענו ונשתמש באינדקס ובתמונה
        for i, data in enumerate(dataloader):
            if current_iter >= TOTAL_ITERATIONS: break

            #נעביר תמונה ברזולוציה גבוהה לGPU
            real_hr = data['HR'].to(DEVICE, non_blocking=True)
            # נעביר תמונה ברזולוציה נמוכה לGPU
            lr = data['LR'].to(DEVICE, non_blocking=True)

            # G Update
            for p in net_d.parameters(): p.requires_grad = False
            fake_hr = net_g(lr)
            l_g_total = (criterion_pixel(fake_hr, real_hr) + criterion_percep(fake_hr, real_hr) + (0.1 * criterion_gan(net_d(fake_hr), True))) / ACCUMULATION_STEPS
            l_g_total.backward()

            # D Update
            for p in net_d.parameters(): p.requires_grad = True
            l_d_total = (criterion_gan(net_d(real_hr), True) + criterion_gan(net_d(fake_hr.detach()), False)) / ACCUMULATION_STEPS
            l_d_total.backward()

            # Step
            if (i + 1) % ACCUMULATION_STEPS == 0:
                optimizer_g.step()
                optimizer_d.step()
                optimizer_g.zero_grad()
                optimizer_d.zero_grad()

                # === עדכון ה-EMA ===
                for p_ema, p in zip(net_g_ema.parameters(), net_g.parameters()):
                    p_ema.data.mul_(EMA_DECAY).add_(p.data, alpha=1 - EMA_DECAY)
                # ============================

                current_iter += 1

                if current_iter % 100 == 0:
                    print(f"[Iter {current_iter}/{TOTAL_ITERATIONS}] Loss: {l_g_total.item()*ACCUMULATION_STEPS:.4f} | LR: {current_lr}")

                if current_iter % 500 == 0:
                    with torch.no_grad():
                        lr_up = nn.functional.interpolate(lr, scale_factor=4, mode='nearest')
                        fake_hr_ema = net_g_ema(lr)
                        vis_grid = torch.cat((lr_up[:4], fake_hr[:4], fake_hr_ema[:4], real_hr[:4]), dim=3)
                        vutils.save_image(vis_grid, f"{VISUAL_DIR}/iter_{current_iter}.png")

                if current_iter % 1000 == 0:
                    torch.save(net_g.state_dict(), f"{SAVE_DIR}/net_g_iter_{current_iter}.pth")
                    torch.save(net_d.state_dict(), f"{SAVE_DIR}/net_d_iter_{current_iter}.pth")
                    # === תוספת 4: שמירת ה-EMA ===
                    torch.save(net_g_ema.state_dict(), f"{SAVE_DIR}/net_g_EMA_iter_{current_iter}.pth")
                    # ============================
                    print(f" צ'קפוינט נשמר : iter_{current_iter}")


if __name__ == '__main__':
    train_gan_final_official_v2()