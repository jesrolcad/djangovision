from django import forms
from principal.models import Pais, Evento
from django.core.validators import  MinValueValidator

class PaisForm(forms.Form):
    pais = forms.ModelChoiceField(label='Seleccione el país', queryset=Pais.objects.all())

class EventoForm(forms.Form):
    evento = forms.ModelChoiceField(label='Seleccione la edición de Eurovisión', queryset=Evento.objects.all())

class TextForm(forms.Form):
    busqueda = forms.CharField(label="Búsqueda por título", widget=forms.TextInput, required=True)

class EventoLetraForm(forms.Form):
    evento = forms.ModelChoiceField(label='Seleccione la edición de Eurovisión', queryset=Evento.objects.all())
    busqueda = forms.CharField(label="Busque por título o letra", widget=forms.TextInput, required=True)

class CancionesNPuntosForm(forms.Form):
    evento = forms.ModelChoiceField(label='Seleccione la edición de Eurovisión', queryset=Evento.objects.all())
    puntuacion = forms.IntegerField(label="Puntuación", widget=forms.TextInput, required=True, validators=[MinValueValidator(0)])

class CancionForm(forms.Form):
    cancion = forms.CharField(label="Id de la canción")