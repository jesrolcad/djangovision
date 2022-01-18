"""djangovision URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from principal import views
from django.conf.urls import handler404

urlpatterns = [
    path('admin/', admin.site.urls),
    path('',views.inicio),
    path('carga/',views.carga),
    path('buscarpais/', views.formulario_pais),
    path('detallesevento/', views.detalles_evento),
    path('cancionespais/', views.pais_canciones),
    path('paisespuntuacionmedia/', views.paises_mejor_puntuacion_media),
    path('detallescancion/<int:id_cancion>', views.detalles_cancion),
    path('detallespais/<int:id_pais>', views.detalles_pais),
    path('detallesevento/<int:id_evento>', views.detalles_evento_2),
    path('busquedacanciontitulo/', views.buscar_cancion_titulo),
    path('busquedacancioneventotituloletra/', views.busqueda_cancion_anyo_titulo_letra),
    path('cancionesporpuntuacion/', views.canciones_mejor_puntuacion),
    path('mejoressemifinalistas/', views.mejores_canciones_semifinalistas),
    path('mejoresfinalistas/', views.mejores_canciones_finalistas),
    path('cancionesmasdocepuntos/', views.canciones_doce_puntos),
    path('cargarSR/', views.loadRS),
    path('recomendarcancionespais/', views.recommendedSongsCountry),
    path('recomendarcancionesitems/', views.recommendedSongsItems),
    path('recomendarpaisescancion/', views.recommendedCountrySongs),
    path('cancionesimilares/', views.similarSongs)
]

handler404 = views.error_404_view