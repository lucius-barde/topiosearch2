from django.shortcuts import render
from django.core import serializers # pour les objets
from django.http import JsonResponse
from django.http import HttpResponse
from .models import Search



# Create your views here.
def api_remote_search_term(request):
    term = request.GET.get('term')
    topio_search = Search.onTopio(term)

    response = {
        "responses":{
            "local":False,
            "topio":topio_search,
            "hsuter": False,
            "hsuternames": False
        }
    }
    return JsonResponse(response)

def api_local_search_term(request):
    return JsonResponse({"todo":"TODO"})