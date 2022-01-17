from django.contrib import admin

from principal.models import Cancion, Pais, Evento, Puntuacion

# Register your models here.
admin.site.register(Pais)
admin.site.register(Cancion)
admin.site.register(Evento)
admin.site.register(Puntuacion)
