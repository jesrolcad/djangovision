from http.client import LENGTH_REQUIRED
import shelve
from django.shortcuts import render, redirect, get_object_or_404
from principal.recommendations import getRecommendations, calculateSimilarItems, transformPrefs, getRecommendedItems, topMatches
from principal.forms import PaisForm, EventoForm, TextForm, EventoLetraForm, CancionesNPuntosForm, CancionForm
from principal.models import Cancion, Pais, Evento, Puntuacion
from principal.populate import populateDB
from whoosh.qparser import QueryParser
from whoosh.index import open_dir
from whoosh.qparser import MultifieldParser
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Avg, Count


#carga los datos desde la web en la BD
def carga(request):
 
    if request.method=='POST':
        if 'Aceptar' in request.POST:      
            num_paises, num_canciones, num_eventos, num_puntuaciones = populateDB()
            mensaje="Se han almacenado: " + str(num_paises) +" países, " + str(num_canciones) +" canciones (en la BD y en el índice de Whoosh), " + str(num_eventos) +" eventos, "  + str(num_puntuaciones) + " puntuaciones"
            return render(request, 'cargaBD.html', {'mensaje':mensaje})
        else:
            return redirect("/")
           
    return render(request, 'confirmacion.html')

#muestra el número de registros que hay en la BD
def inicio(request):
    num_canciones=Cancion.objects.all().count()
    num_paises = Pais.objects.all().count()
    num_eventos = Evento.objects.all().count()
    num_puntuaciones = Puntuacion.objects.all().count()
    return render(request,'inicio.html', {'num_canciones':num_canciones, 'num_paises':num_paises,'num_eventos':num_eventos, 'num_puntuaciones':num_puntuaciones})


def formulario_pais(request):
    formulario = PaisForm()
    pais = None
    if request.method == 'POST':
        formulario = PaisForm(request.POST)
        if formulario.is_valid(): #Corre la validación correspondiente
            pais = Pais.objects.get(id=formulario.cleaned_data['pais'].id)
            #canciones_pais = pais.canciones.all().order_by('evento__anyo')
    return render(request, 'formulariopais.html', {'formulario':formulario, 'pais':pais})

#Para un evento, muestro sus detalles
def detalles_evento(request):
    formulario = EventoForm()
    evento = None
    canciones_evento = None
    if request.method == 'POST':
        formulario = EventoForm(request.POST)
        if formulario.is_valid(): #Corre la validación correspondiente
            evento=Evento.objects.get(id=formulario.cleaned_data['evento'].id)
            canciones_evento = evento.canciones.all().order_by('posicion')
    return render(request, 'detallesevento.html', {'formulario':formulario, 'evento':evento, 'canciones':canciones_evento})


#Agrupación de canciones por país
def pais_canciones(request):
    paises = Pais.objects.all()
    page = request.GET.get('page', 1)

    paginator = Paginator(paises, 3)
    try:
        paises_page = paginator.page(page)
    except PageNotAnInteger:
        paises_page = paginator.page(1)
    except EmptyPage:
        paises_page = paginator.page(paginator.num_pages)

    return render(request, 'cancionespais.html', {'paises_page':paises_page})

def detalles_cancion(request, id_cancion):
    cancion = Cancion.objects.get(id=id_cancion)
    letra = cancion.letra.split("\n")
    return render(request, 'detallescancion.html', {'cancion':cancion, 'letra':letra})

def detalles_pais(request, id_pais):
    pais = Pais.objects.get(id=id_pais)
    return render(request, 'detallespais.html', {'pais':pais})

def detalles_evento_2(request, id_evento):
    evento = Evento.objects.get(id=id_evento)
    return render(request, 'evento.html', {'evento':evento})

def buscar_cancion_titulo(request):
    ix=open_dir("Index") #Abrimos el índice   
    formulario = TextForm()
    consulta = None
    results = None
    canciones = []
    if request.method == 'POST':
        formulario = TextForm(request.POST)
        if formulario.is_valid(): #Corre la validación correspondiente
            consulta = formulario.cleaned_data["busqueda"]
            with ix.searcher() as searcher:
                query = QueryParser("titulo", ix.schema).parse(str(consulta))
                print(query)
                results = searcher.search(query)
                for r in results:
                    cancion = Cancion.objects.get(titulo=r['titulo'])
                    canciones.append(cancion)
    return render(request, 'resultadoscanciones.html', {'formulario':formulario, 'canciones':canciones})

def busqueda_cancion_anyo_titulo_letra(request):
    ix = open_dir("Index")
    formulario = EventoLetraForm()
    id_evento = None
    busqueda = None
    results = None
    canciones = []
    if request.method == 'POST':
        formulario = EventoLetraForm(request.POST)
        if formulario.is_valid(): #Corre la validación correspondiente
            busqueda = formulario.cleaned_data["busqueda"]
            id_evento = formulario.cleaned_data['evento'].id
            with ix.searcher() as searcher: #ix.searcher() sirve para buscar en el índice
                consulta_evento = " evento:" + str(id_evento)
                query = MultifieldParser(["letra", "titulo"], ix.schema).parse(busqueda+consulta_evento)
                print(query)
                #query = "(evento:" + str(id_evento) + ")" + " AND " + "(letra:" + busqueda + ")"
                results = searcher.search(query)
                for r in results:
                    cancion = Cancion.objects.get(titulo=r['titulo'])
                    canciones.append(cancion)
    return render(request, 'resultadoscanciones.html', {'formulario':formulario, 'canciones':canciones})

#Dado un evento, mostrar las canciones que hayan conseguido más de N puntos
def canciones_mejor_puntuacion(request):
    formulario = CancionesNPuntosForm()
    canciones = None
    if request.method == 'POST':
        formulario = CancionesNPuntosForm(request.POST)
        if formulario.is_valid(): #Corre la validación correspondiente
            eventoform = formulario.cleaned_data['evento']
            puntuacion = formulario.cleaned_data['puntuacion']
            filter_evento = Q(evento=eventoform)
            filter_puntuacion = Q(puntos__gt = puntuacion)
            canciones = Cancion.objects.filter(filter_evento & filter_puntuacion)
    return render(request, 'resultadoscanciones.html', {'formulario':formulario, 'canciones':canciones})

#Mostrar los 10 países con mejor puntuación media
def paises_mejor_puntuacion_media(request):
    paises = Pais.objects.annotate(avg_puntuacion=Avg('canciones__puntos')).annotate(num_canciones=Count('canciones')).filter(num_canciones__gt = 4).order_by('-avg_puntuacion')[:10]
    return render(request, 'paisespuntuacionmedia.html', {'paises':paises})

#Mejores canciones que no llegaron a la final
def mejores_canciones_semifinalistas(request):
    canciones = Cancion.objects.filter(posicion__gt = 26).order_by('-puntos')[:10]
    return render(request, 'mejorescanciones.html', {'canciones':canciones, 'mensaje':"semifinalistas"})

#Mejores canciones finalistas
def mejores_canciones_finalistas(request):
    canciones = Cancion.objects.filter(posicion__lt = 26).order_by('-puntos')[:10]
    return render(request, 'mejorescanciones.html', {'canciones':canciones, 'mensaje':"finalistas"})

#Canciones que más veces han recibido 12 puntos. Agrupo por cancion y después veo para cada canción cuantos doce puntos ha obtenido
def canciones_doce_puntos(request):
    #El group by es muy importante para forzar la agrupación después de utilizar el método values()
    #Sobre la tabla puntuaciones
    #puntuaciones = Puntuacion.objects.filter(puntuacion=12).values('id_cancion').annotate(num_doce_puntos = Count('puntuacion')).order_by('id_cancion', '-num_doce_puntos')[:10]
    #print(puntuaciones)

    #Sobre la tabla canciones. Fijarse en la sintaxis 
    canciones = Cancion.objects.annotate(num_doce_puntos = Count('puntuacion', filter=Q(puntuacion__puntuacion = 12))).order_by('-num_doce_puntos')[:10]
    return render(request, 'estadisticascanciones.html', {'canciones':canciones})




### SISTEMAS DE RECOMENDACIÓN ### 
def loadDict():
    Prefs={}  
    shelf = shelve.open("dataRS.dat")
    ratings = Puntuacion.objects.all()
    for ra in ratings:
        pais = int(ra.id_pais.id)
        itemid = int(ra.id_cancion.id)
        rating = float(ra.puntuacion)
        Prefs.setdefault(pais, {})
        Prefs[pais][itemid] = rating
    shelf['Prefs']=Prefs
    shelf['ItemsPrefs']=transformPrefs(Prefs)
    shelf['SimItems']=calculateSimilarItems(Prefs, n=10)
    shelf.close()

def loadRS(request):
    if request.method=='POST':
        if 'Aceptar' in request.POST:
            loadDict()
            mensaje = "Se ha cargado el sistema de recomendación correctamente"
            return render(request, 'cargarSR.html', {'mensaje':mensaje})
        else:
            return redirect("/")
    return render(request,'confirmacionSR.html')

#DADO UN PAÍS, QUE LE RECOMIENDE CANCIONES QUE NO HAYA PUNTUADO (BASADO EN PAÍSES)
def recommendedSongsCountry(request):
    if request.method=='GET':
        form = PaisForm(request.GET, request.FILES)
        if form.is_valid():
            id_pais = form.cleaned_data['pais'].id
            pais = get_object_or_404(Pais, id=id_pais)
            shelf = shelve.open("dataRS.dat")
            Prefs = shelf['Prefs']
            shelf.close()
            rankings = getRecommendations(Prefs,int(id_pais))
            recommended = rankings[:10]
            canciones = []
            scores = []
            for re in recommended:
                canciones.append(Cancion.objects.get(id=re[1]))
                scores.append(re[0])
            items= zip(canciones,scores)
            return render(request,'recommendationItems.html', {'pais': pais, 'items': items})
    form = PaisForm()
    return render(request,'search_pais.html', {'form': form})

#DADO UN PAÍS, QUE LE RECOMIENDE CANCIONES QUE NO HAYA PUNTUADO (BASADO EN ITEMS)
def recommendedSongsItems(request):
    if request.method=='GET':
        form = PaisForm(request.GET, request.FILES)
        if form.is_valid():
            id_pais = form.cleaned_data['pais'].id
            pais = get_object_or_404(Pais, id=id_pais)
            shelf = shelve.open("dataRS.dat")
            Prefs = shelf['Prefs']
            SimItems = shelf['SimItems']
            shelf.close()
            rankings = getRecommendedItems(Prefs,SimItems,id_pais)
            recommended = rankings[:10]
            canciones = []
            scores = []
            for re in recommended:
                canciones.append(Cancion.objects.get(id=re[1]))
                scores.append(re[0])
            items= zip(canciones,scores)
            return render(request,'recommendationItems.html', {'pais': pais, 'items': items})
    form = PaisForm()
    return render(request,'search_pais.html', {'form': form})

#Dada una canción, mostrar países a los que se les recomendaría
def recommendedCountrySongs(request):
    if request.method=='GET':
        form = CancionForm(request.GET, request.FILES)
        if form.is_valid():
            id_cancion = form.cleaned_data['cancion']
            cancion = get_object_or_404(Cancion, id=id_cancion)
            shelf = shelve.open("dataRS.dat")
            Prefs = shelf['ItemsPrefs']
            shelf.close()
            rankings = getRecommendations(Prefs,int(id_cancion))
            recommended = rankings[:10]
            paises = []
            scores = []
            for re in recommended:
                paises.append(Pais.objects.get(id=re[1]))
                scores.append(re[0])
            items= zip(paises,scores)
            return render(request,'recommendationCountries.html', {'cancion': cancion, 'items': items})
    form = CancionForm()
    return render(request,'search_cancion.html', {'form': form, 'mensaje':'Recomendaciones a países'})

#Dada una canción, mostrar canciones que más se le parecen
def similarSongs(request):
    cancion = None
    if request.method=='GET':
        form = CancionForm(request.GET, request.FILES)
        if form.is_valid():
            id_cancion = form.cleaned_data['cancion']
            cancion = get_object_or_404(Cancion, id=id_cancion)
            shelf = shelve.open("dataRS.dat")
            ItemsPrefs = shelf['ItemsPrefs']
            shelf.close()
            rankings = topMatches(ItemsPrefs,int(id_cancion))
            recommended = rankings[:5]
            canciones = []
            similar = []
            for re in recommended:
                canciones.append(Cancion.objects.get(id=re[1]))
                similar.append(re[0])
            items= zip(canciones,similar)
            return render(request,'similarSongs.html', {'cancion': cancion, 'canciones': items})
    form = CancionForm()
    return render(request,'search_cancion.html', {'form': form, 'mensaje':'Canciones similares'})

def error_404_view(request, exception):
    data = {"name": "ThePythonDjango.com"}
    return render(request,'error_404.html', data)




