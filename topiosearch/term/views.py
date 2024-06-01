import html
from django.shortcuts import render
from .models import Term

def index(request):
    terms = Term.objects.all()
    for term in terms:

        # Clean definition
        if(term.definition):
            decoded_def = term.definition.encode().decode('unicode-escape')
            term.definition = decoded_def.replace("\\", "")

        # Clean example
        if(term.example):
            decoded_example = term.example.encode().decode('unicode-escape')
            term.example = decoded_example.replace("\\", "")

        # Type
        if term.type is None:
            term.type = ""

    return render(request, 'terms/index.html',{'terms':terms})