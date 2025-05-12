import pika
import threading
import json
import logging
import time
from json_tricks import dumps, loads
from django.conf import settings

logger = logging.getLogger(__name__)

class RabbitMQServer:
    """
    Server for RabbitMQ communication using RPC pattern
    (Remote Procedure Call)
    """
    def __init__(self, callback_func):
        """
        Initialize the server
        
        Args:
            callback_func: The function to call when a message is received.
                           It should take a message body as input and return a response.
        """
        self.callback_func = callback_func
        self.host = getattr(settings, 'RABBITMQ_HOST', 'localhost')
        self.port = getattr(settings, 'RABBITMQ_PORT', 5672)
        self.user = getattr(settings, 'RABBITMQ_USER', 'guest') 
        self.password = getattr(settings, 'RABBITMQ_PASSWORD', 'guest')
        self.queue_name = getattr(settings, 'RABBITMQ_STOCK_QUEUE', 'stock_queue')
        self.connection = None
        self.channel = None
        self.is_running = False
        self._thread = None
    
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
            
            # Declare the queue for receiving requests
            self.channel.queue_declare(queue=self.queue_name, durable=True)
            
            # Set quality of service (prefetch count)
            self.channel.basic_qos(prefetch_count=1)
            
            # Register consumer
            self.channel.basic_consume(
                queue=self.queue_name,
                on_message_callback=self.on_request,
                auto_ack=False
            )
            
            logger.info(f"Connected to RabbitMQ at {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Error connecting to RabbitMQ: {str(e)}")
            return False
    
    def on_request(self, ch, method, props, body):
        """Handle incoming requests"""
        try:
            # Parse the request
            request_data = loads(body)
            logger.info(f"Received request: {request_data}")
            
            # Process the request
            response_data = self.callback_func(request_data)
            
            # Send the response
            ch.basic_publish(
                exchange='',
                routing_key=props.reply_to,
                properties=pika.BasicProperties(
                    correlation_id=props.correlation_id
                ),
                body=dumps(response_data)
            )
            
            # Acknowledge the message
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            # Still acknowledge the message to avoid leaving it in the queue
            ch.basic_ack(delivery_tag=method.delivery_tag)
            # Try to send an error response
            try:
                error_response = {"error": str(e), "status": 500}
                ch.basic_publish(
                    exchange='',
                    routing_key=props.reply_to,
                    properties=pika.BasicProperties(
                        correlation_id=props.correlation_id
                    ),
                    body=dumps(error_response)
                )
            except:
                # If sending the error response fails, just log it
                logger.error("Failed to send error response")
    
    def run(self):
        """Run the server and start consuming messages"""
        if self.is_running:
            logger.warning("Server is already running")
            return
        
        if not self.connect():
            logger.error("Failed to connect to RabbitMQ")
            return
        
        logger.info(f"Starting to consume from queue: {self.queue_name}")
        self.is_running = True
        
        try:
            # Start consuming
            self.channel.start_consuming()
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received, stopping server")
            self.stop()
        except Exception as e:
            logger.error(f"Error in consumer: {str(e)}")
            self.is_running = False
            # Try to reconnect
            if not self.connect():
                logger.error("Failed to reconnect")
            else:
                # Restart consuming
                self.is_running = True
                self.channel.start_consuming()
    
    def run_in_thread(self):
        """Run the server in a separate thread"""
        if self._thread is not None and self._thread.is_alive():
            logger.warning("Server thread is already running")
            return
        
        logger.info("Starting RabbitMQ server in a thread")
        self._thread = threading.Thread(target=self.run)
        self._thread.daemon = True  # Thread will exit when main thread exits
        self._thread.start()
    
    def stop(self):
        """Stop the server"""
        logger.info("Stopping RabbitMQ server")
        if self.is_running:
            self.is_running = False
            if self.channel:
                try:
                    self.channel.stop_consuming()
                except:
                    pass
            if self.connection and not self.connection.is_closed:
                try:
                    self.connection.close()
                except:
                    pass


# Global server instance
_server = None
_lock = threading.Lock()

def start_rabbitmq_server(callback_func):
    """Start the RabbitMQ server with the given callback function"""
    global _server
    with _lock:
        if _server is None:
            _server = RabbitMQServer(callback_func)
            
        if not _server.is_running:
            _server.run_in_thread()
            # Wait a bit to make sure the server starts
            time.sleep(1)
        
        return _server.is_running