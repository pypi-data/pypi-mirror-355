from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
from .core import get_memory_payload

@csrf_exempt
@require_GET
def ping_view(request):
    response = JsonResponse(get_memory_payload())
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response["Access-Control-Allow-Headers"] = "Content-Type"
    return response

def register_ping():
    return ping_view
