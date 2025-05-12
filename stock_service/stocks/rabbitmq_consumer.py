import pika
import json
import logging
import threading
import time
from json_tricks import dumps, loads
from django.conf import settings
import requests
import csv
import io

logger = logging.getLogger(__name__)

class RabbitMQConsumer:
    """
    Consumer for RabbitMQ that listens for stock requests and processes them
    """
    def __init__(self):
        """Initialize the consumer"""
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
        """Handle incoming stock requests"""
        try:
            # Parse the request
            request_data = loads(body)
            logger.info(f"Received stock request: {request_data}")
            
            # Extract the stock code
            stock_code = (request_data.get('stock_code') or 
                         request_data.get('symbol') or 
                         request_data.get('q'))
            
            if not stock_code:
                error_response = {
                    "error": "Stock code is required (use 'stock_code', 'symbol', or 'q' parameter)",
                    "status": 400
                }
                self.send_response(ch, props, error_response)
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return
            
            # Process the stock request
            try:
                # Make request to the stooq.com API
                url = f"https://stooq.com/q/l/?s={stock_code}&f=sd2t2ohlcvn&h&e=csv"
                logger.info(f"Making request to: {url}")
                response = requests.get(url)
                response.raise_for_status()
                
                # Parse CSV data
                content = response.content.decode('utf-8')
                logger.debug(f"CSV Content: {content[:200]}...")  # Log first 200 chars
                
                csv_reader = csv.reader(io.StringIO(content))
                header = next(csv_reader)
                try:
                    data = next(csv_reader)
                except StopIteration:
                    error_response = {
                        "error": "Invalid data received from stock API. Empty result.",
                        "status": 500
                    }
                    self.send_response(ch, props, error_response)
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                    return
                
                # Create a dictionary from the CSV data
                stock_data = dict(zip(header, data))
                logger.info(f"Parsed stock data: {stock_data}")
                
                # Check for N/A values in the data
                if stock_data.get('Open') == 'N/A' or stock_data.get('Close') == 'N/A':
                    error_response = {
                        "error": "No data available for this stock code",
                        "status": 404
                    }
                    self.send_response(ch, props, error_response)
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                    return
                
                # Format the response
                try:
                    result = {
                        "symbol": stock_data.get('Symbol', '').upper(),
                        "name": stock_data.get('Name', '').upper() or stock_data.get('Symbol', '').upper(),
                        "open": float(stock_data.get('Open', 0)),
                        "high": float(stock_data.get('High', 0)),
                        "low": float(stock_data.get('Low', 0)),
                        "close": float(stock_data.get('Close', 0)),
                        "volume": int(stock_data.get('Volume', 0))
                    }
                    # Send the successful response
                    self.send_response(ch, props, result)
                except ValueError as e:
                    logger.error(f"Error converting values: {e}")
                    error_response = {
                        "error": f"Error converting data values: {str(e)}",
                        "status": 500
                    }
                    self.send_response(ch, props, error_response)
            except requests.RequestException as e:
                logger.error(f"Request error: {e}")
                error_response = {
                    "error": f"Failed to fetch stock data: {str(e)}",
                    "status": 500
                }
                self.send_response(ch, props, error_response)
            except (ValueError, TypeError, IndexError) as e:
                logger.error(f"Data processing error: {e}")
                error_response = {
                    "error": f"Error processing stock data: {str(e)}",
                    "status": 500
                }
                self.send_response(ch, props, error_response)
            
            # Acknowledge the message
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            # Still acknowledge the message to avoid leaving it in the queue
            ch.basic_ack(delivery_tag=method.delivery_tag)
            # Try to send an error response
            try:
                error_response = {"error": str(e), "status": 500}
                self.send_response(ch, props, error_response)
            except:
                # If sending the error response fails, just log it
                logger.error("Failed to send error response")
    
    def send_response(self, ch, props, response_data):
        """Send a response back to the requester"""
        if props.reply_to:
            ch.basic_publish(
                exchange='',
                routing_key=props.reply_to,
                properties=pika.BasicProperties(
                    correlation_id=props.correlation_id
                ),
                body=dumps(response_data)
            )
            logger.info(f"Sent response for correlation ID: {props.correlation_id}")
        else:
            logger.warning("No reply_to queue specified, cannot send response")
    
    def run(self):
        """Run the consumer and start consuming messages"""
        if self.is_running:
            logger.warning("Consumer is already running")
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
            logger.info("Keyboard interrupt received, stopping consumer")
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
        """Run the consumer in a separate thread"""
        if self._thread is not None and self._thread.is_alive():
            logger.warning("Consumer thread is already running")
            return
        
        logger.info("Starting RabbitMQ consumer in a thread")
        self._thread = threading.Thread(target=self.run)
        self._thread.daemon = True  # Thread will exit when main thread exits
        self._thread.start()
    
    def stop(self):
        """Stop the consumer"""
        logger.info("Stopping RabbitMQ consumer")
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

# Global consumer instance
_consumer = None
_lock = threading.Lock()

def start_rabbitmq_consumer():
    """Start the RabbitMQ consumer"""
    global _consumer
    with _lock:
        if _consumer is None:
            _consumer = RabbitMQConsumer()
            
        if not _consumer.is_running:
            _consumer.run_in_thread()
            # Wait a bit to make sure the consumer starts
            time.sleep(1)
        
        return _consumer.is_running