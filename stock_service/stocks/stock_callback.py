import csv
import io
import logging
import requests
from typing import Dict, Any, Union

logger = logging.getLogger(__name__)

def process_stock_request(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a stock request received from RabbitMQ
    
    Args:
        request_data: A dictionary containing the stock request data
                      Expected to have a 'stock_code' key
                      
    Returns:
        A dictionary containing the stock data or an error response
    """
    logger.info(f"Processing stock request: {request_data}")
    
    # Extract the stock code from the request
    stock_code = (request_data.get('stock_code') or 
                 request_data.get('symbol') or
                 request_data.get('q'))
    
    if not stock_code:
        logger.error("Stock code is required but not provided")
        return {
            "error": "Stock code is required (use 'stock_code', 'symbol', or 'q' parameter)",
            "status": 400
        }
    
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
            logger.error("Invalid data received from stock API. Empty result.")
            return {
                "error": "Invalid data received from stock API. Empty result.",
                "status": 500
            }
        
        # Create a dictionary from the CSV data
        stock_data = dict(zip(header, data))
        logger.info(f"Parsed stock data: {stock_data}")
        
        # Check for N/A values in the data
        if stock_data.get('Open') == 'N/A' or stock_data.get('Close') == 'N/A':
            logger.warning(f"No data available for stock code: {stock_code}")
            return {
                "error": "No data available for this stock code",
                "status": 404
            }
        
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
            return {
                "data": result,
                "status": 200
            }
        except ValueError as e:
            logger.error(f"Error converting values: {e}")
            return {
                "error": f"Error converting data values: {str(e)}",
                "status": 500
            }
        
    except requests.RequestException as e:
        logger.error(f"Request error: {e}")
        return {
            "error": f"Failed to fetch stock data: {str(e)}",
            "status": 500
        }
    except (ValueError, TypeError, IndexError) as e:
        logger.error(f"Data processing error: {e}")
        return {
            "error": f"Error processing stock data: {str(e)}",
            "status": 500
        }