from django.contrib import admin
from .models import Term


class TermAdmin(admin.ModelAdmin):
    list_display = ('url','name', 'copyright', 'date_edited')
    search_fields = ['name','url']


admin.site.register(Term, TermAdmin)