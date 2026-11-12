from django.contrib import admin
from django.utils.html import format_html
from .models import Categoria, UnidadeMedida, Produto, MovimentacaoEstoque

admin.site.site_header = "Administração da Marcenaria"
admin.site.site_title = "Administração da Marcenaria"
admin.site.index_title = "Gerenciamento do estoque"

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nome",)
    search_fields = ("nome",)
    ordering = ("nome",)

@admin.register(UnidadeMedida)
class UnidadeMedidaAdmin(admin.ModelAdmin):
    list_display = ("nome", "sigla")
    search_fields = ("nome", "sigla")
    ordering = ("nome",)

@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ("miniatura", "nome", "categoria", "quantidade", "unidade", "quantidade_minima", "estoque_critico")
    list_filter = ("categoria", "unidade", "alerta_manual")
    search_fields = ("nome", "categoria__nome")
    list_select_related = ("categoria", "unidade")
    ordering = ("categoria__nome", "nome")
    fieldsets = (
        ("Dados do produto", {"fields": ("nome", "categoria", "unidade", "imagem")}),
        ("Controle de estoque", {"fields": ("quantidade", "quantidade_minima", "alerta_manual")}),
    )

    @admin.display(boolean=True, description="Estoque crítico")
    def estoque_critico(self, obj):
        return obj.estoque_critico

    @admin.display(description="Foto")
    def miniatura(self, obj):
        if obj.imagem:
            return format_html('<img src="{}" style="width: 36px; height: 36px; object-fit: cover; border-radius: 4px;" />', obj.imagem.url)
        return "—"

@admin.register(MovimentacaoEstoque)
class MovimentacaoEstoqueAdmin(admin.ModelAdmin):
    list_display = ("produto", "tipo", "quantidade", "saldo_resultante", "data")
    list_filter = ("tipo", "data")
    search_fields = ("produto__nome",)
    list_select_related = ("produto",)
    ordering = ("-data",)
    readonly_fields = ("data",)
