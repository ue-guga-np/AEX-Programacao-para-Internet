# Gerenciador de Estoque — Marcenaria

Sistema web de controle de estoque de materiais para marcenaria, desenvolvido com Django, SQLite, Pandas e interface visual personalizada conforme a especificação de requisitos e modelagem UML da AEX (Engenharia de Software II e Programação para a Internet).

## Requisitos
- Python 3.10 ou superior
- pip

## Executar no Windows
Abra o terminal nesta pasta e execute:

```bat
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

> Se o comando `python` não for reconhecido, tente `py`.
> Durante o `createsuperuser`, defina o usuário e a senha de administrador.
> Um usuário comum padrão de teste (**operador** / senha: **operador123**) é criado automaticamente.

### Perfis de Acesso
- **🔨 Usuário Comum (Operador / Marceneiro):**
  - **Usuário:** `operador` | **Senha:** `operador123`
  - Permissões: Consulta de catálogo, foto de insumos, Dar Baixa (retirada) e Adicionar Saldo (entrada), histórico de movimentações e exportação de planilha para conferência.
  - Bloqueios: Não pode cadastrar, editar ou excluir materiais, não pode gerenciar categorias/unidades e não pode importar backups.
- **👑 Administrador (Gestor):**
  - Criado pelo comando `createsuperuser`.
  - Permissões: Acesso irrestrito a todas as operações, cadastros, exclusões, gerenciamento de classificações e backups.

Abra o navegador em:
- **Login do Sistema:** http://127.0.0.1:8000/login/
- **Painel do Sistema:** http://127.0.0.1:8000/
- **Catálogo de Materiais:** http://127.0.0.1:8000/materiais/
- **Categorias e Unidades (Admin):** http://127.0.0.1:8000/classificacoes/
- **Backups e Planilhas Excel (Admin):** http://127.0.0.1:8000/backups/
- **Área Administrativa (Django Admin):** http://127.0.0.1:8000/admin/

## Acessar de outro computador na mesma rede

1. No computador que executa o sistema, descubra o IPv4 com `ipconfig` (Windows) ou `ip a` (Linux).
2. Inicie o servidor com:

   ```bat
   python manage.py runserver 0.0.0.0:8000
   ```

3. No outro computador na mesma rede local, abra `http://IP-DO-COMPUTADOR:8000/`.

## Funcionalidades Implementadas (Conforme PDF da AEX)

- **Identificação Visual por Foto (US01, US08, RF01, RF07):**
  - Anexo de fotos no cadastro e na edição do material.
  - Seleção interativa na tabela: ao clicar em qualquer produto, sua foto é renderizada instantaneamente no painel lateral na proporção correta, ou exibe o selo "Sem Imagem".
  - Miniaturas na tabela e no Django Admin para rápida distinção visual.
  - Limpeza automática de arquivos de imagens órfãs ao excluir um material (RN04).
- **Baixa Rápida e Aumento de Saldo (US05, US06, RF04, RF05, RF10):**
  - **Valores Inteiros**: Operações de entrada e retirada aceitam estritamente números inteiros sem casas decimais.
  - **Dar Baixa (Saída)**: Permite retirar do estoque com trava de saldo (RN02), impedindo valores negativos ou superiores ao disponível.
  - **Adicionar Saldo (Entrada)**: Permite registrar novas compras e chegadas de insumos diretamente pelo painel.
  - **Atalhos Rápidos**: Botões `1`, `5`, `10`, `Tudo` (para baixa) e `+1`, `+5`, `+10`, `+50` (para entrada) para preenchimento ágil.
  - Gravação automática no histórico de auditoria de `MovimentacaoEstoque`.
- **Cadastro Dinâmico de Categorias e Unidades (US03, US04, Quadro 6 2.a.1):**
  - Botões `＋ Nova Categoria` e `＋ Nova Unidade` integrados no formulário de cadastro, permitindo cadastrar novas classificações via janela modal sem sair da página e selecionando-as automaticamente.
- **Relatórios em Planilha Excel (US09, RF08):**
  - Exportação para `.xlsx` formatado usando a biblioteca **Pandas** e **OpenPyXL**, com colunas limpas para cotação e contabilidade (Produto, Categoria, Unidade, Qtd Atual, Qtd Mínima, Status).
  - Importação de planilha Excel para carga e atualização em lote.
- **Cópias de Segurança / Backups (US10, RF09, RNF04):**
  - Exportação de pacote completo `.zip` contendo o banco de dados `db.sqlite3` e a pasta de fotos `media/`.
  - Importação e restauração de backup com caixa de diálogo e confirmação explícita para prevenir perda acidental de dados.
- **Gestão de Alertas e Criticidade (US07, RN03):**
  - Destaque em linha avermelhada e ordenação prioritária no topo da lista para itens com estoque igual ou abaixo do mínimo de segurança ou marcados com urgência manual.
