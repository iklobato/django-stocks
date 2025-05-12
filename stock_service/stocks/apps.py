import logging
import sys
from django.apps import AppConfig

logger = logging.getLogger(__name__)

class StocksConfig(AppConfig):
    name = 'stocks'
    
    def ready(self):
        if 'runserver' in sys.argv:
            from .rabbitmq_consumer import start_rabbitmq_consumer
            
            logger.info("Starting RabbitMQ consumer for stock service...")
            if start_rabbitmq_consumer():
                logger.info("RabbitMQ consumer started successfully")
            else:
                logger.error("Failed to start RabbitMQ consumer")
        
        logger.info("Stock service initialized")