import json
import uuid
import pika
import threading
import logging
from json_tricks import dumps, loads
from django.conf import settings

logger = logging.getLogger(__name__)

class RabbitMQClient:
    """
    Client for RabbitMQ communication using RPC pattern
    (Remote Procedure Call)
    """
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
        """Establish connection to RabbitMQ server"""
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
            
            # Declare the callback queue for receiving responses
            result = self.channel.queue_declare(queue='', exclusive=True)
            self.callback_queue = result.method.queue
            
            # Set up consumption on the callback queue
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
        """Callback when a response is received"""
        if self.corr_id == props.correlation_id:
            self.response = body
    
    def call(self, queue_name, request_data, timeout=10):
        """
        Send a request to the specified queue and wait for a response
        
        Args:
            queue_name: The name of the queue to send the request to
            request_data: The data to send (will be serialized to JSON)
            timeout: How long to wait for a response (in seconds)
            
        Returns:
            The response data or None if timed out or error occurred
        """
        if not self.connection or self.connection.is_closed:
            if not self.connect():
                logger.error("Failed to connect to RabbitMQ")
                return None
        
        # Generate a unique correlation ID for this request
        self.response = None
        self.corr_id = str(uuid.uuid4())
        
        try:
            # Make sure the queue exists
            self.channel.queue_declare(queue=queue_name, durable=True)
            
            # Send the request
            self.channel.basic_publish(
                exchange='',
                routing_key=queue_name,
                properties=pika.BasicProperties(
                    reply_to=self.callback_queue,
                    correlation_id=self.corr_id,
                ),
                body=dumps(request_data)  # Use json_tricks for better serialization
            )
            
            # Wait for the response with timeout
            start_time = self.connection.time
            while self.response is None:
                self.connection.process_data_events()
                if (self.connection.time - start_time) > timeout:
                    logger.warning(f"Request to {queue_name} timed out after {timeout} seconds")
                    return None
            
            # Parse and return the response
            try:
                return loads(self.response)
            except Exception as e:
                logger.error(f"Error parsing response: {str(e)}")
                return None
                
        except Exception as e:
            logger.error(f"Error making RPC call to {queue_name}: {str(e)}")
            # Try to reconnect for next time
            self.connect()
            return None
    
    def close(self):
        """Close the connection"""
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            

# Singleton instance
_client = None
_lock = threading.Lock()

def get_client():
    """Get the singleton RabbitMQ client instance"""
    global _client
    with _lock:
        if _client is None:
            _client = RabbitMQClient()
        return _client