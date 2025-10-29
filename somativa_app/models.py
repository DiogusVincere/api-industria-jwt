from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import validate_email

class FuncionarioManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, numero_registro, email, password=None, **extra_fields):
        if not numero_registro:
            raise ValueError('O número de registro é obrigatório')
        if not email:
            raise ValueError('O email é obrigatório')

        email = self.normalize_email(email)
        user = self.model(numero_registro=numero_registro, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, numero_registro, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        # Para compatibilidade, define username como número de registro
        extra_fields.setdefault('username', numero_registro)

        # Forçar data_contratacao para evitar erro NOT NULL
        if 'data_contratacao' not in extra_fields:
           from datetime import date
           extra_fields['data_contratacao'] = date.today()

        if extra_fields.get('is_staff') is not True:
            raise ValueError('O superusuário deve ter is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('O superusuário deve ter is_superuser=True.')

        return self.create_user(numero_registro, email, password, **extra_fields)

class Cargo(models.TextChoices):
    PRODUCAO = 'PRODUCAO', 'Produção'
    LIDER_PRODUCAO = 'LIDER_PRODUCAO', 'Líder de Produção'
    INSPECAO = 'INSPECAO', 'Inspeção'
    MANUTENCAO = 'MANUTENCAO', 'Manutenção'
    ADMIN = 'ADMIN', 'Administrador'

class Funcionario(AbstractUser):
    username = models.CharField(max_length=150, blank=True, null=True)
    numero_registro = models.CharField(max_length=20, unique=True)
    cpf = models.CharField(max_length=14, unique=True)
    data_contratacao = models.DateField()
    cargo = models.CharField(max_length=20, choices=Cargo.choices)
    
    # Sobrescrever campos necessários do AbstractUser
    email = models.EmailField(unique=True, validators=[validate_email])
    
    USERNAME_FIELD = 'numero_registro'
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name']
    
    objects = FuncionarioManager()  # certifique-se de registrar o manager

    class Meta:
        verbose_name = 'Funcionário'
        verbose_name_plural = 'Funcionários'
    
    def __str__(self):
        return f"{self.get_full_name()} - {self.numero_registro}"

class Produto(models.Model):
    nome = models.CharField(max_length=200)
    codigo = models.CharField(max_length=50, unique=True)
    descricao = models.TextField()
    categoria = models.CharField(max_length=100)
    
    class Meta:
        verbose_name = 'Produto'
        verbose_name_plural = 'Produtos'
    
    def __str__(self):
        return f"{self.codigo} - {self.nome}"

class Maquina(models.Model):
    codigo_identificador = models.CharField(max_length=50, unique=True)
    foto = models.ImageField(upload_to='maquinas/', null=True, blank=True)
    nome = models.CharField(max_length=200)
    descricao = models.TextField()
    
    class Meta:
        verbose_name = 'Máquina'
        verbose_name_plural = 'Máquinas'
    
    def __str__(self):
        return f"{self.codigo_identificador} - {self.nome}"
    
    def precisa_manutencao(self):
        """Verifica se a máquina precisa de manutenção (última há mais de 3 meses)"""
        from django.utils import timezone
        from datetime import timedelta
        
        ultima_manutencao = self.manutencoes.order_by('-data_hora').first()
        if not ultima_manutencao:
            return True
        
        tres_meses_atras = timezone.now() - timedelta(days=90)
        return ultima_manutencao.data_hora < tres_meses_atras

class Manutencao(models.Model):
    maquina = models.ForeignKey(Maquina, on_delete=models.CASCADE, related_name='manutencoes')
    data_hora = models.DateTimeField()
    descricao = models.TextField()
    funcionario_responsavel = models.ForeignKey(
        Funcionario, 
        on_delete=models.PROTECT, 
        related_name='manutencoes_realizadas'
    )
    
    class Meta:
        verbose_name = 'Manutenção'
        verbose_name_plural = 'Manutenções'
        ordering = ['-data_hora']
    
    def __str__(self):
        return f"Manutenção {self.maquina.codigo_identificador} - {self.data_hora}"

class StatusInspecao(models.TextChoices):
    PENDENTE = 'PENDENTE', 'Pendente'
    APROVADO = 'APROVADO', 'Aprovado'
    REPROVADO = 'REPROVADO', 'Reprovado'

class Lote(models.Model):
    codigo = models.CharField(max_length=50, unique=True)
    produto = models.ForeignKey(Produto, on_delete=models.PROTECT, related_name='lotes')
    data_hora_inicio = models.DateTimeField()
    data_hora_finalizacao = models.DateTimeField(null=True, blank=True)
    data_inspecao = models.DateField(null=True, blank=True)
    responsavel_inspecao = models.ForeignKey(
        Funcionario, 
        on_delete=models.PROTECT, 
        related_name='lotes_inspecionados',
        null=True,
        blank=True
    )
    status_inspecao = models.CharField(
        max_length=20, 
        choices=StatusInspecao.choices,
        default=StatusInspecao.PENDENTE
    )
    
    class Meta:
        verbose_name = 'Lote'
        verbose_name_plural = 'Lotes'
    
    def __str__(self):
        return f"Lote {self.codigo}"

class ItemProducao(models.Model):
    lote = models.ForeignKey(Lote, on_delete=models.CASCADE, related_name='itens_producao')
    data_hora = models.DateTimeField()
    maquina = models.ForeignKey(Maquina, on_delete=models.PROTECT, related_name='itens_produzidos')
    
    class Meta:
        verbose_name = 'Item de Produção'
        verbose_name_plural = 'Itens de Produção'
        ordering = ['data_hora']
    
    def __str__(self):
        return f"Item {self.id} - Lote {self.lote.codigo}"