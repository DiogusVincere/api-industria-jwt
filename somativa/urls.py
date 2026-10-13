"""
Rotas do projeto somativa (API Indústria 4.0).

/                 redireciona para a documentação interativa
/api/docs/        Swagger UI
/api/redoc/       ReDoc
/api/schema/      esquema OpenAPI 3 (JSON/YAML)
/api/             endpoints da aplicação (somativa_app/urls.py)
/api/auth/        Djoser: cadastro, usuário atual e tokens JWT
/admin/           admin do Django
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    path('', RedirectView.as_view(url='/api/docs/', permanent=False), name='inicio'),
    path('admin/', admin.site.urls),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('api/', include('somativa_app.urls')),
    path('api/auth/', include('djoser.urls')),
    path('api/auth/', include('djoser.urls.jwt')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
