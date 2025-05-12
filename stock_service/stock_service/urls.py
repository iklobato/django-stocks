# encoding: utf-8

from django.urls import path
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from stocks import views as stocks_views

# Simple health check endpoint for container health checks
@csrf_exempt
def health_check(request):
    return JsonResponse({"status": "healthy", "service": "stock-service"})

urlpatterns = [
    # Both with and without trailing slash to be more flexible
    path('stock', stocks_views.StockView.as_view()),
    path('stock/', stocks_views.StockView.as_view()),
    
    # Health check endpoint for Docker
    path('health/', health_check),
]
