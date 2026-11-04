from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from .forms import ProdutoForm, BaixaEstoqueForm
from .models import Produto, MovimentacaoEstoque

# Página inicial com resumo geral do sistema e visão rápida do estoque.
def inicio(request):
    produtos = Produto.objects.all()
    context = {
        "total_produtos": produtos.count(),
        "total_alertas": sum(1 for p in produtos if p.estoque_critico),
        "ultimas_movimentacoes": MovimentacaoEstoque.objects.select_related("produto")[:5],
    }
    return render(request, "estoque/inicio.html", context)

# Lista e busca dos produtos cadastrados, com ordenação por alerta de estoque.
def lista_produtos(request):
    termo = request.GET.get("q", "").strip()
    produtos = Produto.objects.select_related("categoria", "unidade").all()
    if termo:
        produtos = produtos.filter(Q(nome__icontains=termo) | Q(categoria__nome__icontains=termo))
    produtos = sorted(produtos, key=lambda p: (not p.estoque_critico, p.categoria.nome.lower(), p.nome.lower()))
    return render(request, "estoque/lista.html", {"produtos": produtos, "termo": termo})

# Cadastro de um novo material no sistema.
def criar_produto(request):
    form = ProdutoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        produto = form.save()
        messages.success(request, f'Material "{produto.nome}" cadastrado com sucesso.')
        return redirect("estoque:lista")
    return render(request, "estoque/formulario.html", {"form": form, "titulo": "Cadastrar material"})

# Edição dos dados de um material já cadastrado.
def editar_produto(request, pk):
    produto = get_object_or_404(Produto, pk=pk)
    form = ProdutoForm(request.POST or None, instance=produto)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Material atualizado com sucesso.")
        return redirect("estoque:lista")
    return render(request, "estoque/formulario.html", {"form": form, "titulo": "Editar material", "produto": produto})

# Exclusão de um material, com proteção quando ele já teve movimentação.
def excluir_produto(request, pk):
    produto = get_object_or_404(Produto, pk=pk)
    if request.method == "POST":
        if produto.movimentacoes.exists():
            messages.error(request, "Este material possui movimentações registradas e não pode ser excluído nesta versão.")
        else:
            nome = produto.nome
            produto.delete()
            messages.success(request, f'Material "{nome}" removido.')
        return redirect("estoque:lista")
    return render(request, "estoque/confirmar_exclusao.html", {"produto": produto})

# Registrar a retirada de material e atualizar o saldo do estoque.
def baixa_estoque(request, pk):
    produto = get_object_or_404(Produto, pk=pk)
    form = BaixaEstoqueForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        quantidade = form.cleaned_data["quantidade"]
        if quantidade > produto.quantidade:
            form.add_error("quantidade", "A retirada não pode ser maior que o saldo disponível.")
        else:
            with transaction.atomic():
                produto.quantidade -= quantidade
                produto.save(update_fields=["quantidade"])
                MovimentacaoEstoque.objects.create(
                    produto=produto, tipo=MovimentacaoEstoque.SAIDA,
                    quantidade=quantidade, saldo_resultante=produto.quantidade
                )
            messages.success(request, f"Baixa de estoque registrada para {produto.nome}.")
            if produto.estoque_critico:
                messages.warning(
                    request,
                    f'Atenção: o material "{produto.nome}" entrou em nível de estoque crítico!',
                )
            return redirect("estoque:lista")
    return render(request, "estoque/baixa.html", {"produto": produto, "form": form})

# Exibe o histórico completo de entradas e saídas de material.
def movimentacoes(request):
    registros = MovimentacaoEstoque.objects.select_related("produto").all()
    return render(request, "estoque/movimentacoes.html", {"registros": registros})
