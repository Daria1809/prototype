import os
import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, send_file, flash, jsonify
from werkzeug.utils import secure_filename
import shutil
from utils.web_converter_adapter import process_log_file

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size

# ✅ Добавьте эту строку для доступа к функции any() в шаблонах
app.jinja_env.globals['any'] = any

# Configuration
UPLOAD_FOLDER = 'uploads'
INPUT_FOLDER = os.path.join(UPLOAD_FOLDER, 'input')
OUTPUT_FOLDER = os.path.join(UPLOAD_FOLDER, 'output')
ALLOWED_EXTENSIONS = {
    'log', 'csv', 'dbc', 'ld'
}

# Create directories
os.makedirs(INPUT_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['INPUT_FOLDER'] = INPUT_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def clean_filename(filename):
    """Remove special characters from filename"""
    return secure_filename(filename)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert', methods=['GET', 'POST'])
def convert():
    if request.method == 'POST':
        # Check if files were uploaded
        if 'log_file' not in request.files:
            flash('No log file selected')
            return redirect(request.url)
        
        log_file = request.files['log_file']
        if log_file.filename == '':
            flash('No log file selected')
            return redirect(request.url)
        
        if not allowed_file(log_file.filename):
            flash('Invalid file type. Allowed: .log, .csv')
            return redirect(request.url)
        
        # Get log type
        log_type = request.form.get('log_type', 'CSV').upper()
        
        # Save uploaded files
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save log file
        log_filename = clean_filename(f"{timestamp}_{log_file.filename}")
        log_path = os.path.join(INPUT_FOLDER, log_filename)
        log_file.save(log_path)
        
        # Save DBC file if provided (for CAN logs)
        dbc_path = None
        if log_type == 'CAN':
            if 'dbc_file' not in request.files or request.files['dbc_file'].filename == '':
                flash('DBC file is required for CAN logs')
                return redirect(request.url)
            
            dbc_file = request.files['dbc_file']
            if not allowed_file(dbc_file.filename):
                flash('Invalid DBC file type')
                return redirect(request.url)
            
            dbc_filename = clean_filename(f"{timestamp}_{dbc_file.filename}")
            dbc_path = os.path.join(INPUT_FOLDER, dbc_filename)
            dbc_file.save(dbc_path)
        
        # Get processing parameters
        frequency = request.form.get('frequency', '10')
        output_filename = request.form.get('output_filename', '')
        
        # Get metadata
        metadata = {
            'driver': request.form.get('driver', ''),
            'vehicle_id': request.form.get('vehicle_id', ''),
            'vehicle_weight': request.form.get('vehicle_weight', ''),
            'vehicle_type': request.form.get('vehicle_type', ''),
            'vehicle_comment': request.form.get('vehicle_comment', ''),
            'venue_name': request.form.get('venue_name', ''),
            'event_name': request.form.get('event_name', ''),
            'event_session': request.form.get('event_session', ''),
            'long_comment': request.form.get('long_comment', ''),
            'short_comment': request.form.get('short_comment', ''),
        }
        
        # Process the file
        try:
            # Отладочная информация - добавил эту секцию
            print(f"=== DEBUG CONVERSION START ===")
            print(f"Converting file: {log_path}")
            print(f"Log type: {log_type}")
            print(f"DBC path: {dbc_path}")
            print(f"Output folder: {OUTPUT_FOLDER}")
            print(f"Frequency: {frequency}")
            print(f"Metadata: {metadata}")
            
            output_path = process_log_file(
                log_path=log_path,
                log_type=log_type,
                dbc_path=dbc_path,
                output_folder=OUTPUT_FOLDER,
                frequency=float(frequency),
                output_filename=output_filename,
                metadata=metadata
            )
            
            # Проверяем размер файла
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                print(f"Output file created: {output_path} ({file_size} bytes)")
                
                # Дополнительная проверка: первые 100 байт файла
                with open(output_path, 'rb') as f:
                    header = f.read(100)
                    print(f"File header starts with: {header[:50]}")
            
            print(f"=== DEBUG CONVERSION END ===")
            
            return render_template('result.html', 
                                 output_file=os.path.basename(output_path),
                                 log_type=log_type,
                                 metadata=metadata)
            
        except Exception as e:
            print(f"=== DEBUG ERROR ===")
            print(f"Error details: {str(e)}")
            import traceback
            traceback.print_exc()
            print(f"=== DEBUG ERROR END ===")
            flash(f'Error processing file: {str(e)}')
            return redirect(request.url)
    
    return render_template('convert.html')
@app.route('/download/<filename>')
def download_file(filename):
    file_path = os.path.join(OUTPUT_FOLDER, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        flash('File not found')
        return redirect(url_for('index'))

@app.route('/api/convert', methods=['POST'])
def api_convert():
    """API endpoint for programmatic conversion"""
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        if 'log_path' not in data or 'log_type' not in data:
            return jsonify({'error': 'Missing required fields'}), 400
        
        log_type = data['log_type'].upper()
        if log_type == 'CAN' and 'dbc_path' not in data:
            return jsonify({'error': 'DBC path required for CAN logs'}), 400
        
        # Process file
        output_path = process_log_file(
            log_path=data['log_path'],
            log_type=log_type,
            dbc_path=data.get('dbc_path'),
            output_folder=OUTPUT_FOLDER,
            frequency=data.get('frequency', 10),
            output_filename=data.get('output_filename'),
            metadata=data.get('metadata', {})
        )
        
        return jsonify({
            'success': True,
            'output_file': os.path.basename(output_path),
            'output_path': output_path
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/cleanup', methods=['POST'])
def cleanup():
    """Clean up uploaded files"""
    try:
        # Delete files older than 24 hours
        import time
        now = time.time()
        cutoff = now - (24 * 3600)  # 24 hours
        
        for folder in [INPUT_FOLDER, OUTPUT_FOLDER]:
            for filename in os.listdir(folder):
                file_path = os.path.join(folder, filename)
                if os.path.isfile(file_path):
                    file_age = now - os.path.getmtime(file_path)
                    if file_age > cutoff:
                        os.remove(file_path)
        
        return jsonify({'success': True, 'message': 'Cleanup completed'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)