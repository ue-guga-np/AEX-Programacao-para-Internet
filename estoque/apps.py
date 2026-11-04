from django.apps import AppConfig

class EstoqueConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "estoque"

    def ready(self):
        from django.db.models.signals import post_migrate
        from django.dispatch import receiver

        @receiver(post_migrate, sender=self)
        def criar_opcoes_iniciais(sender, **kwargs):
            from .models import Categoria, UnidadeMedida
            from django.contrib.auth.models import User

            for nome in ["Madeira", "Ferragens", "Acabamento", "Outros"]:
                Categoria.objects.get_or_create(nome=nome)
            for nome, sigla in [("Unidade", "un"), ("Metro", "m"), ("Quilograma", "kg"), ("Litro", "L"), ("Chapa", "ch")]:
                UnidadeMedida.objects.get_or_create(nome=nome, defaults={"sigla": sigla})

            # Cria o usuário comum padrão (Operador) se ainda não existir
            if not User.objects.filter(username="operador").exists():
                User.objects.create_user(
                    username="operador",
                    password="operador123",
                    first_name="Marceneiro (Operador)",
                    is_staff=False,
                    is_superuser=False
                )
