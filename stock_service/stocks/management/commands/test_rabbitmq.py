import logging
import time
import pika
import json
from json_tricks import dumps, loads
from django.core.management.base import BaseCommand
from django.conf import settings
from uuid import uuid4

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Test RabbitMQ integration by sending a test message'
    
    def add_arguments(self, parser):
        parser.add_argument('stock_code', type=str, help='Stock code to request')
    
    def handle(self, *args, **options):
        stock_code = options['stock_code']
        
        self.stdout.write(f"Testing RabbitMQ with stock code: {stock_code}")
        
        # Connect to RabbitMQ
        try:
            # RabbitMQ connection parameters
            credentials = pika.PlainCredentials(
                settings.RABBITMQ_USER,
                settings.RABBITMQ_PASSWORD
            )
            parameters = pika.ConnectionParameters(
                host=settings.RABBITMQ_HOST,
                port=settings.RABBITMQ_PORT,
                credentials=credentials
            )
            
            # Connect to RabbitMQ
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()
            
            # Declare the callback queue
            result = channel.queue_declare(queue='', exclusive=True)
            callback_queue = result.method.queue
            
            # Generate a unique correlation ID
            correlation_id = str(uuid4())
            
            # Store the response when it comes back
            response = None
            
            # Callback function for when a response is received
            def on_response(ch, method, props, body):
                nonlocal response
                if props.correlation_id == correlation_id:
                    response = loads(body)
                    self.stdout.write(f"Received response: {response}")
                    ch.basic_ack(delivery_tag=method.delivery_tag)
            
            # Start consuming from the callback queue
            channel.basic_consume(
                queue=callback_queue,
                on_message_callback=on_response,
                auto_ack=False
            )
            
            # Prepare the request message
            request_data = {
                'stock_code': stock_code
            }
            
            # Publish the message
            channel.basic_publish(
                exchange='',
                routing_key=settings.RABBITMQ_STOCK_QUEUE,
                properties=pika.BasicProperties(
                    reply_to=callback_queue,
                    correlation_id=correlation_id
                ),
                body=dumps(request_data)
            )
            
            # Wait for the response (with timeout)
            timeout = 10
            start_time = time.time()
            
            self.stdout.write(f"Waiting for response (timeout: {timeout}s)")
            
            while response is None:
                # Process data events to check for messages
                connection.process_data_events(time_limit=0.1)
                
                # Check for timeout
                if time.time() - start_time > timeout:
                    self.stdout.write(self.style.ERROR(f"Timeout waiting for response"))
                    break
            
            # Close the connection
            connection.close()
            
            # Print the result
            if response:
                if response.get('status') == 200:
                    self.stdout.write(self.style.SUCCESS(f"Successfully received stock data: {response['data']}"))
                else:
                    self.stdout.write(self.style.ERROR(f"Error: {response.get('error')}"))
            else:
                self.stdout.write(self.style.ERROR("No response received"))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))