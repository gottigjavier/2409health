#!/usr/bin/env python3
"""
Script de Simulación de Llamadas MQTT
Simula la recepción de llamadas desde habitaciones/camas usando MQTT real
"""

import paho.mqtt.client as mqtt
import json
import time
from datetime import datetime

MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "mqtt/call/"
MQTT_KEY = "this&is$a$key&to?prevent?hacking"


class MQTTSimulator:
    def __init__(self):
        self.mqtt_broker = MQTT_BROKER
        self.mqtt_port = MQTT_PORT
        self.mqtt_topic = MQTT_TOPIC
        self.client = None

    def connect_mqtt(self):
        """Conecta al broker MQTT"""
        try:
            self.client = mqtt.Client()
            self.client.connect(self.mqtt_broker, self.mqtt_port, keepalive=60)
            print(f"✓ Connected to MQTT broker at {self.mqtt_broker}:{self.mqtt_port}")
            return True
        except Exception as e:
            print(f"✗ Failed to connect to MQTT broker: {str(e)}")
            return False

    def simulate_call(self, room_id, bed_id, message="Simulated MQTT Call"):
        """
        Simula una llamada desde una habitación/cama
        Formato: {'state': true, 'id': 'room,bed', 'key': 'clave-anti-hacking'}
        """
        try:
            # Format: room,bed (e.g., "1,2")
            call_id = f"{room_id},{bed_id}"

            print(f"\n{'=' * 60}")
            print(f"Simulating Call from Room {room_id}, Bed {bed_id}")
            print(f"{'=' * 60}")

            # Crear mensaje MQTT
            mqtt_message = {"state": True, "id": call_id, "key": MQTT_KEY}

            # Publicar en MQTT
            result = self.client.publish(
                self.mqtt_topic, json.dumps(mqtt_message), qos=1
            )

            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"✓ Call simulation sent successfully via MQTT")
                print(f"  Topic: {self.mqtt_topic}")
                print(f"  Payload: {json.dumps(mqtt_message, indent=2)}")
                print(f"  Message: {message}")
            else:
                print(f"✗ Failed to publish MQTT message (Code: {result.rc})")
        except Exception as e:
            print(f"✗ Error simulating call: {str(e)}")

    def simulate_cancel_call(self, room_id, message="Simulated MQTT Cancel"):
        """
        Simula cancelación de llamadas desde una habitación
        Formato: {'state': false, 'id': 'room,0', 'key': 'clave'}
        """
        try:
            cancel_id = f"{room_id},0"

            print(f"\n{'=' * 60}")
            print(f"Simulating Call Cancellation from Room {room_id}")
            print(f"{'=' * 60}")

            # Crear mensaje MQTT de cancelación
            mqtt_message = {"state": False, "id": cancel_id, "key": MQTT_KEY}

            # Publicar en MQTT
            result = self.client.publish(
                self.mqtt_topic, json.dumps(mqtt_message), qos=1
            )

            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"✓ Cancellation sent successfully via MQTT")
                print(f"  Topic: {self.mqtt_topic}")
                print(f"  Payload: {json.dumps(mqtt_message, indent=2)}")
                print(f"  Message: {message}")
            else:
                print(f"✗ Failed to publish MQTT cancellation (Code: {result.rc})")
        except Exception as e:
            print(f"✗ Error sending cancellation: {str(e)}")

    def run_simulation_scenario(self):
        """
        Ejecuta un escenario de simulación completo
        """
        print("\n" + "=" * 60)
        print("🏥 MQTT CALL SIMULATION SCENARIO")
        print("=" * 60)
        print(f"Timestamp: {datetime.now().isoformat()}")
        print(f"MQTT Broker: {self.mqtt_broker}:{self.mqtt_port}")
        print(f"MQTT Topic: {self.mqtt_topic}")

        # Conectar a MQTT
        if not self.connect_mqtt():
            return

        try:
            # Escenario 1: Llamada simple desde habitación 1, cama 2
            print("\n\n[SCENARIO 1] Single Call from Room 1, Bed 2")
            self.simulate_call(room_id=1, bed_id=2)
            time.sleep(2)

            # Escenario 2: Otra llamada desde diferente cama
            print("\n\n[SCENARIO 2] Another Call from Room 1, Bed 3")
            self.simulate_call(room_id=1, bed_id=3)
            time.sleep(2)

            # Escenario 3: Cancelar todas las llamadas de la habitación
            print("\n\n[SCENARIO 3] Cancel All Calls in Room 1")
            self.simulate_cancel_call(room_id=1)
            time.sleep(2)

            # Escenario 4: Multiple calls in sequence
            print("\n\n[SCENARIO 4] Rapid Calls Sequence")
            for bed in [1, 2, 3]:
                print(f"\nCall {bed}/3...")
                self.simulate_call(room_id=2, bed_id=bed)
                time.sleep(1)

            # Escenario 5: Final cleanup
            print("\n\n[SCENARIO 5] Cleanup - Cancel All")
            self.simulate_cancel_call(room_id=2)

            print("\n\n" + "=" * 60)
            print("✓ SIMULATION COMPLETE")
            print("=" * 60)

        finally:
            # Desconectar
            self.client.disconnect()
            print(f"\n✓ Disconnected from MQTT broker")


if __name__ == "__main__":
    simulator = MQTTSimulator()
    simulator.run_simulation_scenario()
