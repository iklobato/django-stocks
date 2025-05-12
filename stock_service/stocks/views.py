import csv
import io
import logging
import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)

class StockView(APIView):
    def get(self, request, *args, **kwargs):
        logger.info(f"StockView.get called with params: {request.query_params}")
        logger.debug(f"Path: {request.path}")
        
        stock_code = (request.query_params.get('stock_code') or 
                     request.query_params.get('symbol') or
                     request.query_params.get('q'))
        
        if not stock_code:
            logger.warning("Request missing required stock code parameter")
            return Response({"error": "Stock code is required (use 'stock_code', 'symbol', or 'q' parameter)"}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        try:
            url = f"https://stooq.com/q/l/?s={stock_code}&f=sd2t2ohlcvn&h&e=csv"
            logger.debug(f"Making request to: {url}")
            response = requests.get(url, timeout=10)  # Added timeout for safety
            response.raise_for_status()
            
            content = response.content.decode('utf-8')
            logger.debug(f"CSV Content: {content[:200]}...")
            
            csv_reader = csv.reader(io.StringIO(content))
            header = next(csv_reader)
            try:
                data = next(csv_reader)
            except StopIteration:
                logger.error("Invalid data received from stock API. Empty result.")
                return Response(
                    {"error": "Invalid data received from stock API. Empty result."}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            stock_data = dict(zip(header, data))
            logger.debug(f"Parsed stock data: {stock_data}")
            
            if stock_data.get('Open') == 'N/A' or stock_data.get('Close') == 'N/A':
                logger.info(f"No data available for stock code: {stock_code}")
                return Response({"error": "No data available for this stock code"}, 
                               status=status.HTTP_404_NOT_FOUND)
            
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
            except ValueError as e:
                logger.error(f"Error converting stock data values: {e}")
                return Response(
                    {"error": f"Error converting data values: {str(e)}"}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            logger.info(f"Successfully processed stock data for: {stock_code}")
            return Response(result)
            
        except requests.RequestException as e:
            logger.error(f"Request error when fetching stock data: {e}", exc_info=True)
            return Response({"error": f"Failed to fetch stock data: {str(e)}"}, 
                           status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except (ValueError, TypeError, IndexError) as e:
            logger.error(f"Data processing error for stock data: {e}", exc_info=True)
            return Response({"error": f"Error processing stock data: {str(e)}"}, 
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)