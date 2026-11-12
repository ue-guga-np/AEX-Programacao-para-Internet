import io
import os
import tempfile
import zipfile
from decimal import Decimal
import pandas as pd
from PIL import Image
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client
from django.urls import reverse
from .models import Categoria, UnidadeMedida, Produto, MovimentacaoEstoque

class EstoqueFeaturesTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.cat, _ = Categoria.objects.get_or_create(nome="Madeira")
        self.unidade = UnidadeMedida.objects.get(nome="Chapa")
        
        # Cria um admin e um operador
        self.admin_user = User.objects.create_superuser(
            username="admin_teste",
            password="adminpassword123",
            email="admin@teste.com"
        )
        self.operador_user = User.objects.create_user(
            username="operador_teste",
            password="operadorpassword123",
            is_staff=False,
            is_superuser=False
        )

        # Imagem temporária
        image = Image.new("RGB", (100, 100), color="blue")
        temp_file = tempfile.NamedTemporaryFile(suffix=".jpg")
        image.save(temp_file, format="JPEG")
        temp_file.seek(0)
        self.uploaded_image = SimpleUploadedFile("teste.jpg", temp_file.read(), content_type="image/jpeg")
        
        self.produto = Produto.objects.create(
            nome="Compensado Naval 15mm",
            categoria=self.cat,
            unidade=self.unidade,
            quantidade=Decimal("10.00"),
            quantidade_minima=Decimal("3.00"),
            imagem=self.uploaded_image
        )

    def test_produto_com_imagem(self):
        self.assertTrue(bool(self.produto.imagem))
        self.assertTrue(self.produto.imagem.url.startswith("/media/"))

    def test_operador_pode_dar_baixa_rapida(self):
        self.client.login(username="operador_teste", password="operadorpassword123")
        url = reverse("estoque:baixa_rapida", args=[self.produto.pk])
        response = self.client.post(url, {"quantidade": "4"}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.produto.refresh_from_db()
        self.assertEqual(self.produto.quantidade, Decimal("6.00"))
        
        mov = MovimentacaoEstoque.objects.first()
        self.assertEqual(mov.tipo, MovimentacaoEstoque.SAIDA)
        self.assertEqual(mov.quantidade, Decimal("4"))
        self.assertEqual(mov.usuario, self.operador_user)

    def test_operador_pode_adicionar_saldo(self):
        self.client.login(username="operador_teste", password="operadorpassword123")
        url = reverse("estoque:adicionar_saldo", args=[self.produto.pk])
        response = self.client.post(url, {"quantidade": "5"}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.produto.refresh_from_db()
        self.assertEqual(self.produto.quantidade, Decimal("15.00"))
        
        mov = MovimentacaoEstoque.objects.first()
        self.assertEqual(mov.tipo, MovimentacaoEstoque.ENTRADA)
        self.assertEqual(mov.usuario, self.operador_user)

    def test_operador_bloqueado_de_cadastrar_produto(self):
        self.client.login(username="operador_teste", password="operadorpassword123")
        url = reverse("estoque:criar")
        response = self.client.get(url, follow=True)
        self.assertContains(response, "Acesso restrito ao Administrador")
        self.assertRedirects(response, reverse("estoque:lista"))

    def test_operador_bloqueado_de_editar_e_excluir_produto(self):
        self.client.login(username="operador_teste", password="operadorpassword123")
        url_edit = reverse("estoque:editar", args=[self.produto.pk])
        res_edit = self.client.get(url_edit, follow=True)
        self.assertRedirects(res_edit, reverse("estoque:lista"))

        url_del = reverse("estoque:excluir", args=[self.produto.pk])
        res_del = self.client.get(url_del, follow=True)
        self.assertRedirects(res_del, reverse("estoque:lista"))

    def test_operador_bloqueado_de_gerenciar_classificacoes(self):
        self.client.login(username="operador_teste", password="operadorpassword123")
        url = reverse("estoque:classificacoes")
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, reverse("estoque:lista"))

    def test_operador_bloqueado_de_importar_backups(self):
        self.client.login(username="operador_teste", password="operadorpassword123")
        url = reverse("estoque:painel_backups")
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, reverse("estoque:lista"))

    def test_admin_pode_cadastrar_produto(self):
        self.client.login(username="admin_teste", password="adminpassword123")
        url = reverse("estoque:criar")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_admin_exclui_produto_com_movimentacoes(self):
        self.client.login(username="admin_teste", password="adminpassword123")
        MovimentacaoEstoque.objects.create(
            produto=self.produto,
            usuario=self.admin_user,
            tipo=MovimentacaoEstoque.SAIDA,
            quantidade=Decimal("1"),
            saldo_resultante=Decimal("9")
        )
        url = reverse("estoque:excluir", args=[self.produto.pk])
        response = self.client.post(url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Produto.objects.filter(pk=self.produto.pk).exists())
        self.assertEqual(MovimentacaoEstoque.objects.count(), 0)

    def test_gerenciar_categoria_editar_e_excluir_rn01(self):
        self.client.login(username="admin_teste", password="adminpassword123")
        # Bloqueado se em uso
        url_del = reverse("estoque:excluir_categoria", args=[self.cat.pk])
        self.client.post(url_del, follow=True)
        self.assertTrue(Categoria.objects.filter(pk=self.cat.pk).exists())

        # Livre se sem produtos
        cat_nova = Categoria.objects.create(nome="Puxadores Teste")
        url_edit = reverse("estoque:editar_categoria", args=[cat_nova.pk])
        self.client.post(url_edit, {"nome": "Puxadores Renomeados"}, follow=True)
        cat_nova.refresh_from_db()
        self.assertEqual(cat_nova.nome, "Puxadores Renomeados")

        url_del_livre = reverse("estoque:excluir_categoria", args=[cat_nova.pk])
        self.client.post(url_del_livre, follow=True)
        self.assertFalse(Categoria.objects.filter(pk=cat_nova.pk).exists())

    def test_gerenciar_unidade_editar_e_excluir_rn01(self):
        self.client.login(username="admin_teste", password="adminpassword123")
        url_del = reverse("estoque:excluir_unidade", args=[self.unidade.pk])
        self.client.post(url_del, follow=True)
        self.assertTrue(UnidadeMedida.objects.filter(pk=self.unidade.pk).exists())

        unid_nova = UnidadeMedida.objects.create(nome="Galao", sigla="gl")
        url_edit = reverse("estoque:editar_unidade", args=[unid_nova.pk])
        self.client.post(url_edit, {"nome": "Galao Grande", "sigla": "glg"}, follow=True)
        unid_nova.refresh_from_db()
        self.assertEqual(unid_nova.nome, "Galao Grande")

        url_del_livre = reverse("estoque:excluir_unidade", args=[unid_nova.pk])
        self.client.post(url_del_livre, follow=True)
        self.assertFalse(UnidadeMedida.objects.filter(pk=unid_nova.pk).exists())

    def test_movimentacoes_exibe_categoria_e_operador(self):
        self.client.login(username="operador_teste", password="operadorpassword123")
        MovimentacaoEstoque.objects.create(
            produto=self.produto,
            usuario=self.operador_user,
            tipo=MovimentacaoEstoque.SAIDA,
            quantidade=Decimal("2"),
            saldo_resultante=Decimal("8")
        )
        url = reverse("estoque:movimentacoes")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.produto.categoria.nome)
        self.assertContains(response, "operador_teste")

    def test_exportar_excel(self):
        self.client.login(username="operador_teste", password="operadorpassword123")
        url = reverse("estoque:exportar_excel")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", response["Content-Type"])

    def test_exportar_backup_admin(self):
        self.client.login(username="admin_teste", password="adminpassword123")
        url = reverse("estoque:exportar_backup")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/zip")
