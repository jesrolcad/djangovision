# Generated by Django 3.2.7 on 2022-01-14 18:24

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Cancion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo', models.CharField(max_length=40)),
                ('letra', models.TextField()),
                ('puntos', models.PositiveSmallIntegerField()),
                ('posicion', models.PositiveSmallIntegerField()),
                ('artista', models.CharField(max_length=40)),
            ],
            options={
                'ordering': ('titulo',),
            },
        ),
        migrations.CreateModel(
            name='Evento',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('anyo', models.PositiveSmallIntegerField()),
                ('lugar', models.CharField(max_length=25)),
                ('eslogan', models.CharField(max_length=20)),
            ],
            options={
                'ordering': ('anyo',),
            },
        ),
        migrations.CreateModel(
            name='Pais',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=25)),
                ('participaciones', models.PositiveSmallIntegerField()),
                ('victorias', models.PositiveSmallIntegerField()),
                ('ultima_posicion', models.PositiveSmallIntegerField()),
            ],
            options={
                'ordering': ('nombre',),
            },
        ),
        migrations.CreateModel(
            name='Puntuacion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('puntuacion', models.PositiveSmallIntegerField()),
                ('id_cancion', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='principal.cancion')),
                ('id_pais', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='principal.pais')),
            ],
            options={
                'ordering': ('id_pais', 'id_cancion'),
            },
        ),
        migrations.AddField(
            model_name='cancion',
            name='evento',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='canciones', to='principal.evento'),
        ),
        migrations.AddField(
            model_name='cancion',
            name='pais',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='canciones', to='principal.pais'),
        ),
        migrations.AddField(
            model_name='cancion',
            name='puntuaciones',
            field=models.ManyToManyField(through='principal.Puntuacion', to='principal.Pais'),
        ),
    ]