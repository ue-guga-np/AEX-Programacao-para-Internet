from django.contrib import admin
from .models import Categoria, UnidadeMedida, Produto, MovimentacaoEstoque

admin.site.register(Categoria)
admin.site.register(UnidadeMedida)
admin.site.register(Produto)
admin.site.register(MovimentacaoEstoque)
