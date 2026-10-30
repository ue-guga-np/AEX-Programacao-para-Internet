from django.urls import path
from . import views

app_name = "estoque"

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("materiais/", views.lista_produtos, name="lista"),
    path("materiais/novo/", views.criar_produto, name="criar"),
    path("materiais/<int:pk>/editar/", views.editar_produto, name="editar"),
    path("materiais/<int:pk>/excluir/", views.excluir_produto, name="excluir"),
    path("materiais/<int:pk>/baixa/", views.baixa_estoque, name="baixa"),
    path("movimentacoes/", views.movimentacoes, name="movimentacoes"),
]
