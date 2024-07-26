from flask import Flask, request, render_template
import subprocess
import os
import time

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ruta completa a Hashcat
HASHCAT_PATH = '/usr/bin/hashcat'  # Ruta en Kali Linux
OUTPUT_FILE = 'hashcat_output.txt'

# Aseguramos que la carpeta de uploads existe
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

hashcat_process = None

@app.route('/')
def index():
    output = ''
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, 'r') as file:
            output = file.read()
    return render_template('index.html', output=output)

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
    command = f'{HASHCAT_PATH} -m 22000 "{hash_file_path}" -a 3 {mask} {device_option}'

    # Redirigir salida a un archivo
    xterm_command = f'xterm -hold -e "bash -c \'{command} > {OUTPUT_FILE} 2>&1\'"'

    # Imprimir el comando para depuración
    print(f"Ejecutando comando: {xterm_command}")

    try:
        hashcat_process = subprocess.Popen(xterm_command, shell=True)
        return render_template('index.html', output='Hashcat started. Check the output below.')
    except Exception as e:
        return render_template('index.html', output=f"Error: {str(e)}")

@app.route('/update', methods=['POST'])
def update():
    if hashcat_process and hashcat_process.poll() is None:
        try:
            # Enviar 's' usando xdotool
            os.system('xdotool search --name "xterm" key s')
            return render_template('index.html', output="Sent 's' to hashcat.")
        except Exception as e:
            return render_template('index.html', output=f"Error sending 's': {str(e)}")
    return render_template('index.html', output="Hashcat is not running.")

@app.route('/quit', methods=['POST'])
def quit():
    if hashcat_process and hashcat_process.poll() is None:
        try:
            # Enviar 'q' usando xdotool
            os.system('xdotool search --name "xterm" key q')
            hashcat_process.terminate()  # Terminate the process
            return render_template('index.html', output="Sent 'q' to hashcat and terminated the process.")
        except Exception as e:
            return render_template('index.html', output=f"Error sending 'q': {str(e)}")
    return render_template('index.html', output="Hashcat is not running.")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
