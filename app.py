from flask import Flask, request, render_template
from flask_socketio import SocketIO, emit
import subprocess
import os
import time

app = Flask(__name__)
socketio = SocketIO(app)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ruta completa a Hashcat
HASHCAT_PATH = '/usr/bin/hashcat'  # Ruta en Kali Linux

# Aseguramos que la carpeta de uploads existe
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    hash_file = request.files['hash_file']
    if hash_file:
        hash_file_path = os.path.join(app.config['UPLOAD_FOLDER'], hash_file.filename)
        hash_file.save(hash_file_path)
    
    charset = request.form['charset']
    length = int(request.form['length'])
    use_gpu = 'use_gpu' in request.form

    charset_mapping = {
        'numeric': '?d',
        'alpha': '?l',
        'alphanumeric': '?a',
        'special': '?a?s'
    }

    selected_charset = charset_mapping[charset]
    mask = selected_charset * length

    # Construir el comando Hashcat
    device_option = '-D 1' if use_gpu else ''
    command = f'{HASHCAT_PATH} -m 22000 "{hash_file_path}" -a 3 {mask} {device_option}'

    # Imprimir el comando para depuración
    print(f"Ejecutando comando: {command}")

    try:
        # Ejecutar el comando y leer la salida en tiempo real
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                socketio.emit('update', {'data': output.strip()})
            time.sleep(0.1)
        error = process.stderr.read()
        if error:
            socketio.emit('update', {'data': error.strip()})
    except Exception as e:
        socketio.emit('update', {'data': f"Error: {str(e)}"})

    return render_template('index.html')

@app.route('/terminal', methods=['POST'])
def terminal():
    command = request.form['command']
    
    # Imprimir el comando para depuración
    print(f"Ejecutando comando en terminal: {command}")

    try:
        # Ejecutar el comando y leer la salida en tiempo real
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                socketio.emit('update', {'data': output.strip()})
            time.sleep(0.1)
        error = process.stderr.read()
        if error:
            socketio.emit('update', {'data': error.strip()})
    except Exception as e:
        socketio.emit('update', {'data': f"Error: {str(e)}"})

    return render_template('index.html')

@socketio.on('connect')
def test_connect():
    emit('my response', {'data': 'Connected'})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
