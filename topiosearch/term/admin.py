from django.contrib import admin
from .models import Term


class TermAdmin(admin.ModelAdmin):
    list_display = ('name', 'copyright', 'date_edited')
    search_fields = ['name']


admin.site.register(Term, TermAdmin)