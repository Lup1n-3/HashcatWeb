from flask import Flask, request, render_template
import subprocess
import os
import time

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ruta completa a Hashcat
HASHCAT_PATH = '/usr/bin/hashcat'  # Ruta en Kali Linux

# Aseguramos que la carpeta de uploads existe
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Variables para manejar procesos de hashcat y salida en tiempo real
hashcat_session_name = 'hashcat_session'
hashcat_process = None
hashcat_output_file = 'hashcat_output.txt'

@app.route('/')
def index():
    output = ''
    if os.path.exists(hashcat_output_file):
        with open(hashcat_output_file, 'r') as file:
            output = file.read()
    return render_template('index.html', output=output)

@app.route('/submit', methods=['POST'])
def submit():
    global hashcat_process

    # Detener cualquier proceso de Hashcat ya en ejecución
    if hashcat_process:
        subprocess.call(['tmux', 'kill-session', '-t', hashcat_session_name])
    
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

    # Ejecutar Hashcat en una nueva sesión de tmux
    tmux_command = f'tmux new-session -d -s {hashcat_session_name} "bash -c \'{command} | tee {hashcat_output_file}\'"'

    # Imprimir el comando para depuración
    print(f"Ejecutando comando: {tmux_command}")

    try:
        subprocess.Popen(tmux_command, shell=True)
        time.sleep(2)  # Dar tiempo para que tmux se abra y comience a ejecutar
    except Exception as e:
        output = f"Error: {str(e)}"
        return render_template('index.html', output=output)

    return render_template('index.html', output="Hashcat started. Check the output below.")

@app.route('/update', methods=['POST'])
def update():
    if hashcat_process:
        try:
            # Enviar 's' a la sesión de tmux
            subprocess.call(['tmux', 'send-keys', '-t', hashcat_session_name, 's', 'C-m'])
            time.sleep(1)  # Esperar un momento para que el proceso maneje el comando
            return index()  # Actualizar la página para mostrar la salida
        except Exception as e:
            return render_template('index.html', output=f"Error sending 's': {str(e)}")
    return render_template('index.html', output="Hashcat is not running.")

@app.route('/quit', methods=['POST'])
def quit():
    if hashcat_process:
        try:
            # Enviar 'q' a la sesión de tmux y terminar el proceso
            subprocess.call(['tmux', 'send-keys', '-t', hashcat_session_name, 'q', 'C-m'])
            subprocess.call(['tmux', 'kill-session', '-t', hashcat_session_name])
            return render_template('index.html', output="Sent 'q' to hashcat and terminated the process.")
        except Exception as e:
            return render_template('index.html', output=f"Error sending 'q': {str(e)}")
    return render_template('index.html', output="Hashcat is not running.")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
