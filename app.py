from flask import Flask, request, render_template
import subprocess
import os
import signal
import time

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ruta completa a Hashcat
HASHCAT_PATH = '/usr/bin/hashcat'  # Ruta en Kali Linux

# Aseguramos que la carpeta de uploads existe
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Variable para almacenar el proceso de hashcat
hashcat_process = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    global hashcat_process

    if hashcat_process and hashcat_process.poll() is None:
        return render_template('index.html', output="Hashcat is already running. Please stop it before starting a new analysis.")

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
    command = f'xterm -e "{HASHCAT_PATH} -m 22000 \'{hash_file_path}\' -a 3 {mask} {device_option}"'

    # Imprimir el comando para depuración
    print(f"Ejecutando comando: {command}")

    try:
        hashcat_process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        output = ''
        for line in hashcat_process.stdout:
            output += line
        error = hashcat_process.stderr.read()
        if hashcat_process.returncode != 0:
            output += error
    except Exception as e:
        output = f"Error: {str(e)}"

    # Imprimir salida para depuración
    print(f"Salida: {output}")

    return render_template('index.html', output=output)

@app.route('/terminal', methods=['POST'])
def terminal():
    command = request.form['command']
    
    # Imprimir el comando para depuración
    print(f"Ejecutando comando en terminal: {command}")

    try:
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        output = ''
        for line in process.stdout:
            output += line
        error = process.stderr.read()
        if process.returncode != 0:
            output += error
    except Exception as e:
        output = f"Error: {str(e)}"

    # Imprimir salida para depuración
    print(f"Salida de terminal: {output}")

    return render_template('index.html', output=output)

@app.route('/update', methods=['POST'])
def update():
    global hashcat_process
    if hashcat_process and hashcat_process.poll() is None:
        hashcat_process.stdin.write(b's\n')
        hashcat_process.stdin.flush()
        return render_template('index.html', output="Sent 's' to hashcat.")
    return render_template('index.html', output="Hashcat is not running.")

@app.route('/quit', methods=['POST'])
def quit():
    global hashcat_process
    if hashcat_process and hashcat_process.poll() is None:
        hashcat_process.stdin.write(b'q\n')
        hashcat_process.stdin.flush()
        hashcat_process.terminate()  # Terminate the process
        hashcat_process = None
        return render_template('index.html', output="Sent 'q' to hashcat and terminated the process.")
    return render_template('index.html', output="Hashcat is not running.")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
