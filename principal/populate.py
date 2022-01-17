import shutil
from selenium.webdriver.chrome.options import Options 
from selenium import webdriver
from bs4 import BeautifulSoup
from requests_html import HTMLSession
from principal.models import Cancion, Pais, Evento, Puntuacion
import time
import numpy
import os
from whoosh.index import create_in
from whoosh.fields import Schema, TEXT, NUMERIC

####### MUY IMPORTANTE #######

### SI SE QUIERE POPULAR LA BASE DE DATOS ESTAS LÍNEAS DEBEN SER DESCOMENTADAS Y ES NECESARIO TENER INSTALADO CHROMEDRIVER
### ES NECESARIO QUE INDIQUE LA RUTA DONDE SE ENCUENTRA EL ARCHIVO chromedriver.exe, EN MI CASO ESTÁ EN LA RUTA 

# C:/Scraping/chromedriver.exe
# option = webdriver.ChromeOptions()
# option.headless = True
# option.add_argument("--incognito")
# #we create the driver specifying the origin of chrome browser
# driver = webdriver.Chrome("C:/Scraping/chromedriver.exe", chrome_options=option)

def scrapingSelenium(url,driver):
    driver.get(url)
    driver.maximize_window()
    html_source_code = driver.execute_script("return document.body.innerHTML;")
    return html_source_code


def populateDB():
    #borrar tablas
    Pais.objects.all().delete()
    Cancion.objects.all().delete()
    Evento.objects.all().delete()
    Puntuacion.objects.all().delete()

    anyos_lugares = {"2021": "rotterdam", "2019":"tel-aviv", "2018": "lisbon", "2017":"kyiv", "2016":"stockholm"}
    paises = [] #Listado de países que se utilizará para el bulk_create
    canciones = [] #Listado de canciones
    canciones2 = [] #Canciones para el bulk_create
    eventos = [] #Listado de eventos para el bulk_create
    puntuaciones = [] #Listado de puntuaciones para el bulk_create
    paises_canciones = {} #Diccionario {nombrepais:listacanciones}
    eventos_canciones = {} #Diccionario {id:listacanciones}
    dictpaises = {} #Diccionario {nombrepais:objetopais}
    dictcanciones = {} #Diccionario {idcancion:objetocancion}
    paises_semifinales = {} #Diccionario {anyo:{idsemifinal:[paises]}} Clave año del evento valor diccionario donde la clave
    #es la semifinal (1 o 2) y el valor es el listado de países pertenecientes a dicha semifinal
    pp = 1 #Id para el país
    c = 1 #Id para la canción
    e = 1 #Id para los eventos
    pun = 1 #Id para la puntuación


    for an in anyos_lugares.keys():  
        print("### CARGANDO EUROVISION SONG CONTEST " + an + " ###")
        session = HTMLSession()
        html = scrapingSelenium("https://eurovisionworld.com/eurovision/" + an,driver)
        # resp = session.get("https://eurovisionworld.com/eurovision/" + an)
        # resp.html.render(timeout=60)
        s = BeautifulSoup(html, "html.parser")
        datos = s.find("div", id="voting_table").find_all("tr", id=True)
        for d in datos:
            enlace_pais = "https://eurovisionworld.com" + d.a['href']
            nombre_pais = d.a['title'].split(" in")[0].strip() ###Parto por donde dice "in" y me quedo 

            if nombre_pais not in dictpaises.keys():
                #DATOS ESPECÍFICOS DEL PAÍS
                html2 = scrapingSelenium(enlace_pais,driver)
                # resp2.html.render(timeout=20)
                s2 = BeautifulSoup(html2, "html.parser")
                estadisticas = s2.find("table", class_ = "voting_stat")
                num_participaciones = int(estadisticas.find("td", text="Participations").find_next_sibling().text)
                num_victorias_aux = estadisticas.find("td", text="Victories").find_next_sibling().text
                num_victorias = "none"

                if num_victorias_aux == num_victorias:
                    num_victorias = 0
                else:
                    num_victorias = int(num_victorias_aux)

                veces_ultima_posicion_aux = estadisticas.find("td", text="Came last").find_next_sibling().text
                veces_ultima_posicion = "never"

                if veces_ultima_posicion_aux == veces_ultima_posicion:
                    veces_ultima_posicion = 0
                else:
                    veces_ultima_posicion = int(veces_ultima_posicion_aux)

                # YA PODEMOS METER EL PAÍS EN LA LISTA
                objeto_pais = Pais(id=pp,nombre=nombre_pais, participaciones=num_participaciones, victorias=num_victorias,ultima_posicion=veces_ultima_posicion)
                paises.append(objeto_pais)
                dictpaises[nombre_pais] = objeto_pais
                pp+=1

            ### DATOS DE LAS CANCIONES
            nombre_pais_enlace = enlace_pais.split("/")[-1]
            enlace_cancion = "https://eurovisionworld.com/eurovision/" + an + "/" + nombre_pais_enlace
            posicion_cancion = int(d.td.text)
            clase = "r500n"
            if posicion_cancion < 27: ###Si la posición es menor que el 27 sí puedo buscar así porque es otra tabla
                clase = "v_td_point"
            cabecera = d.find("td", class_= clase).find_previous_sibling().a['title'].split(":")
            cancion_y_artista = cabecera[1].split("-")
            artista_cancion = cancion_y_artista[0].strip()
            cancion = cancion_y_artista[1].strip().replace('"', "")

            if cancion == "Tick": #Es la única canción que tiene un guión en su título
                cancion = "Tick-Tock"

            if posicion_cancion < 27:
                clase = "v_td_point"
                puntos_cancion = int(d.find("td", class_= clase).a.text)
            else:
                puntos_cancion = int(d.find("td", class_= clase).text)
            if posicion_cancion >= 27:
                semifinal = int(d.find("span", class_= "r600n").text.strip()[-1])
                if an in paises_semifinales:
                    dicc = paises_semifinales[an] #Esto es un diccionario de la forma {idsemifinal:[listapaises]}
                    if semifinal in dicc:
                        lista = dicc[semifinal] #Cojo la lista de países pertenecientes a esa semifinal
                        lista.append(nombre_pais) #Añado el país a dicha lista
                        dicc[semifinal] = lista #El valor es la lista actualizada
                    else: #Si la semifinal no es clave la añado con el país como lista de único elemento
                        dicc[semifinal] = [nombre_pais] 
                else: #Si el año no está en el diccionario, lo añado como clave y como valor el diccionario
                    dicc = {semifinal:[nombre_pais]}
                    paises_semifinales[an] = dicc

                #print("Este país está en la semifinal " + str(semifinal))

            print("Nombre del país: " + nombre_pais + " " + "Nombre de la canción: " + cancion)
            html3 = scrapingSelenium(enlace_cancion,driver)
            # resp3 = session.get(enlace_cancion)
            # resp3.html.render(timeout=20)
            s3 = BeautifulSoup(html3, "html.parser")
            letra_parrafos = s3.find("div", id="lyrics_0").find_all("p")
            letra_cancion = ""
            for p in letra_parrafos:
                estrofa = p.get_text(separator=u'\n')
                letra_cancion += "\n"+estrofa

            objeto_cancion = ((c,cancion,letra_cancion,puntos_cancion,posicion_cancion, artista_cancion,dictpaises[nombre_pais])) 
            #Cancion(id=c,titulo=cancion, letra=letra_cancion, puntos=puntos_cancion, posicion=posicion_cancion, artista=artista_cancion, pais=dictpaises[nombre_pais])
            dictcanciones[c] = objeto_cancion
            c+=1
            canciones.append(objeto_cancion)
        
        #Completamos el diccionario de los países y sus canciones.
        #Si el nombre del país ya es una clave, cojo su valor (lista) y le añado la nueva canción
        #En caso contrario, añado una nueva clave que sea el nombre del país, y le añado la canción (lista)
            if nombre_pais in paises_canciones:
                listcanciones = paises_canciones[nombre_pais]
                listcanciones.append(objeto_cancion)
                paises_canciones[nombre_pais] = listcanciones
            else:
                paises_canciones[nombre_pais] = [objeto_cancion]

        #DATOS DE LOS EVENTOS
        datos_evento = s.find("div", class_="voting_info mm")
        anyo_evento = int(datos_evento.p.a.text.split(" ")[2].replace(",", ""))
        lugar_evento = datos_evento.p.find_all("a")[1].text
        slogan_evento = datos_evento.p.find_all()[-1].text

        objeto_evento = Evento(id=e,anyo=anyo_evento, lugar=lugar_evento,eslogan=slogan_evento)
        eventos.append(objeto_evento)
        eventos_canciones[objeto_evento] = canciones #Añado a los eventos sus canciones
        canciones = []
        e+=1

    print("Creando países...")
    Pais.objects.bulk_create(paises)
    print("Países insertados en la base de datos")

    print("Creando eventos...")
    Evento.objects.bulk_create(eventos)
    print("Eventos insertados en la base de datos")

    for ev in eventos_canciones:
        songs = eventos_canciones[ev]
        for s in songs:
            cancion_obj = Cancion(id=s[0],titulo=s[1], letra=s[2],puntos=s[3],posicion=s[4],artista=s[5],pais=s[6], evento=ev)
            canciones2.append(cancion_obj)

    print("Creando canciones...")
    Cancion.objects.bulk_create(canciones2)
    print("Canciones insertadas en la base de datos")

    print("Creando esquema de Whoosh...")
    crearWhoosh()
    print("Índice de canciones creado")
    

    #DATOS DE LAS PUNTUACIONES
    puntuaciones_posibles = [1,2,3,4,5,6,7,8,10,12]
    canciones = Cancion.objects.all()
    for ev in eventos:
        for pais in paises:
            #Un país no se puede votar a sí mismo y tiene que votar canciones de cada año!
            lista_canciones = [c for c in canciones if c.pais.id != pais.id and c.evento.anyo == ev.anyo]
            canciones_elegidas = numpy.random.choice(lista_canciones,10,False)
            canciones_puntuadas = zip(puntuaciones_posibles,canciones_elegidas)
            for cp in canciones_puntuadas:
                puntuaciones.append(Puntuacion(id=pun,puntuacion = cp[0], id_pais = pais, id_cancion = cp[1]))
                pun+=1
    
    print("Creando puntuaciones")
    Puntuacion.objects.bulk_create(puntuaciones)
    print("Puntuaciones insertadas en la base de datos")

    return ((Pais.objects.count(), Cancion.objects.count(), Evento.objects.count(), Puntuacion.objects.count()))



#Le paso como parámetro
def crearWhoosh():
    
    canciones_whoosh = Schema(id=NUMERIC(stored=True), titulo=TEXT(stored=True), letra= TEXT(stored=True), 
    puntos= NUMERIC(stored=True), artista=TEXT(stored=True), pais = NUMERIC(stored=True), evento=NUMERIC(stored=True))

    if os.path.exists("Index"):
        shutil.rmtree("Index")
    os.mkdir("Index")

    ix = create_in("Index", schema=canciones_whoosh)
    writer = ix.writer()
    lista_canciones = Cancion.objects.all()

    for cancion in lista_canciones:
        writer.add_document(id=cancion.id, titulo=cancion.titulo,letra=cancion.letra,puntos=cancion.puntos,
        artista=cancion.artista,pais=cancion.pais.id,evento=cancion.evento.id)
    writer.commit()




#A CONTINUACIÓN SE DEJA EL SCRAPPING QUE INICIALMENTE HICE PARA LAS PUNTUACIONES, AUNQUE FINALMENTE DECIDÍ INVENTARLAS
#PARA EVITAR TANTA COMPLEJIDAD


    #for ev in eventos_canciones:
    #     eventos_canciones[ev] = [c for c in canciones2 if c.evento.anyo == ev.anyo]
    # print("Populando puntuaciones...") 
    # for an in anyos_lugares.keys():
    #     canciones_evento = eventos_canciones[Evento.objects.get(anyo=an)] #Cojo las canciones del año
    #     for c in canciones_evento:
    #         cancionobjid = c.id
    #         pais_cancion = c.pais.nombre #Obtengo el nombre del país de la canción
    #         pais_lower = pais_cancion.lower().replace(" ", "-")
    #         if pais_cancion == "Netherlands":
    #             pais_lower = "the-netherlands"
    #         elif pais_cancion == "North Macedonia":
    #             pais_lower = "fyr-macedonia"
    #         diccionario_semifinal = paises_semifinales[an]  #{anyo:{idsemifinal:[paises]}}
    #         if c.posicion < 27: #Si la posición es menor que 27 cojo las puntuaciones de la gran final
    #             enlace_puntuaciones = "https://eurovision.tv/event/" + anyos_lugares[an] + "-" + an + "/grand-final/results/" + pais_lower
    #         elif c.posicion >= 27 and pais_cancion in diccionario_semifinal[1]:
    #             enlace_puntuaciones = "https://eurovision.tv/event/" + anyos_lugares[an] + "-" + an + "/first-semi-final/results/" + pais_lower

    #         else: # si no se dan las anteriores, está en la semifinal dos
    #             enlace_puntuaciones = "https://eurovision.tv/event/" + anyos_lugares[an] + "-" + an + "/second-semi-final/results/" + pais_lower

    #             # resp4 = session.get(enlace_puntuaciones)
    #             # resp4.html.render(timeout=60)
    #         html4 = scrapingSelenium(enlace_puntuaciones, driver)
    #         s4 = BeautifulSoup(html4, "html.parser")
    #         puntuaciones_aux = s4.find_all("table", class_ = "w-full")
    #         tabla_jurado = puntuaciones_aux[1] #Cojo las puntuaciones de los jurados
    #         if len(puntuaciones_aux) == 3: #Falta la tabla del televoto, entonces la del jurado está en primera posición de la lista
    #             tabla_jurado = puntuaciones_aux[0]
    #         titulo_tabla = tabla_jurado.thead.tr.th.text.strip()
    #         puntuaciones = tabla_jurado.tbody.find_all("tr", class_="text-base")
    #         if titulo_tabla != "Points given by the jury": #Esto significa que sí obtuvo votos
    #             puntuacion_pais = 0
    #             for p in puntuaciones:
    #                 celdas = p.find_all("td")
    #                 if len(celdas) > 1: #Esto significa que una celda es para la puntuación y otra es para el nombre del país
    #                     puntuacion_pais = int(p.td.text.strip())
    #                     pais  = p.td.find_next_sibling().text.strip()
    #                 else:
    #                     pais = p.td.text.strip()
                        
    #                 paisobj = Pais.objects.get(nombre=pais)
    #                 punt = Puntuacion(id=pun,puntuacion=puntuacion_pais, id_pais=paisobj, id_cancion=c)
    #                 puntuaciones.append(punt)
    #                 pun += 1
    #                 print("El país " + pais + " ha dado " + str(puntuacion_pais) + " puntos al país " + nombre_pais)
    #             else:
    #                 print("Nadie ha votado a este país")