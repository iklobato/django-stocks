import logging
import sys
from django.apps import AppConfig

logger = logging.getLogger(__name__)

class StocksConfig(AppConfig):
    name = 'stocks'
    
    def ready(self):
        """
        Initialize the stocks app and start the RabbitMQ consumer when Django starts
        """
        # Don't start the RabbitMQ consumer when running management commands
        if 'runserver' in sys.argv:
            # Import here to avoid AppRegistryNotReady exception
            from .rabbitmq_consumer import start_rabbitmq_consumer
            
            logger.info("Starting RabbitMQ consumer for stock service...")
            if start_rabbitmq_consumer():
                logger.info("RabbitMQ consumer started successfully")
            else:
                logger.error("Failed to start RabbitMQ consumer")
        
        logger.info("Stock service initialized")
