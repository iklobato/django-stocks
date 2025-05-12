# encoding: utf-8

from django.contrib import admin
from django.urls import path
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from api import views as api_views

# Simple health check endpoint for container health checks
@csrf_exempt
def health_check(request):
    return JsonResponse({"status": "healthy"})

urlpatterns = [
    # Support both with and without trailing slashes
    path('stock', api_views.StockView.as_view()),
    path('stock/', api_views.StockView.as_view()),
    
    path('history', api_views.HistoryView.as_view()),
    path('history/', api_views.HistoryView.as_view()),
    
    path('stats', api_views.StatsView.as_view()),
    path('stats/', api_views.StatsView.as_view()),
    
    path('admin/', admin.site.urls),
    path('admin', admin.site.urls),
    
    # Health check endpoint for Docker
    path('health/', health_check),
    
    # Add a root path for API documentation
    path('', api_views.ApiRoot.as_view()),
]
