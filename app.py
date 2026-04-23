from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import numpy as np
from main import process_for_web

app = Flask(__name__, static_folder='frontend/dist')
CORS(app)  # Allow cross-origin requests during development

# Configure upload settings
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/analyze', methods=['POST'])
def analyze():
    if 'image' not in request.files:
        return jsonify({"error": "No image uploaded"}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({"error": "Empty filename"}), 400
    
    if file and allowed_file(file.filename):
        try:
            image_bytes = file.read()
            results = process_for_web(image_bytes)
            
            # Convert NumPy types to Python types for JSON serialization
            serializable_results = {}
            for k, v in results.items():
                if isinstance(v, (np.float32, np.float64)):
                    serializable_results[k] = float(v)
                elif isinstance(v, (np.int32, np.int64)):
                    serializable_results[k] = int(v)
                else:
                    serializable_results[k] = v
            
            # Remove non-serializable objects (bleach_mask was converted to base64)
            if "bleach_mask" in serializable_results:
                del serializable_results["bleach_mask"]
                
            return jsonify(serializable_results)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({"error": str(e)}), 500
    
    return jsonify({"error": "Invalid file type"}), 400

# Serve frontend in production
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    app.run(debug=True, port=5003)
