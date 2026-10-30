from django.contrib import admin
from .models import Categoria, UnidadeMedida, Produto, MovimentacaoEstoque


admin.site.site_header = "Estoque da Marcenaria"
admin.site.site_title = "Estoque da Marcenaria"
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
    list_display = ("nome", "categoria", "quantidade", "unidade", "quantidade_minima", "estoque_critico")
    list_filter = ("categoria", "unidade", "alerta_manual")
    search_fields = ("nome", "categoria__nome")
    list_select_related = ("categoria", "unidade")
    ordering = ("categoria__nome", "nome")
    fieldsets = (
        ("Dados do produto", {"fields": ("nome", "categoria", "unidade")}),
        ("Controle de estoque", {"fields": ("quantidade", "quantidade_minima", "alerta_manual")}),
    )

    @admin.display(boolean=True, description="Estoque crítico")
    def estoque_critico(self, obj):
        return obj.estoque_critico


@admin.register(MovimentacaoEstoque)
class MovimentacaoEstoqueAdmin(admin.ModelAdmin):
    list_display = ("produto", "tipo", "quantidade", "saldo_resultante", "data")
    list_filter = ("tipo", "data")
    search_fields = ("produto__nome",)
    list_select_related = ("produto",)
    ordering = ("-data",)
    readonly_fields = ("data",)
