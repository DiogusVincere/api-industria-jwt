from rest_framework import serializers
from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer
from djoser.serializers import UserSerializer as BaseUserSerializer
from .models import (
    Funcionario, Produto, Maquina, Manutencao, 
    Lote, ItemProducao, StatusInspecao, Cargo
)

# Serializadores para Funcionário (Usuário customizado)
class FuncionarioCreateSerializer(BaseUserCreateSerializer):
    """Serializer para criar funcionário com Djoser"""
    class Meta(BaseUserCreateSerializer.Meta):
        model = Funcionario
        fields = [
            'id', 'username', 'numero_registro', 'email', 'cpf', 
            'first_name', 'last_name', 'data_contratacao', 'cargo', 'password'
        ]
        extra_kwargs = {
            'password': {'write_only': True}
        }

class FuncionarioSerializer(BaseUserSerializer):
    """Serializer para exibir funcionário"""
    cargo_display = serializers.CharField(source='get_cargo_display', read_only=True)
    nome_completo = serializers.SerializerMethodField()
    
    class Meta(BaseUserSerializer.Meta):
        model = Funcionario
        fields = [
            'id', 'username', 'numero_registro', 'email', 'cpf', 
            'first_name', 'last_name', 'nome_completo', 
            'data_contratacao', 'cargo', 'cargo_display'
        ]
    
    def get_nome_completo(self, obj):
        return obj.get_full_name()

# Serializadores para Produto
class ProdutoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Produto
        fields = ['id', 'nome', 'codigo', 'descricao', 'categoria']

# Serializadores para Manutenção
class ManutencaoSerializer(serializers.ModelSerializer):
    funcionario_nome = serializers.CharField(
        source='funcionario_responsavel.get_full_name', 
        read_only=True
    )
    funcionario_registro = serializers.CharField(
        source='funcionario_responsavel.numero_registro',
        read_only=True
    )
    
    class Meta:
        model = Manutencao
        fields = [
            'id', 'maquina', 'data_hora', 'descricao', 
            'funcionario_responsavel', 'funcionario_nome', 'funcionario_registro'
        ]

class ManutencaoCreateSerializer(serializers.ModelSerializer):
    """Serializer para criar manutenção - automaticamente pega o usuário logado"""
    class Meta:
        model = Manutencao
        fields = ['id', 'maquina', 'data_hora', 'descricao']
    
    def create(self, validated_data):
        # Pega o usuário logado automaticamente
        validated_data['funcionario_responsavel'] = self.context['request'].user
        return super().create(validated_data)

# Serializadores para Máquina
class MaquinaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Maquina
        fields = ['id', 'codigo_identificador', 'foto', 'nome', 'descricao']

class MaquinaDetalhadaSerializer(serializers.ModelSerializer):
    manutencoes = ManutencaoSerializer(many=True, read_only=True)
    precisa_manutencao = serializers.SerializerMethodField()
    
    class Meta:
        model = Maquina
        fields = [
            'id', 'codigo_identificador', 'foto', 'nome', 
            'descricao', 'manutencoes', 'precisa_manutencao'
        ]
    
    def get_precisa_manutencao(self, obj):
        return obj.precisa_manutencao()

# Serializadores para Item de Produção
class ItemProducaoSerializer(serializers.ModelSerializer):
    maquina_codigo = serializers.CharField(source='maquina.codigo_identificador', read_only=True)
    maquina_nome = serializers.CharField(source='maquina.nome', read_only=True)
    
    class Meta:
        model = ItemProducao
        fields = ['id', 'lote', 'data_hora', 'maquina', 'maquina_codigo', 'maquina_nome']

# Serializadores para Lote
class LoteSerializer(serializers.ModelSerializer):
    status_inspecao_display = serializers.CharField(
        source='get_status_inspecao_display', 
        read_only=True
    )
    produto_nome = serializers.CharField(source='produto.nome', read_only=True)
    produto_codigo = serializers.CharField(source='produto.codigo', read_only=True)
    
    class Meta:
        model = Lote
        fields = [
            'id', 'codigo', 'produto', 'produto_nome', 'produto_codigo',
            'data_hora_inicio', 'data_hora_finalizacao', 
            'data_inspecao', 'responsavel_inspecao', 
            'status_inspecao', 'status_inspecao_display'
        ]

class LoteDetalhadoSerializer(serializers.ModelSerializer):
    status_inspecao_display = serializers.CharField(
        source='get_status_inspecao_display', 
        read_only=True
    )
    produto = ProdutoSerializer(read_only=True)
    responsavel_inspecao_nome = serializers.CharField(
        source='responsavel_inspecao.get_full_name',
        read_only=True,
        allow_null=True
    )
    responsavel_inspecao_registro = serializers.CharField(
        source='responsavel_inspecao.numero_registro',
        read_only=True,
        allow_null=True
    )
    itens_producao = ItemProducaoSerializer(many=True, read_only=True)
    total_itens = serializers.SerializerMethodField()
    
    class Meta:
        model = Lote
        fields = [
            'id', 'codigo', 'produto', 
            'data_hora_inicio', 'data_hora_finalizacao', 
            'data_inspecao', 'responsavel_inspecao', 
            'responsavel_inspecao_nome', 'responsavel_inspecao_registro',
            'status_inspecao', 'status_inspecao_display',
            'itens_producao', 'total_itens'
        ]
    
    def get_total_itens(self, obj):
        return obj.itens_producao.count()