import torch
import cv2
import numpy as np
import io
from flask import Flask, request, send_file
from realesrgan import RealESRGANer
from model_arch import RRDBNet
from gfpgan import GFPGANer

app = Flask(__name__)

print("Loading RealESRGAN model")
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Running on: {device}")

# הגדרת המחלקה של הגנרטור
model = RRDBNet(num_in_ch=3, num_out_ch=3)

# הגדרת המודל Real-ESRGAN
upsampler = RealESRGANer(
    scale=4,
    model_path="weights_fixed.pth",
    model=model,
    tile=200, # גודל כל חתיכה לעיבוד
    tile_pad=10,#pedding לעיבוד
    pre_pad=0,
    half=False,
    device=device
)

# הגדרת המודל GFPGAN
face_enhancer = GFPGANer(
    model_path='https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.4.pth',
    upscale=4,
    arch='clean',
    channel_multiplier=2,
    bg_upsampler=upsampler,
    device=device
)

print("Server is up!")


@app.route('/enhance', methods=['POST'])
def enhance_image():
    if 'image' not in request.files:
        return "No image uploaded", 400

    file = request.files['image']

    # קריאת התמונה
    file_bytes = np.frombuffer(file.read(), np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

    try:
        #הפונקציה מחזירה 3 ערכים - השלישי הוא התמונה המשופרת
        _, _, enhanced_img = face_enhancer.enhance(img, has_aligned=False, only_center_face=False, paste_back=True)
    except Exception as error:
        print('Error processing image:', error)
        return "Model failed to process image", 500

    # המרה חזרה לקובץ JPG ושליחה ל-C#
    is_success, buffer = cv2.imencode(".jpg", enhanced_img)
    #המרה לקובץ bytesIO כדי ש
    img_io = io.BytesIO(buffer)
    img_io.seek(0)

    return send_file(img_io, mimetype='image/jpeg')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=False)