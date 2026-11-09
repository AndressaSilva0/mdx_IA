# Guia de Deploy Gratuito - Mermãs Digitais | MDX STEAM 2026

Este projeto foi estruturado para ser hospedado **100% gratuitamente** em plataformas que aceitam Python/Django com banco de dados SQLite ou MySQL e entrega de arquivos estáticos via WhiteNoise.

---

## Opção 1: Render.com (Recomendado — Deploy em 1 Clique)

O Render oferece plano gratuito com suporte nativo a Python e deploy automático via GitHub utilizando o arquivo `render.yaml` já configurado na raiz do projeto.

### Passo a Passo:
1. Acesse [render.com](https://render.com) e crie ou faça login na sua conta gratuita com o GitHub.
2. No painel inicial (Dashboard), clique no botão **New +** e selecione **Blueprint**.
3. Conecte sua conta do GitHub e selecione o repositório:
   `https://github.com/AndressaSilva0/mdx_IA`
4. O Render detectará automaticamente o arquivo `render.yaml` contendo:
   - **Build Command**: `./build.sh` (instala dependências, executa migrações e coleta estáticos).
   - **Start Command**: `gunicorn mdx_project.wsgi:application --bind 0.0.0.0:$PORT`
   - **Ambiente**: Python 3.11 com SQLite (`USE_SQLITE=True`).
5. Informe a variável de ambiente:
   - `GEMINI_API_KEY`: sua chave de API da IA.
6. Clique em **Apply** / **Create Web Service**.
7. Em cerca de 2 a 3 minutos, seu app estará no ar com HTTPS gratuito em:
   `https://mermas-digitais-mdx2026.onrender.com`

---

## Opção 2: PythonAnywhere (Excelente para Feiras e Demonstrações)

O PythonAnywhere permite hospedar gratuitamente aplicações WSGI em Python sem desligar por inatividade.

### Passo a Passo:
1. Acesse [pythonanywhere.com](https://www.pythonanywhere.com) e crie uma conta gratuita (ex: `mermasifma`).
2. Abra um terminal **Bash Console** no painel do PythonAnywhere e execute:
   ```bash
   git clone https://github.com/AndressaSilva0/mdx_IA.git
   cd mdx_IA
   chmod +x deploy_pa.sh
   ./deploy_pa.sh
   ```
3. Acesse a aba **Web** no painel do PythonAnywhere:
   - Crie um novo Web App selecionando **Manual Configuration** -> **Python 3.10** ou **3.11**.
   - Defina o **Source code**: `/home/seu-usuario/mdx_IA`
   - Defina o **Virtualenv**: `/home/seu-usuario/mdx_IA/.venv`
   - No arquivo **WSGI configuration file**, abra e cole o conteúdo do arquivo `pythonanywhere_wsgi.py` presente na raiz do projeto, ajustando seu nome de usuário.
4. Na seção **Static Files**:
   - URL: `/static/` -> Directory: `/home/seu-usuario/mdx_IA/staticfiles`
   - URL: `/media/` -> Directory: `/home/seu-usuario/mdx_IA/media`
5. Clique no botão verde **Reload seu-usuario.pythonanywhere.com** no topo da página.
6. Acesse seu endereço: `https://seu-usuario.pythonanywhere.com`

---

## Opção 3: Railway ou Fly.io (Via Docker)

O repositório já possui um `Dockerfile` otimizado:
1. Acesse [railway.app](https://railway.app).
2. Clique em **New Project** -> **Deploy from GitHub repo**.
3. Selecione o repositório `mdx_IA`.
4. Defina as variáveis de ambiente (`SECRET_KEY`, `USE_SQLITE=True`, `GEMINI_API_KEY`).
5. O Railway fará o build e fornecerá uma URL pública imediatamente.

---

## Credenciais Padrão do Modo Equipe

* **PIN de 6 dígitos**: `262026`
* **Usuário Admin padrão (se criado)**: `operador`