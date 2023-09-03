# TFM-BLE-LAN
Una utilidad simple escrita en Python para monitorear y registrar dispositivos BLE en entonrnos Linux, con instalaciones en equipos físicos o máquinas virtuales.

# Dependencias
Como este proyecto se basa en btle-sniffer (https://github.com/scipag/btle-sniffer/tree/master), ÚNICAMENTE se ejecutará en SISTEMAS LINUX.
El proyecto requiere además GLib2, PyGobject (comúnmente conocido como python-gi, python-gobject o pygobject, pero no empaquetado en PyPi) y D-Bus.
Adicionalmente, al trabajar con btle-sniffer como comando de Linux y contar con interfaz gráfica, requiere Flask y otros módulos nativos como subprocess, time, signal, oickle y os.

# Instalación
Al clonar o descargar el el repositorio se contará con un directorio llamado "requerimientos", dentro del cual se encuentran los archivos necesarios para la instalación de btle-sniffer.
Una vez en el directorio (/requerimientos/btle-sniffer) es posible observar un archivo denominado "setup.py", del cual puede consultar la ayuda mediante el comando:
python3 setup.py --help. Para el caso del sniffer será suficiente con realizar la instalación de la herramienta como pre requisito, para ello es necesario lanzar el siguiente comando: sudo python3 setup.py install. 
Una vez finalice la instalación, podrá notar que se ha incorporado como un comando más de Linux.

También es neceario contar con dependencias adecuadas, por lo que es necesario realizar la instalación de aquella que no tenga el sistema destino a través del archivo requirements.txt. Es decir, pip install -r requirements.txt
Nota: puede que varias de las dependencias ya se encuentres satisfechas puesto que son nativas a los sistemas Linux.

# Utilización 

Con los pre requisitos cumplidos y ubicados en el directorio principal del proyecto, es posible ejecutar el Sniffer BLE a través del comando python3 app.py.
