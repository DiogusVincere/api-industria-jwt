from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    Funcionario, Produto, Maquina, Manutencao, 
    Lote, ItemProducao
)

@admin.register(Funcionario)
class FuncionarioAdmin(UserAdmin):
    model = Funcionario
    list_display = ['numero_registro', 'get_full_name', 'email', 'cargo', 'data_contratacao']
    list_filter = ['cargo', 'data_contratacao', 'is_staff', 'is_superuser']
    search_fields = ['numero_registro', 'first_name', 'last_name', 'email', 'cpf']
    ordering = ['numero_registro']

    fieldsets = (
        (None, {'fields': ('numero_registro', 'email', 'password')}),
        ('Informações Pessoais', {'fields': ('first_name', 'last_name', 'cpf', 'data_contratacao', 'cargo')}),
        ('Permissões', {'fields': ('is_staff', 'is_superuser', 'is_active', 'groups', 'user_permissions')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('numero_registro', 'email', 'first_name', 'last_name', 'cpf', 'data_contratacao', 'cargo', 'password1', 'password2', 'is_staff', 'is_superuser')}
        ),
    )

@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nome', 'categoria']
    list_filter = ['categoria']
    search_fields = ['codigo', 'nome', 'categoria']

@admin.register(Maquina)
class MaquinaAdmin(admin.ModelAdmin):
    list_display = ['codigo_identificador', 'nome']
    search_fields = ['codigo_identificador', 'nome']

class ManutencaoInline(admin.TabularInline):
    model = Manutencao
    extra = 0
    fields = ['data_hora', 'descricao', 'funcionario_responsavel']

@admin.register(Manutencao)
class ManutencaoAdmin(admin.ModelAdmin):
    list_display = ['maquina', 'data_hora', 'funcionario_responsavel']
    list_filter = ['data_hora', 'maquina']
    search_fields = ['maquina__codigo_identificador', 'descricao']
    date_hierarchy = 'data_hora'

class ItemProducaoInline(admin.TabularInline):
    model = ItemProducao
    extra = 0
    fields = ['data_hora', 'maquina']

@admin.register(Lote)
class LoteAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'produto', 'status_inspecao', 'data_hora_inicio', 'responsavel_inspecao']
    list_filter = ['status_inspecao', 'data_hora_inicio', 'produto__categoria']
    search_fields = ['codigo', 'produto__nome']
    date_hierarchy = 'data_hora_inicio'
    inlines = [ItemProducaoInline]

@admin.register(ItemProducao)
class ItemProducaoAdmin(admin.ModelAdmin):
    list_display = ['id', 'lote', 'maquina', 'data_hora']
    list_filter = ['data_hora', 'maquina']
    search_fields = ['lote__codigo', 'maquina__codigo_identificador']
    date_hierarchy = 'data_hora'