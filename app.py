from flask import Flask, request, render_template
import subprocess
import os

app = Flask(__name__)
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
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        output, error = process.communicate()
        if process.returncode != 0:
            output = error
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
        output, error = process.communicate()
        if process.returncode != 0:
            output = error
    except Exception as e:
        output = f"Error: {str(e)}"

    # Imprimir salida para depuración
    print(f"Salida de terminal: {output}")

    return render_template('index.html', output=output)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
