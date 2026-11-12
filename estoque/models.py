import os
from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator

# Modelo para classificar os materiais cadastrados no estoque.
class Categoria(models.Model):
    nome = models.CharField(max_length=80, unique=True)

    class Meta:
        ordering = ["nome"]
        verbose_name_plural = "categorias"

    def __str__(self):
        return self.nome

# Modelo para definir a unidade usada para medir cada material.
class UnidadeMedida(models.Model):
    nome = models.CharField(max_length=40, unique=True)
    sigla = models.CharField(max_length=10)

    class Meta:
        ordering = ["nome"]
        verbose_name = "unidade de medida"
        verbose_name_plural = "unidades de medida"

    def __str__(self):
        return f"{self.nome} ({self.sigla})"

# Modelo principal do estoque: representa cada material disponível.
class Produto(models.Model):
    nome = models.CharField(max_length=120)
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name="produtos")
    unidade = models.ForeignKey(UnidadeMedida, on_delete=models.PROTECT, related_name="produtos")
    quantidade = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    quantidade_minima = models.DecimalField(max_digits=10, decimal_places=2, default=1, validators=[MinValueValidator(1)])
    alerta_manual = models.BooleanField(default=False)
    imagem = models.ImageField(upload_to="produtos/", blank=True, null=True, verbose_name="Foto do produto")
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["categoria__nome", "nome"]

    def __str__(self):
        return self.nome

    @property
    def estoque_critico(self):
        return self.quantidade <= self.quantidade_minima or self.alerta_manual

    def possui_estoque_suficiente(self, qtd):
        return self.quantidade >= qtd

    def debitar_estoque(self, qtd):
        if not self.possui_estoque_suficiente(qtd):
            raise ValueError("Quantidade retirada é maior que o estoque atual!")
        self.quantidade -= qtd
        self.save(update_fields=["quantidade"])

    def delete(self, *args, **kwargs):
        # RN04: Limpar arquivo de imagem caso nenhum outro produto faça referência
        imagem_path = self.imagem.path if self.imagem and hasattr(self.imagem, "path") else None
        imagem_name = self.imagem.name if self.imagem else None
        super().delete(*args, **kwargs)
        if imagem_path and imagem_name:
            if not Produto.objects.filter(imagem=imagem_name).exists():
                try:
                    if os.path.exists(imagem_path):
                        os.remove(imagem_path)
                except Exception:
                    pass

# Histórico de entradas e saídas para acompanhar o saldo do estoque.
class MovimentacaoEstoque(models.Model):
    ENTRADA = "E"
    SAIDA = "S"
    TIPOS = [(ENTRADA, "Entrada"), (SAIDA, "Saída")]
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, related_name="movimentacoes")
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="movimentacoes")
    tipo = models.CharField(max_length=1, choices=TIPOS)
    quantidade = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    saldo_resultante = models.DecimalField(max_digits=10, decimal_places=2)
    observacao = models.CharField(max_length=255, blank=True, default="", verbose_name="Observação / O.S")
    data = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ["-data"]

    def __str__(self):
        return f"{self.get_tipo_display()} — {self.produto.nome} ({self.quantidade})"
