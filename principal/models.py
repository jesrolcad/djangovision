from django.db import models
from django.core.validators import  MinValueValidator

# Create your models here.

#El modelo País es sustitutivo del modelo "Usuario" en el sistema de recomendación
class Pais(models.Model):
    nombre = models.CharField(max_length=25)
    participaciones = models.PositiveSmallIntegerField()
    victorias = models.PositiveSmallIntegerField()
    ultima_posicion = models.PositiveSmallIntegerField()

    def __str__(self):
        return self.nombre

    class Meta:
        ordering = ('nombre',)

class Evento(models.Model):
    anyo = models.PositiveSmallIntegerField()
    lugar = models.CharField(max_length=25)
    eslogan = models.CharField(max_length=20)

    def __str__(self):
        return "Eurovision " + (str(self.anyo))

    class Meta:
        ordering = ('anyo',)

class Cancion(models.Model):
    titulo = models.CharField(max_length=40)
    letra = models.TextField()
    puntos = models.PositiveSmallIntegerField(validators=[MinValueValidator(0)])
    posicion = models.PositiveSmallIntegerField()
    artista = models.CharField(max_length=40) 
    pais = models.ForeignKey(Pais, on_delete=models.CASCADE, related_name="canciones")
    evento = models.ForeignKey(Evento, on_delete=models.CASCADE, related_name="canciones")
    puntuaciones = models.ManyToManyField(Pais, through='Puntuacion')

    def __str__(self):
        return self.titulo

    class Meta:
        ordering = ('evento',)

class Puntuacion(models.Model):
    puntuacion = models.PositiveSmallIntegerField()
    id_pais = models.ForeignKey(Pais, on_delete=models.SET_NULL, null=True)
    id_cancion = models.ForeignKey(Cancion, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return (str(self.puntuacion))

    class Meta:
        ordering = ('id_pais', 'id_cancion')