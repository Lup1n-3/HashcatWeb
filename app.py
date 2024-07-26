from flask import Flask, request, render_template
from flask_socketio import SocketIO, emit
import subprocess
import os
import threading
import time

app = Flask(__name__)
socketio = SocketIO(app, async_mode=None)

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

    # Ejecutar el comando Hashcat en una nueva terminal
    terminal_command = f'gnome-terminal -- bash -c "{command}; exec bash"'
    try:
        subprocess.Popen(terminal_command, shell=True)
    except Exception as e:
        print(f"Error: {str(e)}")

    # Ejecutar Hashcat en segundo plano para capturar la salida
    def run_hashcat():
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        while True:
            output = process.stdout.readline()
            if output:
                socketio.emit('update', {'output': output.strip()})
            if process.poll() is not None:
                break
            time.sleep(2)  # Esperar 2 segundos entre cada actualización

    threading.Thread(target=run_hashcat).start()

    return render_template('index.html')

@app.route('/terminal', methods=['POST'])
def terminal():
    command = request.form['command']
    
    # Ejecutar el comando en una nueva terminal
    terminal_command = f'gnome-terminal -- bash -c "{command}; exec bash"'
    try:
        subprocess.Popen(terminal_command, shell=True)
    except Exception as e:
        print(f"Error: {str(e)}")

    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0')
