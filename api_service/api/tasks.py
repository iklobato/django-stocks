import csv
import io
import logging
import requests
from celery import shared_task
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model

from .models import UserRequestHistory

logger = logging.getLogger(__name__)
User = get_user_model()

@shared_task
def fetch_stock_and_store(symbol, user_id=None):
    """
    Celery task to fetch stock data from Stooq API and store it in the database.
    
    Args:
        symbol (str): The stock symbol to query
        user_id (int, optional): The user ID to associate with the query
    
    Returns:
        dict: The stock data or error message
    """
    logger.info(f"Fetching stock data for symbol: {symbol}")
    
    try:
        # Call Stooq API
        url = f"https://stooq.com/q/l/?s={symbol}&f=sd2t2ohlcvn&h&e=csv"
        logger.info(f"Making request to: {url}")
        response = requests.get(url)
        response.raise_for_status()
        
        # Parse CSV data
        content = response.content.decode('utf-8')
        csv_reader = csv.reader(io.StringIO(content))
        header = next(csv_reader)
        
        try:
            data = next(csv_reader)
        except StopIteration:
            logger.error("Invalid data received from stock API. Empty result.")
            return {"error": "Invalid data received from stock API. Empty result."}
        
        stock_data = dict(zip(header, data))
        logger.info(f"Parsed stock data: {stock_data}")
        
        # Validate response
        if stock_data.get('Open') == 'N/A' or stock_data.get('Close') == 'N/A':
            logger.warning(f"No data available for stock code: {symbol}")
            return {"error": "No data available for this stock code"}
        
        try:
            # Format stock data result
            result = {
                "symbol": stock_data.get('Symbol', '').upper(),
                "name": stock_data.get('Name', '').upper() or stock_data.get('Symbol', '').upper(),
                "open": float(stock_data.get('Open', 0)),
                "high": float(stock_data.get('High', 0)),
                "low": float(stock_data.get('Low', 0)),
                "close": float(stock_data.get('Close', 0)),
                "volume": int(stock_data.get('Volume', 0))
            }
            
            # Store in database if user_id is provided
            if user_id:
                try:
                    user = User.objects.get(id=user_id)
                    
                    # Create a history record
                    UserRequestHistory.objects.create(
                        user=user,
                        date=timezone.now(),
                        symbol=result["symbol"],
                        name=result["name"],
                        open=result["open"],
                        high=result["high"],
                        low=result["low"],
                        close=result["close"],
                        data=result  # Store the full result
                    )
                    logger.info(f"Stored stock query result for user {user_id}, symbol {symbol}")
                    
                except User.DoesNotExist:
                    logger.error(f"User with ID {user_id} does not exist")
                    # Still return the result even if we couldn't store it
                except Exception as e:
                    logger.error(f"Error storing stock result: {str(e)}")
                    # Still return the result even if we couldn't store it
            
            return result
            
        except ValueError as e:
            logger.error(f"Error converting values: {e}")
            return {"error": f"Error converting data values: {str(e)}"}
            
    except requests.RequestException as e:
        logger.error(f"Request error: {e}")
        return {"error": f"Failed to fetch stock data: {str(e)}"}
    except (ValueError, TypeError, IndexError) as e:
        logger.error(f"Data processing error: {e}")
        return {"error": f"Error processing stock data: {str(e)}"}