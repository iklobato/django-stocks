# encoding: utf-8

import csv
import io
import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


class StockView(APIView):
    """
    Receives stock requests from the API service.
    Fetches stock data from the stooq.com API and returns it.
    """
    def get(self, request, *args, **kwargs):
        # Print debug info
        print(f"StockView.get called with params: {request.query_params}")
        print(f"Path: {request.path}")
        
        # Look for stock_code, symbol, or q parameter (accept any of them)
        stock_code = (request.query_params.get('stock_code') or 
                     request.query_params.get('symbol') or
                     request.query_params.get('q'))
        
        if not stock_code:
            return Response({"error": "Stock code is required (use 'stock_code', 'symbol', or 'q' parameter)"}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Make request to the stooq.com API
            url = f"https://stooq.com/q/l/?s={stock_code}&f=sd2t2ohlcvn&h&e=csv"
            print(f"Making request to: {url}")
            response = requests.get(url)
            response.raise_for_status()
            
            # Parse CSV data
            content = response.content.decode('utf-8')
            print(f"CSV Content: {content[:200]}...")  # Print first 200 chars
            
            csv_reader = csv.reader(io.StringIO(content))
            header = next(csv_reader)
            try:
                data = next(csv_reader)
            except StopIteration:
                return Response(
                    {"error": "Invalid data received from stock API. Empty result."}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Create a dictionary from the CSV data
            stock_data = dict(zip(header, data))
            print(f"Parsed stock data: {stock_data}")
            
            # Check for N/A values in the data
            if stock_data.get('Open') == 'N/A' or stock_data.get('Close') == 'N/A':
                return Response({"error": "No data available for this stock code"}, 
                               status=status.HTTP_404_NOT_FOUND)
            
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
            except ValueError as e:
                print(f"Error converting values: {e}")
                return Response(
                    {"error": f"Error converting data values: {str(e)}"}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            return Response(result)
            
        except requests.RequestException as e:
            print(f"Request error: {e}")
            return Response({"error": f"Failed to fetch stock data: {str(e)}"}, 
                           status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except (ValueError, TypeError, IndexError) as e:
            print(f"Data processing error: {e}")
            return Response({"error": f"Error processing stock data: {str(e)}"}, 
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
