"""
Dados de demonstração para a API Indústria 4.0.

    python manage.py seed_demo

Cria um funcionário por cargo (login = número de registro, senha ``demo1234``),
três produtos, três máquinas, duas manutenções, três lotes e os itens de produção
de cada lote, coerentes entre si: uma máquina com manutenção recente, uma com a
manutenção vencida (mais de 90 dias) e uma sem manutenção; um lote aprovado, um
reprovado e um pendente de inspeção.

Pode rodar quantas vezes quiser: cada registro é procurado pela sua chave
natural (número de registro, código, código identificador...) e atualizado em
vez de duplicado. É o que o start do Render faz a cada subida (render.yaml).

A senha é pública de propósito: estes usuários existem só para a demonstração.
"""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from somativa_app.models import (
    Cargo, Funcionario, ItemProducao, Lote, Manutencao, Maquina, Produto, StatusInspecao,
)

SENHA_DEMO = "demo1234"
REGISTRO_ADMIN = "demo"

# Um funcionário por cargo: (número de registro = login, nome, sobrenome).
# Cargo que não estiver aqui ganha "demo-<cargo>" automaticamente.
FUNCIONARIOS = {
    Cargo.ADMIN: (REGISTRO_ADMIN, "Ana", "Administradora"),
    Cargo.PRODUCAO: ("demo-producao", "Bruno", "Operador"),
    Cargo.LIDER_PRODUCAO: ("demo-lider", "Carla", "Líder"),
    Cargo.INSPECAO: ("demo-inspecao", "Diego", "Inspetor"),
    Cargo.MANUTENCAO: ("demo-manutencao", "Elisa", "Mecânica"),
}

# (código, nome, categoria, descrição)
PRODUTOS = [
    ("EX-020", "Eixo 20 mm", "Usinagem", "Eixo de aço SAE 1045, 20 mm de diâmetro, 300 mm de comprimento."),
    ("ENG-45", "Engrenagem 45 dentes", "Usinagem", "Engrenagem cilíndrica de dentes retos, módulo 2."),
    ("CX-RED", "Caixa de redução", "Montagem", "Conjunto montado: carcaça, dois eixos e três engrenagens."),
]

# (código identificador, nome, descrição) — a foto fica em branco.
MAQUINAS = [
    ("TOR-01", "Torno CNC", "Torno CNC de dois eixos para usinagem de eixos e buchas."),
    ("FRE-02", "Fresadora vertical", "Fresadora vertical com mesa de 1.200 mm e cabeçote de 7,5 cv."),
    ("PRE-03", "Prensa hidráulica", "Prensa hidráulica de 40 t para montagem por interferência."),
]

# (máquina, dias atrás, descrição). TOR-01 teve manutenção recente; FRE-02 há mais
# de 90 dias e PRE-03 nunca teve — as duas aparecem em maquinas/precisam_manutencao/.
MANUTENCOES = [
    ("TOR-01", 10, "Troca de óleo do cabeçote e ajuste das guias."),
    ("FRE-02", 120, "Substituição da correia do fuso e lubrificação geral."),
]

# (código, produto, dias atrás do início, horas até terminar ou None, status, máquina dos itens, nº de itens)
LOTES = [
    ("L-DEMO-001", "EX-020", 5, 8, StatusInspecao.APROVADO, "TOR-01", 5),
    ("L-DEMO-002", "ENG-45", 3, 8, StatusInspecao.REPROVADO, "FRE-02", 4),
    ("L-DEMO-003", "CX-RED", 1, None, StatusInspecao.PENDENTE, "PRE-03", 3),
]


def cpf_de_demonstracao(sequencia):
    """CPF formatado com dígitos verificadores válidos a partir de um número de 9 dígitos."""
    digitos = [int(d) for d in f"{sequencia:09d}"]
    for peso_inicial in (10, 11):
        soma = sum(d * p for d, p in zip(digitos, range(peso_inicial, 1, -1)))
        resto = (soma * 10) % 11
        digitos.append(0 if resto == 10 else resto)
    d = "".join(str(x) for x in digitos)
    return f"{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9:]}"


class Command(BaseCommand):
    help = "Cria (ou atualiza) os dados de demonstração: um funcionário por cargo, máquinas, manutenções, lotes e itens."

    @transaction.atomic
    def handle(self, *args, **opcoes):
        agora = timezone.now()
        hoje = timezone.localtime(agora).replace(hour=7, minute=0, second=0, microsecond=0)

        funcionarios, novos_funcionarios = self._funcionarios(hoje.date())
        produtos = self._produtos()
        maquinas = self._maquinas()
        manutencoes = self._manutencoes(agora, maquinas, funcionarios[Cargo.MANUTENCAO])
        lotes, itens = self._lotes(hoje, produtos, maquinas, funcionarios[Cargo.INSPECAO])

        self.stdout.write(
            f"Funcionários: {len(funcionarios)} ({novos_funcionarios} novos) · Produtos: {len(produtos)} · "
            f"Máquinas: {len(maquinas)} · Manutenções: {manutencoes} · Lotes: {len(lotes)} · Itens: {itens}"
        )
        outros = ", ".join(
            f"{registro} ({cargo.label})"
            for cargo, (registro, _, _) in FUNCIONARIOS.items() if cargo != Cargo.ADMIN
        )
        self.stdout.write(self.style.SUCCESS(
            f'Login da demonstração: numero_registro "{REGISTRO_ADMIN}" (ADMIN) e senha "{SENHA_DEMO}" '
            f"em POST /api/auth/jwt/create/. Os outros cargos: {outros} — todos com a senha {SENHA_DEMO}."
        ))

    def _funcionarios(self, data_base):
        por_cargo, novos = {}, 0
        for indice, cargo in enumerate(Cargo, start=1):
            registro, nome, sobrenome = FUNCIONARIOS.get(cargo) or (
                f"demo-{cargo.value.lower()}"[:20], "Demo", cargo.label,
            )
            e_admin = cargo == Cargo.ADMIN
            funcionario, criado = Funcionario.objects.update_or_create(
                numero_registro=registro,
                defaults={
                    "username": registro,
                    "email": f"{registro}@exemplo.com",
                    "cpf": cpf_de_demonstracao(900_000_000 + indice),
                    "first_name": nome,
                    "last_name": sobrenome,
                    "data_contratacao": data_base - timedelta(days=365 * indice),
                    "cargo": cargo,
                    "is_active": True,
                    # O ADMIN da demonstração também entra no /admin/.
                    "is_staff": e_admin,
                    "is_superuser": e_admin,
                },
            )
            if criado or not funcionario.check_password(SENHA_DEMO):
                funcionario.set_password(SENHA_DEMO)
                funcionario.save(update_fields=["password"])
            novos += int(criado)
            por_cargo[cargo] = funcionario
        return por_cargo, novos

    def _produtos(self):
        return {
            codigo: Produto.objects.update_or_create(
                codigo=codigo, defaults={"nome": nome, "categoria": categoria, "descricao": descricao},
            )[0]
            for codigo, nome, categoria, descricao in PRODUTOS
        }

    def _maquinas(self):
        return {
            codigo: Maquina.objects.update_or_create(
                codigo_identificador=codigo, defaults={"nome": nome, "descricao": descricao},
            )[0]
            for codigo, nome, descricao in MAQUINAS
        }

    def _manutencoes(self, agora, maquinas, responsavel):
        for codigo, dias, descricao in MANUTENCOES:
            Manutencao.objects.update_or_create(
                maquina=maquinas[codigo], descricao=descricao,
                defaults={"data_hora": agora - timedelta(days=dias), "funcionario_responsavel": responsavel},
            )
        return len(MANUTENCOES)

    def _lotes(self, hoje, produtos, maquinas, inspetor):
        lotes, total_itens = {}, 0
        for codigo, produto, dias, horas, status, maquina, quantidade in LOTES:
            inicio = hoje - timedelta(days=dias)
            inspecionado = status != StatusInspecao.PENDENTE
            lote, _ = Lote.objects.update_or_create(
                codigo=codigo,
                defaults={
                    "produto": produtos[produto],
                    "data_hora_inicio": inicio,
                    "data_hora_finalizacao": inicio + timedelta(hours=horas) if horas else None,
                    "status_inspecao": status,
                    "data_inspecao": (inicio + timedelta(days=1)).date() if inspecionado else None,
                    "responsavel_inspecao": inspetor if inspecionado else None,
                },
            )
            # Os itens só são criados quando o lote ainda não tem nenhum: rodar de
            # novo não duplica peças.
            if not lote.itens_producao.exists():
                ItemProducao.objects.bulk_create([
                    ItemProducao(lote=lote, maquina=maquinas[maquina], data_hora=inicio + timedelta(hours=1 + i))
                    for i in range(quantidade)
                ])
            total_itens += lote.itens_producao.count()
            lotes[codigo] = lote
        return lotes, total_itens
