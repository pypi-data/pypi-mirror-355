from aia_utils.logs_cfg import config_logger
import paho.mqtt.client as paho
from dotenv import load_dotenv
import os
from aia_utils.toml_utils import aia_utils_version
__version__ = aia_utils_version()
import logging
load_dotenv()


# Clase base para MqttClient que contiene la lógica compartida
class MqttClient:
    def __init__(self, topic: str, client_id: str):
        config_logger()
        self.logger = logging.getLogger(__name__)
        self.host = os.environ['MQTT_HOST']
        self.port = int(os.environ['MQTT_PORT'])  # Convertir a entero
        self.username = os.environ['MQTT_USERNAME']
        self.password = os.environ['MQTT_PASSWORD']
        self.client_id = client_id
        self.topic = topic
        self.client = paho.Client(paho.CallbackAPIVersion.VERSION2, client_id=client_id, clean_session=True, userdata=None, protocol=paho.MQTTv31)
        #self.client = paho.Client(client_id=client_id, userdata=None, protocol=paho.MQTTv5)
        #self.client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)

        # Establecer credenciales de usuario
        self.client.username_pw_set(self.username, self.password)


    def on_connect(self, client, userdata, flags, rc):
        """Callback cuando se establece la conexión."""
        if rc == 0:
            self.logger.info(f"Connected to MQTT broker with client ID: {self.client_id}")
        else:
            self.logger.error(f"Connection failed with code {rc}")

    def on_message(self, client, userdata, message):
        """Callback para manejar mensajes entrantes. Este método es sobreescrito por MqttConsumer."""
        self.logger.debug(f"Received message: {message.payload.decode()} on topic {message.topic}")
        # Aquí solo ejecutará las funciones de callback en el consumidor.


# Clase específica para el productor
class MqttProducer(MqttClient):
    def __init__(self, topic: str, client_id: str):
        super().__init__(topic, client_id)
        # Conectar al servidor MQTT
        self.client.connect(self.host, keepalive=60, bind_address="")
        #self.client.connect("14b5793c334743769b3e9fb1e4008401.s2.eu.hivemq.cloud", 8883)
        self.client.loop_start()
        self.logger.info(f"MQTT ProducerClient Ready v{__version__}")

    def send_message(self, message: str):
        """Función para enviar un mensaje al topic."""
        msg_info = self.client.publish(self.topic, message, qos=1)
        msg_info.wait_for_publish()
        self.logger.debug(f"Message sent: {message}")

class MqttConsumer():

    def on_subscribe(self, client, userdata, mid, reason_code_list, properties):
        # Since we subscribed only for a single channel, reason_code_list contains
        # a single entry
        if reason_code_list[0].is_failure:
            self.logger.error(f"Broker rejected you subscription: {reason_code_list[0]}")
        else:
            self.logger.info(f"Broker granted the following QoS: {reason_code_list[0].value} in topic {self.topic}")

    def on_unsubscribe(self, client, userdata, mid, reason_code_list, properties):
        # Be careful, the reason_code_list is only present in MQTTv5.
        # In MQTTv3 it will always be empty
        if len(reason_code_list) == 0 or not reason_code_list[0].is_failure:
            self.logger.info("unsubscribe succeeded (if SUBACK is received in MQTTv3 it success)")
        else:
            self.logger.error(f"Broker replied with failure: {reason_code_list[0]}")
        client.disconnect()

    def on_message(self, client, userdata, message):
        # userdata is the structure we choose to provide, here it's a list()
        userdata.append(message.payload)
        msg_txt = message.payload.decode()
        self.logger.debug(f"Received message: {msg_txt} from topic: {message.topic}")
        
        # We only want to process 10 messages
        #if len(userdata) >= 2:
        #    client.unsubscribe(self.topic)
        
        for callback in self.callbacks:
            try:
                callback(msg_txt)  # Pasar el mensaje decodificado a las callbacks
            except Exception as e:
                self.logger.error(f"Error executing callback {callback.__name__}: {e}")

    def on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code.is_failure:
            self.logger.error(f"Failed to connect: {reason_code}. loop_forever() will retry connection")
        else:
            # we should always subscribe from on_connect callback to be sure
            # our subscribed is persisted across reconnections.
            client.subscribe(self.topic)


    def __init__(self, topic: str, client_id: str, callbacks=[]):
        self.topic = topic
        config_logger()
        # Lista interna de callbacks (para el consumidor)
        self.callbacks = callbacks
        self.logger = logging.getLogger(__name__)
        self.host = os.environ['MQTT_HOST']
        self.port = int(os.environ['MQTT_PORT'])  # Convertir a entero
        self.username = os.environ['MQTT_USERNAME']
        self.password = os.environ['MQTT_PASSWORD']
        self.client_id = client_id
        self.topic = topic
        mqttc = paho.Client(paho.CallbackAPIVersion.VERSION2)
        mqttc.username_pw_set(self.username, self.password)
        mqttc.on_connect = self.on_connect
        mqttc.on_message = self.on_message
        mqttc.on_subscribe = self.on_subscribe
        mqttc.on_unsubscribe = self.on_unsubscribe

        mqttc.user_data_set([])
        mqttc.connect(self.host)
        self.logger.info(f"MQTT ConsumerClient Ready v{__version__}")
        mqttc.loop_forever()

