# BS FastAPI CLI

Uma ferramenta CLI para gerar estruturas e código FastAPI automaticamente. Acelere seu desenvolvimento FastAPI com geração automática de modelos, schemas, routers e estrutura de projeto completa.

## Características

- ✅ **Inicialização de projeto completa** - Cria estrutura FastAPI organizada
- ✅ **Geração automática de modelos** - SQLAlchemy models com tipos customizados
- ✅ **Schemas Pydantic** - Validação automática com Create/Update/Response schemas
- ✅ **Routers FastAPI** - CRUD completo com paginação e autenticação
- ✅ **ORM operations** - Operações de banco de dados prontas para uso
- ✅ **Segurança integrada** - Autenticação JWT e hash de senhas
- ✅ **Conexão de banco** - Configuração SQLAlchemy com PostgreSQL/SQLite

## Instalação

```bash
pip install bs-fastapi-cli
```

## Uso Rápido

### 1. Inicializar um projeto

```bash
bs init --name "meu_projeto"
cd meu_projeto
```

Isso cria a seguinte estrutura:
```
meu_projeto/
├── main.py                    # Aplicação FastAPI principal
├── bs__connection/            # Configuração de banco de dados
│   ├── __init__.py
│   └── database.py
├── bs__security/              # Autenticação e segurança
│   ├── __init__.py
│   └── auth.py
├── models/                    # Modelos SQLAlchemy
│   └── __init__.py
├── schemas/                   # Schemas Pydantic
│   └── __init__.py
├── routers/                   # Routers FastAPI
│   └── __init__.py
└── orm/                       # Operações de banco
    └── __init__.py
```

### 2. Criar um modelo

```bash
bs create Usuario --fields "nome:str,email:str,idade:int,ativo:bool"
```

Isso gera automaticamente:
- `models/modelsUsuario.py` - Modelo SQLAlchemy
- `schemas/schemaUsuario.py` - Schemas Pydantic (Create/Update/Response)
- `routers/routeUsuario.py` - Router FastAPI com CRUD completo
- `orm/ormUsuario.py` - Operações de banco de dados

### 3. Instalar dependências e executar

```bash
pip install fastapi uvicorn sqlalchemy python-jose passlib bcrypt
uvicorn main:app --reload
```

## Comandos Disponíveis

### `bs init`

Inicializa uma nova estrutura de projeto FastAPI.

**Opções:**
- `-n, --name` - Nome do projeto (padrão: "fastapi_project")
- `-p, --path` - Caminho onde criar o projeto (padrão: ".")

**Exemplos:**
```bash
bs init --name "api_vendas"
bs init --name "blog_api" --path "./projetos"
```

### `bs create`

Cria um novo modelo com todos os arquivos associados.

**Parâmetros:**
- `MODEL_NAME` - Nome do modelo (obrigatório)

**Opções:**
- `-f, --fields` - Campos do modelo no formato "nome:tipo,nome:tipo"
- `-p, --path` - Caminho do projeto (padrão: ".")

**Tipos suportados:**
- `str` - String/Texto
- `int` - Número inteiro
- `bool` - Booleano (True/False)
- `text` - Texto longo
- `datetime` - Data e hora

**Exemplos:**
```bash
bs create Produto
bs create Cliente --fields "nome:str,email:str,telefone:str"
bs create Pedido --fields "total:int,data_criacao:datetime,ativo:bool,observacoes:text"
```

## Estrutura Gerada

### Modelo (SQLAlchemy)
```python
class Usuario(Base):
    __tablename__ = "usuarios"
    
    nome = Column(String, nullable=True)
    email = Column(String, nullable=True)
    idade = Column(Integer, nullable=True)
    ativo = Column(Boolean, default=False)
```

### Schema (Pydantic)
```python
class UsuarioCreate(UsuarioBase):
    nome: str  # Campo obrigatório
    
class UsuarioUpdate(UsuarioBase):
    pass
    
class UsuarioResponse(UsuarioInDB):
    pass
```

### Router (FastAPI)
```python
@router.post("/usuarios/", response_model=UsuarioResponse)
async def create_usuario(...)

@router.get("/usuarios/", response_model=UsuarioListResponse)
async def get_usuarios(...)

@router.get("/usuarios/{usuario_id}", response_model=UsuarioResponse)
async def get_usuario(...)

@router.put("/usuarios/{usuario_id}", response_model=UsuarioResponse)
async def update_usuario(...)

@router.delete("/usuarios/{usuario_id}")
async def delete_usuario(...)
```

## Configuração do Banco de Dados

O projeto gerado suporta PostgreSQL e SQLite através da variável de ambiente `DATABASE_URL`:

```bash
# PostgreSQL
export DATABASE_URL="postgresql://user:password@localhost/dbname"

# SQLite (padrão)
export DATABASE_URL="sqlite:///./app.db"
```

## Autenticação

O sistema de segurança inclui:
- Hash de senhas com bcrypt
- Tokens JWT para autenticação
- Middleware de segurança configurado
- Funções helper para autenticação

## Exemplos de Uso

### Projeto E-commerce
```bash
bs init --name "ecommerce_api"
cd ecommerce_api

bs create Produto --fields "nome:str,preco:int,descricao:text,ativo:bool"
bs create Cliente --fields "nome:str,email:str,telefone:str,data_cadastro:datetime"
bs create Pedido --fields "cliente_id:int,total:int,status:str,data_pedido:datetime"
```

### API de Blog
```bash
bs init --name "blog_api"
cd blog_api

bs create Post --fields "titulo:str,conteudo:text,publicado:bool,data_publicacao:datetime"
bs create Autor --fields "nome:str,email:str,bio:text,ativo:bool"
bs create Comentario --fields "post_id:int,autor:str,texto:text,aprovado:bool"
```

## Contribuição

Este projeto está em desenvolvimento ativo. Sugestões e contribuições são bem-vindas!

## Licença

MIT License
