import csv
import io
import logging
import requests
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)

def process_stock_request(request_data):
    """
    Process a stock request and return stock data.
    
    Args:
        request_data (dict): A dictionary containing the stock request parameters.
            Expected to have one of: 'stock_code', 'symbol', or 'q'.
            
    Returns:
        dict: A dictionary with 'status' and either 'data' (success) or 'error' (failure).
    """
    logger.info(f"Processing stock request: {request_data}")
    
    # Extract stock code from request data
    stock_code = (request_data.get('stock_code') or 
                 request_data.get('symbol') or 
                 request_data.get('q'))
    
    # Check if stock code is provided
    if not stock_code:
        logger.warning("Missing required stock code parameter")
        return {
            "error": "Stock code is required (use 'stock_code', 'symbol', or 'q' parameter)",
            "status": 400
        }
    
    try:
        # Fetch stock data from Stooq API
        url = f"https://stooq.com/q/l/?s={stock_code}&f=sd2t2ohlcvn&h&e=csv"
        logger.debug(f"Making request to: {url}")
        
        # Add timeout to prevent hanging
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # Parse CSV response
        content = response.content.decode('utf-8')
        logger.debug(f"CSV Content: {content[:200]}...")
        
        csv_reader = csv.reader(io.StringIO(content))
        header = next(csv_reader)
        
        try:
            data = next(csv_reader)
        except StopIteration:
            logger.error("Invalid data received from stock API. Empty result.")
            return {
                "error": "Invalid data received from stock API. Empty result.",
                "status": 500
            }
        
        # Convert CSV data to dictionary
        stock_data = dict(zip(header, data))
        logger.debug(f"Parsed stock data: {stock_data}")
        
        # Check for N/A values in critical fields
        if stock_data.get('Open') == 'N/A' or stock_data.get('Close') == 'N/A':
            logger.info(f"No data available for stock code: {stock_code}")
            return {
                "error": "No data available for this stock code",
                "status": 404
            }
        
        try:
            # Format result data
            result = {
                "symbol": stock_data.get('Symbol', '').upper(),
                "name": stock_data.get('Name', '').upper() or stock_data.get('Symbol', '').upper(),
                "open": float(stock_data.get('Open', 0)),
                "high": float(stock_data.get('High', 0)),
                "low": float(stock_data.get('Low', 0)),
                "close": float(stock_data.get('Close', 0)),
                "volume": int(stock_data.get('Volume', 0))
            }
            
            logger.info(f"Successfully processed stock data for: {stock_code}")
            return {
                "data": result,
                "status": 200
            }
            
        except ValueError as e:
            logger.error(f"Error converting stock data values: {e}")
            return {
                "error": f"Error converting data values: {str(e)}",
                "status": 500
            }
            
    except RequestException as e:
        logger.error(f"Request error when fetching stock data: {e}", exc_info=True)
        return {
            "error": f"Failed to fetch stock data: {str(e)}",
            "status": 500
        }
    except (ValueError, TypeError, IndexError) as e:
        logger.error(f"Data processing error for stock data: {e}", exc_info=True)
        return {
            "error": f"Error processing stock data: {str(e)}",
            "status": 500
        }