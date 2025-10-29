from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Q
from .models import Lote, ItemProducao, StatusInspecao

def verificar_maquinas_precisam_manutencao():
    """
    Retorna lista de máquinas que precisam manutenção
    (última manutenção há mais de 3 meses)
    """
    from .models import Maquina
    
    maquinas = Maquina.objects.all()
    maquinas_necessitam = []
    
    for maquina in maquinas:
        if maquina.precisa_manutencao():
            maquinas_necessitam.append(maquina)
    
    return maquinas_necessitam

def calcular_estatisticas_producao(data_inicio=None, data_fim=None, funcionario_id=None):
    """
    Calcula estatísticas de produção (aprovadas/reprovadas)
    
    Args:
        data_inicio: Data inicial para filtro (opcional)
        data_fim: Data final para filtro (opcional)
        funcionario_id: ID do funcionário inspetor (opcional)
    
    Returns:
        dict: Dicionário com estatísticas de peças e lotes
    """
    
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
    return {
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
            'data_inicio': str(data_inicio) if data_inicio else None,
            'data_fim': str(data_fim) if data_fim else None,
            'funcionario_id': funcionario_id
        }
    }

def filtrar_producao_reprovada(data_inicio=None, data_fim=None, maquina_id=None, categoria=None):
    """
    Filtra lotes de produção reprovada
    
    Args:
        data_inicio: Data inicial (opcional)
        data_fim: Data final (opcional)
        maquina_id: ID da máquina (opcional)
        categoria: Categoria do produto (opcional)
    
    Returns:
        QuerySet: Lotes reprovados filtrados
    """
    queryset = Lote.objects.filter(status_inspecao=StatusInspecao.REPROVADO)
    
    # Filtro por data de produção
    if data_inicio:
        queryset = queryset.filter(data_hora_inicio__gte=data_inicio)
    if data_fim:
        queryset = queryset.filter(data_hora_inicio__lte=data_fim)
    
    # Filtro por máquina
    if maquina_id:
        queryset = queryset.filter(itens_producao__maquina_id=maquina_id).distinct()
    
    # Filtro por categoria do produto
    if categoria:
        queryset = queryset.filter(produto__categoria=categoria)
    
    return queryset

def get_lotes_por_funcionario_inspecao(user):
    """
    Retorna lotes que o funcionário de inspeção pode visualizar:
    - Lotes não inspecionados (PENDENTE)
    - Lotes inspecionados por ele mesmo
    
    Args:
        user: Funcionário (usuário logado)
    
    Returns:
        QuerySet: Lotes filtrados
    """
    from .models import Cargo
    
    if user.cargo != Cargo.INSPECAO:
        return Lote.objects.all()
    
    return Lote.objects.filter(
        Q(status_inspecao=StatusInspecao.PENDENTE) | 
        Q(responsavel_inspecao=user)
    )

def validar_permissao_cargo(user, cargos_permitidos):
    """
    Valida se o usuário tem um dos cargos permitidos
    
    Args:
        user: Funcionário (usuário logado)
        cargos_permitidos: Lista de cargos permitidos
    
    Returns:
        bool: True se tem permissão, False caso contrário
    """
    from .models import Cargo
    
    if not user or not user.is_authenticated:
        return False
    
    if user.cargo == Cargo.ADMIN:
        return True
    
    return user.cargo in cargos_permitidos