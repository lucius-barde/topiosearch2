from django.shortcuts import render
from django.core import serializers # pour les objets
from django.http import JsonResponse
from django.http import HttpResponse
from .models import Search



# Create your views here.
def api_remote_search_term(request):
    term = request.GET.get('term')
    responses = []
    topio_search = Search.onTopio(term)

    responses.append(topio_search) # TODO: only if not false

    hsuter_search = False
    responses.append(hsuter_search)  # TODO: only if not false

    hsuternames_search = False
    responses.append(hsuternames_search)  # TODO: only if not false

    response = {
        "responses": responses
    }

    return JsonResponse(response)

def api_local_search_term(request):
    term = request.GET.get('term')
    response = {
        "responses": Search.onLocalDatabase(term)
    }
    return JsonResponse(response)