from django.urls import path
from . import views

# Define o nome do app para que os links e redirecionamentos funcionem.
app_name = "estoque"

# Rotas do sistema de controle de estoque da marcenaria.
urlpatterns = [
    # Autenticação e Perfis (Administrador e Operador)
    path("login/", views.fazer_login, name="login"),
    path("logout/", views.fazer_logout, name="logout"),

    # Visão Geral e Catálogo
    path("", views.inicio, name="inicio"),
    path("materiais/", views.lista_produtos, name="lista"),
    path("materiais/novo/", views.criar_produto, name="criar"),
    path("materiais/<int:pk>/editar/", views.editar_produto, name="editar"),
    path("materiais/<int:pk>/baixa/", views.baixa_estoque, name="baixa"),
    path("materiais/<int:pk>/baixa-rapida/", views.baixa_rapida, name="baixa_rapida"),
    path("materiais/<int:pk>/adicionar-saldo/", views.adicionar_saldo, name="adicionar_saldo"),
    path("materiais/<int:pk>/excluir/", views.excluir_produto, name="excluir"),
    path("movimentacoes/", views.movimentacoes, name="movimentacoes"),

    # Gerenciamento de Categorias e Unidades de Medida (US03 / US04 / Quadro 8)
    path("classificacoes/", views.gerenciar_classificacoes, name="classificacoes"),
    path("classificacoes/categoria/nova/", views.criar_categoria, name="criar_categoria"),
    path("classificacoes/categoria/<int:pk>/editar/", views.editar_categoria, name="editar_categoria"),
    path("classificacoes/categoria/<int:pk>/excluir/", views.excluir_categoria, name="excluir_categoria"),
    path("classificacoes/unidade/nova/", views.criar_unidade, name="criar_unidade"),
    path("classificacoes/unidade/<int:pk>/editar/", views.editar_unidade, name="editar_unidade"),
    path("classificacoes/unidade/<int:pk>/excluir/", views.excluir_unidade, name="excluir_unidade"),

    # APIs para criação dinâmica de categorias e unidades no formulário de produtos
    path("api/categorias/nova/", views.criar_categoria_ajax, name="api_criar_categoria"),
    path("api/unidades/nova/", views.criar_unidade_ajax, name="api_criar_unidade"),

    # Backups e Planilhas Excel
    path("backups/", views.painel_backups, name="painel_backups"),
    path("exportar/excel/", views.exportar_excel, name="exportar_excel"),
    path("importar/excel/", views.importar_excel, name="importar_excel"),
    path("backups/exportar/", views.exportar_backup, name="exportar_backup"),
    path("backups/importar/", views.importar_backup, name="importar_backup"),
]
