"""
URL configuration for mdx_project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('game.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

admin.site.site_header = "Mermãs Digitais | MDX 2026 • Painel do Operador"
admin.site.site_title = "MDX 2026 Admin"
admin.site.index_title = "Gestão dos Desafios e Tentativas das Alunas"

