from django import forms
from .models import Produto

# Formulário para cadastrar ou editar um material do estoque.
class ProdutoForm(forms.ModelForm):
    class Meta:
        model = Produto
        fields = [
            "nome",
            "categoria",
            "unidade",
            "quantidade",
            "quantidade_minima",
            "alerta_manual",
            "imagem",
        ]
        labels = {
            "nome": "Nome do material",
            "categoria": "Categoria",
            "unidade": "Unidade de medida",
            "quantidade": "Quantidade inicial / atual",
            "quantidade_minima": "Quantidade mínima para alerta (aviso)",
            "alerta_manual": "Marcar como urgente (alerta prioritário)",
            "imagem": "Foto do produto (opcional)",
        }
        widgets = {
            "nome": forms.TextInput(attrs={"placeholder": "Ex.: Compensado Naval 15mm"}),
            "quantidade": forms.NumberInput(attrs={"min": "0", "step": "1", "placeholder": "Ex.: 10"}),
            "quantidade_minima": forms.NumberInput(attrs={"min": "1", "step": "1", "placeholder": "Ex.: 2"}),
            "imagem": forms.FileInput(attrs={"accept": "image/*"}),
        }

    def clean_nome(self):
        nome = self.cleaned_data["nome"].strip()
        if not nome:
            raise forms.ValidationError("Informe o nome do material.")
        return nome

    def clean_quantidade(self):
        quantidade = self.cleaned_data.get("quantidade")
        if quantidade is not None and quantidade < 0:
            raise forms.ValidationError("A quantidade inicial não pode ser negativa.")
        return quantidade

    def clean_quantidade_minima(self):
        quantidade_minima = self.cleaned_data.get("quantidade_minima")
        if quantidade_minima is not None and quantidade_minima < 1:
            raise forms.ValidationError("A quantidade de aviso deve ser no mínimo 1.")
        return quantidade_minima

# Formulário usado para registrar a saída de um material do estoque.
class BaixaEstoqueForm(forms.Form):
    quantidade = forms.DecimalField(
        label="Quantidade a retirar",
        min_value=0.01,
        decimal_places=2,
        max_digits=10,
        widget=forms.NumberInput(attrs={"min": "0.01", "step": "0.01", "placeholder": "Qtd."})
    )
