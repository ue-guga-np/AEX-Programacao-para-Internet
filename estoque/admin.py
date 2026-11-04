from django.contrib import admin
from .models import Categoria, UnidadeMedida, Produto, MovimentacaoEstoque

admin.site.site_header = "Administração da Marcenaria"
admin.site.site_title = "Administração da Marcenaria"
admin.site.index_title = "Administração da Marcenaria"

admin.site.register(Categoria)
admin.site.register(UnidadeMedida)
admin.site.register(Produto)
admin.site.register(MovimentacaoEstoque)
