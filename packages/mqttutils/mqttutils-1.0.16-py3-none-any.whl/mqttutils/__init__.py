import threading
import logging
import json
import queue
import hashlib
import sys
import time
import ssl

import paho.mqtt.client as mqtt
from abc import abstractmethod, ABC
from pydantic import BaseModel
from typing import Any, Callable

logger = logging.getLogger(__name__)

class Message(BaseModel):
    payload:Any = None
    message_id:int
    transmitter_id:str

class AbstractMessager(ABC):
    @abstractmethod
    def start():
        raise NotImplementedError()
    
    @abstractmethod
    def stop():
        raise NotImplementedError()
    
    @abstractmethod
    def publish_message(self, topic: str, payload: Any, timeout:int=5, on_publish:Callable|None=None, wait_for_response:bool=True):
        raise NotImplementedError()
    
    @abstractmethod
    def reply_to_message(self, payload:Any, original_message:Message)->None:
        raise NotImplementedError()

    @abstractmethod
    def subscribe(self, topic: str, callback: Callable|None = None):
        raise NotImplementedError()
    

class MQTTMessager(AbstractMessager):    
    def __init__(
        self,
        name:str, 
        mqtt_host:str,
        mqtt_port:int,
        transmitter_id:str, 
        enable_tls:bool=False, 
        username:str='username', 
        password:str='password',
        disable_ca_check:bool=False,
        ca_cert_location:str='./certs/ca-root-cert.crt'
    ):
        self.name = name
        self.mqtt_host = mqtt_host
        self.mqtt_port = mqtt_port
        self.transmitter_id = transmitter_id
        self.username = username
        self.password = password
        self.enable_tls = enable_tls
        self.disable_ca_check = disable_ca_check
        self.ca_cert_location = ca_cert_location

        self.message_id = 0        
        self.main_thread = None

        self.response_queue:dict[int, queue.Queue[Message]] = {}
        self.messages_info:dict[int, mqtt.MQTTMessageInfo] = {}
        self.topic_to_callback:dict[str, Callable] = {}

        self.subscriptions:list[tuple] = []


        self.connected = False       
        self.lock = threading.Lock()
        self._init_client()
        self.subscribe(f'msgbox/{self.transmitter_id}', self._on_receive_message)

    def start(self):
        def connect(self):
            while(not self.connected):
                try:
                    self._mqtt_client.connect(
                        self.mqtt_host,
                        self.mqtt_port
                    )
                    break
                except:
                    logger.exception(f"Could not establish connection with mqtt broker at {self.mqtt_host}:{self.mqtt_port}")
                    time.sleep(1)
            self._mqtt_client.loop_start()

        self._init_client()
        connection_loop_thread = threading.Thread(target=connect, args={self})
        connection_loop_thread.start()

    def stop(self):
        self._mqtt_client.disconnect()
        self._mqtt_client.loop_stop()

    def _init_client(self):
        self._mqtt_client = mqtt.Client()
        if self.enable_tls:
            logger.info('TLS is enabled on the mqqt client')
            if not self.disable_ca_check:
                self._mqtt_client.tls_set(ca_certs=self.ca_cert_location)
                self._mqtt_client.tls_insecure_set(False)
            else:
                self._mqtt_client.tls_set(cert_reqs=ssl.CERT_NONE)
                self._mqtt_client.tls_insecure_set(True)
        else:
            logger.warning('TLS is disabled on the mqqt client')
        self._mqtt_client.on_connect = self._on_connect
        self._mqtt_client.on_disconnect = self._on_disconnect
        self._mqtt_client.on_publish = self._on_publish
        self._mqtt_client.on_message = self._on_message
        self._mqtt_client.username_pw_set(
            self.username, 
            self.password
        )

    def _check_payload(self, payload:str)->tuple[int, str]:
        payload_size = sys.getsizeof(payload)
        payload_md5_hash = hashlib.md5(payload.encode('utf-8')).hexdigest()
        return payload_size, payload_md5_hash

    def _publish(self, topic:str, payload:str, qos:int=1)->mqtt.MQTTMessageInfo:
        payload_size, payload_md5_hash = self._check_payload(payload)
        logger.info(f'Sending payload of size {payload_size} bytes with MD5 hash: {payload_md5_hash}')
        return self._mqtt_client.publish(topic, payload, qos=qos)

    def publish(self, topic: str, payload: Any, on_publish:Callable|None=None):
        with self.lock:
            message_info = self._publish(topic, payload)
        if on_publish is not None:
            self.messages_info[message_info.mid] = on_publish

    def publish_message(self, topic: str, payload: Any, timeout:int=5, on_publish:Callable|None=None, wait_for_response=True)->Message:
        with self.lock:
            self.message_id += 1
            message_id = self.message_id
        if not wait_for_response:
            message_id = -1 #This is interpreted by the other side as an unsollicated message (i.e. not as the reply to an earlier message)
        payload = Message(
            payload=payload, 
            message_id=message_id, 
            transmitter_id=self.transmitter_id
        )
        self.response_queue[message_id] = queue.Queue(maxsize=1) #prepare blocking queue to wait for response
        with self.lock:
            message_info = self._publish(topic, payload=payload.model_dump_json(), qos=2)
        if on_publish is not None:
            self.messages_info[message_info.mid] = on_publish
        if not wait_for_response:
            return None
        try:
            response = self.response_queue[message_id].get(timeout=timeout)
        except queue.Empty:
            raise TimeoutError('No response was received within timeout')
        finally:
            del self.response_queue[message_id]
        return response

    def reply_to_message(self, payload:Any, original_message:Message)->None:
        message = Message(
            payload=payload, 
            message_id=original_message.message_id, 
            transmitter_id=self.transmitter_id
        )
        receiver = original_message.transmitter_id
        self._publish(f'msgbox/{receiver}', message.model_dump_json())

    def _on_receive_message(self, message:Message):
        if message.message_id == -1:
            logging.info(f'Unsollicated message from {message.transmitter_id}:{message.payload}')
            return 
        rq = self.response_queue.get(message.message_id, None)
        if rq is None:
            logger.error(f'Received a reply to message with id {message.message_id} but no response queue has been registrated')
            return 
        rq.put(message)

    def subscribe(self, topic: str, callback: Callable, qos=2):
        logger.info(f"Subscribing to topic {topic}")
        self.subscriptions.append((topic, qos)) 
        self.topic_to_callback[topic] = callback
        if self.connected:
            logger.info(f'Activating subscriptions for topic: {topic}')
            self._mqtt_client.subscribe(topic, qos)

    def _on_connect(self, client, userdata, flags, rc):
        self.connected = True
        logger.info(f'Successfully connected to opra2opra mqtt broker ({self.mqtt_host}:{self.mqtt_port})')
        self._renew_subscriptions()

    def _renew_subscriptions(self):
        for topic, qos in self.subscriptions:
            logger.info(f'Activating subscriptions for topic: {topic}')
            self._mqtt_client.subscribe(topic, qos)

    def _on_disconnect(self, client, userdata, rc):
        self.connected = False
        logger.error('Connection to opra2opra mqtt broker lost')

    def _on_publish(self, mqttc, userdata, mid):
        logger.info(f"Successfully published message with 'mid' id {mid} to mqtt broker")
        try:
            f = self.messages_info.pop(mid)
        except KeyError:
            logger.info(f'No on_publish callback registered for the message with id {mid}')
            return
        f()

    def _on_message(self, client, userdata, message: mqtt.MQTTMessage):
        logger.info(f'Message received on topic {message.topic}')
        try:
            callback = self.topic_to_callback[message.topic]
        except KeyError:
            logger.error(f'Received a message on topic {message.topic} but no callback was registered.')
            return
        def target():
            try:
                payload = message.payload.decode('utf-8')
                payload_size, payload_md5_hash = self._check_payload(payload)
                logger.info(f'Received payload of size {payload_size} bytes with MD5 hash: {payload_md5_hash}')
                m = Message(**json.loads(message.payload))
            except:
                logger.error('Failed to deserialize message')
                return 
            callback(m)
        t = threading.Thread(target=target)
        t.start()