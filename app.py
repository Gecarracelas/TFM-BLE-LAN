from flask import Flask, render_template, request, send_file
import subprocess
import time
import signal
import pickle
import os

app = Flask(__name__)

ruta = './backup.pickle'

def ejecutar_sniffer():
    crear_auxfile = subprocess.run(['touch', ruta])
    desbloquear_rfkill = subprocess.run(['rfkill', 'unblock', 'bluetooth'])
    encender_bluetooth()
    listar = subprocess.run(['rfkill', '-r'])
    sniffer = subprocess.Popen(['btlesniffer', '-c', '-o', ruta])
    time.sleep(30)
    sniffer.send_signal(signal.SIGINT)
    sniffer.wait()
    guardar_datos_en_archivo()

def encender_bluetooth():
    subprocess.run(["bluetoothctl", "power", "on"])

def apagar_bluetooth():
    subprocess.run(["bluetoothctl", "power", "off"])

def guardar_datos_en_archivo():
    with open(ruta, 'rb') as f:
        datos_serializados = f.read()

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
