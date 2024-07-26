from flask import Flask, request, render_template
from flask_socketio import SocketIO, emit
import subprocess
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
socketio = SocketIO(app)

# Ruta completa a Hashcat
HASHCAT_PATH = '/usr/bin/hashcat'  # Actualiza esta ruta en Kali Linux

# Aseguramos que la carpeta de uploads existe
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

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

    # Ejecutar el comando y enviar actualizaciones al cliente en tiempo real
    def run_command(command):
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        for line in process.stdout:
            socketio.emit('update', {'data': line})
        process.stdout.close()
        process.wait()
        if process.returncode != 0:
            error = process.stderr.read()
            socketio.emit('update', {'data': error})

    socketio.start_background_task(run_command, command)

    return render_template('index.html')

@app.route('/terminal', methods=['POST'])
def terminal():
    command = request.form['command']
    
    # Ejecutar el comando y enviar actualizaciones al cliente en tiempo real
    def run_command(command):
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        for line in process.stdout:
            socketio.emit('update', {'data': line})
        process.stdout.close()
        process.wait()
        if process.returncode != 0:
            error = process.stderr.read()
            socketio.emit('update', {'data': error})

    socketio.start_background_task(run_command, command)

    return render_template('index.html')

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0')
