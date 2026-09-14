import os
import glob
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
import torchvision.utils as vutils
import DataSet_class
from model_arch import RRDBNet
from discriminaor_1 import UNetDiscriminatorSN
from Loss_functions import GANLoss, PerceptualLoss
# ==============================================================================
# לולאת האימון הראשית
# ==============================================================================

def train_gan_final_official_v2():
    torch.set_grad_enabled(True)
    #נגדיר את המעבד עליו ירוץ הקוד
    DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

   #הגדרת נתיבים
    PROJECT_DIR = '/content/drive/MyDrive/RealESRGAN_Project'
    EXPERIMENT_NAME = 'official_run_batch48'
    SAVE_DIR = os.path.join(PROJECT_DIR, EXPERIMENT_NAME, 'models')
    VISUAL_DIR = os.path.join(PROJECT_DIR, EXPERIMENT_NAME, 'visuals')
    PRETRAIN_DIR = os.path.join(PROJECT_DIR, 'pretrained_models')

    # תיקיות לשמירת הקבצים בדרייב
    os.makedirs(SAVE_DIR, exist_ok=True)
    os.makedirs(VISUAL_DIR, exist_ok=True)
    os.makedirs(PRETRAIN_DIR, exist_ok=True)

    official_model_path = os.path.join(PRETRAIN_DIR, 'RealESRNet_x4plus.pth')


    # פרמטרים
    PHYSICAL_BATCH_SIZE = 4 #גודל הbatch
    ACCUMULATION_STEPS = 12 #כל כמה איטרציות מבצעים עדכון משקלים
    TOTAL_ITERATIONS = 400000
    EMA_DECAY = 0.999 #  קצב עדכון EMA
    # קצב למידה התחלתי
    BASE_LR = 1e-4

    if 'HR_PATHS' in globals(): train_paths = globals()['HR_PATHS']
    else: train_paths = ['/content/datasets/DF2K/DF2K_train_HR']

    dataset = DataSet_class(train_paths, patch_size=128)
    dataloader = DataLoader(dataset, batch_size=PHYSICAL_BATCH_SIZE, shuffle=True, num_workers=2, pin_memory=True)

    #יצירת הגנרטור
    net_g = RRDBNet(num_in_ch=3, num_out_ch=3, scale=4).to(DEVICE)

  # יצירת מודל EMA
    net_g_ema = RRDBNet(num_in_ch=3, num_out_ch=3, scale=4).to(DEVICE)
    for p in net_g_ema.parameters():
        p.requires_grad = False

    #יצירת הדיסקרימינטור
    net_d = UNetDiscriminatorSN(num_in_ch=3, num_feat=64).to(DEVICE)

    # טעינת Checkpoint
    checkpoints = glob.glob(os.path.join(SAVE_DIR, 'net_g_iter_*.pth'))
    current_iter = 0

    if checkpoints:
        latest = max(checkpoints, key=lambda x: int(os.path.basename(x).split('_')[3].split('.')[0]))
        print(f" המשך אימון מהקובץ: {os.path.basename(latest)}")
        try:
            current_iter = int(os.path.basename(latest).split('_')[3].split('.')[0])
            net_g.load_state_dict(torch.load(latest))

            d_path = latest.replace('net_g', 'net_d')
            if os.path.exists(d_path): net_d.load_state_dict(torch.load(d_path))

            #  טעינת EMA
            ema_path = latest.replace('net_g', 'net_g_EMA')
            if os.path.exists(ema_path):
                print(f" טוען משקלי EMA מהקובץ: {os.path.basename(ema_path)}")
                net_g_ema.load_state_dict(torch.load(ema_path))
            else:
                # אם קובץ המשקלים של הEMA לא קיים, נזרוק שגיאה
                raise FileNotFoundError(f" קובץ EMA לא נמצא : {ema_path}")

        except Exception as e:
            #  בלוק השגיאה שתופס את השגיאה ומעביר אותה הלאה
            raise e
    else:
        state_dict = torch.load(official_model_path)
        if 'params_ema' in state_dict:
            state_dict = state_dict['params_ema']
        elif 'params' in state_dict:
            state_dict = state_dict['params']
        net_g.load_state_dict(state_dict, strict=True)
        # בהתחלה ה-EMA זהה בדיוק למשקלי הגנרטור
        net_g_ema.load_state_dict(state_dict, strict=True)

    # הגדרת פונקציות הפסד
    criterion_pixel = nn.L1Loss().to(DEVICE)
    criterion_percep = PerceptualLoss().to(DEVICE)
    criterion_gan = GANLoss().to(DEVICE)

    #בניית האופטימייזרים
    optimizer_g = optim.Adam(net_g.parameters(), lr=BASE_LR, betas=(0.9, 0.99))
    optimizer_d = optim.Adam(net_d.parameters(), lr=BASE_LR, betas=(0.9, 0.99))

    # 5. הלולאה הראשית
    while current_iter < TOTAL_ITERATIONS:

        # עדכון קצב הלמידה לפי האיטרציה הנוכחית
        if current_iter < 200000:
            current_lr = 1e-4
        elif current_iter < 300000:
            current_lr = 5e-5  # חצי מהקצב
        else:
            current_lr = 2.5e-5 # רבע מהקצב

        # עדכון הקצב אצל האופטימייזרים
        for param_group in optimizer_g.param_groups:
            param_group['lr'] = current_lr
        for param_group in optimizer_d.param_groups:
            param_group['lr'] = current_lr

        #העברת המודלים למצב אימון
        net_g.train()
        net_d.train()

        for i, data in enumerate(dataloader):
            if current_iter >= TOTAL_ITERATIONS: break

            real_hr = data['HR'].to(DEVICE, non_blocking=True)
            lr = data['LR'].to(DEVICE, non_blocking=True)

            # G Update
            #הקפאת המשקלים של ה-D כדי שהעדכון של ה-G לא ישנה את המשקלים של הD
            for p in net_d.parameters(): p.requires_grad = False
            #העברת התמונה המטושטשת לשיפור בגנרטור
            fake_hr = net_g(lr)
            #חישוב ההפסד לגנרטור (תוך כדי מעבירים אצל הדיסקרימינטור)
            #---------------------צבירת ההפסד /12 ---------------
            l_g_total = (criterion_pixel(fake_hr, real_hr) + criterion_percep(fake_hr, real_hr)
                         + (0.1 * criterion_gan(net_d(fake_hr), True))) / ACCUMULATION_STEPS
            # ----------- צבירת הגרדיאנטים-----------------
            l_g_total.backward()

            # D Update
            for p in net_d.parameters(): p.requires_grad = True
            # ---------------------צבירת ההפסד /12 ---------------
            l_d_total = (criterion_gan(net_d(real_hr), True) + criterion_gan(net_d(fake_hr.detach()), False)) / ACCUMULATION_STEPS
            #----------- צבירת הגרדיאנטים-----------------
            l_d_total.backward()

            # Step
            if (i + 1) % ACCUMULATION_STEPS == 0:
                optimizer_g.step()
                optimizer_d.step()
                optimizer_g.zero_grad()
                optimizer_d.zero_grad()

                # עדכון ה-EMA
                for p_ema, p in zip(net_g_ema.parameters(), net_g.parameters()):
                    p_ema.data.mul_(EMA_DECAY).add_(p.data, alpha=1 - EMA_DECAY)

                current_iter += 1

                #הדפסה של הLOSS
                if current_iter % 100 == 0:
                    print(f"[Iter {current_iter}/{TOTAL_ITERATIONS}] Loss: {l_g_total.item()*ACCUMULATION_STEPS:.4f} | LR: {current_lr}")
                #שמירת תמונות
                if current_iter % 500 == 0:
                    with torch.no_grad():
                        lr_up = nn.functional.interpolate(lr, scale_factor=4, mode='nearest')
                        fake_hr_ema = net_g_ema(lr)
                        vis_grid = torch.cat((lr_up[:4], fake_hr[:4], fake_hr_ema[:4], real_hr[:4]), dim=3)
                        vutils.save_image(vis_grid, f"{VISUAL_DIR}/iter_{current_iter}.png")
                #שמירת קבצי המשקלים
                if current_iter % 1000 == 0:
                    torch.save(net_g.state_dict(), f"{SAVE_DIR}/net_g_iter_{current_iter}.pth")
                    torch.save(net_d.state_dict(), f"{SAVE_DIR}/net_d_iter_{current_iter}.pth")
                    torch.save(net_g_ema.state_dict(), f"{SAVE_DIR}/net_g_EMA_iter_{current_iter}.pth")

    print("400000!!!")

if __name__ == '__main__':
    train_gan_final_official_v2()