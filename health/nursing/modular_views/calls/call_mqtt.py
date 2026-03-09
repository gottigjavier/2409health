import paho.mqtt.client as mqtt
import json
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .call_new import new_call
from ..app.app_ws_update import ws_load


def mqtt_service():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("mqtt_service --> connected to MQTT Broker!")
            client.subscribe("mqtt/call/")
            print("mqtt_service --> subscribed to mqtt/call/")
        else:
            print("mqtt_service --> bad connection. Code: ", rc)

    def on_message(client, userdata, message):
        msg = message.payload
        try:
            data = json.loads(msg)
            # no need to send status // without "," -> answer call
            if ",0" not in data["bed"]:
                data["state"] = True
            else:
                data["state"] = False
            if data["key"] == "this&is$a$key&to?prevent?hacking":
                if data["state"]:
                    key = data["key"]
                    state = data["state"]
                    bed = data["bed"]
                    n_call = new_call(bed)
                    call = {"key": key, "state": state, "bed": bed, "call": n_call}
                else:
                    key = data["key"]
                    state = data["state"]
                    bed = data["bed"]
                    ans_call = ws_load()
                    call = {"key": key, "state": state, "bed": bed, "call": ans_call}
                layer = get_channel_layer()
                async_to_sync(layer.group_send)(
                    "callsboard",
                    {
                        "type": "deprocessing",
                        "call": call,
                    },
                )
            else:
                print("Clave incorrecta. Cuidado!!! Posible hacking!!")
        except Exception:
            print("Desde views: El dato tiene formato incorrecto")

    try:
        client = mqtt.Client()
        client.on_connect = on_connect
        client.on_message = on_message
        # Corriendo la app en 'localhost' o '0.0.0.0' la IP debe ser una de estas dos.

        # Corriendo la app en Docker, colocar una IP como 192.168.0.xx y
        # observar en el mensaje de error en qué puerto está escuchando mosquitto.
        # En este caso es 10.10.8.1 (voilà). Entonces:

        # Para localhost
        # client.connect("0.0.0.0", 1883)

        # Para Docker - usar el hostname del contenedor
        client.connect("mosquitto", 1883)

        client.loop_start()
        # client.loop_forever()
    except Exception:
        print("no mqtt broker found")
