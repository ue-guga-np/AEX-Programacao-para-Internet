# Gerenciador de Estoque — Marcenaria

Sistema web de controle de estoque feito com Django e SQLite. O aplicativo permite gerenciar materiais e movimentações, e o painel administrativo padrão do Django continua disponível em `/admin/`.

## Requisitos
- Python instalado
- pip

## Executar no Windows
Abra o terminal nesta pasta e execute um comando por vez:

```bat
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python manage.py makemigrations estoque
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Durante `createsuperuser`, escolha um nome de usuário e uma senha. A senha não aparece enquanto você digita; isso é normal.

Abra http://127.0.0.1:8000/ para ser direcionado ao Django Admin, ou acesse diretamente http://127.0.0.1:8000/admin/. Entre com o usuário e a senha criados.

## Acessar de outro computador na mesma rede

1. No computador que executa o sistema, descubra o IPv4 com `ipconfig`.
2. Inicie o servidor com:

   ```bat
   python manage.py runserver 0.0.0.0:8000
   ```

3. No outro computador conectado à mesma rede, abra `http://IP-DO-COMPUTADOR:8000/`, substituindo pelo IPv4 encontrado no passo 1; o endereço direcionará ao Django Admin.
4. Se o Windows perguntar, permita o acesso na rede privada. Pode ser necessário ajustar o Firewall do Windows.

O computador que executa o Django precisa permanecer ligado e com o terminal aberto. Esta configuração é para demonstração em rede local, não para publicar o sistema na internet. Para acesso externo, é necessário hospedar a aplicação com configuração de segurança apropriada.

## O que está disponível
- Cadastro, edição, consulta e exclusão de produtos pela interface do sistema e pelo Django Admin.
- Cadastro e consulta de categorias e unidades de medida pelo Django Admin.
- Busca de produtos por nome ou categoria e indicação de estoque crítico.
- Retirada de estoque com atualização do saldo e registro da movimentação.
- Consulta do histórico de movimentações.
- Banco de dados SQLite.

O registro de entradas pela interface do sistema, exportação para Excel, fotos dos produtos e backup/restauração não estão implementados nesta versão.
