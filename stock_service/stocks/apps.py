import logging
from django.apps import AppConfig

logger = logging.getLogger(__name__)

class StocksConfig(AppConfig):
    name = 'stocks'
    
    def ready(self):
        """
        Initialize the stocks app when Django starts
        """
        logger.info("Stock service initialized")
