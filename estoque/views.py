from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from .forms import ProdutoForm, BaixaEstoqueForm
from .models import Produto, MovimentacaoEstoque

def inicio(request):
    produtos = Produto.objects.all()
    context = {
        "total_produtos": produtos.count(),
        "total_alertas": sum(1 for p in produtos if p.estoque_critico),
        "ultimas_movimentacoes": MovimentacaoEstoque.objects.select_related("produto")[:5],
    }
    return render(request, "estoque/inicio.html", context)

def lista_produtos(request):
    termo = request.GET.get("q", "").strip()
    produtos = Produto.objects.select_related("categoria", "unidade").all()
    if termo:
        produtos = produtos.filter(Q(nome__icontains=termo) | Q(categoria__nome__icontains=termo))
    produtos = sorted(produtos, key=lambda p: (not p.estoque_critico, p.categoria.nome.lower(), p.nome.lower()))
    return render(request, "estoque/lista.html", {"produtos": produtos, "termo": termo})

def criar_produto(request):
    form = ProdutoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        produto = form.save()
        messages.success(request, f'Material "{produto.nome}" cadastrado com sucesso.')
        return redirect("estoque:lista")
    return render(request, "estoque/formulario.html", {"form": form, "titulo": "Cadastrar material"})

def editar_produto(request, pk):
    produto = get_object_or_404(Produto, pk=pk)
    form = ProdutoForm(request.POST or None, instance=produto)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Material atualizado com sucesso.")
        return redirect("estoque:lista")
    return render(request, "estoque/formulario.html", {"form": form, "titulo": "Editar material", "produto": produto})

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
            messages.success(request, "Baixa de estoque registrada.")
            return redirect("estoque:lista")
    return render(request, "estoque/baixa.html", {"produto": produto, "form": form})

def movimentacoes(request):
    registros = MovimentacaoEstoque.objects.select_related("produto").all()
    return render(request, "estoque/movimentacoes.html", {"registros": registros})
