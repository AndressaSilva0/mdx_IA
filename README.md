# 🌟 Mermãs Digitais | MDX 2026 • IFMA
## Jogo Interativo de Decodificação de Prompts de Inteligência Artificial

Aplicação web desenvolvida em **Python** e **Django** (padrão MVT/MVC) com integração nativa ao **Google Gemini AI**, suporte a banco de dados **MySQL** e estilização via **Tailwind CSS**, reproduzindo com máxima fidelidade o layout e identidade visual do evento **MDX 2026 (Mermãs Digitais • IFMA)**.

---

## 🚀 Opções de Deploy Gratuito

O projeto já está 100% configurado com arquivos de build, middleware de arquivos estáticos (**WhiteNoise**), servidor WSGI de produção (**Gunicorn**) e drivers para deploy imediato em duas plataformas gratuitas:

1. **[Render.com](#1-deploy-no-rendercom-recomendado--git-push)**: Deploy contínuo automático a cada `git push` com HTTPS grátis.
2. **[PythonAnywhere](#2-deploy-no-pythonanywhere-com-mysql-grátis)**: Hospedagem com **MySQL nativo gratuito** sem expirar.

---

### 1. Deploy no Render.com (Recomendado / Git Push)

O Render permite conectar seu repositório GitHub e fazer o deploy gratuitamente em minutos.

#### Arquivos inclusos no projeto:
- `build.sh`: Instala dependências, roda migrações, coleta estáticos via WhiteNoise e cria o desafio inicial.
- `Procfile`: Inicia o servidor de produção com Gunicorn.
- `render.yaml`: Blueprint com configurações pré-definidas.

#### Passo a Passo no Render:
1. Suba o projeto para seu GitHub (privado ou público):
   ```bash
   git add .
   git commit -m "Deploy MDX 2026"
   git remote add origin https://github.com/SEU_USUARIO/mdx_IA.git
   git push -u origin main
   ```
2. Acesse [render.com](https://render.com) e faça login (pode usar o login do GitHub).
3. No painel, clique em **New +** ➔ **Web Service**.
4. Conecte o repositório `mdx_IA`.
5. Preencha as configurações:
   - **Name**: `mermas-digitais-mdx2026`
   - **Language**: `Python`
   - **Region**: Qualquer uma (ex: `Ohio` ou `Frankfurt`)
   - **Branch**: `main` (ou `master`)
   - **Build Command**: `./build.sh`
   - **Start Command**: `gunicorn mdx_project.wsgi:application --bind 0.0.0.0:$PORT`
   - **Plan**: `Free`
6. Na seção **Environment Variables** (Variáveis de Ambiente), adicione:
   - `SECRET_KEY`: `sua-chave-super-secreta-mdx-2026`
   - `DEBUG`: `False`
   - `USE_SQLITE`: `True` *(ou conecte a um MySQL externo)*
   - `GEMINI_API_KEY`: `AQ.Ab8RN6LhFJXwc2NrAaSy6reqdrwFHuVXlxoUa6PoCeLcl7DoLw`
   - `GEMINI_MODEL`: `gemini-3.1-flash-lite`
   - `ALLOWED_HOSTS`: `.onrender.com`
7. Clique em **Create Web Service**. Em poucos minutos sua aplicação estará no ar com link público `https://mermas-digitais-mdx2026.onrender.com`!

---

### 2. Deploy no PythonAnywhere (com MySQL Grátis)

O PythonAnywhere é ideal para quem quer manter o **banco MySQL gratuito**:

#### Passo 1: Criar o Banco MySQL
1. Acesse o [pythonanywhere.com](https://www.pythonanywhere.com) e faça login na sua conta gratuita.
2. Vá na aba **Databases**.
3. Crie uma senha para o MySQL e clique em **Initialize MySQL**.
4. Crie o banco `mdx_db`. O nome completo será `seu_usuario$mdx_db`.
5. Anote o host MySQL: `seu_usuario.mysql.pythonanywhere-services.com`.

#### Passo 2: Clonar o Código e Rodar o Deploy Automatizado
Abra um **Bash Console** no PythonAnywhere e execute:
```bash
git clone https://github.com/SEU_USUARIO/mdx_IA.git
cd mdx_IA
bash deploy_pa.sh
```

#### Passo 3: Configurar o `.env` no PythonAnywhere
Edite o `.env` do servidor:
```bash
nano .env
```
Preencha com seus dados do PythonAnywhere:
```env
SECRET_KEY=sua-chave-secreta-complexa
DEBUG=False
ALLOWED_HOSTS=seu_usuario.pythonanywhere.com

USE_SQLITE=False
DB_ENGINE=mysql
DB_NAME=seu_usuario$mdx_db
DB_USER=seu_usuario
DB_PASSWORD=sua_senha_mysql_pythonanywhere
DB_HOST=seu_usuario.mysql.pythonanywhere-services.com
DB_PORT=3306

GEMINI_API_KEY=AQ.Ab8RN6LhFJXwc2NrAaSy6reqdrwFHuVXlxoUa6PoCeLcl7DoLw
GEMINI_MODEL=gemini-3.1-flash-lite
```

#### Passo 4: Configurar a Aba "Web"
1. Vá na aba **Web** do PythonAnywhere e clique em **Add a new web app** (Manual configuration ➔ Python 3.10+).
2. Na seção **Virtualenv**, informe: `/home/seu_usuario/mdx_IA/.venv`.
3. Na seção **Code**, clique no link do **WSGI configuration file** e cole o conteúdo do arquivo [`pythonanywhere_wsgi.py`](file:///home/andressa-silva/mdx_IA/pythonanywhere_wsgi.py).
4. Na seção **Static files**:
   - **URL**: `/static/` ➔ **Directory**: `/home/seu_usuario/mdx_IA/staticfiles`
   - **URL**: `/media/` ➔ **Directory**: `/home/seu_usuario/mdx_IA/media`
5. Clique no botão verde **Reload seu_usuario.pythonanywhere.com**.

---

## 🎮 Operação no Estande do Evento
- **Alternância Rápida de Modalidade**:
  - No topo da tela há o botão **"Mudar para Modo Equipe"**.
  - Digite a **Senha de 6 Dígitos** (padrão: `262026`, configurável via `EQUIPE_PIN` no `.env`) para entrar no modo de gestão técnica.
  - Para voltar à tela das alunas, basta clicar em **"👩‍🎓 Mudar para Modo Participante"**.
- **Registro das Participantes**:
  - Cada aluna digita seu **Nome Completo** e **E-mail**.
  - O sistema registra e trava após exatamente **3 tentativas** por rodada.
  - O ranking e o relatório para certificados guardam tanto o nome quanto o e-mail da participante.
- **Link do Jogo**: `/`
- **Placar das Mermãs**: `/ranking/`
- **Painel Administrativo da Equipe**: `/operador/desafios/` e `/operador/julgamento/` (ou `/admin/`)
