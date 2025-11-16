# Publishing Guide - Spotichart GitHub Package

Este documento fornece instruções para maintainers publicarem novas versões do pacote no GitHub Packages.

## 📋 Pré-requisitos

- Acesso de maintainer ao repositório `yurivalicelle/spotichart`
- Permissões para criar releases no GitHub
- GitHub CLI (`gh`) instalado (opcional, mas recomendado)

## 🚀 Processo de Publicação

### 1. Preparação da Nova Versão

#### a) Atualizar a Versão

Edite o arquivo `pyproject.toml` e atualize a versão:

```toml
[project]
name = "spotichart"
version = "2.1.0"  # ← Atualize aqui
```

#### b) Atualizar o CHANGELOG.md

Adicione as mudanças da nova versão no arquivo `CHANGELOG.md`:

```markdown
### Version 2.1.0 (2025-01-XX)

**New Features:**
- Feature 1
- Feature 2

**Bug Fixes:**
- Fix 1
- Fix 2

**Improvements:**
- Improvement 1
```

#### c) Executar Testes

Certifique-se de que todos os testes passam:

```bash
# Executar todos os testes
pytest

# Executar linting
make lint

# Executar formatação
make format

# Executar tudo
make test
```

### 2. Commit e Push

```bash
# Adicionar arquivos modificados
git add pyproject.toml CHANGELOG.md

# Criar commit
git commit -m "Bump version to 2.1.0"

# Push para main
git push origin main
```

### 3. Criar a Release

#### Opção A: Via GitHub CLI (Recomendado)

```bash
# Criar release e tag
gh release create v2.1.0 \
  --title "v2.1.0 - Release Title" \
  --notes "$(cat <<'EOF'
## What's Changed

### New Features
- Feature 1 description
- Feature 2 description

### Bug Fixes
- Fix 1 description
- Fix 2 description

### Improvements
- Improvement 1 description

**Full Changelog**: https://github.com/yurivalicelle/spotichart/compare/v2.0.0...v2.1.0
EOF
)"
```

#### Opção B: Via Interface Web do GitHub

1. Acesse: https://github.com/yurivalicelle/spotichart/releases/new
2. Preencha os campos:
   - **Tag version**: `v2.1.0`
   - **Release title**: `v2.1.0 - Release Title`
   - **Description**: Copie as notas do CHANGELOG
3. Marque "Set as the latest release"
4. Clique em "Publish release"

### 4. Aguardar a Publicação Automática

O workflow `.github/workflows/publish.yml` será acionado automaticamente e irá:

1. ✅ Fazer checkout do código
2. ✅ Configurar Python 3.11
3. ✅ Instalar dependências de build
4. ✅ Extrair versão do pyproject.toml
5. ✅ Construir o pacote (wheel e source)
6. ✅ Verificar a integridade do pacote
7. ✅ Publicar no GitHub Packages

### 5. Verificar a Publicação

#### Via GitHub Actions

1. Acesse: https://github.com/yurivalicelle/spotichart/actions
2. Verifique se o workflow "Publish to GitHub Packages" foi executado com sucesso
3. Clique no workflow para ver os logs detalhados

#### Via GitHub Packages

1. Acesse: https://github.com/yurivalicelle/spotichart/packages
2. Verifique se a nova versão aparece na lista

#### Via GitHub CLI

```bash
# Listar pacotes
gh api /users/yurivalicelle/packages

# Verificar versões
gh api /users/yurivalicelle/packages/container/spotichart/versions
```

### 6. Testar a Instalação

Teste a instalação do pacote publicado:

```bash
# Criar ambiente virtual limpo
python -m venv test-env
source test-env/bin/activate

# Instalar a nova versão
export GITHUB_TOKEN="your_token_here"
pip install spotichart==2.1.0 \
  --index-url https://oauth2:${GITHUB_TOKEN}@pypi.pkg.github.com/yurivalicelle/spotichart/simple/

# Verificar versão instalada
spotichart --version

# Desativar e remover
deactivate
rm -rf test-env
```

## 🔄 Publicação Manual (Emergência)

Se o workflow automático falhar, você pode publicar manualmente:

### 1. Build Local

```bash
# Limpar builds anteriores
rm -rf dist/ build/ src/*.egg-info

# Instalar dependências de build
pip install build twine

# Build do pacote
python -m build

# Verificar pacote
twine check dist/*
```

### 2. Publicar Manualmente

```bash
# Configurar token
export GITHUB_TOKEN="your_github_token"

# Criar arquivo .pypirc temporário
cat > ~/.pypirc << EOF
[distutils]
index-servers =
    github

[github]
repository = https://maven.pkg.github.com/yurivalicelle/spotichart
username = yurivalicelle
password = ${GITHUB_TOKEN}
EOF

# Upload para GitHub Packages
twine upload --repository github dist/*

# Remover .pypirc por segurança
rm ~/.pypirc
```

## 🔧 Troubleshooting

### Erro: Workflow não foi acionado

**Solução**: Execute manualmente via workflow dispatch:

```bash
gh workflow run publish.yml
```

Ou via interface web:
1. Acesse: https://github.com/yurivalicelle/spotichart/actions/workflows/publish.yml
2. Clique em "Run workflow"
3. Selecione a branch "main"
4. Clique em "Run workflow"

### Erro: "Package already exists"

**Causa**: A versão já foi publicada anteriormente.

**Solução**:
1. Incremente a versão no `pyproject.toml`
2. Refaça o processo de publicação

### Erro: "Permission denied"

**Causa**: Token sem permissões adequadas.

**Solução**:
1. Verifique se você tem permissões de maintainer no repositório
2. Verifique se o `GITHUB_TOKEN` nas Actions tem permissão de `packages: write`

### Build falha localmente

**Solução**:

```bash
# Limpar tudo
make clean
rm -rf dist/ build/ src/*.egg-info

# Reinstalar dependências
pip install -e ".[dev]"

# Tentar build novamente
python -m build
```

## 📝 Checklist de Publicação

Use este checklist antes de publicar:

- [ ] Todos os testes passam (`pytest`)
- [ ] Linting está ok (`make lint`)
- [ ] Código está formatado (`make format`)
- [ ] Versão atualizada em `pyproject.toml`
- [ ] CHANGELOG.md atualizado
- [ ] Commit e push para main
- [ ] Release criada no GitHub
- [ ] Workflow executou com sucesso
- [ ] Pacote aparece no GitHub Packages
- [ ] Instalação testada em ambiente limpo
- [ ] Documentação atualizada (se necessário)

## 🔐 Segurança

### Tokens e Secrets

- **NUNCA** commite tokens no repositório
- Use GitHub Secrets para armazenar tokens sensíveis
- Revogue tokens antigos periodicamente
- Use tokens com escopos mínimos necessários

### Verificação de Pacote

Sempre execute `twine check` antes de publicar:

```bash
twine check dist/*
```

### Assinatura de Releases (Opcional)

Para adicionar uma camada extra de segurança:

```bash
# Criar release assinada
gh release create v2.1.0 --verify-tag
```

## 📊 Métricas e Monitoramento

### Visualizar Downloads

Acesse: https://github.com/yurivalicelle/spotichart/packages para ver estatísticas de download.

### Logs de Publicação

Todos os workflows são registrados em: https://github.com/yurivalicelle/spotichart/actions

## 🆘 Suporte

Se você encontrar problemas durante a publicação:

1. Verifique os logs do GitHub Actions
2. Consulte este guia
3. Verifique a documentação do GitHub Packages
4. Abra uma issue no repositório

## 📚 Recursos Adicionais

- [GitHub Packages Documentation](https://docs.github.com/en/packages)
- [Python Packaging Guide](https://packaging.python.org/)
- [Semantic Versioning](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)

---

**Última atualização**: 2025-01-16
**Maintainer**: Yuri Valicelle
