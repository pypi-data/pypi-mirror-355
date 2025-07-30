#!/usr/bin/env python3
# coding: utf8

from dotenv import load_dotenv
import sys
import os
from confluent_kafka import Consumer, KafkaException, KafkaError, Producer
import json
import time
from datetime import datetime
from aia_utils.logs_cfg import config_logger
import logging
load_dotenv()
import traceback
#import pkg_resources
#__version__ = pkg_resources.get_distribution('aia-utils').version
from aia_utils.toml_utils import aia_utils_version
__version__ = aia_utils_version()

class QueueConsumer:
    
    def __init__(self, topic, clientId = "aiaClient"):
        config_logger()
        self.logger = logging.getLogger(__name__)
        self.topic = topic
        if "CLOUDKAFKA_ANONIMOUS_ACCESS" in os.environ and os.environ['CLOUDKAFKA_ANONIMOUS_ACCESS'] == 'True':
            self.conf = {
                'client.id': clientId,
                'bootstrap.servers': os.environ['CLOUDKARAFKA_BROKERS'],
                'group.id': "%s-consumer-%s" % (os.environ['CLOUDKARAFKA_USERNAME'], topic),
                'auto.offset.reset': 'earliest'
            }
        else:
            self.conf = {
                'client.id': clientId,            
                'bootstrap.servers': os.environ['CLOUDKARAFKA_BROKERS'],
                'group.id': "%s-consumer-%s" % (os.environ['CLOUDKARAFKA_USERNAME'], topic),
                'auto.offset.reset': 'earliest',        
                'session.timeout.ms': 6000,
                'default.topic.config': {'auto.offset.reset': 'smallest'},
                'security.protocol': 'SASL_SSL',
                'sasl.mechanisms': 'SCRAM-SHA-512',
                'sasl.username': os.environ['CLOUDKARAFKA_USERNAME'],
                'sasl.password': os.environ['CLOUDKARAFKA_PASSWORD']            
            }
        self.consumer = Consumer(**self.conf)
        self.logger.info("Topic Consumer = " + topic)
        self.consumer.subscribe([topic])

    def validateJSON(self, jsonData):
        try:
            json.loads(jsonData)
        except ValueError as err:
            self.logger.error(err)
            traceback.print_exc()
            return False
        return True

    def listen(self, callback_queue = None, validate_JSON = True):
        self.logger.info(f"Listener Queue Ready v{__version__}")
        try:
            while True:
                msg = self.consumer.poll(timeout=1.0)
                if msg is None:
                    continue
                if msg.error():
                    # Error or event
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        # End of partition event
                        sys.stderr.write('%% %s [%d] reached end at offset %d\n' %
                                        (msg.topic(), msg.partition(), msg.offset()))
                    elif msg.error():
                        # Error
                        raise KafkaException(msg.error())
                else:
                    if validate_JSON:
                        self.logger.debug("Validating JSON")
                        # Proper message
                        #sys.stderr.write('%% %s [%d] at offset %d with key %s:\n' %
                        #                (msg.topic(), msg.partition(), msg.offset(),
                        #                str(msg.key())))
                        msgValue = msg.value().decode('utf-8').replace("'", '"')
                        self.logger.debug(msgValue)
                        if self.validateJSON(msgValue):
                            res = json.loads(msgValue)
                            callback_queue(res)
                        else:
                            self.logger.warning("[WARN] Not JS Valid")
                    else:
                        callback_queue(msg.value())
                    
        except Exception as e:
            self.logger.error('Error en recibir mensaje')
            self.logger.error(e)
            traceback.print_exc()

class QueueProducer:
    def __init__(self, topic, version = None, project_name = "unknown"):
        config_logger()
        self.logger = logging.getLogger(__name__)  
        self.version = version
        self.topic = topic
        if "CLOUDKAFKA_ANONIMOUS_ACCESS" in os.environ and os.environ['CLOUDKAFKA_ANONIMOUS_ACCESS'] == 'True':
            self.conf = {
                'bootstrap.servers': os.environ['CLOUDKARAFKA_BROKERS']
            }
        else:
            self.conf = {
                'bootstrap.servers': os.environ['CLOUDKARAFKA_BROKERS'],
                'security.protocol': 'SASL_SSL',
                'sasl.mechanisms': 'SCRAM-SHA-512',
                'sasl.username': os.environ['CLOUDKARAFKA_USERNAME'],
                'sasl.password': os.environ['CLOUDKARAFKA_PASSWORD']            
            }
        self.project_name = project_name
        self.producer = Producer(**self.conf)
        self.logger.info(f"Topic [{topic}] QueProducer v{__version__}")      

    def msgBuilder(self, bodyObject):
        now = datetime.now()
        objMessage = {
            "head": {
                "producer": self.project_name,
                "creationDate": now.strftime("%Y-%m-%d %H:%M:%S"),
                "version": self.version
            }, 
            "body": bodyObject,
            "breadcrumb": [{
                "creationDate": now.strftime("%Y-%m-%d %H:%M:%S"),
                "name": self.project_name
            }],
            "status": {
                "creationDate": now.strftime("%Y-%m-%d %H:%M:%S"),
                "code": "SEND",
                "description": "AIA new message arrived"
            }
        }
        return objMessage

    # Define a custom function to serialize datetime objects 
    def serialize_datetime(self, obj): 
        if isinstance(obj, datetime): 
            return obj.isoformat() 
        raise TypeError("Type not serializable") 

    def sendMsg(self, bodyObject, callback_queue = None):
        objStr = self.msgBuilder(bodyObject)
        self.send(objStr, callback_queue)

    def produce(self, msg_str, callback_queue = None):
        self.producer.produce(self.topic, msg_str, callback=callback_queue)
        self.producer.poll(0)

    def send(self, msg, callback_queue = None):
        msg_str = json.dumps(msg, default=self.serialize_datetime)
        self.produce(msg_str, callback_queue)
    
    def flush(self):
        self.producer.flush()