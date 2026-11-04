from django.urls import path

from . import views

# Define o nome do app para que os links e redirecionamentos funcionem.
app_name = "estoque"

# Rotas do sistema de controle de estoque.
urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("materiais/", views.lista_produtos, name="lista"),
    path("materiais/novo/", views.criar_produto, name="criar"),
    path("materiais/<int:pk>/editar/", views.editar_produto, name="editar"),
    path("materiais/<int:pk>/baixa/", views.baixa_estoque, name="baixa"),
    path("materiais/<int:pk>/excluir/", views.excluir_produto, name="excluir"),
    path("movimentacoes/", views.movimentacoes, name="movimentacoes"),
]
