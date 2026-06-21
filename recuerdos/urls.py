from django.urls import path
from . import views

urlpatterns = [
    path('', views.inicio, name='inicio'),  # Nuevo inicio
    path('inicio/', views.inicio),  # <--- esta línea nueva
    path('', views.lista_recuerdos, name='lista_recuerdos'),
    path('mapa/', views.mapa, name='mapa'),
    path('nuevo/', views.crear_recuerdo, name='crear_recuerdo'),
    path('editar/<int:pk>/', views.editar_recuerdo, name='editar_recuerdo'),
    path('eliminar/<int:pk>/', views.eliminar_recuerdo, name='eliminar_recuerdo'),
    path('exportar-pdf/', views.exportar_pdf, name='exportar_pdf'),
    path('exportar-pdf/categoria/<int:categoria_id>/', views.exportar_pdf_categoria, name='exportar_pdf_categoria'),
    path('exportar-pdf/anio/<int:anio>/', views.exportar_pdf_por_anio, name='exportar_pdf_anio'),
    path('recuerdo/<int:pk>/', views.detalle_recuerdo, name='detalle_recuerdo'),
    path('pagina-romantica/', views.pagina_romantica, name='pagina_romantica'),
    path('recuerdos/', views.lista_recuerdos, name='lista_recuerdos'),
    path("admin_oculto/", views.login_editor, name="login_editor"),
    path("editor_oculto/", views.editor_oculto, name="editor_oculto"),
    path("editor_oculto/subir-musica/", views.subir_musica, name="subir_musica"),
    path('corazones/', views.corazones_view, name='corazones'),
    path('favoritos/', views.recuerdos_favoritos, name='recuerdos_favoritos'),
    path('games/', views.games_view, name='games'),
    path('zona-zoro/', views.zona_zoro, name='zona_zoro'),
    path('rincon-pochacco/', views.rincon_pochacco, name='rincon_pochacco'),
    path('manifest.webmanifest', views.manifest, name='manifest'),
    path('service-worker.js', views.service_worker, name='service_worker'),
]