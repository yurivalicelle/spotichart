# GitHub Packages - Spotichart

<div align="center">

![GitHub Package](https://img.shields.io/badge/GitHub-Packages-blue?logo=github)
![Private Package](https://img.shields.io/badge/Access-Private-red)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![Version](https://img.shields.io/badge/version-2.0.0-green)

</div>

Este documento fornece um guia completo para instalação, uso e publicação do pacote **spotichart** hospedado no GitHub Packages.

---

## 📋 Índice

- [O que é GitHub Packages](#o-que-é-github-packages)
- [Pré-requisitos](#pré-requisitos)
- [Instalação](#instalação)
- [Autenticação](#autenticação)
- [Uso](#uso)
- [Publicação (Maintainers)](#publicação-maintainers)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)

---

## 🎯 O que é GitHub Packages

GitHub Packages é um serviço de hospedagem de pacotes totalmente integrado ao GitHub. O **spotichart** está configurado como um **pacote privado**, o que significa que:

- ✅ Apenas usuários autorizados podem instalar o pacote
- ✅ Integração nativa com o repositório GitHub
- ✅ Publicação automatizada via GitHub Actions
- ✅ Versionamento vinculado às releases do GitHub
- ✅ Segurança enterprise-grade

---

## 🔑 Pré-requisitos

### 1. Acesso ao Repositório

Você precisa ter acesso ao repositório privado `yurivalicelle/spotichart`:

```bash
# Verifique se você tem acesso
gh repo view yurivalicelle/spotichart
```

### 2. Personal Access Token (PAT)

Crie um Personal Access Token com permissões de `read:packages`:

1. Acesse: https://github.com/settings/tokens/new
2. Dê um nome descritivo (ex: "Spotichart Package Access")
3. Selecione os escopos:
   - ✅ `read:packages` - Download de pacotes do GitHub Packages
   - ✅ `repo` (opcional) - Se o repositório for privado
4. Clique em "Generate token"
5. **IMPORTANTE**: Copie e salve o token imediatamente (você não poderá vê-lo novamente)

### 3. Python 3.9+

```bash
python --version  # Deve ser 3.9 ou superior
```

---

## 📦 Instalação

### Método 1: Via pip com autenticação inline (Recomendado para CI/CD)

```bash
pip install spotichart \
  --index-url https://oauth2:YOUR_GITHUB_TOKEN@pypi.pkg.github.com/yurivalicelle/spotichart/simple/
```

Substitua `YOUR_GITHUB_TOKEN` pelo seu Personal Access Token.

### Método 2: Via pip.conf (Recomendado para desenvolvimento local)

#### Linux/macOS

1. Crie ou edite o arquivo `~/.pip/pip.conf`:

```bash
mkdir -p ~/.pip
cat > ~/.pip/pip.conf << 'EOF'
[global]
extra-index-url = https://oauth2:YOUR_GITHUB_TOKEN@pypi.pkg.github.com/yurivalicelle/spotichart/simple/
EOF
```

2. Instale o pacote normalmente:

```bash
pip install spotichart
```

#### Windows

1. Crie ou edite o arquivo `%APPDATA%\pip\pip.ini`:

```ini
[global]
extra-index-url = https://oauth2:YOUR_GITHUB_TOKEN@pypi.pkg.github.com/yurivalicelle/spotichart/simple/
```

2. Instale o pacote normalmente:

```bash
pip install spotichart
```

### Método 3: Via requirements.txt

```txt
# requirements.txt
--index-url https://oauth2:YOUR_GITHUB_TOKEN@pypi.pkg.github.com/yurivalicelle/spotichart/simple/
spotichart==2.0.0
```

```bash
pip install -r requirements.txt
```

### Método 4: Via pyproject.toml (Poetry)

```toml
[[tool.poetry.source]]
name = "github"
url = "https://pypi.pkg.github.com/yurivalicelle/spotichart/simple/"
priority = "primary"

[tool.poetry.dependencies]
python = "^3.9"
spotichart = "^2.0.0"
```

Configure a autenticação:

```bash
poetry config http-basic.github oauth2 YOUR_GITHUB_TOKEN
poetry install
```

---

## 🔐 Autenticação

### Variável de Ambiente (Seguro)

A forma mais segura de armazenar seu token é usando variáveis de ambiente:

```bash
# Linux/macOS
echo 'export GITHUB_TOKEN="your_token_here"' >> ~/.bashrc
source ~/.bashrc

# Windows PowerShell
[System.Environment]::SetEnvironmentVariable('GITHUB_TOKEN', 'your_token_here', 'User')
```

Então use no pip:

```bash
pip install spotichart \
  --index-url https://oauth2:${GITHUB_TOKEN}@pypi.pkg.github.com/yurivalicelle/spotichart/simple/
```

### GitHub CLI (gh)

Se você usa o GitHub CLI:

```bash
gh auth login
gh auth token | pip install spotichart \
  --index-url https://oauth2:$(cat)@pypi.pkg.github.com/yurivalicelle/spotichart/simple/
```

---

## 🚀 Uso

Após a instalação, você pode usar o spotichart normalmente:

### CLI

```bash
# Verificar instalação
spotichart --version

# Configurar credenciais
spotichart config

# Criar playlist
spotichart create --region brazil --limit 1000
```

### Python API

```python
from spotichart.core.factory import SpotifyServiceFactory
from spotichart.core.scraper import KworbScraper

# Criar serviço
service = SpotifyServiceFactory.create()

# Scrape e criar playlist
scraper = KworbScraper()
tracks = scraper.scrape_region('brazil', limit=100)

# Processar tracks...
```

---

## 📤 Publicação (Maintainers)

### Publicação Automática (Recomendado)

A publicação é automática ao criar uma release no GitHub:

1. **Atualize a versão** no `pyproject.toml`:

```toml
[project]
version = "2.1.0"  # Nova versão
```

2. **Commit e push** das alterações:

```bash
git add pyproject.toml
git commit -m "Bump version to 2.1.0"
git push origin main
```

3. **Crie uma release** no GitHub:

```bash
# Via GitHub CLI
gh release create v2.1.0 \
  --title "v2.1.0 - Release Title" \
  --notes "Release notes here"

# Ou via interface web
# https://github.com/yurivalicelle/spotichart/releases/new
```

4. **Aguarde o workflow** `.github/workflows/publish.yml` executar automaticamente.

### Publicação Manual (Emergência)

Se precisar publicar manualmente:

```bash
# 1. Instalar dependências de build
pip install build twine

# 2. Build do pacote
python -m build

# 3. Verificar pacote
twine check dist/*

# 4. Publicar (requer GITHUB_TOKEN)
export GITHUB_TOKEN="your_token_here"
twine upload --repository-url https://upload.pypi.org/legacy/ \
  -u __token__ -p $GITHUB_TOKEN dist/*
```

### Publicação via Workflow Dispatch

Você também pode publicar manualmente via GitHub Actions:

1. Acesse: https://github.com/yurivalicelle/spotichart/actions/workflows/publish.yml
2. Clique em "Run workflow"
3. (Opcional) Especifique uma versão customizada
4. Clique em "Run workflow"

---

## 🔧 Troubleshooting

### Erro: "Could not find a version that satisfies the requirement spotichart"

**Causa**: Token inválido ou sem permissões corretas.

**Solução**:
1. Verifique se o token tem escopo `read:packages`
2. Verifique se você tem acesso ao repositório
3. Teste o token:

```bash
curl -H "Authorization: token YOUR_TOKEN" \
  https://api.github.com/user/packages
```

### Erro: "HTTP 401 Unauthorized"

**Causa**: Token expirado ou inválido.

**Solução**:
1. Gere um novo token em https://github.com/settings/tokens
2. Atualize suas configurações de pip

### Erro: "Package not found"

**Causa**: Pacote ainda não foi publicado ou versão não existe.

**Solução**:
1. Verifique as versões disponíveis:

```bash
curl -H "Authorization: token YOUR_TOKEN" \
  https://maven.pkg.github.com/yurivalicelle/spotichart/
```

2. Liste os pacotes publicados:

```bash
gh api /user/packages/container/spotichart/versions
```

### Cache de pip causando problemas

Limpe o cache:

```bash
pip cache purge
pip install --no-cache-dir spotichart
```

---

## ❓ FAQ

### 1. **O pacote é gratuito?**

Sim! GitHub Packages é gratuito para repositórios públicos e tem uma cota generosa para repositórios privados.

### 2. **Posso usar em CI/CD?**

Sim! Use o método de autenticação inline ou configure o token como secret:

```yaml
# GitHub Actions
- name: Install spotichart
  run: |
    pip install spotichart \
      --index-url https://oauth2:${{ secrets.GITHUB_TOKEN }}@pypi.pkg.github.com/yurivalicelle/spotichart/simple/
```

### 3. **Como atualizar para uma nova versão?**

```bash
pip install --upgrade spotichart
```

### 4. **Posso usar com Docker?**

Sim! Veja o exemplo no `Dockerfile`:

```dockerfile
FROM python:3.11-slim

ARG GITHUB_TOKEN
ENV GITHUB_TOKEN=${GITHUB_TOKEN}

RUN pip install spotichart \
  --index-url https://oauth2:${GITHUB_TOKEN}@pypi.pkg.github.com/yurivalicelle/spotichart/simple/

CMD ["spotichart", "--help"]
```

Build com:

```bash
docker build --build-arg GITHUB_TOKEN=$GITHUB_TOKEN -t my-spotichart .
```

### 5. **O token é seguro em requirements.txt?**

NÃO! Nunca commite tokens em arquivos. Use variáveis de ambiente:

```txt
# requirements.txt (SEGURO)
--index-url https://oauth2:${GITHUB_TOKEN}@pypi.pkg.github.com/yurivalicelle/spotichart/simple/
spotichart==2.0.0
```

### 6. **Como revogar acesso?**

Delete o Personal Access Token em:
https://github.com/settings/tokens

### 7. **Posso usar múltiplos índices?**

Sim! Use `extra-index-url` em vez de `index-url`:

```bash
pip install spotichart \
  --extra-index-url https://oauth2:${GITHUB_TOKEN}@pypi.pkg.github.com/yurivalicelle/spotichart/simple/
```

---

## 📚 Recursos Adicionais

- [GitHub Packages Documentation](https://docs.github.com/en/packages)
- [Working with the Python registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-python-registry)
- [Managing access to packages](https://docs.github.com/en/packages/learn-github-packages/configuring-a-packages-access-control-and-visibility)

---

## 📞 Suporte

Se você encontrar problemas:

1. Verifique este documento de troubleshooting
2. Consulte as [Issues do GitHub](https://github.com/yurivalicelle/spotichart/issues)
3. Entre em contato com os maintainers

---

<div align="center">

**🔒 Pacote Privado GitHub Packages**

Made with ❤️ by Yuri Valicelle

[⬆ Voltar ao topo](#github-packages---spotichart)

</div>
