from rest_framework import permissions
from .models import Cargo

class IsAdmin(permissions.BasePermission):
    """Apenas usuários ADMIN têm acesso"""
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.cargo == Cargo.ADMIN
        )

class IsProducao(permissions.BasePermission):
    """Apenas funcionários de PRODUÇÃO têm acesso"""
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.cargo in [Cargo.PRODUCAO, Cargo.LIDER_PRODUCAO, Cargo.ADMIN]
        )

class IsLiderProducao(permissions.BasePermission):
    """Apenas LIDER_PRODUCAO têm acesso"""
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.cargo in [Cargo.LIDER_PRODUCAO, Cargo.ADMIN]
        )

class IsInspecao(permissions.BasePermission):
    """Apenas funcionários de INSPEÇÃO têm acesso"""
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.cargo in [Cargo.INSPECAO, Cargo.ADMIN]
        )

class IsManutencao(permissions.BasePermission):
    """Apenas funcionários de MANUTENÇÃO têm acesso"""
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.cargo in [Cargo.MANUTENCAO, Cargo.ADMIN]
        )

class IsManutencaoOrReadOnly(permissions.BasePermission):
    """
    Funcionários de MANUTENÇÃO podem criar/editar.
    Outros podem apenas visualizar.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin pode tudo
        if request.user.cargo == Cargo.ADMIN:
            return True
        
        # GET, HEAD, OPTIONS são permitidos para todos autenticados
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # POST, PUT, PATCH, DELETE apenas para MANUTENÇÃO
        return request.user.cargo == Cargo.MANUTENCAO