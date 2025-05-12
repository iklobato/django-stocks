# encoding: utf-8

from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response

from api.models import UserRequestHistory
from api.serializers import UserRequestHistorySerializer


class ApiRoot(APIView):
    """
    API documentation page
    """
    def get(self, request, *args, **kwargs):
        api_endpoints = {
            "endpoints": {
                "stock": "/stock?q=SYMBOL - Get stock data (e.g., /stock?q=aapl.us)",
                "history": "/history - Get your query history",
                "stats": "/stats - Get top 5 most requested stocks (admin only)"
            },
            "authentication": "Use Basic Authentication or Token Authentication"
        }
        return Response(api_endpoints)


class StockView(APIView):
    """
    Endpoint to allow users to query stocks
    """
    def get(self, request, *args, **kwargs):
        import logging
        from django.conf import settings
        from .rabbitmq_client import get_client
        
        logger = logging.getLogger(__name__)
        
        # Get stock code from query parameters
        stock_code = request.query_params.get('q') or request.query_params.get('symbol')
        if not stock_code:
            return Response({"error": "Stock code is required. Use 'q' or 'symbol' parameter."}, status=400)
        
        # Call the stock service via RabbitMQ
        try:
            # Get the RabbitMQ client
            rabbitmq_client = get_client()
            queue_name = settings.RABBITMQ_STOCK_QUEUE
            
            # Prepare the request data
            request_data = {
                'stock_code': stock_code
            }
            
            logger.info(f"Sending RabbitMQ request for stock: {stock_code}")
            
            # Make the RPC call
            response_data = rabbitmq_client.call(queue_name, request_data, timeout=settings.RABBITMQ_TIMEOUT)
            
            # Check if we got a response
            if response_data is None:
                # Try fallback to direct HTTP request if RabbitMQ fails
                return self.fallback_http_request(stock_code)
            
            # Check if there was an error
            if isinstance(response_data, dict) and 'error' in response_data:
                error_message = response_data.get('error', 'Unknown error')
                error_status = response_data.get('status', 500)
                return Response({"error": error_message}, status=error_status)
            
            # Save the request to history if a user is authenticated
            if request.user and request.user.is_authenticated:
                UserRequestHistory.objects.create(
                    user=request.user,
                    stock_symbol=stock_code.upper(),
                    data=response_data
                )
            
            # Return the stock data to the user
            return Response(response_data)
                
        except Exception as e:
            logger.error(f"Error calling stock service via RabbitMQ: {str(e)}")
            # Try fallback to direct HTTP request
            return self.fallback_http_request(stock_code)
    
    def fallback_http_request(self, stock_code):
        """Fallback method to call the stock service directly via HTTP"""
        import requests
        import logging
        from django.conf import settings
        
        logger = logging.getLogger(__name__)
        logger.warning(f"Using HTTP fallback for stock: {stock_code}")
        
        try:
            # Use the configured stock service URL from settings
            stock_service_url = getattr(settings, 'STOCK_SERVICE_URL', 'http://localhost:8001')
            request_url = f"{stock_service_url}/stock?symbol={stock_code}"
            
            logger.info(f"Making fallback HTTP request to: {request_url}")
            response = requests.get(request_url)
            
            # Log response for debugging
            logger.info(f"HTTP fallback response: {response.status_code}")
            
            # If the request was successful
            if response.status_code == 200:
                stock_data = response.json()
                
                # Save the request to history if a user is authenticated
                if self.request.user and self.request.user.is_authenticated:
                    UserRequestHistory.objects.create(
                        user=self.request.user,
                        stock_symbol=stock_code.upper(),
                        data=stock_data
                    )
                
                # Return the stock data to the user
                return Response(stock_data)
            else:
                # Return any error from the stock service
                try:
                    error_data = response.json()
                    return Response(error_data, status=response.status_code)
                except:
                    return Response(
                        {"error": f"Stock service error: {response.text}"}, 
                        status=response.status_code
                    )
                
        except requests.RequestException as e:
            return Response(
                {"error": f"Failed to connect to stock service: {str(e)}"}, 
                status=500
            )


class HistoryView(generics.ListAPIView):
    """
    Returns queries made by current user.
    """
    serializer_class = UserRequestHistorySerializer
    
    def get_queryset(self):
        """
        This view returns a list of all the stock queries
        for the currently authenticated user.
        """
        user = self.request.user
        if user.is_authenticated:
            return UserRequestHistory.objects.filter(user=user).order_by('-created_at')
        return UserRequestHistory.objects.none()


class StatsView(APIView):
    """
    Allows super users to see which are the most queried stocks.
    """
    def get(self, request, *args, **kwargs):
        from django.db.models import Count
        
        # Check if user is a superuser
        if not request.user.is_superuser:
            return Response(
                {"error": "You must be a superuser to access this endpoint"}, 
                status=403
            )
        
        # Get the top 5 most requested stocks
        top_stocks = UserRequestHistory.objects.values('stock_symbol')\
            .annotate(times_requested=Count('stock_symbol'))\
            .order_by('-times_requested')[:5]
        
        # Format the response as specified in the README
        result = [
            {
                "stock": item['stock_symbol'].lower(),
                "times_requested": item['times_requested']
            }
            for item in top_stocks
        ]
        
        return Response(result)
