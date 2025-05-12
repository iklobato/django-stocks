from django.urls import path
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from stocks import views as stocks_views

@csrf_exempt
def health_check(request):
    return JsonResponse({"status": "healthy", "service": "stock-service"})

urlpatterns = [
    path('stock', stocks_views.StockView.as_view()),
    path('stock/', stocks_views.StockView.as_view()),
    
    path('health/', health_check),
]