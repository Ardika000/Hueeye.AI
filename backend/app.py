from flask import Flask, render_template, Response, jsonify
import cv2
import numpy as np
from tensorflow.keras.models import load_model
import threading
import time
import queue
import os
import logging
from flask_cors import CORS

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS untuk semua origin

# Configuration
CONFIG = {
    'camera_index': 0,
    'frame_width': 640,
    'frame_height': 480,
    'fps': 30,
    'prediction_interval': 0.5,
    'jpeg_quality': 80,
    'confidence_threshold': 0.7
}

# Global variables
model = None
class_names = ["Blue", "Green", "red", "yellow"]
latest_color = "TIDAK PASTI"
current_frame = None
camera_active = False

# Threading setup
frame_lock = threading.Lock()
prediction_queue = queue.Queue(maxsize=1)
frame_queue = queue.Queue(maxsize=2)

# Load model dengan error handling
def load_ai_model():
    global model
    try:
        model_path = 'color_classifier_model_augmented.h5'
        if os.path.exists(model_path):
            model = load_model(model_path)
            logger.info("✅ Model loaded successfully!")
            logger.info(f"📊 Model input shape: {model.input_shape}")
            return True
        else:
            logger.error(f"❌ Model file not found: {model_path}")
            return False
    except Exception as e:
        logger.error(f"❌ Error loading model: {e}")
        return False

def process_frame(frame):
    """Process frame and return color prediction"""
    if model is None:
        return "MODEL TIDAK TERSEDIA"
    
    try:
        # Get expected input shape
        expected_shape = model.input_shape[1:3]  # (height, width)
        
        # Resize frame to model's expected input
        resized = cv2.resize(frame, expected_shape)

        # Normalize
        normalized = resized / 255.0
        
        # Handle different input types
        if model.input_shape[-1] == 1:
            # Grayscale conversion
            gray = cv2.cvtColor(normalized, cv2.COLOR_BGR2GRAY)
            input_array = np.expand_dims(gray, axis=-1)
            input_array = np.expand_dims(input_array, axis=0)
        else:
            # RGB input
            input_array = np.expand_dims(normalized, axis=0)
        
        # Prediction
        predictions = model.predict(input_array, verbose=0)
        predicted_class = np.argmax(predictions[0])
        confidence = np.max(predictions[0])
        
        if confidence > CONFIG['confidence_threshold']:
            return class_names[predicted_class]
        else:
            return "TIDAK PASTI"
            
    except Exception as e:
        logger.error(f"❌ Error processing frame: {e}")
        return "ERROR"

def prediction_worker():
    """Worker thread for predictions"""
    global latest_color
    last_prediction_time = 0
    
    while True:
        try:
            # Get frame from queue with timeout
            frame = frame_queue.get(timeout=1.0)
            
            # Throttle predictions
            current_time = time.time()
            if current_time - last_prediction_time >= CONFIG['prediction_interval']:
                color_name = process_frame(frame)
                latest_color = color_name
                last_prediction_time = current_time
                
                # Update prediction queue
                if prediction_queue.empty():
                    prediction_queue.put(color_name)
                    
        except queue.Empty:
            continue
        except Exception as e:
            logger.error(f"❌ Error in prediction worker: {e}")
            time.sleep(0.1)

def camera_worker():
    """Worker thread for camera operations"""
    global current_frame, camera_active
    
    # Check if we're in production (Railway doesn't support camera)
    is_production = os.environ.get('RAILWAY_ENVIRONMENT') == 'production'
    
    if is_production:
        logger.info("🚫 Camera disabled in production environment")
        camera_active = False
        
        # Generate demo frames for production
        while True:
            demo_frame = generate_demo_frame()
            ret, buffer = cv2.imencode('.jpg', demo_frame, 
                                     [cv2.IMWRITE_JPEG_QUALITY, CONFIG['jpeg_quality']])
            if ret:
                with frame_lock:
                    current_frame = buffer.tobytes()
            time.sleep(1/CONFIG['fps'])
        return
    
    # Development mode - real camera
    cap = cv2.VideoCapture(CONFIG['camera_index'])
    
    # Optimize camera settings
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CONFIG['frame_width'])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CONFIG['frame_height'])
    cap.set(cv2.CAP_PROP_FPS, CONFIG['fps'])
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    
    if not cap.isOpened():
        logger.error("❌ Cannot open camera")
        camera_active = False
        return
    
    camera_active = True
    logger.info("✅ Camera started successfully")
    
    try:
        while True:
            success, frame = cap.read()
            if not success:
                logger.warning("⚠️ Can't receive frame from camera")
                time.sleep(0.1)
                continue
                
            # Mirror effect
            frame = cv2.flip(frame, 1)
            
            # Add current color text to frame
            cv2.putText(frame, latest_color, (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            # Add detection area rectangle
            height, width = frame.shape[:2]
            roi_size = 200
            x1 = width // 2 - roi_size // 2
            y1 = height // 2 - roi_size // 2
            x2 = x1 + roi_size
            y2 = y1 + roi_size
            
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 255), 2)
            
            # Send frame to prediction queue (non-blocking)
            if frame_queue.empty():
                try:
                    frame_queue.put_nowait(frame.copy())
                except queue.Full:
                    pass
            
            # Encode frame for streaming
            ret, buffer = cv2.imencode('.jpg', frame, 
                                     [cv2.IMWRITE_JPEG_QUALITY, CONFIG['jpeg_quality']])
            if ret:
                with frame_lock:
                    current_frame = buffer.tobytes()
            
            time.sleep(1/CONFIG['fps'])
            
    except Exception as e:
        logger.error(f"❌ Error in camera worker: {e}")
    finally:
        cap.release()
        camera_active = False
        logger.info("🛑 Camera stopped")

def generate_demo_frame():
    """Generate demo frame for production environment"""
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # Create a colorful demo background
    for i in range(3):
        color_value = int((time.time() * 50 + i * 85) % 255)
        frame[:, :, i] = color_value
    
    # Add demo text
    cv2.putText(frame, "DEMO MODE", (200, 150), 
               cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    cv2.putText(frame, "Camera not available in production", (120, 200), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(frame, f"Current Color: {latest_color}", (200, 250), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    # Add detection area
    cv2.rectangle(frame, (220, 280), (420, 380), (255, 255, 255), 2)
    
    return frame

def generate_frames():
    """Video stream generator"""
    while True:
        with frame_lock:
            if current_frame is not None:
                frame = current_frame
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            else:
                # Send placeholder frame
                placeholder = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(placeholder, "Starting camera...", (200, 240), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                ret, buffer = cv2.imencode('.jpg', placeholder)
                if ret:
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
        
        time.sleep(1/CONFIG['fps'])

# Routes
@app.route('/')
def index():
    return jsonify({
        "status": "running",
        "service": "HueEye.AI Backend API",
        "environment": "production" if os.environ.get('RAILWAY_ENVIRONMENT') else "development",
        "endpoints": {
            "video_feed": "/video_feed",
            "get_color": "/get_color",
            "health": "/health",
            "camera_status": "/camera_status"
        }
    })

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), 
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/get_color')
def get_color():
    """API endpoint untuk mendapatkan warna terbaru"""
    try:
        # Try to get latest prediction from queue
        if not prediction_queue.empty():
            latest_color = prediction_queue.get_nowait()
        return jsonify({'color': latest_color})
    except Exception as e:
        logger.error(f"❌ Error in get_color: {e}")
        return jsonify({'color': 'ERROR'})

@app.route('/health')
def health():
    """Health check endpoint"""
    is_production = os.environ.get('RAILWAY_ENVIRONMENT') == 'production'
    return jsonify({
        'status': 'healthy',
        'model_loaded': model is not None,
        'camera_active': not is_production and camera_active,
        'environment': 'production' if is_production else 'development',
        'timestamp': time.time()
    })

@app.route('/camera_status')
def camera_status():
    """Camera status endpoint"""
    is_production = os.environ.get('RAILWAY_ENVIRONMENT') == 'production'
    return jsonify({
        'active': not is_production and camera_active,
        'environment': 'production' if is_production else 'development'
    })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

def initialize_app():
    """Initialize application components"""
    logger.info("🚀 Initializing HueEye.AI Backend...")
    
    # Load AI model
    model_loaded = load_ai_model()
    
    # Start worker threads
    camera_thread = threading.Thread(target=camera_worker, daemon=True)
    camera_thread.start()
    
    prediction_thread = threading.Thread(target=prediction_worker, daemon=True)
    prediction_thread.start()
    
    logger.info("✅ Application initialized successfully")
    return model_loaded

# Initialize application
if __name__ == '__main__':
    initialize_app()
    
    # Determine if we're in development or production
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    if debug_mode:
        # Development mode
        app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
    else:
        # Production mode
        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port, debug=False)
else:
    # For Gunicorn
    initialize_app()