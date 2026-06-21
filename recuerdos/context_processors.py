from django.db.models.functions import ExtractYear

from .models import Categoria, Recuerdo


def nav_context(request):
    return {
        'categorias': Categoria.objects.all(),
        'anios': (
            Recuerdo.objects
            .annotate(anio=ExtractYear('fecha'))
            .values_list('anio', flat=True)
            .distinct()
            .order_by('-anio')
        ),
    }
