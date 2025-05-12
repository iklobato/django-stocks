import json
import uuid
import pika
import time
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
        self.host = getattr(settings, 'RABBITMQ_HOST', 'localhost')
        self.port = getattr(settings, 'RABBITMQ_PORT', 5672)
        self.user = getattr(settings, 'RABBITMQ_USER', 'guest') 
        self.password = getattr(settings, 'RABBITMQ_PASSWORD', 'guest')
        self._lock = threading.Lock()  # Instance lock for thread safety
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
        # Store the response in the response dict using correlation ID as key
        with self._lock:
            if hasattr(self, '_responses') and props.correlation_id in self._responses:
                self._responses[props.correlation_id] = body
    
    def call(self, queue_name, request_data, timeout=10):
        # Use a lock to ensure thread safety
        with self._lock:
            if not self.connection or self.connection.is_closed:
                if not self.connect():
                    logger.error("Failed to connect to RabbitMQ")
                    return None
            
            # Create new response storage for this request
            if not hasattr(self, '_responses'):
                self._responses = {}
            
            # Generate a unique correlation ID for this request
            corr_id = str(uuid.uuid4())
            self._responses[corr_id] = None
            
            try:
                self.channel.queue_declare(queue=queue_name, durable=True)
                
                self.channel.basic_publish(
                    exchange='',
                    routing_key=queue_name,
                    properties=pika.BasicProperties(
                        reply_to=self.callback_queue,
                        correlation_id=corr_id,
                    ),
                    body=dumps(request_data)
                )
                
                # Use standard library time instead of connection.time
                start_time = time.time()
                
                # Wait for the response with timeout
                while self._responses[corr_id] is None:
                    # Process events to receive the response
                    self.connection.process_data_events()
                    
                    # Check for timeout
                    if (time.time() - start_time) > timeout:
                        logger.warning(f"Request to {queue_name} timed out after {timeout} seconds")
                        del self._responses[corr_id]  # Clean up
                        return None
                
                # Get the response and clean up
                response = self._responses[corr_id]
                del self._responses[corr_id]
                
                try:
                    return loads(response)
                except Exception as e:
                    logger.error(f"Error parsing response: {str(e)}")
                    return None
                    
            except Exception as e:
                logger.error(f"Error making RPC call to {queue_name}: {str(e)}")
                # Clean up and try to reconnect
                if corr_id in self._responses:
                    del self._responses[corr_id]
                self.connect()
                return None
    
    def close(self):
        if self.connection and not self.connection.is_closed:
            self.connection.close()

# Thread-local storage to ensure one client per thread
_thread_local = threading.local()
_lock = threading.Lock()

def get_client():
    # Check if client exists in thread-local storage
    if not hasattr(_thread_local, 'client'):
        with _lock:
            # Create a new client for this thread
            _thread_local.client = RabbitMQClient()
    
    # Return the thread's client
    return _thread_local.client