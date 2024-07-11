import html
from django.shortcuts import render
from .models import Term

def index(request):
    terms = Term.objects.all().order_by('name')
    for term in terms:

        # Clean definition
        if(term.definition):
            term.definition = term.definition.replace("\\", "")

        # Clean example
        if(term.example):
            term.example = term.example.replace("\\", "")

        # Type
        if term.type is None:
            term.type = ""

    return render(request, 'terms/index.html',{'terms':terms})

def term(request,url):
    term = Term.objects.get(url=url)
    params = {
        'term': term,
    }
    return render(request, 'term/index.html',params)