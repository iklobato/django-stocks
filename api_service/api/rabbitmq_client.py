import json
import uuid
import pika
import threading
import logging
from json_tricks import dumps, loads
from django.conf import settings

logger = logging.getLogger(__name__)

class RabbitMQClient:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.callback_queue = None
        self.response = None
        self.corr_id = None
        self.host = getattr(settings, 'RABBITMQ_HOST', 'localhost')
        self.port = getattr(settings, 'RABBITMQ_PORT', 5672)
        self.user = getattr(settings, 'RABBITMQ_USER', 'guest') 
        self.password = getattr(settings, 'RABBITMQ_PASSWORD', 'guest')
        self.connect()
        
    def connect(self):
        try:
            credentials = pika.PlainCredentials(self.user, self.password)
            parameters = pika.ConnectionParameters(
                host=self.host,
                port=self.port,
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300
            )
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
            result = self.channel.queue_declare(queue='', exclusive=True)
            self.callback_queue = result.method.queue
            
            self.channel.basic_consume(
                queue=self.callback_queue,
                on_message_callback=self.on_response,
                auto_ack=True
            )
            
            logger.info(f"Connected to RabbitMQ at {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Error connecting to RabbitMQ: {str(e)}")
            return False
    
    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = body
    
    def call(self, queue_name, request_data, timeout=10):
        if not self.connection or self.connection.is_closed:
            if not self.connect():
                logger.error("Failed to connect to RabbitMQ")
                return None
        
        self.response = None
        self.corr_id = str(uuid.uuid4())
        
        try:
            self.channel.queue_declare(queue=queue_name, durable=True)
            
            self.channel.basic_publish(
                exchange='',
                routing_key=queue_name,
                properties=pika.BasicProperties(
                    reply_to=self.callback_queue,
                    correlation_id=self.corr_id,
                ),
                body=dumps(request_data)
            )
            
            start_time = self.connection.time
            while self.response is None:
                self.connection.process_data_events()
                if (self.connection.time - start_time) > timeout:
                    logger.warning(f"Request to {queue_name} timed out after {timeout} seconds")
                    return None
            
            try:
                return loads(self.response)
            except Exception as e:
                logger.error(f"Error parsing response: {str(e)}")
                return None
                
        except Exception as e:
            logger.error(f"Error making RPC call to {queue_name}: {str(e)}")
            self.connect()
            return None
    
    def close(self):
        if self.connection and not self.connection.is_closed:
            self.connection.close()

_client = None
_lock = threading.Lock()

def get_client():
    global _client
    with _lock:
        if _client is None:
            _client = RabbitMQClient()
        return _client