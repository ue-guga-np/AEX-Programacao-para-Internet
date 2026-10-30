from django import forms
from .models import Produto

class ProdutoForm(forms.ModelForm):
    class Meta:
        model = Produto
        fields = ["nome", "categoria", "unidade", "quantidade", "quantidade_minima", "alerta_manual"]
        labels = {
            "nome": "Nome do material",
            "categoria": "Categoria",
            "unidade": "Unidade de medida",
            "quantidade": "Quantidade atual",
            "quantidade_minima": "Quantidade mínima para alerta",
            "alerta_manual": "Marcar como urgente",
        }
        widgets = {
            "nome": forms.TextInput(attrs={"placeholder": "Ex.: Compensado 15 mm"}),
            "quantidade": forms.NumberInput(attrs={"min": "0", "step": "0.01"}),
            "quantidade_minima": forms.NumberInput(attrs={"min": "1", "step": "0.01"}),
        }

    def clean_nome(self):
        nome = self.cleaned_data["nome"].strip()
        if not nome:
            raise forms.ValidationError("Informe o nome do material.")
        return nome

class BaixaEstoqueForm(forms.Form):
    quantidade = forms.DecimalField(
        label="Quantidade a retirar",
        min_value=0.01,
        decimal_places=2,
        max_digits=10,
        widget=forms.NumberInput(attrs={"min": "0.01", "step": "0.01"})
    )
