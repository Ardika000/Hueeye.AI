from flask import Flask, render_template, Response, jsonify
import cv2
import numpy as np
from tensorflow.keras.models import load_model
import threading
import time
import queue
import time

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
current_frame = None
frame_lock = threading.Lock()

# Queue untuk komunikasi antara thread
prediction_queue = queue.Queue(maxsize=1)
frame_queue = queue.Queue(maxsize=1)

# Variabel untuk kontrol frame rate
last_prediction_time = 0
prediction_interval = 0.5  # Prediksi setiap 0.5 detik (bisa disesuaikan)

def process_frame(frame):
    """Fungsi untuk memproses frame dan melakukan prediksi"""
    if model is None:
        return frame, "MODEL TIDAK TERSEDIA"
    
    try:
        # Dapatkan input shape yang diharapkan model
        expected_shape = model.input_shape[1:3]  # (height, width)
        
        # Resize frame ke bentuk yang diharapkan model
        resized = cv2.resize(frame, expected_shape)

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
        
        if confidence > 0.7:
            color_name = class_names[predicted_class]
            return color_name
        else:
            return "TIDAK PASTI"
            
    except Exception as e:
        print(f"Error processing frame: {e}")
        return "ERROR"

def prediction_thread():
    """Thread terpisah untuk melakukan prediksi"""
    global latest_color, last_prediction_time
    
    while True:
        try:
            # Ambil frame dari queue (tunggu maksimal 0.1 detik)
            frame = frame_queue.get(timeout=0.1)
            
            # Lakukan prediksi hanya jika sudah melewati interval waktu
            current_time = time.time()
            if current_time - last_prediction_time >= prediction_interval:
                color_name = process_frame(frame)
                latest_color = color_name
                last_prediction_time = current_time
                
                # Masukkan hasil prediksi ke queue
                if prediction_queue.empty():
                    prediction_queue.put(color_name)
                    
        except queue.Empty:
            # Queue kosong, lanjutkan
            continue
        except Exception as e:
            print(f"Error in prediction thread: {e}")
            time.sleep(0.1)

def camera_thread():
    """Thread untuk menangani kamera"""
    global current_frame
    
    cap = cv2.VideoCapture(0)
    
    # Set camera properties untuk performa lebih baik
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Buffer kecil untuk mengurangi latency
    
    if not cap.isOpened():
        print("Cannot open camera")
        return
    
    try:
        while True:
            success, frame = cap.read()
            if not success:
                print("Can't receive frame")
                time.sleep(0.1)
                continue
                
            # Flip frame horizontally for mirror effect
            frame = cv2.flip(frame, 1)
            
            # Tambahkan teks warna terbaru ke frame
            cv2.putText(frame, latest_color, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            # Masukkan frame ke queue untuk prediksi (jika queue kosong)
            if frame_queue.empty():
                try:
                    frame_queue.put_nowait(frame.copy())
                except queue.Full:
                    pass  # Queue penuh, skip frame ini untuk prediksi
            
            # Encode frame to JPEG
            ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])  # Quality 80 untuk ukuran lebih kecil
            if ret:
                with frame_lock:
                    current_frame = buffer.tobytes()
            
            time.sleep(0.03)  # Kontrol frame rate
            
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
        time.sleep(0.03)

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
    global latest_color
    return jsonify({'color': latest_color})

if __name__ == '__main__':
    # Start camera thread
    cam_thread = threading.Thread(target=camera_thread, daemon=True)
    cam_thread.start()
    
    # Start prediction thread
    pred_thread = threading.Thread(target=prediction_thread, daemon=True)
    pred_thread.start()
    
    # Run Flask app
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False, threaded=True)