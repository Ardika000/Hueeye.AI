from flask import Flask, render_template, Response, jsonify
import cv2
import numpy as np
from tensorflow.keras.models import load_model
import threading
import time
import queue

app = Flask(__name__)

# Load model
try:
    model = load_model('color_classifier_model_augmented.h5')
    print("Model loaded successfully!")
    print(f"Model input shape: {model.input_shape}")
except Exception as e:
    print(f"Error loading model: {e}")
    model = None

class_names = ["Blue", "Green", "red", "yellow"]
latest_color = "TIDAK PASTI"
latest_confidence = 0.0
current_frame = None
frame_lock = threading.Lock()

# Variabel untuk kontrol frame rate
last_prediction_time = 0
prediction_interval = 0.3  # Prediksi setiap 0.3 detik

# Threshold untuk confidence
CONFIDENCE_THRESHOLD = 0.7

# Ukuran area kecil di tengah untuk deteksi
DETECTION_SIZE = 50  # 50x50 pixels di tengah frame

def extract_center_region(frame, size=50):
    """Mengambil area kecil di tengah frame untuk deteksi"""
    height, width = frame.shape[:2]
    center_x, center_y = width // 2, height // 2
    
    # Pastikan ROI tidak melebihi batas frame
    half_size = size // 2
    x1 = max(0, center_x - half_size)
    y1 = max(0, center_y - half_size)
    x2 = min(width, center_x + half_size)
    y2 = min(height, center_y + half_size)
    
    return frame[y1:y2, x1:x2]

def process_center_color(center_region):
    """Hanya memproses area kecil di tengah frame"""
    if model is None:
        return "MODEL TIDAK TERSEDIA", 0.0
    
    try:
        if center_region.size == 0:
            return "TIDAK PASTI", 0.0
        
        # Dapatkan input shape yang diharapkan model
        expected_shape = model.input_shape[1:3]
        
        # Resize ke bentuk yang diharapkan model
        resized = cv2.resize(center_region, expected_shape)
        
        # Normalisasi
        normalized = resized / 255.0
        
        # Jika model mengharapkan grayscale, konversi
        if model.input_shape[-1] == 1:
            gray = cv2.cvtColor(normalized, cv2.COLOR_BGR2GRAY)
            input_array = np.expand_dims(gray, axis=-1)
            input_array = np.expand_dims(input_array, axis=0)
        else:
            # Untuk RGB
            input_array = np.expand_dims(normalized, axis=0)
        
        # Prediksi
        predictions = model.predict(input_array, verbose=0)
        predicted_class = np.argmax(predictions[0])
        confidence = np.max(predictions[0])
        
        if confidence > CONFIDENCE_THRESHOLD:
            color_name = class_names[predicted_class]
            return color_name, confidence
        else:
            return "TIDAK PASTI", confidence
            
    except Exception as e:
        print(f"Error processing frame: {e}")
        return "ERROR", 0.0

def camera_thread():
    """Thread untuk menangani kamera dan prediksi"""
    global current_frame, latest_color, latest_confidence, last_prediction_time
    
    cap = cv2.VideoCapture(0)
    
    # Optimasi pengaturan kamera untuk performa lebih baik
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
    
    if not cap.isOpened():
        print("Cannot open camera")
        return
    
    try:
        while True:
            success, frame = cap.read()
            if not success:
                print("Can't receive frame")
                time.sleep(0.01)
                continue
                
            # Flip frame horizontally for mirror effect
            frame = cv2.flip(frame, 1)
            
            # Gambar target di tengah frame (hanya UI)
            height, width = frame.shape[:2]
            center_x, center_y = width // 2, height // 2
            
            # Gambar crosshair (tanda +) di tengah
            crosshair_size = 30
            cv2.line(frame, (center_x - crosshair_size, center_y), 
                    (center_x + crosshair_size, center_y), (0, 255, 0), 2)
            cv2.line(frame, (center_x, center_y - crosshair_size), 
                    (center_x, center_y + crosshair_size), (0, 255, 0), 2)
            
            # Gambar lingkaran di tengah
            cv2.circle(frame, (center_x, center_y), 15, (0, 255, 0), 2)
            
            # Lakukan prediksi hanya jika sudah melewati interval waktu
            current_time = time.time()
            if current_time - last_prediction_time >= prediction_interval:
                # Ekstrak hanya area kecil di tengah untuk deteksi
                center_region = extract_center_region(frame, DETECTION_SIZE)
                color_name, confidence = process_center_color(center_region)
                latest_color = color_name
                latest_confidence = confidence
                last_prediction_time = current_time
            
            # Tambahkan teks warna terbaru ke frame
            text_color = (0, 255, 0) if latest_confidence > CONFIDENCE_THRESHOLD else (0, 165, 255)
            cv2.putText(frame, f"{latest_color}", (width - 150, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, text_color, 2)
            
            # Encode frame to JPEG dengan optimasi
            ret, buffer = cv2.imencode('.jpg', frame, [
                cv2.IMWRITE_JPEG_QUALITY, 75,  # Quality lebih rendah untuk performa
                cv2.IMWRITE_JPEG_OPTIMIZE, 1
            ])
            
            if ret:
                with frame_lock:
                    current_frame = buffer.tobytes()
            
            time.sleep(0.01)  # Reduced sleep untuk frame rate lebih tinggi
            
    except Exception as e:
        print(f"Error in camera thread: {e}")
    finally:
        cap.release()

def generate_frames():
    """Generator untuk video streaming"""
    while True:
        with frame_lock:
            if current_frame is not None:
                frame = current_frame
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        time.sleep(0.01)  # Reduced sleep untuk responsivitas lebih baik

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scan.html')
def scan():
    return render_template('scan.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), 
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/get_color')
def get_color():
    global latest_color, latest_confidence
    return jsonify({
        'color': latest_color,
        'confidence': float(latest_confidence)
    })

if __name__ == '__main__':
    # Start camera thread
    cam_thread = threading.Thread(target=camera_thread, daemon=True)
    cam_thread.start()
    
    # Run Flask app
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False, threaded=True)