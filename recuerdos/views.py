from django.shortcuts import render, redirect
from .models import Recuerdo, Categoria
import folium
from .forms import RecuerdoForm
from django.shortcuts import get_object_or_404
from django.db.models.functions import ExtractYear
from django.contrib.auth.decorators import user_passes_test

#PARA EXPORTAR A PDF
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from django.http import HttpResponse
from reportlab.lib.utils import ImageReader
from django.conf import settings
from django.template.loader import render_to_string
from django.views.decorators.cache import cache_control
from django.templatetags.static import static
import os
import random

from .blessings import BENDICIONES
from datetime import date

from django.utils.html import escape
from datetime import datetime
from collections import defaultdict
import json
from django.core.serializers.json import DjangoJSONEncoder
from django import template
register = template.Library()

def check_password(request):
    return request.session.get('editor_autorizado', False)

def login_editor(request):
    error = None
    if request.method == "POST":
        if request.POST.get("password") == settings.EDITOR_PASSWORD:
            request.session['editor_autorizado'] = True
            return redirect("editor_oculto")
        else:
            error = "Contraseña incorrecta"
    return render(request, "editor/login_editor.html", {"error": error})

@user_passes_test(check_password)
def editor_oculto(request):
    recuerdos = Recuerdo.objects.all().order_by("-fecha")
    return render(request, "editor/panel.html", {"recuerdos": recuerdos})

@user_passes_test(check_password)
def subir_musica(request):
    mensaje = ""
    if not settings.DEBUG:
        mensaje = "Subida de música deshabilitada en producción."
        return render(request, "editor/subir_musica.html", {"mensaje": mensaje})
    if request.method == "POST" and request.FILES.get("archivo"):
        archivo = request.FILES["archivo"]
        ruta = os.path.join(settings.BASE_DIR, "static/musica", archivo.name)
        with open(ruta, "wb+") as destino:
            for chunk in archivo.chunks():
                destino.write(chunk)
        mensaje = "Música subida correctamente."
    return render(request, "editor/subir_musica.html", {"mensaje": mensaje})

def inicio(request):
    recuerdos = Recuerdo.objects.all().order_by('-fecha')[:12]

    datos_mapa = [
        {
            'id': r.id,
            'titulo': escape(r.titulo),
            'descripcion': escape(r.descripcion[:80] + "...") if r.descripcion else "",
            'fecha': r.fecha.strftime('%d %b %Y'),
            'latitud': r.latitud,
            'longitud': r.longitud,
            'imagen': request.build_absolute_uri(r.imagen.url) if r.imagen else ''
        }
        for r in recuerdos if r.latitud and r.longitud
    ]

    # Bendición del día: misma para todos
    dia = date.today().toordinal()
    bendicion = BENDICIONES[dia % len(BENDICIONES)]

    return render(request, 'recuerdos/inicio.html', {
        'recuerdos': recuerdos,
        'datos_mapa': datos_mapa,
        'bendicion': bendicion,
    })


def editar_recuerdo(request, pk):
    recuerdo = get_object_or_404(Recuerdo, pk=pk)
    if request.method == 'POST':
        form = RecuerdoForm(request.POST, request.FILES, instance=recuerdo)
        if form.is_valid():
            form.save()
            return redirect('lista_recuerdos')
    else:
        form = RecuerdoForm(instance=recuerdo)
    return render(request, 'recuerdos/editar.html', {'form': form, 'recuerdo': recuerdo})

def eliminar_recuerdo(request, pk):
    recuerdo = get_object_or_404(Recuerdo, pk=pk)
    if request.method == 'POST':
        recuerdo.delete()
        return redirect('lista_recuerdos')
    return render(request, 'recuerdos/eliminar.html', {'recuerdo': recuerdo})


def mapa(request):
    recuerdos = Recuerdo.objects.all()
    datos = [
        {
            "titulo": r.titulo,
            "fecha": r.fecha.strftime("%d %b %Y"),
            "latitud": r.latitud,
            "longitud": r.longitud
        } for r in recuerdos if r.latitud and r.longitud
    ]
    return render(request, 'recuerdos/mapa.html', {"recuerdos": datos})

def crear_recuerdo(request):
    if request.method == 'POST':
        form = RecuerdoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('lista_recuerdos')
    else:
        form = RecuerdoForm()
    return render(request, 'recuerdos/crear.html', {'form': form})

def lista_recuerdos(request):
    recuerdos = Recuerdo.objects.all().order_by('-fecha')
    categorias = Categoria.objects.all()
    anios = Recuerdo.objects.annotate(anio=ExtractYear('fecha')).values_list('anio', flat=True).distinct()
    return render(request, 'recuerdos/lista.html', {
        'recuerdos': recuerdos,
        'categorias': categorias,
        'anios': anios
    })


def detalle_recuerdo(request, pk):
    recuerdo = get_object_or_404(Recuerdo, pk=pk)
    return render(request, 'recuerdos/detalle_recuerdo.html', {'recuerdo': recuerdo})


#====================================
#====================================
#====================================
#====================================
#====================================
def games_view(request):
    return render(request, 'recuerdos/games.html') 
#EXPORTACIÓN A PDF

def exportar_pdf(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="recuerdos_bonitos.pdf"'

    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter
    y = height - 80

    p.setFont("Helvetica-Bold", 24)
    p.drawCentredString(width / 2, y, "Nuestros Recuerdos 💞")
    y -= 40

    recuerdos = Recuerdo.objects.all().order_by('-fecha')

    for r in recuerdos:
        if y < 200:
            p.showPage()
            y = height - 80

        p.setFont("Helvetica-Bold", 16)
        p.drawString(50, y, f"{r.fecha.strftime('%d/%m/%Y')} – {r.titulo}")
        y -= 20

        if r.categoria:
            p.setFont("Helvetica-Oblique", 12)
            p.drawString(60, y, f"Categoría: {r.categoria.nombre}")
            y -= 15

        p.setFont("Helvetica", 12)
        desc_lines = r.descripcion.splitlines()
        for line in desc_lines:
            p.drawString(60, y, line)
            y -= 15

        # Agrega la imagen si existe
        if r.imagen:
            imagen_path = os.path.join(settings.MEDIA_ROOT, r.imagen.name)
            if os.path.exists(imagen_path):
                try:
                    image = ImageReader(imagen_path)
                    img_width = 200
                    img_height = 150
                    p.drawImage(image, 60, y - img_height, width=img_width, height=img_height)
                    y -= img_height + 20
                except:
                    y -= 10
        else:
            y -= 10

        y -= 30  # Espacio extra

    p.showPage()
    p.save()

    return response

def exportar_pdf_categoria(request, categoria_id):
    categoria = get_object_or_404(Categoria, pk=categoria_id)
    recuerdos = Recuerdo.objects.filter(categoria=categoria).order_by('-fecha')

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="recuerdos_{categoria.nombre}.pdf"'

    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter
    y = height - 80

    p.setFont("Helvetica-Bold", 22)
    p.drawCentredString(width / 2, y, f"Recuerdos: {categoria.nombre}")
    y -= 40

    for r in recuerdos:
        if y < 200:
            p.showPage()
            y = height - 80

        p.setFont("Helvetica-Bold", 14)
        p.drawString(50, y, f"{r.fecha.strftime('%d/%m/%Y')} – {r.titulo}")
        y -= 20

        p.setFont("Helvetica", 12)
        for line in r.descripcion.splitlines():
            p.drawString(60, y, line)
            y -= 15

        y -= 30

    p.showPage()
    p.save()
    return response

def exportar_pdf_por_anio(request, anio):
    recuerdos = Recuerdo.objects.filter(fecha__year=anio).order_by('-fecha')

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="recuerdos_{anio}.pdf"'

    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter
    y = height - 80

    p.setFont("Helvetica-Bold", 22)
    p.drawCentredString(width / 2, y, f"Recuerdos del año {anio} 📅")
    y -= 40

    for r in recuerdos:
        if y < 200:
            p.showPage()
            y = height - 80

        p.setFont("Helvetica-Bold", 14)
        p.drawString(50, y, f"{r.fecha.strftime('%d/%m/%Y')} – {r.titulo}")
        y -= 20

        p.setFont("Helvetica", 12)
        for line in r.descripcion.splitlines():
            p.drawString(60, y, line)
            y -= 15

        y -= 30

    p.showPage()
    p.save()
    return response


#=========================================
#=========================================
#=========================================
#=========================================
#=========================================
#=========================================
#=========================================

# MÓDULO 2

def pagina_romantica(request):
    recuerdos = Recuerdo.objects.all().order_by('fecha')
    recuerdos_por_dia = defaultdict(list)
    for r in recuerdos:
        recuerdos_por_dia[r.fecha.day].append(r)

    dias_del_mes = range(1, 32)  # ejemplo mes de 31 días
    dias_con_recuerdo = set(recuerdo.fecha.day for recuerdo in recuerdos)

    context = {
        'recuerdos': recuerdos,
        'recuerdos_por_dia': recuerdos_por_dia,
        'dias_del_mes': dias_del_mes,
        'dias_con_recuerdo': dias_con_recuerdo,
    }
    return render(request, 'recuerdos/romantica.html', context)

def romantica(request):
    recuerdos_galeria = Recuerdo.objects.all().order_by('?')[:6]
    recuerdos_timeline = Recuerdo.objects.exclude(fecha__isnull=True).order_by('fecha')
    return render(request, 'recuerdos/romantica.html', {
        'recuerdos': recuerdos_galeria,
        'eventos': recuerdos_timeline,
        'mensaje': "Tu mensaje aquí"
    })

def galeria_polaroid(request):
    recuerdos = Recuerdo.objects.all().order_by('-fecha')
    return render(request, 'galeria_polaroid.html', {'recuerdos': recuerdos})

def corazones_view(request):
    return render(request, 'recuerdos/corazones.html')

#=========================================
#=========================================
#=========================================
#=========================================
#=========================================
#=========================================
#=========================================


def recuerdos_favoritos(request):
    recuerdos = Recuerdo.objects.all()  # ¡Importante: TODOS!
    return render(request, 'recuerdos/favoritos.html', {'recuerdos': recuerdos})


def zona_zoro(request):
    frases = [
        "Solo un tonto muere sin pelear.",
        "Prometí que nunca perdería de nuevo.",
        "No me importa si muero, mientras cumpla mi promesa.",
        "Los verdaderos hombres no rompen sus palabras.",
        "Puedo soportar el dolor, pero no fallarte a ti."
    ]
    return render(request, 'recuerdos/zona_zoro.html', {'frases': frases})

def rincon_pochacco(request):
    return render(request, 'recuerdos/rincon_pochacco.html')


def _pwa_context():
    return {
        'icon_192': static('img/icon-192.png'),
        'icon_512': static('img/icon-512.png'),
        'css_url': static('css/style.css'),
        'fondo_url': static('img/fondo_pochacco.jpg'),
        'pochacco_url': static('img/pochacco_face.jpg'),
    }


@cache_control(max_age=0, no_cache=True, no_store=True, must_revalidate=True)
def service_worker(request):
    content = render_to_string('service-worker.js', _pwa_context(), request=request)
    return HttpResponse(content, content_type='application/javascript')


def manifest(request):
    content = render_to_string('manifest.webmanifest', _pwa_context(), request=request)
    return HttpResponse(content, content_type='application/manifest+json')
