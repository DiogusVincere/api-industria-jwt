# API Indústria 4.0 (Django REST + JWT)

API para controle de chão de fábrica: funcionários com cargos, produtos, máquinas e manutenções, lotes de produção com inspeção de qualidade e um dashboard de peças aprovadas e reprovadas, tudo autenticado por token JWT.

## Funcionalidades

Lidas de `somativa_app/models.py`, `views.py`, `permissions.py` e `urls.py`:

- **Funcionário é o usuário do sistema** (`Funcionario` estende `AbstractUser`): entra com o **número de registro** e tem CPF, data de contratação e cargo.
- **Cargos e permissões**: `PRODUCAO`, `LIDER_PRODUCAO`, `INSPECAO`, `MANUTENCAO` e `ADMIN`. O ADMIN pode tudo; os demais só o que o cargo permite (tabela abaixo).
- **Produtos**: cadastro com código único, categoria e descrição; filtro por `categoria` e `codigo`, busca por nome.
- **Máquinas**: cadastro com foto opcional; a listagem traz as manutenções e o campo `precisa_manutencao` (sem manutenção ou última há mais de 90 dias); rota extra `precisam_manutencao/`.
- **Manutenções**: registro por máquina, com data/hora, descrição e funcionário responsável; filtro por máquina e responsável.
- **Lotes de produção**: código, produto, início/fim; **inspeção** por `PATCH` (status `PENDENTE`/`APROVADO`/`REPROVADO`, data e responsável). O inspetor só enxerga lotes pendentes ou inspecionados por ele. Rotas extras `nao_inspecionados/` e `producao_reprovada/` (filtros por período, máquina e categoria).
- **Itens de produção**: cada peça produzida, ligada ao lote e à máquina que a produziu.
- **Dashboard** (líder de produção): `dashboard/estatisticas/` conta peças e lotes aprovados e reprovados, com percentuais e filtros por período e inspetor.
- Paginação de 20 itens, filtros (`django-filter`), busca e ordenação em todas as listas; admin do Django com todos os modelos.

| Recurso | Leitura | Criar / editar / apagar |
|---------|---------|-------------------------|
| `funcionarios` | ADMIN | ADMIN |
| `produtos` | qualquer autenticado | qualquer autenticado |
| `maquinas`, `manutencoes` | qualquer autenticado | MANUTENCAO (e ADMIN) |
| `lotes` | autenticado (inspetor vê só os seus) | PRODUCAO, LIDER_PRODUCAO (e ADMIN) |
| `lotes/nao_inspecionados/` | INSPECAO (e ADMIN) | — |
| `itens-producao` | PRODUCAO, LIDER_PRODUCAO, ADMIN | idem |
| `dashboard/estatisticas/` | LIDER_PRODUCAO (e ADMIN) | — |

## Autenticação: como obter o token JWT

O login é feito com `numero_registro` e `password` nas rotas do Djoser em `/api/auth/`:

```http
POST /api/auth/jwt/create/
Content-Type: application/json

{"numero_registro": "1001", "password": "sua-senha"}
```

Resposta: `{"access": "<token de acesso, vale 1 hora>", "refresh": "<token de renovação, vale 1 dia>"}`.
Nas demais chamadas envie o cabeçalho `Authorization: Bearer <access>`.

| Método | Rota | Corpo | O que faz |
|--------|------|-------|-----------|
| POST | `/api/auth/jwt/create/` | `{"numero_registro", "password"}` | gera `access` e `refresh` |
| POST | `/api/auth/jwt/refresh/` | `{"refresh": "..."}` | novo `access` (o refresh rotaciona) |
| POST | `/api/auth/jwt/verify/` | `{"token": "..."}` | confirma se o token vale |
| POST | `/api/auth/users/` | `{"username", "numero_registro", "email", "cpf", "first_name", "last_name", "data_contratacao", "cargo", "password", "re_password"}` | cadastra funcionário |
| GET | `/api/auth/users/me/` | — | dados do funcionário logado |

Atenção: a rota de cadastro do Djoser é aberta por padrão e aceita o campo `cargo`, inclusive `ADMIN`. Para uso fora de sala de aula, restrinja esse cadastro (por exemplo, só ADMIN cria funcionários).

## Endpoints da API

Base: `/api/`. Todas exigem `Authorization: Bearer <access>`. Listas aceitam `?page=`, `?search=` e `?ordering=`.

| Método | Rota | Corpo de exemplo |
|--------|------|------------------|
| GET / POST | `funcionarios/` | igual ao cadastro do Djoser |
| GET / PUT / PATCH / DELETE | `funcionarios/{id}/` | — |
| GET / POST | `produtos/` (`?categoria=`, `?codigo=`) | `{"nome": "Eixo 20mm", "codigo": "EX-020", "descricao": "Eixo de aço", "categoria": "Usinagem"}` |
| GET / PUT / PATCH / DELETE | `produtos/{id}/` | — |
| GET / POST | `maquinas/` | `{"codigo_identificador": "TOR-01", "nome": "Torno CNC", "descricao": "Torno de bancada"}` (foto opcional, multipart) |
| GET / PUT / PATCH / DELETE | `maquinas/{id}/` | — |
| GET | `maquinas/precisam_manutencao/` | — (cargo MANUTENCAO) |
| GET / POST | `manutencoes/` (`?maquina=`, `?funcionario_responsavel=`) | `{"maquina": 1, "data_hora": "2025-06-10T08:00:00", "descricao": "Troca de óleo", "funcionario_responsavel": 3}` |
| GET / PUT / PATCH / DELETE | `manutencoes/{id}/` | — |
| GET / POST | `lotes/` (`?produto=`, `?status_inspecao=`) | `{"codigo": "L-2025-001", "produto": 1, "data_hora_inicio": "2025-06-10T07:00:00", "data_hora_finalizacao": "2025-06-10T15:00:00"}` |
| PATCH | `lotes/{id}/` (inspeção) | `{"data_inspecao": "2025-06-11", "responsavel_inspecao": 4, "status_inspecao": "APROVADO"}` |
| GET | `lotes/nao_inspecionados/` | — (cargo INSPECAO) |
| GET | `lotes/producao_reprovada/?data_inicio=&data_fim=&maquina=&categoria=` | — |
| GET / POST | `itens-producao/` (`?lote=`, `?maquina=`) | `{"lote": 1, "data_hora": "2025-06-10T09:30:00", "maquina": 1}` |
| GET / PUT / PATCH / DELETE | `itens-producao/{id}/` | — |
| GET | `dashboard/estatisticas/?data_inicio=AAAA-MM-DD&data_fim=AAAA-MM-DD&funcionario=` | — (cargo LIDER_PRODUCAO) |

A coleção do Postman em `docs/` tem todas essas chamadas prontas (variáveis `base_url`, `access_token` e `refresh_token`), inclusive uma pasta de setup que cria um usuário de cada cargo.

## Estrutura

```
somativa/            projeto Django (settings.py lê tudo do ambiente; urls.py monta /api/, /api/auth/ e /admin/)
somativa_app/        app: models, serializers, views (ViewSets), permissions (por cargo), utils, admin, migrations
docs/                coleção do Postman "Sistema Indústria 4.0 - JWT"
requirements.txt     Django, DRF, SimpleJWT, Djoser, django-filter, django-cors-headers, Pillow
.env.example         variáveis de ambiente documentadas
```

## Como rodar

Pré-requisito: Python 3.10 ou mais novo.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate      Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
```

As configurações vêm de variáveis de ambiente (ver `.env.example`). O projeto não carrega `.env` sozinho: exporte as variáveis no terminal ou use a ferramenta de sua preferência.

```bash
# Windows (PowerShell):  $env:DEBUG = "True"
# Linux/macOS:           export DEBUG=True
python manage.py migrate
python manage.py createsuperuser      # pede número de registro, e-mail, nome e senha
python manage.py runserver
```

Depois crie os funcionários de cada cargo pelo admin (`/admin/`) ou pela pasta "Setup" da coleção do Postman, e gere o token em `/api/auth/jwt/create/`.

Sem `SECRET_KEY` definida, o Django gera uma chave aleatória a cada inicialização e os tokens JWT emitidos antes deixam de valer. Em produção defina `SECRET_KEY`, `DEBUG=False` e `ALLOWED_HOSTS`.

## Demonstração

<!-- prints: adicionar -->

## Licença

MIT — ver [LICENSE](LICENSE).
