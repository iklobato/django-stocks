from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response

from api.models import UserRequestHistory
from api.serializers import UserRequestHistorySerializer
from api.tasks import fetch_stock_and_store


class ApiRoot(APIView):
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
    def get(self, request, *args, **kwargs):
        import logging
        
        logger = logging.getLogger(__name__)
        
        stock_code = request.query_params.get('q') or request.query_params.get('symbol')
        if not stock_code:
            return Response({"error": "Stock code is required. Use 'q' or 'symbol' parameter."}, status=400)
        
        # Get user ID if authenticated
        user_id = request.user.id if request.user and request.user.is_authenticated else None
        
        try:
            # Enqueue the Celery task
            fetch_stock_and_store.delay(stock_code, user_id)
            
            logger.info(f"Enqueued Celery task for stock symbol: {stock_code}")
            
            # Return immediate response
            return Response({
                "message": f"Stock request for {stock_code} received and is being processed."
            })
                
        except Exception as e:
            logger.error(f"Error enqueueing Celery task: {str(e)}")
            return Response({
                "error": f"Failed to process stock request: {str(e)}"
            }, status=500)


class HistoryView(generics.ListAPIView):
    serializer_class = UserRequestHistorySerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return UserRequestHistory.objects.filter(user=user).order_by('-date')
        return UserRequestHistory.objects.none()


class StatsView(APIView):
    def get(self, request, *args, **kwargs):
        from django.db.models import Count
        
        if not request.user.is_superuser:
            return Response(
                {"error": "You must be a superuser to access this endpoint"}, 
                status=403
            )
        
        top_stocks = UserRequestHistory.objects.values('symbol')\
            .annotate(times_requested=Count('symbol'))\
            .order_by('-times_requested')[:5]
        
        result = [
            {
                "stock": item['symbol'].lower(),
                "times_requested": item['times_requested']
            }
            for item in top_stocks
        ]
        
        return Response(result)