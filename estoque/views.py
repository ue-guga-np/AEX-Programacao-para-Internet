import functools
import io
import os
import zipfile
from datetime import datetime
from decimal import Decimal

import pandas as pd
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.db import transaction
from django.db.models import Count, Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .forms import ProdutoForm, BaixaEstoqueForm
from .models import Produto, MovimentacaoEstoque, Categoria, UnidadeMedida

# Decorator para exigir login
def requer_login(view_func):
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"{reverse('estoque:login')}?next={request.path}")
        return view_func(request, *args, **kwargs)
    return wrapper

# Decorator para restringir ações a Administradores (is_staff ou is_superuser)
def requer_administrador(view_func):
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"{reverse('estoque:login')}?next={request.path}")
        if not (request.user.is_staff or request.user.is_superuser):
            messages.error(
                request,
                "Acesso restrito ao Administrador. Usuários comuns (Operadores) possuem permissão apenas para consultar materiais e movimentar o estoque (baixas e entradas)."
            )
            return redirect("estoque:lista")
        return view_func(request, *args, **kwargs)
    return wrapper

# Tela de Login com suporte a atalhos de demonstração (Administrador e Operador)
def fazer_login(request):
    if request.user.is_authenticated:
        return redirect("estoque:inicio")

    next_url = request.GET.get("next") or request.POST.get("next") or reverse("estoque:inicio")
    erro = None

    if request.method == "POST":
        usuario = request.POST.get("username", "").strip()
        senha = request.POST.get("password", "")
        user = authenticate(request, username=usuario, password=senha)
        if user is not None:
            auth_login(request, user)
            nome_exibicao = user.first_name or user.username
            perfil = "Administrador" if (user.is_staff or user.is_superuser) else "Operador"
            messages.success(request, f"Bem-vindo(a), {nome_exibicao}! Sessão iniciada como {perfil}.")
            return redirect(next_url)
        else:
            erro = "Usuário ou senha incorretos."

    return render(request, "estoque/login.html", {
        "next": next_url,
        "erro": erro,
    })

# Logout
def fazer_logout(request):
    auth_logout(request)
    messages.success(request, "Você encerrou a sessão.")
    return redirect("estoque:login")

# Página inicial com resumo geral do sistema
@requer_login
def inicio(request):
    produtos = list(Produto.objects.select_related("categoria", "unidade").all())
    produtos_criticos = [produto for produto in produtos if produto.estoque_critico]
    ultimas_movimentacoes = MovimentacaoEstoque.objects.select_related(
        "produto", "produto__categoria", "produto__unidade", "usuario"
    )[:5]
    context = {
        "total_produtos": len(produtos),
        "total_alertas": len(produtos_criticos),
        "produtos_criticos": produtos_criticos[:5],
        "total_movimentacoes": MovimentacaoEstoque.objects.count(),
        "ultimas_movimentacoes": ultimas_movimentacoes,
    }
    return render(request, "estoque/inicio.html", context)

# Lista e busca dos produtos cadastrados (acessível para Administrador e Operador)
@requer_login
def lista_produtos(request):
    termo = request.GET.get("q", "").strip()
    categoria_id = request.GET.get("categoria", "").strip()
    selecionado_id = request.GET.get("selecionado", "").strip()

    produtos_qs = Produto.objects.select_related("categoria", "unidade").all()
    if termo:
        produtos_qs = produtos_qs.filter(Q(nome__icontains=termo) | Q(categoria__nome__icontains=termo))
    if categoria_id:
        produtos_qs = produtos_qs.filter(categoria_id=categoria_id)

    # Ordenação conforme US07 e RN03
    produtos = sorted(
        produtos_qs,
        key=lambda p: (not p.estoque_critico, p.categoria.nome.lower(), p.nome.lower())
    )

    categorias = Categoria.objects.all()

    produto_selecionado = None
    if selecionado_id:
        produto_selecionado = next((p for p in produtos if str(p.pk) == selecionado_id), None)
    if not produto_selecionado and produtos:
        produto_selecionado = produtos[0]

    return render(request, "estoque/lista.html", {
        "produtos": produtos,
        "categorias": categorias,
        "termo": termo,
        "categoria_ativa": categoria_id,
        "produto_selecionado": produto_selecionado,
    })

# Cadastro de novo material (Restrito ao Administrador)
@requer_administrador
def criar_produto(request):
    form = ProdutoForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        produto = form.save()
        messages.success(request, f'Material "{produto.nome}" cadastrado com sucesso.')
        return redirect(f"{reverse('estoque:lista')}?selecionado={produto.pk}")
    return render(request, "estoque/formulario.html", {
        "form": form,
        "titulo": "Cadastrar material",
    })

# Edição dos dados de um material (Restrito ao Administrador)
@requer_administrador
def editar_produto(request, pk):
    produto = get_object_or_404(Produto, pk=pk)
    form = ProdutoForm(request.POST or None, request.FILES or None, instance=produto)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f'Material "{produto.nome}" atualizado com sucesso.')
        return redirect(f"{reverse('estoque:lista')}?selecionado={produto.pk}")
    return render(request, "estoque/formulario.html", {
        "form": form,
        "titulo": "Editar material",
        "produto": produto,
    })

# Exclusão de material (Restrito ao Administrador)
@requer_administrador
def excluir_produto(request, pk):
    produto = get_object_or_404(Produto, pk=pk)
    if request.method == "POST":
        nome = produto.nome
        produto.delete()
        messages.success(request, f'Material "{nome}" removido do catálogo com sucesso.')
        return redirect("estoque:lista")

    total_mov = produto.movimentacoes.count()
    return render(request, "estoque/confirmar_exclusao.html", {
        "produto": produto,
        "total_movimentacoes": total_mov,
    })

# Registrar retirada rápida pela lista (Permitido para Operador e Administrador)
@requer_login
def baixa_rapida(request, pk):
    produto = get_object_or_404(Produto, pk=pk)
    if request.method == "POST":
        raw_qtd = request.POST.get("quantidade", "").strip()

        try:
            if "." in raw_qtd or "," in raw_qtd:
                raise ValueError("Valor fracionário não permitido")
            quantidade_int = int(raw_qtd)
        except (ValueError, TypeError):
            messages.error(request, "Informe um valor inteiro válido (números inteiros sem casas decimais).")
            return redirect(f"{reverse('estoque:lista')}?selecionado={produto.pk}")

        if quantidade_int <= 0:
            messages.error(request, "A quantidade a retirar deve ser um número inteiro maior que zero.")
            return redirect(f"{reverse('estoque:lista')}?selecionado={produto.pk}")

        saldo_atual_int = int(produto.quantidade)
        if quantidade_int > saldo_atual_int:
            messages.error(
                request,
                f'Quantidade retirada ({quantidade_int}) é maior que o estoque atual! Saldo disponível: {saldo_atual_int} {produto.unidade.sigla}.'
            )
            return redirect(f"{reverse('estoque:lista')}?selecionado={produto.pk}")

        qtd_decimal = Decimal(quantidade_int)
        user_reg = request.user if request.user.is_authenticated else None
        observacao = request.POST.get("observacao", "").strip()
        
        with transaction.atomic():
            produto.quantidade -= qtd_decimal
            produto.save(update_fields=["quantidade"])
            MovimentacaoEstoque.objects.create(
                produto=produto,
                usuario=user_reg,
                tipo=MovimentacaoEstoque.SAIDA,
                quantidade=qtd_decimal,
                saldo_resultante=produto.quantidade,
                observacao=observacao,
            )

        saldo_formatado = int(produto.quantidade) if produto.quantidade % 1 == 0 else produto.quantidade
        messages.success(
            request,
            f'Baixa de {quantidade_int} {produto.unidade.sigla} registrada para "{produto.nome}". Novo saldo: {saldo_formatado} {produto.unidade.sigla}.'
        )
        if produto.estoque_critico:
            messages.warning(
                request,
                f'Atenção: o material "{produto.nome}" entrou em nível de estoque crítico ({saldo_formatado} {produto.unidade.sigla})!'
            )

    return redirect(f"{reverse('estoque:lista')}?selecionado={produto.pk}")

# Adicionar saldo rapidamente (Permitido para Operador e Administrador)
@requer_login
def adicionar_saldo(request, pk):
    produto = get_object_or_404(Produto, pk=pk)
    if request.method == "POST":
        raw_qtd = request.POST.get("quantidade", "").strip()

        try:
            if "." in raw_qtd or "," in raw_qtd:
                raise ValueError("Valor fracionário não permitido")
            quantidade_int = int(raw_qtd)
        except (ValueError, TypeError):
            messages.error(request, "Informe um valor inteiro válido para adicionar ao saldo.")
            return redirect(f"{reverse('estoque:lista')}?selecionado={produto.pk}")

        if quantidade_int <= 0:
            messages.error(request, "A quantidade a adicionar deve ser um número inteiro maior que zero.")
            return redirect(f"{reverse('estoque:lista')}?selecionado={produto.pk}")

        qtd_decimal = Decimal(quantidade_int)
        user_reg = request.user if request.user.is_authenticated else None
        with transaction.atomic():
            produto.quantidade += qtd_decimal
            produto.save(update_fields=["quantidade"])
            MovimentacaoEstoque.objects.create(
                produto=produto,
                usuario=user_reg,
                tipo=MovimentacaoEstoque.ENTRADA,
                quantidade=qtd_decimal,
                saldo_resultante=produto.quantidade,
            )

        saldo_formatado = int(produto.quantidade) if produto.quantidade % 1 == 0 else produto.quantidade
        messages.success(
            request,
            f'Entrada de +{quantidade_int} {produto.unidade.sigla} adicionada com sucesso ao material "{produto.nome}". Novo saldo: {saldo_formatado} {produto.unidade.sigla}.'
        )

    return redirect(f"{reverse('estoque:lista')}?selecionado={produto.pk}")

# Registrar retirada pela página de baixa dedicada (Permitido para Operador e Administrador)
@requer_login
def baixa_estoque(request, pk):
    produto = get_object_or_404(Produto, pk=pk)
    form = BaixaEstoqueForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        quantidade = form.cleaned_data["quantidade"]
        if quantidade > produto.quantidade:
            form.add_error("quantidade", "A retirada não pode ser maior que o saldo disponível.")
        else:
            user_reg = request.user if request.user.is_authenticated else None
            with transaction.atomic():
                produto.quantidade -= quantidade
                produto.save(update_fields=["quantidade"])
                MovimentacaoEstoque.objects.create(
                    produto=produto,
                    usuario=user_reg,
                    tipo=MovimentacaoEstoque.SAIDA,
                    quantidade=quantidade,
                    saldo_resultante=produto.quantidade
                )
            messages.success(request, f"Baixa de estoque registrada para {produto.nome}.")
            if produto.estoque_critico:
                messages.warning(
                    request,
                    f'Atenção: o material "{produto.nome}" entrou em nível de estoque crítico!',
                )
            return redirect(f"{reverse('estoque:lista')}?selecionado={produto.pk}")
    return render(request, "estoque/baixa.html", {"produto": produto, "form": form})

# Histórico de movimentações (Permitido para Operador e Administrador)
@requer_login
def movimentacoes(request):
    tipo_filtro = request.GET.get("tipo", "").strip()
    termo = request.GET.get("q", "").strip()

    registros = MovimentacaoEstoque.objects.select_related("produto", "produto__categoria", "produto__unidade", "usuario").all()
    if tipo_filtro in ["E", "S"]:
        registros = registros.filter(tipo=tipo_filtro)
    if termo:
        registros = registros.filter(Q(produto__nome__icontains=termo) | Q(produto__categoria__nome__icontains=termo))

    total_entradas = sum(1 for m in registros if m.tipo == "E")
    total_saidas = sum(1 for m in registros if m.tipo == "S")

    return render(request, "estoque/movimentacoes.html", {
        "registros": registros,
        "tipo_filtro": tipo_filtro,
        "termo": termo,
        "total_entradas": total_entradas,
        "total_saidas": total_saidas,
    })

# Gerência de Categorias e Unidades (Restrito ao Administrador)
@requer_administrador
def gerenciar_classificacoes(request):
    categorias = Categoria.objects.annotate(total_produtos=Count("produtos")).order_by("nome")
    unidades = UnidadeMedida.objects.annotate(total_produtos=Count("produtos")).order_by("nome")
    return render(request, "estoque/classificacoes.html", {
        "categorias": categorias,
        "unidades": unidades,
    })

# Criar categoria (Restrito ao Administrador)
@requer_administrador
def criar_categoria(request):
    if request.method == "POST":
        nome = request.POST.get("nome", "").strip()
        if not nome:
            messages.error(request, "O nome da categoria não pode ser vazio.")
        elif Categoria.objects.filter(nome__iexact=nome).exists():
            messages.error(request, f'A categoria "{nome}" já existe.')
        else:
            Categoria.objects.create(nome=nome)
            messages.success(request, f'Categoria "{nome}" cadastrada com sucesso.')
    return redirect("estoque:classificacoes")

# Editar categoria (Restrito ao Administrador)
@requer_administrador
def editar_categoria(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    if request.method == "POST":
        novo_nome = request.POST.get("nome", "").strip()
        if not novo_nome:
            messages.error(request, "O nome da categoria não pode ser vazio.")
        elif Categoria.objects.filter(nome__iexact=novo_nome).exclude(pk=pk).exists():
            messages.error(request, f'Já existe uma categoria cadastrada com o nome "{novo_nome}".')
        else:
            categoria.nome = novo_nome
            categoria.save()
            messages.success(request, f'Categoria renomeada para "{categoria.nome}" com sucesso.')
    return redirect("estoque:classificacoes")

# Excluir categoria (Restrito ao Administrador)
@requer_administrador
def excluir_categoria(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    if request.method == "POST":
        total_vinculados = categoria.produtos.count()
        if total_vinculados > 0:
            messages.error(
                request,
                f'Bloqueio de Integridade (RN01): A categoria "{categoria.nome}" não pode ser excluída pois possui {total_vinculados} material(is) vinculado(s).'
            )
        else:
            nome = categoria.nome
            categoria.delete()
            messages.success(request, f'Categoria "{nome}" excluída com sucesso.')
    return redirect("estoque:classificacoes")

# Criar unidade de medida (Restrito ao Administrador)
@requer_administrador
def criar_unidade(request):
    if request.method == "POST":
        nome = request.POST.get("nome", "").strip()
        sigla = request.POST.get("sigla", "").strip()
        if not nome or not sigla:
            messages.error(request, "Nome e sigla da unidade de medida são obrigatórios.")
        elif UnidadeMedida.objects.filter(nome__iexact=nome).exists():
            messages.error(request, f'A unidade "{nome}" já existe.')
        else:
            UnidadeMedida.objects.create(nome=nome, sigla=sigla)
            messages.success(request, f'Unidade "{nome} ({sigla})" cadastrada com sucesso.')
    return redirect("estoque:classificacoes")

# Editar unidade de medida (Restrito ao Administrador)
@requer_administrador
def editar_unidade(request, pk):
    unidade = get_object_or_404(UnidadeMedida, pk=pk)
    if request.method == "POST":
        novo_nome = request.POST.get("nome", "").strip()
        nova_sigla = request.POST.get("sigla", "").strip()
        if not novo_nome or not nova_sigla:
            messages.error(request, "Nome e sigla da unidade de medida são obrigatórios.")
        elif UnidadeMedida.objects.filter(nome__iexact=novo_nome).exclude(pk=pk).exists():
            messages.error(request, f'Já existe uma unidade com o nome "{novo_nome}".')
        else:
            unidade.nome = novo_nome
            unidade.sigla = nova_sigla
            unidade.save()
            messages.success(request, f'Unidade de medida atualizada para "{unidade.nome} ({unidade.sigla})".')
    return redirect("estoque:classificacoes")

# Excluir unidade de medida (Restrito ao Administrador)
@requer_administrador
def excluir_unidade(request, pk):
    unidade = get_object_or_404(UnidadeMedida, pk=pk)
    if request.method == "POST":
        total_vinculados = unidade.produtos.count()
        if total_vinculados > 0:
            messages.error(
                request,
                f'Bloqueio de Integridade (RN01): A unidade "{unidade.nome}" não pode ser excluída pois está em uso por {total_vinculados} material(is).'
            )
        else:
            nome = unidade.nome
            unidade.delete()
            messages.success(request, f'Unidade de medida "{nome}" excluída com sucesso.')
    return redirect("estoque:classificacoes")

# Endpoint AJAX para criar categoria (Restrito ao Administrador)
@require_POST
def criar_categoria_ajax(request):
    if not (request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser)):
        return JsonResponse({"sucesso": False, "erro": "Apenas administradores podem cadastrar categorias."}, status=403)

    nome = request.POST.get("nome", "").strip()
    if not nome:
        return JsonResponse({"sucesso": False, "erro": "O nome da categoria é obrigatório."}, status=400)
    
    if Categoria.objects.filter(nome__iexact=nome).exists():
        cat = Categoria.objects.filter(nome__iexact=nome).first()
        return JsonResponse({"sucesso": True, "id": cat.id, "nome": cat.nome, "ja_existia": True})
    
    cat = Categoria.objects.create(nome=nome)
    return JsonResponse({"sucesso": True, "id": cat.id, "nome": cat.nome, "ja_existia": False})

# Endpoint AJAX para criar unidade (Restrito ao Administrador)
@require_POST
def criar_unidade_ajax(request):
    if not (request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser)):
        return JsonResponse({"sucesso": False, "erro": "Apenas administradores podem cadastrar unidades de medida."}, status=403)

    nome = request.POST.get("nome", "").strip()
    sigla = request.POST.get("sigla", "").strip()
    if not nome or not sigla:
        return JsonResponse({"sucesso": False, "erro": "Nome e sigla da unidade são obrigatórios."}, status=400)
    
    if UnidadeMedida.objects.filter(nome__iexact=nome).exists():
        unidade = UnidadeMedida.objects.filter(nome__iexact=nome).first()
        return JsonResponse({"sucesso": True, "id": unidade.id, "nome": str(unidade), "ja_existia": True})
    
    unidade = UnidadeMedida.objects.create(nome=nome, sigla=sigla)
    return JsonResponse({"sucesso": True, "id": unidade.id, "nome": str(unidade), "ja_existia": False})

# Exportação do inventário para Excel (.xlsx) (Permitido para consulta)
@requer_login
def exportar_excel(request):
    produtos = Produto.objects.select_related("categoria", "unidade").all().order_by("categoria__nome", "nome")
    
    dados = []
    for p in produtos:
        dados.append({
            "Produto": p.nome,
            "Categoria": p.categoria.nome,
            "Unidade": p.unidade.sigla,
            "Qtd Atual": int(p.quantidade) if p.quantidade % 1 == 0 else float(p.quantidade),
            "Qtd Mínima": int(p.quantidade_minima) if p.quantidade_minima % 1 == 0 else float(p.quantidade_minima),
            "Status": "Estoque Crítico" if p.estoque_critico else "Normal",
        })

    df = pd.DataFrame(dados)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Estoque")
    
    buffer.seek(0)
    data_hoje = datetime.now().strftime("%Y-%m-%d")
    nome_arquivo = f"estoque_marcenaria_{data_hoje}.xlsx"
    
    response = HttpResponse(
        buffer.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = f'attachment; filename="{nome_arquivo}"'
    return response

# Importação de planilha Excel (Restrito ao Administrador)
@requer_administrador
def importar_excel(request):
    if request.method == "POST" and request.FILES.get("arquivo_excel"):
        arquivo = request.FILES["arquivo_excel"]
        try:
            df = pd.read_excel(arquivo)
            colunas_map = {}
            for col in df.columns:
                c_clean = str(col).strip().lower()
                if "prod" in c_clean or "material" in c_clean or "nome" in c_clean:
                    colunas_map[col] = "nome"
                elif "cat" in c_clean:
                    colunas_map[col] = "categoria"
                elif "unid" in c_clean:
                    colunas_map[col] = "unidade"
                elif "atual" in c_clean or "qtd" in c_clean or "saldo" in c_clean or "quant" in c_clean:
                    if "min" not in c_clean:
                        colunas_map[col] = "quantidade"
                if "min" in c_clean or "aviso" in c_clean:
                    colunas_map[col] = "quantidade_minima"

            df = df.rename(columns=colunas_map)
            if "nome" not in df.columns:
                messages.error(request, 'A planilha precisa conter ao menos uma coluna com o nome do produto ("Produto" ou "Nome").')
                return redirect("estoque:painel_backups")

            total_processados = 0
            with transaction.atomic():
                for _, row in df.iterrows():
                    nome_prod = str(row.get("nome", "")).strip()
                    if not nome_prod or nome_prod.lower() == "nan":
                        continue
                    
                    cat_nome = str(row.get("categoria", "Outros")).strip()
                    if not cat_nome or cat_nome.lower() == "nan":
                        cat_nome = "Outros"
                    categoria, _ = Categoria.objects.get_or_create(nome=cat_nome)

                    unid_sigla = str(row.get("unidade", "un")).strip()
                    if not unid_sigla or unid_sigla.lower() == "nan":
                        unid_sigla = "un"
                    unidade, _ = UnidadeMedida.objects.get_or_create(nome=unid_sigla, defaults={"sigla": unid_sigla})

                    try:
                        qtd_val = Decimal(str(row.get("quantidade", 0)).replace(",", "."))
                        if qtd_val < 0:
                            qtd_val = Decimal(0)
                    except Exception:
                        qtd_val = Decimal(0)

                    try:
                        qtd_min_val = Decimal(str(row.get("quantidade_minima", 1)).replace(",", "."))
                        if qtd_min_val < 1:
                            qtd_min_val = Decimal(1)
                    except Exception:
                        qtd_min_val = Decimal(1)

                    produto, criado = Produto.objects.update_or_create(
                        nome=nome_prod,
                        defaults={
                            "categoria": categoria,
                            "unidade": unidade,
                            "quantidade": qtd_val,
                            "quantidade_minima": qtd_min_val,
                        }
                    )
                    total_processados += 1

            messages.success(request, f"Planilha importada com sucesso! {total_processados} produtos processados.")
        except Exception as e:
            messages.error(request, f"Erro ao processar o arquivo Excel: {str(e)}")

    return redirect("estoque:painel_backups")

# Exportar pacote completo de backup (Restrito ao Administrador)
@requer_administrador
def exportar_backup(request):
    buffer = io.BytesIO()
    db_path = str(settings.DATABASES["default"]["NAME"])
    if not os.path.exists(db_path):
        real_db = os.path.join(settings.BASE_DIR, "db.sqlite3")
        if os.path.exists(real_db):
            db_path = real_db

    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        if os.path.exists(db_path):
            zip_file.write(db_path, arcname="db.sqlite3")

        media_root = settings.MEDIA_ROOT
        if os.path.exists(media_root):
            for raiz, _, arquivos in os.walk(media_root):
                for arq in arquivos:
                    caminho_completo = os.path.join(raiz, arq)
                    caminho_relativo = os.path.relpath(caminho_completo, media_root)
                    zip_file.write(caminho_completo, arcname=os.path.join("media", caminho_relativo))

    buffer.seek(0)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    nome_zip = f"backup_estoque_marcenaria_{timestamp}.zip"

    response = HttpResponse(buffer.getvalue(), content_type="application/zip")
    response["Content-Disposition"] = f'attachment; filename="{nome_zip}"'
    return response

# Importar pacote de backup (Restrito ao Administrador)
@requer_administrador
def importar_backup(request):
    if request.method == "POST":
        arquivo_zip = request.FILES.get("arquivo_backup")
        confirmado = request.POST.get("confirmar_restauracao") == "sim"

        if not confirmado:
            messages.error(request, "Você precisa marcar a caixa confirmando a substituição dos dados atuais.")
            return redirect("estoque:painel_backups")

        if not arquivo_zip:
            messages.error(request, "Nenhum arquivo de backup (.zip) foi selecionado.")
            return redirect("estoque:painel_backups")

        try:
            with zipfile.ZipFile(arquivo_zip, "r") as zf:
                nomes_arquivos = zf.namelist()
                if "db.sqlite3" not in nomes_arquivos:
                    messages.error(request, "Arquivo de backup inválido: não contém o banco 'db.sqlite3'.")
                    return redirect("estoque:painel_backups")

                db_path = settings.DATABASES["default"]["NAME"]
                with open(db_path, "wb") as f_db:
                    f_db.write(zf.read("db.sqlite3"))

                media_root = str(settings.MEDIA_ROOT)
                for item in nomes_arquivos:
                    if item.startswith("media/") and not item.endswith("/"):
                        caminho_rel = item[len("media/"):]
                        caminho_dest = os.path.join(media_root, caminho_rel)
                        os.makedirs(os.path.dirname(caminho_dest), exist_ok=True)
                        with open(caminho_dest, "wb") as f_img:
                            f_img.write(zf.read(item))

            messages.success(request, "Backup restaurado com sucesso! Os dados e imagens foram recuperados.")
        except Exception as e:
            messages.error(request, f"Falha na restauração do backup: {str(e)}")

    return redirect("estoque:painel_backups")

# Painel central para gerenciamento de Backups (Restrito ao Administrador)
@requer_administrador
def painel_backups(request):
    total_produtos = Produto.objects.count()
    total_movimentacoes = MovimentacaoEstoque.objects.count()
    return render(request, "estoque/backups.html", {
        "total_produtos": total_produtos,
        "total_movimentacoes": total_movimentacoes,
    })
