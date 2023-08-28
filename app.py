from flask import Flask, render_template, request, send_file
import subprocess
import time
import signal
import pickle
import os

app = Flask(__name__)

ruta = './backup.pickle'
contador = 1

def ejecutar_sniffer():
    global ejecutar
    crear_auxfile = subprocess.run(['touch', ruta])
    if crear_auxfile.returncode == 0:
        print('Archivo aux creado correctamente')
    desbloquear_rfkill = subprocess.run(['rfkill', 'unblock', 'bluetooth'])
    if desbloquear_rfkill.returncode == 0:
        print('Interfaces BLE desbloqueadas OK')
        encender_bluetooth()

        listar = subprocess.run(['rfkill', '-r'])

        sniffer = subprocess.Popen(['btlesniffer', '-c', '-o', ruta])

        print('El Sniffer BLE está en funcionamiento durante 30 segundos...')
        time.sleep(30)
        sniffer.send_signal(signal.SIGINT)
        sniffer.wait()

        print('Sniffer BLE detenido y Bluetooth apagado.')

        guardar_datos_en_archivo()

        ejecutar = False

    else:
        print('Error al desbloquear las interfaces BLE')

def encender_bluetooth():
    subprocess.run(["bluetoothctl", "power", "on"])

def apagar_bluetooth():
    subprocess.run(["bluetoothctl", "power", "off"])

def guardar_datos_en_archivo():
    with open(ruta, 'rb') as f:
        datos_serializados = f.read()

    datos_deserializados = pickle.loads(datos_serializados)

    archivo_texto = './backup_legible.txt'
    with open(archivo_texto, 'w') as f:
        for item in datos_deserializados:
            f.write(str(item) + '\n')

    print(f'Los datos se han convertido y guardado en {archivo_texto}.')

def cargar_datos(ruta):
    datos = []
    try:
        with open(ruta, 'r') as f:
            for linea in f:
                partes = linea.strip().split(";")
                if len(partes) != 4:
                    print(f'Línea con formato incorrecto: {linea.strip()}')
                    continue

                nombre, mac_potencia, vendedor, servicios = [parte.strip() for parte in                                                                                                                                                                                                                                                                               partes]
                mac, potencia = mac_potencia.split(' ', 1)
                item = {
                    "Nombre": nombre,
                    "MAC": mac,
                    "Potencia de Señal": potencia,
                    "Vendedor": vendedor.split(": ")[1],
                    "Servicios": servicios.split(": ")[1]
                }
                datos.append(item)
    except FileNotFoundError:
        print(f'El archivo {ruta} no se encuentra. No se han cargado los datos.')
    return datos

def renombrar_archivos():
    global contador
    if contador > 1:
        contador += 1
    while os.path.exists(f"{contador}-backup_legible.txt") or os.path.exists(f"{contador}-backup.pickle"):
        contador += 1
    
    os.rename("backup_legible.txt", f"{contador}-backup_legible.txt")
    os.rename("backup.pickle", f"{contador}-backup.pickle")
    print(f"Archivos renombrados como {contador}-backup_legible.txt y {contador}-backup.pickle")

def cargar_historico():
    global contador
    contador = 1
    historico = []
    while os.path.exists(f"{contador}-backup_legible.txt") and os.path.exists(f"{contador}-backup.pickle"):
        if contador > 1:
            historico.append({
                'nombre_legible': f"{contador}-backup_legible.txt",
                'nombre_pickle': f"{contador}-backup.pickle"
            })
        contador += 1
    return historico

@app.route('/', methods=['GET', 'POST'])
def index():
    datos = cargar_datos(f"{contador}-backup_legible.txt")

    if request.method == 'POST':
        accion = request.form.get('accion')

        if accion == 'iniciar_escaneo':
            ejecutar_sniffer()
            guardar_datos_en_archivo()
        elif accion == 'visualizar_dispositivos':
            renombrar_archivos()
            datos = cargar_datos(f"{contador}-backup_legible.txt")
        elif accion == 'cargar_historico':
            historico = cargar_historico()
            return render_template('historico.html', historico=historico)
        else:
            print('Acción desconocida:', accion)

    return render_template('data_table.html', datos=datos)

@app.route('/ver_historico/<nombre>')
def ver_historico(nombre):
    datos = cargar_datos(nombre)
    return render_template('data_table.html', datos=datos)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
