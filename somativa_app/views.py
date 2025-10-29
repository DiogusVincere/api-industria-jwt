from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count
from django.utils import timezone
from datetime import datetime, timedelta

from .models import (
    Funcionario, Produto, Maquina, Manutencao, 
    Lote, ItemProducao, StatusInspecao, Cargo
)
from .serializers import (
    FuncionarioSerializer, ProdutoSerializer, MaquinaSerializer,
    MaquinaDetalhadaSerializer, ManutencaoSerializer, LoteSerializer,
    LoteDetalhadoSerializer, ItemProducaoSerializer
)
from .permissions import (
    IsAdmin, IsProducao, IsLiderProducao, 
    IsInspecao, IsManutencao, IsManutencaoOrReadOnly
)

class FuncionarioViewSet(viewsets.ModelViewSet):
    queryset = Funcionario.objects.all()
    serializer_class = FuncionarioSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['numero_registro', 'first_name', 'last_name', 'email', 'cargo']
    ordering_fields = ['data_contratacao', 'cargo']

class ProdutoViewSet(viewsets.ModelViewSet):
    queryset = Produto.objects.all()
    serializer_class = ProdutoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['categoria', 'codigo']
    search_fields = ['nome', 'codigo', 'categoria']

class MaquinaViewSet(viewsets.ModelViewSet):
    queryset = Maquina.objects.all()
    permission_classes = [IsAuthenticated, IsManutencaoOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['codigo_identificador', 'nome']
    
    def get_serializer_class(self):
        if self.action == 'retrieve' or self.action == 'list':
            return MaquinaDetalhadaSerializer
        return MaquinaSerializer
    
    @action(detail=False, methods=['get'], permission_classes=[IsManutencao])
    def precisam_manutencao(self, request):
        """
        Endpoint que retorna máquinas que precisam de manutenção
        (última manutenção há mais de 3 meses)
        """
        maquinas = Maquina.objects.all()
        maquinas_necessitam = [m for m in maquinas if m.precisa_manutencao()]
        serializer = self.get_serializer(maquinas_necessitam, many=True)
        return Response(serializer.data)

class ManutencaoViewSet(viewsets.ModelViewSet):
    queryset = Manutencao.objects.all()
    serializer_class = ManutencaoSerializer
    permission_classes = [IsAuthenticated, IsManutencaoOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['maquina', 'funcionario_responsavel']
    ordering_fields = ['data_hora']
    ordering = ['-data_hora']

class LoteViewSet(viewsets.ModelViewSet):
    queryset = Lote.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['produto', 'status_inspecao']
    search_fields = ['codigo']
    ordering_fields = ['data_hora_inicio', 'data_inspecao']
    ordering = ['-data_hora_inicio']
    
    def get_serializer_class(self):
        if self.action == 'retrieve' or self.action == 'list':
            return LoteDetalhadoSerializer
        return LoteSerializer
    
    def get_permissions(self):
        """Define permissões baseadas na ação"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            # Apenas funcionários de produção podem criar/editar lotes
            permission_classes = [IsAuthenticated, IsProducao]
        elif self.action == 'nao_inspecionados':
            permission_classes = [IsAuthenticated, IsInspecao]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Filtro personalizado para funcionários de inspeção"""
        queryset = Lote.objects.all()
        user = self.request.user
        
        # Funcionários de inspeção veem apenas não inspecionados ou inspecionados por eles
        if user.cargo == Cargo.INSPECAO:
            queryset = queryset.filter(
                Q(status_inspecao=StatusInspecao.PENDENTE) | 
                Q(responsavel_inspecao=user)
            )
        
        return queryset
    
    @action(detail=False, methods=['get'], permission_classes=[IsInspecao])
    def nao_inspecionados(self, request):
        """Retorna apenas lotes pendentes de inspeção"""
        lotes = Lote.objects.filter(status_inspecao=StatusInspecao.PENDENTE)
        serializer = self.get_serializer(lotes, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def producao_reprovada(self, request):
        """
        Filtrar produção reprovada por:
        - data_inicio e data_fim (range de datas)
        - maquina (opcional)
        - categoria (opcional)
        """
        queryset = Lote.objects.filter(status_inspecao=StatusInspecao.REPROVADO)
        
        # Filtro por data de produção
        data_inicio = request.query_params.get('data_inicio')
        data_fim = request.query_params.get('data_fim')
        
        if data_inicio:
            queryset = queryset.filter(data_hora_inicio__gte=data_inicio)
        if data_fim:
            queryset = queryset.filter(data_hora_inicio__lte=data_fim)
        
        # Filtro por máquina
        maquina_id = request.query_params.get('maquina')
        if maquina_id:
            queryset = queryset.filter(itens_producao__maquina_id=maquina_id).distinct()
        
        # Filtro por categoria do produto
        categoria = request.query_params.get('categoria')
        if categoria:
            queryset = queryset.filter(produto__categoria=categoria)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class ItemProducaoViewSet(viewsets.ModelViewSet):
    queryset = ItemProducao.objects.all()
    serializer_class = ItemProducaoSerializer
    permission_classes = [IsAuthenticated, IsProducao]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['lote', 'maquina']
    ordering_fields = ['data_hora']
    ordering = ['-data_hora']

class DashboardViewSet(viewsets.ViewSet):
    """
    Endpoint de dashboard acessível apenas para líderes de produção
    Mostra quantidade de peças aprovadas e reprovadas
    Permite filtrar por data (range) e por funcionário inspetor
    """
    permission_classes = [IsAuthenticated, IsLiderProducao]
    
    @action(detail=False, methods=['get'])
    def estatisticas(self, request):
        """
        Retorna estatísticas de produção
        Parâmetros:
        - data_inicio: data inicial (formato: YYYY-MM-DD)
        - data_fim: data final (formato: YYYY-MM-DD)
        - funcionario: ID do funcionário inspetor (opcional)
        """
        # Pega os parâmetros
        data_inicio = request.query_params.get('data_inicio')
        data_fim = request.query_params.get('data_fim')
        funcionario_id = request.query_params.get('funcionario')
        
        # Query base - conta itens de produção
        queryset_aprovados = ItemProducao.objects.filter(
            lote__status_inspecao=StatusInspecao.APROVADO
        )
        queryset_reprovados = ItemProducao.objects.filter(
            lote__status_inspecao=StatusInspecao.REPROVADO
        )
        
        # Filtro por data
        if data_inicio:
            queryset_aprovados = queryset_aprovados.filter(data_hora__gte=data_inicio)
            queryset_reprovados = queryset_reprovados.filter(data_hora__gte=data_inicio)
        
        if data_fim:
            queryset_aprovados = queryset_aprovados.filter(data_hora__lte=data_fim)
            queryset_reprovados = queryset_reprovados.filter(data_hora__lte=data_fim)
        
        # Filtro por funcionário inspetor
        if funcionario_id:
            queryset_aprovados = queryset_aprovados.filter(
                lote__responsavel_inspecao_id=funcionario_id
            )
            queryset_reprovados = queryset_reprovados.filter(
                lote__responsavel_inspecao_id=funcionario_id
            )
        
        # Conta as peças
        total_aprovadas = queryset_aprovados.count()
        total_reprovadas = queryset_reprovados.count()
        total_geral = total_aprovadas + total_reprovadas
        
        # Calcula percentuais
        percentual_aprovadas = (
            (total_aprovadas / total_geral * 100) if total_geral > 0 else 0
        )
        percentual_reprovadas = (
            (total_reprovadas / total_geral * 100) if total_geral > 0 else 0
        )
        
        # Estatísticas por lote
        lotes_aprovados = Lote.objects.filter(
            status_inspecao=StatusInspecao.APROVADO
        )
        lotes_reprovados = Lote.objects.filter(
            status_inspecao=StatusInspecao.REPROVADO
        )
        
        if data_inicio:
            lotes_aprovados = lotes_aprovados.filter(data_hora_inicio__gte=data_inicio)
            lotes_reprovados = lotes_reprovados.filter(data_hora_inicio__gte=data_inicio)
        
        if data_fim:
            lotes_aprovados = lotes_aprovados.filter(data_hora_inicio__lte=data_fim)
            lotes_reprovados = lotes_reprovados.filter(data_hora_inicio__lte=data_fim)
        
        if funcionario_id:
            lotes_aprovados = lotes_aprovados.filter(
                responsavel_inspecao_id=funcionario_id
            )
            lotes_reprovados = lotes_reprovados.filter(
                responsavel_inspecao_id=funcionario_id
            )
        
        total_lotes_aprovados = lotes_aprovados.count()
        total_lotes_reprovados = lotes_reprovados.count()
        
        # Monta resposta
        data = {
            'pecas': {
                'aprovadas': total_aprovadas,
                'reprovadas': total_reprovadas,
                'total': total_geral,
                'percentual_aprovadas': round(percentual_aprovadas, 2),
                'percentual_reprovadas': round(percentual_reprovadas, 2)
            },
            'lotes': {
                'aprovados': total_lotes_aprovados,
                'reprovados': total_lotes_reprovados,
                'total': total_lotes_aprovados + total_lotes_reprovados
            },
            'filtros_aplicados': {
                'data_inicio': data_inicio,
                'data_fim': data_fim,
                'funcionario_id': funcionario_id
            }
        }
        
        return Response(data)