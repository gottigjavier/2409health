# Aplicación para manejo de llamadas y tareas en sector de internación.

### Descripción General.

Esta aplicación recibe y administra las llamadas y tareas programadas que se dan en el sector de internación de un hospital o clínica.

Utilizar el navegador como interfaz con el usuario hace posible su manejo descentralizado. 
Esto implica que cualquier miembro del personal de salud (médico, enfermero, administrativo) con las credenciales correpondientes puede acceder a la información y a las funciones de la aplicación (ej: ocupar cama, programar tareas, etc) desde cualquier punto de la red.

Si bien, por el tipo de aplicación, la tendencia es a su uso en PC, es totalmente compatible con móviles o tablets. 

También hay que destacar que el sistema de llamadas provenientes de los botones pulsadores de cada cama y del botón de cancelación de llamadas de cada habitación puede ser configurado de tres formas:

- Cableado: todo el recorrido de la señal desde cada pulsador hasta el servidor viaja a través de un cable.

- Mixto: desde el pulsador de cada cama hasta el nodo instalado en cada habitación la señal viaja por cable. Desde allí hasta el servidor lo hace a través de Wi-Fi.

- Inalámbrico: cada pulsador continiene una placa con capacidad de comunicación Wi-Fi con lo cual no tiene ninguna conexión cableada. Esto implica que cada pulsador tendrá dimensiones algo mayores y una batería interna.


Las carpetas "healthproject" y "nurse" contienen los archivos correspondientes al backend y fueron codificados en Python a través del framework Django.

La base de datos usa PostgreSQL.

La carpeta "nurse-react" contiene los archivos del frontend codificados en Javascript a través de la librería Reactjs.

Dentro de la carpeta "nurse-react" se encuentran las subcarpetas "components", "context" y "services". Como su nombre lo indica, la carpeta "components" contiene los componentes que serán renderizados en el DOM. Estos componentes están estructurados y nombrados de tal manera que su nombre exlique de la mejor manera posible su naturaleza y función.

En la carpeta /health/mosquitto/ se encuentra el archivo de configuración del broker y los archivos para programar la placa arduino que se encarga de recibir la señal de los pulsadores.

Algunos archivos por ahora innecesarios o redundantes han sido preservados pensando en futuras modificaciones.

### Algunos detalles previos 

La aplicación maneja un estado global a través del "contexto". 

El estado de la app y tareas son actualizadas via websockets (Django channels). Las llamadas provenientes de las placas arduino usan el protocolo MQTT. 

No se utilizan actualizaciones optimistas de la interfaz de usuario. Esto es así porque los estados de la interfaz dependen en muchos casos de las actualizaciones que vienen del backend a través de websockets (channels). 

Generalmente, en las áreas de hospitalización, cada cama tiene un botón de llamada y cada habitación tiene un botón para cancelar las llamadas de todas las camas en esa habitación.

Se espera que, a través de sistemas como Arduino y Raspberry, la señal producida por los pulsadores se transforme en datos del siguiente formato JSON: 
 {'state': state, 'id': 'call-id', 'key': 'clave-anti-hacking'}, que es el tipo de datos que espera la aplicación. El tipo de datos 'state' es booleano. El tipo de datos 'id' y 'key' son una cadena. En caso de llamada, 'id' tiene el formato 'número de habitación, número de cama' (por ejemplo: {'state': true,' id ': '12, 3', 'key': 'clave-anti-hacking'}) y en caso de cancelación, el número de llamada es de la forma 'número de habitación,0' (por ejemplo: {'state': false, 'id': '12,0', 'key': 'clave-anti-hacking'}).

 
El módulo NodeMCU 1.0 - ESP8266 cuenta con sólo 3 pines para ingreso de señal. Por el momento se designa un pin para cada cama lo que restringe el número de camas al de pines.
Se puede extender a 6 camas más botón de anulación de llamada, es decir 7 => (2³ = 8) si utilizamos cada pin como bit de un sistema binario. No son 8 sino 7 las combinaciones ya que 000 se corresponde a ninguna llamada o llamadas en reposo.
Cada cable de señal que proviene del botón puede disgregarse en bits = 1 y entonces, de acuerdo a la combinación, enviar el json al sistema.

 27/01/23 La función "recording()" graba los estados de las habitaciones, llamadas y tareas antes y después de cualquier cambio en una cadena de texto. En esta cadena de texto, los campos están separados por comas, lo que podría llegar a producir una incongruencia al encontrarse con el dato 'id': '12,3'. Esto podría solucionarse cambiando el formato de dato de '12,3' a '12.3'. Otra oción, que parecería ser la óptima, es mantener ese formato de datos, y a la hora de tratarlos, tomar por dato separado (por comas) a la habitación y la cama. El único inconveniente que se presentaba en versiones previas era con el formato del la cancelación de llamada, que constaba de un dato sin coma (Ej: 'id': '12'). Esto podía generar una falta de correspondencia entre los datos y el campo al que pertenecía porque faltaría un registro correspondiente a ese campo y el resto de los registros se trasladaría un lugar ocupando un campo incorrecto. Para solucionar esto se cambió el formato de cancelación de llamada de '12' a 12,0', lo cual no solo es menos trabajo sino que se adapta mejor a las funciones de formateo y filtración del análisis de datos. 

En las primeras versiones se podía obviar el dato 'state' ya que la app entendía que si llegaba una 'id' sin coma, el dato provenía de la cancelación de llamada. Esto quedó deprecado. 

Para las pruebas sin las placas arduino los botones pulsadores se simulan a través de "localhost:8000/nursing/rooms".

### Atención!!

Si va a probar llamadas desde una placa arduino en modo de desarrollo local, deberá decirle al servidor Django que no restrinja el puerto 8000 a la máquina local. De lo contrario, el puerto no aceptará ninguna solicitud entrante, incluso si los puertos se abren en el firewall con ufw y/o se abren en el enrutador.

Para ello debe utilizar "python3 manage.py runserver 0.0.0.0:8000".
La IP ya no será "localhost" o "127.0.0.1" sino "0.0.0.0"

También puede usar, si tiene instalado el servidor daphne:
$ daphne -b 0.0.0.0 -p 8000 healthproject.asgi:application

También deberá verificar las direcciones IP de los componentes de React que realizan solicitudes http al servidor.

Corriendo la app sobre Docker, el archivo docker-compose ya tiene la instrucción adecuada así que los puertos 8000 y 1883 (mqtt) están accesibles más allá de la máquina local, y dado que los contenedores tienen su propia subred no hace falta hacer ningún cambio.
El archivo "defines.h" contiene los valores de las constantes que se grabarán en el módulo NodeMCU 1.0 - ESP8266
así que allí habrá que definir el SSID de la red, su password y la IP a la que debe enviar los datos. En desarrollo, esta IP local es la de nuestra máquina.

En algunos sistemas Linux como Arch, el sistema denegará el acceso al path donde se monta el módulo. Este path normalmente es "/dev/ttyUSB0". Recordar que ttyUSB0 recién aparece cuando se conecta el módulo NodeMCU. 
Este error puede verse en la consola de mensajes del IDE Arduino.

Para verificar permisos:
```
ll /dev/ttyUSB0

```

ó
```
ls -l /dev/ttyUSB0

```

Para cambiar los permisos de usuarios y otros:

```
sudo chmod uo+rw /dev/ttyUSB0

```


### Configuración del archivo settings.py

Las variables de entorno utilizadas por el archivo "settings.py" se importan a través de la biblioteca django-environment desde un archivo .env en la misma carpeta que el archivo "settings.py".

Advertencia: si no está configurando su entorno por separado, cree uno.

Si no va a utilizar un archivo .env de todos modos, la aplicación utilizará los valores predeterminados definidos en "settings.py". También puede configurar los ajustes manualmente. 

Para más información vea: https://pypi.org/project/django-environ/

Para index.html con React Components... 

```
TEMPLATES= [{ ...
    'DIRS':[ 
        os.path.join(BASE_DIR, 'nursing-react/build')
    ], ...
}]
```

Configure TIME_ZONE para su hora local para mantener sincronizados la hora de la plantilla, la hora del controlador y la hora de la base de datos.

```
Set USE_TZ = False 
```

Por ejemplo: en Argentina (UTC-3) establezca 

```
TIME_ZONE = 'Etc/GMT+3' 
```

Agregue 

```
ASGI_APPLICATION = 'healthproject.routing.application'
```
 para channels-websocket.

### Desarrollo local:

```
DATABASES = {... 
    'NAME': ['database_name'], ... 
    'HOST': 'localhost', ... 
}
```

```
CHANNEL_LAYERS= {
    ... "hosts": [('localhost', 6379)],   
}
```

### Versión Docker:

Verificar que el servicio Docker esté levantado

```
$ systemctl status docker
```

Importante!: Si de todas maneras usará archivos .env para settings.py y para docker-compose.yml, asegúrese de que NAME y HOST sean:

```
DATABASES = {... 
    'NAME': 'db', ... 
    'HOST': 'db', ...
    }
```
```
CHANNEL_LAYERS= {
    ... "hosts": [('redis', 6379)],   
}
```
### Docker-compose. Instalando la App

Este proyecto fue desarrollado en Ubuntu. Si tiene otro sistema operativo, tal vez necesite cambiar la forma en que accede a las carpetas o cambiar algunos permisos. 

En la misma carpeta que contiene el archivo docker-compose.yml, cree un archivo .env que contenga las variables de entorno que usarán los contenedores.
Advertencia: si no está configurando su entorno por separado, cree uno.
Si no va a utilizar un archivo .env de todos modos, la aplicación utilizará los valores predeterminados definidos en el archivo .yml. También puede configurar los ajustes manualmente. 

Para más información vea: https://docs.docker.com/compose/environment-variables/

Esto arrancará cuatro contenedores, uno para la base de datos PostgreSQL, uno para el servidor Redis, uno para el broker MQTT Mosquitto, y otro para la App.

Al correr el contenedor de la App, también creará automáticamente un super usuario. Las credenciales son las que se encuentran en la lista de comandos del archivo docker-compose.yml

#### Método 1:

A través del repositorio GitHub:

Si ha clonado la versión de desarrollo del proyecto desde GitHub, incluye carpetas de desarrollo como "src", "node_modules", etc., pero la imagen creada para docker-compose no incluirá carpetas de desarrollo ni archivos .env. Ver: .dockerignore 

"appdirectory" será la carpeta que contiene el archivo docker-compose.

```
mypc@mypc:~appdirectory$ docker-compose up --build -d (optional --> -d: detached mode)
```

Para parar los contenedores, borrarlos y dar de baja la red interna entre ellos: 

```
mypc@mypc:~appdirectory$ docker-compose down
```

Para omitir el error db auth.User al migrar, docker-compose.yml ejecuta los comandos: 

```
mypc@mypc:~appdirectory$ python3 manage.py migrate auth  (r1)
```

```
mypc@mypc:~appdirectory$ python3 manage.py migrate --run-syncdb  (r2)
```

Cuando las tablas están configuradas se ejecuta:

```
mypc@mypc:~appdirectory$ python3 manage.py runserver 0.0.0.0:8000
```

#### Método 2:

A través del repositorio Docker:

Renombre o borre docker-compose.yml y renombre docker-compose-hub.yml como docker-compose.yml

Ahora el archivo docker-compose usa la imagen de https://hub.docker.com/repository/docker/gottigjavier/health-app

Archivos de desarrollo y .env no están incluídos en la imagen docker. Vea el archivo .dockerignore.

```
mypc@mypc:~appdirectory$ docker-compose up --build -d (optional --> -d: detached mode)
```

## Postgresql, redis y MQTT (sin Docker)

Particularmente en el uso de desarrollo local opto por deshabilitar todos los servicios no indispensables en el arranque. En caso de usar docker-compose, los servicios se levantan automáticamente. Es más, si alguno de estos ya está corriendo, aparecerá un error diciento que el puerto ya está ocupado.

Para habilitar que el servicio no arranque con el inicio de la máquina:

```
mypc@mypc:~$ sudo systemctl disable <servicio>.service ("enable" para habilitar)
```

Dado este caso, los servidores de la db Postgresql, Redis, y Mosquitto no estarán corriendo, por lo tanto hay que levantarlos.

### Postgresql:

```
mypc@mypc:~$ sudo systemctl start postgresql (opcional "postgreql.service")
```

Comandos adicionales: status y stop

### Mosquitto:

```
mypc@mypc:~$ sudo systemctl start mosquitto (o "mosquitto.service")
```

Comandos adicionales: status y stop

### Redis:

```
mypc@mypc:~$ redis-server (queda ocupado el terminal)
```

> Detener Redis server: Ctrl + C

para ejecutar Redis en segundo plano:

```
mypc@mypc:~$ redis-server &
```

o:

```
mypc@mypc:~$ redis-server --daemonize yes
```

Para ver el status de Redis:

```
mypc@mypc:~$ ps aux | grep redis-server
```

Para parar el servidor Redis corriendo en segundo plano:

```
mypc@mypc:~$ pkill redis-server
```

### Mosquitto en views.py

En el archivo "views.py", se importa el módulo paho.mqtt.client para que la aplicación se suscriba al broker mosquitto.

Si enumeramos las conexiones (ss -tlnp), veremos que el corredor está escuchando en *: 1883.
Al enumerar los contenedores en ejecución (docker ps), devolverá algo similar: 0.0.0.0:1883.

Para desarrollo local sin Docker:

```
client.connect("0.0.0.0", 1883)
```

> En todos lo casos recordar que en el archivo "defines.h", el cual le pasa los valores de las variables (similar a .env) al archivo fuente "HealthMQTTClient.ino", se establecen los valores de la red wifi y la ip del servidor en el que está corriendo la app y a la cual la placa arduino enviará los datos. En caso dev local es la máquina propia. Verificar siempre esto.

## MQTT con Docker

En el archivo "views.py", se importa el módulo paho.mqtt.client para que la aplicación se suscriba al broker mosquitto.

Si enumeramos las conexiones (ss -tlnp), veremos que el corredor está escuchando en *: 1883.
Al enumerar los contenedores en ejecución (docker ps), devolverá algo similar: 0.0.0.0:1883.

La lógica indicaría que al lanzar la conexión desde el archivo "views.py" con la declaración "client.connect (IP, Port)" se deberían utilizar los datos anteriores.

Ejecutando en "localhost" o "0.0.0.0", y con el servicio mosquitto ya corriendo en la máquina local la ip será una de estas.

Al ejecutarse en Docker, funcionó al poner, por ejemplo, "client.connect ("192.168.0.xx, 1883)" y
observar en el mensaje de error en qué puerto está realmente escuchando mosquitto.
En este caso 10.10.8.1 (voilà).

Entonces, para ejecutar a través de docker, queda: 

```
client.connect ('10.10.8.1', 1883)
``` 

#### Solo usuarios autorizados pueden acceder a la aplicación. Se debe crear el primer ususario como superusuario de Django:

Liste los contenedores que están corriendo con:

```
mypc@mypc:~appdirectory$ docker ps
```

Ingrese al contenedor donde corre la app para escribir comandos:

```
mypc@mypc:~appdirectory$ docker exec -it [app container ID] bash
```

Creando un superusuario:

```
root@containerID:/healt# python3 manage.py createsuperuser
```

Si por alguna razón los comandos (r1) y (r2) no ejecutaron las migraciones en su sistema o arrojaron un error, ejecútelas manualmente dentro del contenedor antes de crear el superusuario. 

### Listos para trabajar:

Abra su navegador en la dirección localhost:8000 (exposed port)

>La página localhost:8000/nursing/rooms simula los botones de llamada y cancelación de llamadas de las camas y habitaciones.

>La página de administración de Django está en: localhost:8000/admin (nombre de superusuario y contraseña de superusuario)

Las carpetas data/db se crean con permisos restringidos. Si necesita reconstruir los contenedores, debe cambiar los permisos. Ejemplo (Sistemas Unix):

```
sudo chmod 777 -R health/
```

Recuerde que la opción 777 -R da permiso total para esa carpeta en forma recursiva a cualquier usuario.  

Cuando se crea el nuevo contenedor de la aplicación, los permisos se volverán a restringir. 

Para detener el servidor si no lanzó en detached mode:

>CTRL+C

Detenga los servicios y la red y elimine los contenedores con: 

```
mypc@mypc:~appdirectory$ docker-compose down (2)
```

Si obtiene el error "Cannot remove container ..." (Ubuntu):

```
mypc@mypc:~appdirectory$ sudo aa-remove-unknown
```

y repita (2).

Para restablecer apparmor:

```
mypc@mypc:~appdirectory$ sudo /etc/init.d/apparmor restart
```

### Acceso a la aplicación

Si no iniciño sesión, será redirigido a: http://localhost:8000/login

Iniciada la sesión, será llevado a la página de inicio: http://localhost:8000/nursing/home

Allí, usted puede ingresar a la app, registrar un nuevo ususario (solo administradores), ir a la página de administración de Django (solo superusuarios) o cerrar sesión.

Para mantener la ventana de la aplicación lo más limpia posible no se han incluído botones para navegar a la hompage. Si usted necesita, por ejemplo, cerrar sesión dirigiéndose a la página de inicio, puede escribir http://localhost:8000/nursing/home en la barra de direcciones o agregarla a la barra de favoritos del navegador. 

### Manejo de aplicación

Para acceder a la aplicación es necesario iniciar sesión. En el caso de que un dispositivo sea utilizado por varias personas, solo una de ellas debe iniciar sesión; normalmente será la que esté a cargo del equipo de trabajo o líder, quien a su vez será responsable de las acciones declaradas durante esa sesión. 


Cuando se declara una acción (ocupar cama, programar tarea, etc.) se brinda la opción de declarar quién la realiza (o la realizó). Toda declaración se guarda en la base de datos identificando siempre dos roles: quien inició sesión y quien se declara como realizador de la acción (anónimo por defecto). Se implementó de esta manera para agilizar y flexibilizar el manejo de la aplicación. Entonces, dependiendo de la confianza en los miembros del equipo para manipular la aplicación y teniendo en cuenta que el responsable de lo que se ingrese en ese dispositivo es quien inició sesión, se puede optar por que cualquier miembro de dicho equipo pueda ingresar reportes identificándose a si mismo o a un tercero como realizador de una acción sin tener que ingresar constantemente contraseñas.

### Colores y sonidos

La aplicación fue concebida para que se pueda identificar fácil e inmediatamente su estado a través del uso de colores y sonidos. Se busca que el usuario, después de un periodo corto y sencillo de adaptación, logre percibir en todo momento y en forma automática la información que le brinda el sistema. Para ello se han escogido colores que frecuentemente se asocian a tipos de alertas y sonidos que, sin apabullar, logran captar la atención.

#### **Color de la cama:**

gris : desocupada

verde : ocupada, sin llamadas no contestadas ni tareas pendientes cuyo momento programado se haya cumplido. 

azul : tarea pendiente cuyo momento programado se ha cumplido.

rojo : con llamada todavía no contestada

violeta : tarea(s) pendiente(s) y llamada no contestada

#### **Haciendo click en la cama**


Abre la ventana para ver la información, ocupar, desocupar y editar datos de la cama, o programar una nueva tarea.

"Ocupar" cama: se abre el menú para ingresar datos del paciente así como momento de ocupación y desocupación. Si no se especifica alguno de estos momentos, toma por defecto el momento actual para ocupar y siete días a partir de el momento actual para desocupar.

#### **Tareas**

Las tareas generalmente pueden realizarse minutos antes o despúes del momento para el que fueron programadas. Para que el personal responsable de realizarlas tenga la opción de organizarse mejor, las tareas constan de tres momentos:

- "10 minutos previos al momento programado para la tarea": cambio de color en la tarea.
- "momento programado para la tarea": alerta sonora, cambio de color en la tarea y la cama.
- "momento en que efectivamente se realiza la tarea"  

"Nueva tarea": de manera predeterminada, el "momento programado para la tarea" figurará como para dentro de 30 minutos. Se puede cambiar esto en el cuadro de tiempo de programación.

Para una tarea que se repite periódicamente se debe tildar el checkbox "repetir" y elegir la frecuencia con que se repetirá. Por defecto las tareas se repetirán hasta el momento en que se espera desocupar la cama salvo que se indique hasta cuándo se repetirá la secuencia.

Todas las tareas aparecen en la lista en orden de ejecución. En las tareas que se repiten periódicamente, el ícono de la cama aparecerá dentro de un rectángulo. 

Cuando falten "10 minutos para la hora programada", el color de la tarea cambiará de *gris* a *azul claro* y la hora programada a *verde*.

Cuando se alcance el "momento programado para la tarea", el color de la tarea cambiará a *azul* y la hora a *rojo*, el color de la cama cambiará también a *azul* (si tiene una llamada pendiente, la cama estará en *rojo*, entonces cambiará a *violeta*) y se escuchará una advertencia audible por única vez.

Las tareas de la lista se pueden editar haciendo clicK en ellas. Si la tarea se repite, la edición no tendrá ningún efecto en las otras tareas. La única acción por lotes permitida es eliminar todas las tareas que comparten la recurrencia.

Si se hace click en la tarea y luego en "Editar", se puede observar el cuadro "Se Cumplió o Cumplirá". Esta es la marca para el "momento en que efectivamente se realizará la tarea" y es por defecto dos horas después del "momento programado para la tarea". Además se puede modificar para un momento todavía posterior.

Para declarar una tarea como "realizada", se supone que el hecho ya ha ocurrido, ergo, en el cuadro "Se Cumplió o Cumplirá" se colocará un momento pasado. Esto hará que al hacer click en "Guardar Edición", la tarea se elimine de la lista de tareas pendientes y se guarde en la base de datos como "Cumplida". También tiene la opción de marcarlo rápidamente con el botón "Recién Cumplida". Esto tendrá el mismo efecto sólo que se guardará con el momento actual. 

Si la tarea no se realizó ni se realizará y elige eliminarla, no se guardará en la base de datos. 


#### **Llamadas**

Cuando se presiona el botón de llamada desde una cama, el servidor envía una alerta sonora (que se repetirá cada 15 segundos hasta que se responda la llamada) y la llamada se agrega a la lista de llamadas. Las llamadas no respondidas aparecen en color *rojo* al igual que la cama. Si la cama tiene una tarea pendiente cuyo momento programado ya pasó, y por lo tanto está en *azul*, el color de la cama cambiará a *violeta*. Si hace click en la llamada puede ver información más detallada tanto sobre esta como sobre la cama que la originó.

Para que la llamada cambie a "respondida", la enfermera debe concurrir personalmente a presionar el botón en la habitación de donde proviene la llamada (generalmente hay un botón para cancelar llamadas por habitación).

Al presionar el botón cancelar, todas las llamadas de esa habitación se cambian a "respondidas".

El color de las llamadas respondidas cambia a *gris* y la cama vuelve a su color anterior (*gris*, o *azul* si tiene una tarea pendiente).

Al hacer click en una llamada respondida, puede ingresar el motivo de la llamada y la respuesta dada, así como quién la respondió. También puede ver a qué hora se realizó la llamada y a qué hora se respondió.

Cuando cierra la llamada, desaparece de la lista y se guarda en la base de datos.

> Por defecto se presenta la versión Dark. Para esto se modificó el "background-color" en el tag "body" del archivo "/nursing_react/src/bootstrap.css". Además tuvo que agregarse el atributo "color:rgb(182, 255, 179);" a la clase ".room-free" del archivo "/nursing_react/src/components/rooms-beds-sketch/rooms-beds/room/room.css"

#### **Tabla Record**

Ante cualquier acción aplicada a una cama, paciente, tarea o llamada, la tabla "record" guarda automáticamente el estado anterior a la acción y el estado posterior, incluyendo los datos del momento, quién realizó la acción, así como el usuario logueado (responsable) en ese momento.
Estos datos quedan como registro de acciones y sólo pueden ser accedidos y/o modificados por un superususario con acceso a modificaciones directas sobre la base de datos.
