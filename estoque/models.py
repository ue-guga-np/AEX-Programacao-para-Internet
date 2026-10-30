from django.db import models
from django.core.validators import MinValueValidator

class Categoria(models.Model):
    nome = models.CharField(max_length=80, unique=True)

    class Meta:
        ordering = ["nome"]
        verbose_name_plural = "categorias"

    def __str__(self):
        return self.nome

class UnidadeMedida(models.Model):
    nome = models.CharField(max_length=40, unique=True)
    sigla = models.CharField(max_length=10)

    class Meta:
        ordering = ["nome"]
        verbose_name = "unidade de medida"
        verbose_name_plural = "unidades de medida"

    def __str__(self):
        return f"{self.nome} ({self.sigla})"

class Produto(models.Model):
    nome = models.CharField(max_length=120)
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name="produtos")
    unidade = models.ForeignKey(UnidadeMedida, on_delete=models.PROTECT, related_name="produtos")
    quantidade = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    quantidade_minima = models.DecimalField(max_digits=10, decimal_places=2, default=1, validators=[MinValueValidator(1)])
    alerta_manual = models.BooleanField(default=False)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["categoria__nome", "nome"]

    def __str__(self):
        return self.nome

    @property
    def estoque_critico(self):
        return self.quantidade <= self.quantidade_minima or self.alerta_manual

class MovimentacaoEstoque(models.Model):
    ENTRADA = "E"
    SAIDA = "S"
    TIPOS = [(ENTRADA, "Entrada"), (SAIDA, "Saída")]
    produto = models.ForeignKey(Produto, on_delete=models.PROTECT, related_name="movimentacoes")
    tipo = models.CharField(max_length=1, choices=TIPOS)
    quantidade = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    saldo_resultante = models.DecimalField(max_digits=10, decimal_places=2)
    data = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-data"]

    def __str__(self):
        return f"{self.get_tipo_display()} — {self.produto.nome} ({self.quantidade})"
