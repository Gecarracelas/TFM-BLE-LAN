from flask import Flask, render_template, request, send_file
import subprocess
import time
import signal
import pickle
import os

app = Flask(__name__)

ruta = './backup.pickle'

def verificar_rfkill_desbloqueado():
    try:
        output = subprocess.check_output(['rfkill', 'list', 'bluetooth'], text=True)
        return 'Soft blocked: yes' not in output
    except subprocess.CalledProcessError:
        return False

def verificar_bluetooth_encendido():
    try:
        output = subprocess.check_output(['bluetoothctl', 'show'], text=True)
        return 'Powered: yes' in output
    except subprocess.CalledProcessError:
        return False

def ejecutar_sniffer():
    crear_auxfile = subprocess.run(['touch', ruta])

    desbloquear_rfkill = subprocess.run(['rfkill', 'unblock', 'bluetooth'])
    # Control de desbloqueo y encendido de interfaces Bluetooth a nivel de SO
    if not verificar_rfkill_desbloqueado():
        print("Error: No se pudo desbloquear la interfaz Bluetooth.")
        return

    encender_bluetooth()

    if not verificar_bluetooth_encendido():
        print("Error: No se pudo encender la interfaz Bluetooth.")
        return

    # Listar interfaces Bluetooth disponibles

    listar = subprocess.run(['rfkill', '-r'])

    # btlesniffer se utiliza como subproceso dado que fue instalado y es utilizado como un comando más de Linux
    # Source: https://github.com/scipag/btle-sniffer

    # MIT License
    # Copyright (c) 2017 scip AG
    # Permission is hereby granted, free of charge, to any person obtaining a copy
    # of this software and associated documentation files (the "Software"), to deal
    # in the Software without restriction, including without limitation the rights
    # to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    # copies of the Software, and to permit persons to whom the Software is
    # furnished to do so, subject to the following conditions:

    # The above copyright notice and this permission notice shall be included in all
    # copies or substantial portions of the Software.

    # THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    # IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    # FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    # AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    # LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    # OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    # SOFTWARE.

    #license_attributions: https://github.com/scipag/btle-sniffer/blob/master/LICENSE

    # Params para ajustar la salida del sniffer y tiempo de ejecución
    sniffer = subprocess.Popen(['btlesniffer', '-c', '-o', ruta])
    time.sleep(30)
    sniffer.send_signal(signal.SIGINT)
    sniffer.wait()
    guardar_datos_en_archivo()

def encender_bluetooth():
    subprocess.run(['bluetoothctl', 'power', 'on'])

def apagar_bluetooth():
    subprocess.run(['bluetoothctl', 'power', 'off'])

def guardar_datos_en_archivo():
    with open(ruta, 'rb') as f:
        datos_serializados = f.read()
    # Los datos de salida de btlesniffer son serializados y almacenados en binario
    # Para no modificar el códido fuente del sniffer, se realiza deserializado y agrega fecha y hora luego de pasarlo a texto
    datos_deserializados = pickle.loads(datos_serializados)
    fecha_hora_escaneo = time.strftime('%Y-%m-%d %H:%M:%S')
    archivo_texto = './backup_legible.txt'
    with open(archivo_texto, 'w') as f:
        for item in datos_deserializados:
            f.write(fecha_hora_escaneo + ';' + str(item) + '\n')

def cargar_datos(ruta):
    datos = []
    try:
        with open(ruta, 'r') as f:
            for linea in f:
                # Se recolectan los datos más relevantes de cada dispositivo y se aplica parsing para lograr un diccionario legible
                partes = linea.strip().split(";")
                while len(partes) < 5:
                    partes.append("")
                fecha_hora, nombre, mac_potencia, vendedor, servicios = [parte.strip() for parte in partes]
                mac, potencia = mac_potencia.split(' ', 1) if ' ' in mac_potencia else (mac_potencia, "")
                item = {
                    "Fecha y Hora": fecha_hora,
                    "Nombre": nombre,
                    "MAC": mac,
                    "Potencia de Señal": potencia,
                    "Vendedor": vendedor.split(": ")[1] if ": " in vendedor else vendedor,
                    "Servicios": servicios.split(": ")[1] if ": " in servicios else servicios
                }
                datos.append(item)
    except FileNotFoundError:
        print(f'El archivo {ruta} no se encuentra. No se han cargado los datos.')
    return datos


def renombrar_archivos():
    contador = 1
    while os.path.exists(f"{contador}-backup_legible.txt"):
        contador += 1
    if os.path.exists("backup_legible.txt"):
        os.rename("backup_legible.txt", f"{contador}-backup_legible.txt")

def eliminar_todos_los_archivos():
    contador = 1
    while os.path.exists(f"{contador}-backup_legible.txt"):
        os.remove(f"{contador}-backup_legible.txt")
        contador += 1
    if os.path.exists("backup_legible.txt"):
        os.remove("backup_legible.txt")

def recolectar_todos_los_dispositivos():
    contador = 1
    todos_los_dispositivos = []
    while os.path.exists(f"{contador}-backup_legible.txt"):
        datos = cargar_datos(f"{contador}-backup_legible.txt")
        todos_los_dispositivos.extend(datos)
        contador += 1
    return todos_los_dispositivos

@app.route('/', methods=['GET', 'POST'])
def index():
    datos = cargar_datos("backup_legible.txt")
    if request.method == 'POST':
        accion = request.form.get('accion')
        if accion == 'iniciar_escaneo':
            ejecutar_sniffer()
            datos = cargar_datos("backup_legible.txt")
        elif accion == 'visualizar_dispositivos':
            renombrar_archivos()
        elif accion == 'cargar_historico':
            return todos_dispositivos()
        elif accion == 'eliminar_dispositivos':
            eliminar_todos_los_archivos()
            datos = []
    return render_template('data_table.html', datos=datos)

@app.route('/todos_los_dispositivos', methods=['GET'])
def todos_dispositivos():
    datos = recolectar_todos_los_dispositivos()
    return render_template('todos_dispositivos.html', datos=datos)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
