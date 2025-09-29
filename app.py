from flask import Flask, render_template, request, jsonify
import cv2
import numpy as np
from tensorflow.keras.models import load_model
import base64

app = Flask(__name__)

# Load model
try:
    model = load_model('color_classifier_model_augmented.h5')
    print("Model loaded successfully!")
except Exception as e:
    print(f"Error loading model: {e}")
    model = None

class_names = ["Blue", "Green", "Red", "Yellow"]

def process_frame(frame):
    """Proses frame untuk prediksi warna"""
    try:
        expected_shape = model.input_shape[1:3]
        resized = cv2.resize(frame, expected_shape)
        normalized = resized / 255.0
        input_array = np.expand_dims(normalized, axis=0)

        predictions = model.predict(input_array, verbose=0)
        predicted_class = np.argmax(predictions[0])
        confidence = np.max(predictions[0])

        if confidence > 0.7:
            return class_names[predicted_class]
        else:
            return "TIDAK PASTI"
    except Exception as e:
        print(f"Error processing frame: {e}")
        return "ERROR"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scan.html')
def scan():
    return render_template('scan.html')

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.json['image']
        # Hilangkan prefix base64
        img_data = data.split(',')[1]
        nparr = np.frombuffer(base64.b64decode(img_data), np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        color_name = process_frame(frame)
        return jsonify({"color": color_name})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=7860, debug=True)
