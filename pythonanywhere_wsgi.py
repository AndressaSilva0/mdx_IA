"""
Configuração WSGI pronta para o PythonAnywhere
Copie e cole este conteúdo no seu arquivo WSGI do PythonAnywhere
(aba 'Web' -> link 'WSGI configuration file')
Substitua 'seu_usuario' pelo seu nome de usuário no PythonAnywhere.
"""

import os
import sys

# Caminho absoluto da pasta do projeto no PythonAnywhere
USERNAME = 'seu_usuario'  # <-- ALTERE AQUI PARA SEU USERNAME
PROJECT_DIR = f'/home/{USERNAME}/mdx_IA'

if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

# Ativa as variáveis do .env
from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_DIR, '.env'))

# Define o módulo de settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'mdx_project.settings'

# Importa o PyMySQL para o MySQL do PythonAnywhere
try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

