from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    FuncionarioViewSet, ProdutoViewSet, MaquinaViewSet,
    ManutencaoViewSet, LoteViewSet, ItemProducaoViewSet,
    DashboardViewSet
)

router = DefaultRouter()
router.register(r'funcionarios', FuncionarioViewSet, basename='funcionario')
router.register(r'produtos', ProdutoViewSet, basename='produto')
router.register(r'maquinas', MaquinaViewSet, basename='maquina')
router.register(r'manutencoes', ManutencaoViewSet, basename='manutencao')
router.register(r'lotes', LoteViewSet, basename='lote')
router.register(r'itens-producao', ItemProducaoViewSet, basename='itemproducao')
router.register(r'dashboard', DashboardViewSet, basename='dashboard')

urlpatterns = [
    path('', include(router.urls)),
]