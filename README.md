# Gerenciador de Estoque — Marcenaria

Sistema web para controle básico de materiais de uma marcenaria, desenvolvido com **Python, Django e SQLite**.

O projeto pode ser executado localmente em outro computador, desde que ele tenha Python instalado e que as etapas deste README sejam seguidas. Não é necessário copiar o banco de dados do computador de quem desenvolveu o sistema: o banco SQLite será criado no primeiro uso das migrações.

## Funcionalidades

- Painel inicial com total de materiais, alertas de estoque crítico e últimas movimentações.
- Cadastro, consulta, edição, exclusão e busca de materiais.
- Categorias e unidades de medida iniciais cadastradas automaticamente.
- Alerta visual quando a quantidade está no limite mínimo ou quando o item é marcado como urgente.
- Registro de retirada (baixa), impedindo retirada maior que o saldo disponível.
- Histórico de movimentações.
- Área administrativa Django em `/admin/` para gerenciar categorias, unidades, produtos e movimentações.

## Requisitos para executar em outro computador

- Windows, Linux ou macOS.
- Python **3.10 ou superior** instalado.
- Conexão com a internet na primeira instalação, para baixar o Django.
- Git é opcional. Também é possível baixar o projeto em ZIP.

> No Windows, durante a instalação do Python, marque a opção **Add Python to PATH**. Depois, abra um novo terminal e confira a instalação com `python --version`. Em alguns computadores, o comando pode ser `py --version`.

## Instalação e execução no Windows

### 1. Baixar e extrair o projeto

Baixe o ZIP do projeto e extraia a pasta `gerenciador_estoque_django` em um local de sua preferência.

### 2. Abrir o terminal na pasta do projeto

Abra a pasta `gerenciador_estoque_django`, clique na barra de endereço do Explorador de Arquivos, digite `cmd` e pressione Enter. O terminal deve abrir dentro da pasta onde está o arquivo `manage.py`.

### 3. Criar e ativar o ambiente virtual

Execute um comando por vez:

```bat
python -m venv .venv
.venv\Scripts\activate
```

Se o computador não reconhecer `python`, tente substituir por `py` no primeiro comando.

### 4. Instalar as dependências

```bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 5. Criar o banco de dados

```bat
python manage.py migrate
```

Esse comando cria o arquivo `db.sqlite3` e prepara as tabelas necessárias. As categorias e unidades de medida iniciais são cadastradas automaticamente. Não é necessário executar `makemigrations` para a instalação normal, pois as migrações do projeto já estão incluídas nos arquivos.

### 6. Iniciar o sistema

```bat
python manage.py runserver
```

Abra o navegador e acesse:

- Sistema: http://127.0.0.1:8000/
- Administração: http://127.0.0.1:8000/admin/

Para encerrar o servidor, volte ao terminal e pressione `Ctrl + C`.

### 7. Acesso à área administrativa (opcional)

Se precisar acessar o `/admin/`, crie um usuário administrador com:

```bat
python manage.py createsuperuser
```

Siga as perguntas do terminal e depois entre em http://127.0.0.1:8000/admin/ com os dados criados.

## Instalação no Linux ou macOS

Na pasta do projeto, abra o terminal e execute:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Acesse http://127.0.0.1:8000/ no navegador. Para criar um administrador, execute `python manage.py createsuperuser`.

## Como testar em outro computador

1. Baixe uma cópia nova do projeto em outro computador.
2. Siga as etapas de instalação deste README desde a criação do ambiente virtual.
3. Execute `python manage.py migrate` e depois `python manage.py runserver`.
4. Abra http://127.0.0.1:8000/ e teste o cadastro e a listagem de materiais.
5. Cadastre um material de teste, edite-o, registre uma retirada e confira o histórico.

Se essas etapas funcionarem em um computador que ainda não tinha o projeto configurado, isso demonstra que a instalação não depende do ambiente de desenvolvimento original.

## Acesso por outro computador na mesma rede (opcional)

Se a intenção for acessar o servidor de um computador diferente, mas conectado à mesma rede Wi-Fi ou cabeada, no computador que executa o sistema inicie o servidor assim:

```bat
python manage.py runserver 0.0.0.0:8000
```

Descubra o endereço IPv4 desse computador com `ipconfig`. No outro computador, abra `http://IP-DO-COMPUTADOR:8000/`, substituindo pelo IPv4 encontrado. O computador servidor precisa permanecer ligado, com o terminal aberto. Talvez seja necessário permitir o acesso na Firewall do Windows.

> O acesso pela rede local é opcional. Para a avaliação de execução em outro computador, cada integrante também pode instalar e executar sua própria cópia localmente, acessando `http://127.0.0.1:8000/`.

## Solução de problemas

- **`python` não é reconhecido:** instale o Python e marque `Add Python to PATH`; depois feche e abra o terminal novamente. No Windows, tente usar `py` no lugar de `python`.
- **`No module named django`:** confira se o ambiente virtual está ativado e execute `python -m pip install -r requirements.txt`.
- **A página não abre:** confira se o comando `runserver` continua em execução no terminal e se o endereço digitado é `http://127.0.0.1:8000/`.
- **A porta 8000 já está em uso:** execute `python manage.py runserver 8001` e acesse `http://127.0.0.1:8001/`.
- **Problemas com o banco de dados em uma instalação nova:** pare o servidor e execute `python manage.py migrate` novamente.

## Telas principais

1. **Início (`/`)**: resumo do estoque e atalhos.
2. **Materiais (`/materiais/`)**: listagem, pesquisa e ações de gerenciamento.
3. **Cadastro/edição (`/materiais/novo/` e `/materiais/<id>/editar/`)**: formulário de produtos.
4. **Movimentações (`/movimentacoes/`)**: histórico de retiradas.
5. **Baixa (`/materiais/<id>/baixa/`)**: registro de retirada de material.

## Limitações conhecidas desta primeira versão

- O registro de movimentação implementado pela interface é de saída/retirada; o cadastro de entradas ainda não está disponível como operação própria.
- Não há exportação para Excel, anexos/fotos de materiais nem rotina de backup/restauração pela interface.
- A exclusão de materiais com movimentações é bloqueada para preservar o histórico.
- O projeto usa SQLite, adequado para protótipo e demonstração acadêmica.
- O servidor de desenvolvimento do Django é destinado a desenvolvimento e demonstração, não à publicação direta na internet.

## Integrantes

- Anna Flávia Guenta Tsurushima
- Gustavo Alexandro Pelissari
- Letícia Aparecida Fernandes
- Mário Francisco da Silva
- Pedro Henrique Camargo de Lima
