"""
Testes da demonstração pública: documentação interativa (drf-spectacular),
comando seed_demo, login JWT dos usuários demo e a restrição do cadastro aberto.

    python manage.py test
"""
import json
from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APIClient

from .models import Cargo, Funcionario, ItemProducao, Lote, Manutencao, Maquina, Produto

SENHA_DEMO = "demo1234"
SENHA_FORTE = "Trocar-Esta-Senha-2026"


def rodar_seed():
    saida = StringIO()
    call_command("seed_demo", stdout=saida)
    return saida.getvalue()


def token_de(client, numero_registro, senha=SENHA_DEMO):
    resposta = client.post(
        "/api/auth/jwt/create/", {"numero_registro": numero_registro, "password": senha}, format="json",
    )
    assert resposta.status_code == 200, resposta.content
    return resposta.data["access"]


class DocumentacaoTests(TestCase):
    def test_raiz_redireciona_para_o_swagger(self):
        resposta = self.client.get("/")
        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(resposta["Location"], "/api/docs/")

    def test_swagger_e_redoc_sao_publicos(self):
        for rota in ("/api/docs/", "/api/redoc/"):
            with self.subTest(rota=rota):
                resposta = self.client.get(rota)
                self.assertEqual(resposta.status_code, 200)
                self.assertIn("API Indústria 4.0", resposta.content.decode("utf-8"))

    def test_schema_descreve_a_api_e_o_jwt(self):
        resposta = self.client.get("/api/schema/?format=json")
        self.assertEqual(resposta.status_code, 200)
        esquema = json.loads(resposta.content)
        self.assertEqual(esquema["info"]["title"], "API Indústria 4.0")
        for rota in (
            "/api/lotes/", "/api/lotes/producao_reprovada/", "/api/maquinas/precisam_manutencao/",
            "/api/dashboard/estatisticas/", "/api/auth/jwt/create/", "/api/auth/users/me/",
        ):
            self.assertIn(rota, esquema["paths"])
        self.assertIn("jwtAuth", esquema["components"]["securitySchemes"])


class SeedDemoTests(TestCase):
    def contagens(self):
        return (
            Funcionario.objects.count(), Produto.objects.count(), Maquina.objects.count(),
            Manutencao.objects.count(), Lote.objects.count(), ItemProducao.objects.count(),
        )

    def test_cria_os_dados_e_rodar_de_novo_nao_duplica(self):
        saida = rodar_seed()
        primeira = self.contagens()
        self.assertEqual(primeira, (len(Cargo), 3, 3, 2, 3, 12))
        self.assertIn("demo1234", saida)
        rodar_seed()
        self.assertEqual(self.contagens(), primeira)

    def test_um_funcionario_por_cargo_com_a_senha_demo(self):
        rodar_seed()
        self.assertEqual(set(Funcionario.objects.values_list("cargo", flat=True)), set(Cargo.values))
        demo = Funcionario.objects.get(numero_registro="demo")
        self.assertEqual(demo.cargo, Cargo.ADMIN)
        self.assertTrue(demo.check_password(SENHA_DEMO))
        self.assertTrue(demo.is_staff and demo.is_superuser)


class FluxoDaDemonstracaoTests(TestCase):
    def setUp(self):
        rodar_seed()
        self.client = APIClient()

    def test_sem_token_a_api_responde_401(self):
        self.assertEqual(self.client.get("/api/maquinas/").status_code, 401)

    def test_demo_entra_e_usa_os_endpoints_autenticados(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token_de(self.client, 'demo')}")

        eu = self.client.get("/api/auth/users/me/")
        self.assertEqual(eu.status_code, 200)
        self.assertEqual(eu.data["numero_registro"], "demo")

        maquinas = self.client.get("/api/maquinas/")
        self.assertEqual(maquinas.status_code, 200)
        self.assertEqual(maquinas.data["count"], 3)

        precisam = self.client.get("/api/maquinas/precisam_manutencao/")
        self.assertEqual(sorted(m["codigo_identificador"] for m in precisam.data), ["FRE-02", "PRE-03"])

        estatisticas = self.client.get("/api/dashboard/estatisticas/")
        self.assertEqual(estatisticas.status_code, 200)
        self.assertEqual(estatisticas.data["pecas"]["aprovadas"], 5)
        self.assertEqual(estatisticas.data["pecas"]["reprovadas"], 4)
        self.assertEqual(estatisticas.data["lotes"], {"aprovados": 1, "reprovados": 1, "total": 2})

    def test_cargo_operacional_entra_e_respeita_as_permissoes(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token_de(self.client, 'demo-producao')}")
        self.assertEqual(self.client.get("/api/lotes/").status_code, 200)
        self.assertEqual(self.client.get("/api/dashboard/estatisticas/").status_code, 403)
        self.assertEqual(self.client.get("/api/funcionarios/").status_code, 403)


class CadastroDjoserTests(TestCase):
    def dados(self, cargo, registro, cpf):
        return {
            "username": registro, "numero_registro": registro, "email": f"{registro}@exemplo.com",
            "cpf": cpf, "first_name": "Novo", "last_name": "Funcionário", "data_contratacao": "2026-01-05",
            "cargo": cargo, "password": SENHA_FORTE, "re_password": SENHA_FORTE,
        }

    def test_cadastro_aberto_nao_cria_admin(self):
        resposta = APIClient().post(
            "/api/auth/users/", self.dados(Cargo.ADMIN, "novo-admin", "111.222.333-44"), format="json",
        )
        self.assertEqual(resposta.status_code, 400, resposta.content)
        self.assertIn("cargo", resposta.data)
        self.assertFalse(Funcionario.objects.filter(numero_registro="novo-admin").exists())

    def test_cadastro_aberto_cria_os_cargos_operacionais(self):
        resposta = APIClient().post(
            "/api/auth/users/", self.dados(Cargo.PRODUCAO, "novo-prod", "111.222.333-55"), format="json",
        )
        self.assertEqual(resposta.status_code, 201, resposta.content)
        self.assertEqual(Funcionario.objects.get(numero_registro="novo-prod").cargo, Cargo.PRODUCAO)

    def test_admin_autenticado_cria_outro_admin(self):
        rodar_seed()
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token_de(client, 'demo')}")
        resposta = client.post(
            "/api/auth/users/", self.dados(Cargo.ADMIN, "novo-admin", "111.222.333-66"), format="json",
        )
        self.assertEqual(resposta.status_code, 201, resposta.content)
        self.assertEqual(Funcionario.objects.get(numero_registro="novo-admin").cargo, Cargo.ADMIN)
