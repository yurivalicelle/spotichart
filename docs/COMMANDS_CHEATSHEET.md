# 🎵 Spotify Playlist Creator - Cheatsheet de Comandos

Guia rápido com os comandos mais usados!

---

## 🚀 Início Rápido

```bash
# 1. Verificar configuração
spotify-playlist config

# 2. Ver regiões disponíveis
spotify-playlist regions

# 3. Preview dos charts (sem criar playlist)
spotify-playlist preview --region brazil --limit 10

# 4. Criar sua primeira playlist
spotify-playlist create --region brazil --limit 100 --name "Meu Top 100"
```

---

## 📋 Comandos Principais

### ⚙️ Configuração

```bash
# Ver configuração atual
spotify-playlist config

# Verificar credenciais
cat .env

# Editar configuração
nano .env
```

### 🌍 Regiões

```bash
# Listar todas as regiões
spotify-playlist regions

# Regiões disponíveis:
# - brazil
# - global
# - us
# - uk
```

### 👀 Preview (sem criar playlist)

```bash
# Preview Brazil top 10
spotify-playlist preview --region brazil --limit 10

# Preview Global top 20
spotify-playlist preview --region global --limit 20

# Preview US top 50
spotify-playlist preview --region us --limit 50
```

### ✨ Criar Playlists

```bash
# Criar playlist Brasil - Top 500
spotify-playlist create --region brazil --limit 500

# Criar com nome customizado
spotify-playlist create --region global --limit 100 --name "My Global Top 100"

# Criar playlist pública
spotify-playlist create --region us --public --limit 200

# Playlist com debug ativado
spotify-playlist --debug create --region uk --limit 50
```

---

## 🛠️ Comandos Make

### Instalação

```bash
# Setup completo
make setup

# Instalar dependências de produção
make install

# Instalar dependências de dev
make install-dev
```

### Execução

```bash
# Mostrar help do CLI
make run

# Criar playlist Brasil (500 tracks)
make run-brazil

# Criar playlist Global (500 tracks)
make run-global

# Preview charts
make preview
```

### Testes

```bash
# Rodar todos os testes
make test

# Testes com output verbose
make test-verbose

# Gerar relatório de coverage
make coverage
```

### Qualidade de Código

```bash
# Formatar código
make format

# Rodar linters
make lint

# Type checking
make type-check

# Security scan
make security

# Rodar todos os pre-commit hooks
make pre-commit
```

### Docker

```bash
# Build da imagem
make docker-build

# Rodar container
make docker-run

# Limpar recursos Docker
make docker-clean
```

### Manutenção

```bash
# Limpar cache
make clean

# Limpeza profunda (remove venv)
make clean-all

# Ver documentação
make docs
```

---

## 🐳 Comandos Docker

### Docker Compose

```bash
# Build
docker-compose build

# Ver configuração
docker-compose run --rm spotify-playlist config

# Ver regiões
docker-compose run --rm spotify-playlist regions

# Preview
docker-compose run --rm spotify-playlist preview --region brazil --limit 10

# Criar playlist
docker-compose run --rm spotify-playlist create --region brazil --limit 500

# Com debug
docker-compose run --rm -e LOG_LEVEL=DEBUG spotify-playlist create --region brazil
```

### Docker Direto

```bash
# Build
docker build -t spotify-playlist-creator .

# Run
docker run --rm \
  --env-file .env \
  -v $(pwd)/logs:/app/logs \
  spotify-playlist-creator config

# Criar playlist
docker run --rm \
  --env-file .env \
  -v $(pwd)/logs:/app/logs \
  spotify-playlist-creator create --region brazil --limit 500
```

---

## 🔍 Debug e Troubleshooting

### Ver Logs

```bash
# Logs em tempo real
tail -f logs/spotify_playlist.log

# Últimas 50 linhas
tail -50 logs/spotify_playlist.log

# Ver todos os logs
cat logs/spotify_playlist.log

# Buscar erros
grep ERROR logs/spotify_playlist.log
```

### Debug Mode

```bash
# Ativar debug (muito verbose)
spotify-playlist --debug create --region brazil

# Ver logs detalhados
LOG_LEVEL=DEBUG spotify-playlist create --region brazil
```

### Limpar Cache

```bash
# Remover cache do Spotify
rm -rf .cache/ .spotify_cache

# Limpar tudo
make clean

# Reinstalar
pip install -e .
```

---

## 📊 Exemplos de Uso

### Caso 1: Criar múltiplas playlists

```bash
# Loop para criar playlists de todas as regiões
for region in brazil global us uk; do
  spotify-playlist create --region $region --limit 100 --name "Top 100 - $region"
done
```

### Caso 2: Playlist diária automatizada

```bash
# Adicionar ao crontab
crontab -e

# Executar todo dia às 8h
0 8 * * * cd /path/to/project && spotify-playlist create --region brazil --limit 500
```

### Caso 3: Preview antes de criar

```bash
# Ver preview primeiro
spotify-playlist preview --region global --limit 20

# Se gostar, criar
spotify-playlist create --region global --limit 500 --name "My Global 500"
```

### Caso 4: Teste rápido

```bash
# Testar com poucos tracks
spotify-playlist create --region brazil --limit 10 --name "Teste"
```

---

## 🎯 Atalhos Úteis

### Aliases (adicione ao .bashrc ou .zshrc)

```bash
# Adicionar aliases
echo 'alias spc="spotify-playlist"' >> ~/.bashrc
echo 'alias spc-br="spotify-playlist create --region brazil --limit 500"' >> ~/.bashrc
echo 'alias spc-preview="spotify-playlist preview --region brazil --limit 20"' >> ~/.bashrc

# Recarregar
source ~/.bashrc

# Agora use:
spc config
spc-preview
spc-br
```

### Funções Shell

```bash
# Adicionar ao .bashrc
spc-create() {
    spotify-playlist create --region "$1" --limit "$2" --name "Top $2 - $1"
}

# Usar:
spc-create brazil 500
spc-create global 200
```

---

## 🔑 Variáveis de Ambiente

```bash
# .env file
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
REDIRECT_URI=http://localhost:8888/callback
LOG_LEVEL=INFO                    # DEBUG, INFO, WARNING, ERROR
PLAYLIST_LIMIT=1000               # Default limit
REQUEST_TIMEOUT=30                # HTTP timeout
CACHE_ENABLED=True                # Enable/disable cache
```

---

## 📱 Comandos Por Caso de Uso

### Para Iniciantes

```bash
spotify-playlist config          # Verificar setup
spotify-playlist regions         # Ver opções
spotify-playlist preview -r brazil -l 10  # Testar
spotify-playlist create -r brazil -l 50   # Criar pequena
```

### Para Uso Regular

```bash
make run-brazil                  # Playlist Brasil
make run-global                  # Playlist Global
make preview                     # Preview rápido
```

### Para Desenvolvedores

```bash
make test                        # Testes
make lint                        # Linting
make format                      # Formatar
make coverage                    # Coverage
```

### Para DevOps

```bash
make docker-build                # Build
docker-compose up                # Deploy
make docker-clean                # Cleanup
```

---

## 🆘 Resolução de Problemas

### Erro de Autenticação

```bash
# Limpar cache
rm -rf .cache .spotify_cache

# Verificar credenciais
spotify-playlist config

# Testar novamente
spotify-playlist create -r brazil -l 10
```

### Erro de Scraping

```bash
# Testar preview primeiro
spotify-playlist preview -r brazil -l 5

# Ver logs
tail -50 logs/spotify_playlist.log

# Tentar com debug
spotify-playlist --debug preview -r brazil -l 5
```

### Erro de Instalação

```bash
# Reinstalar
pip uninstall spotify-playlist-creator
pip install -e .

# Verificar
spotify-playlist --version
```

---

## 📝 Notas Importantes

1. **Primeiro uso**: Browser abrirá para autenticação OAuth
2. **Cache**: Token salvo em `.spotify_cache` (válido por 1h)
3. **Limits**: Spotify aceita max 100 tracks por batch (automático)
4. **Rate limit**: Delay automático entre requests
5. **Logs**: Salvos em `logs/spotify_playlist.log` com rotação

---

## 🎓 Recursos Adicionais

- **Help detalhado**: `spotify-playlist COMMAND --help`
- **Makefile**: `make help`
- **Documentação**: Ver `docs/` e arquivos `.md`
- **Issues**: GitHub Issues para reportar problemas

---

## ⚡ Comandos Mais Usados

```bash
# Top 5 comandos essenciais:

1. spotify-playlist config
2. spotify-playlist preview --region brazil --limit 20
3. spotify-playlist create --region brazil --limit 500
4. make run-brazil
5. make test
```

---

**Dica**: Use `Tab` para autocompletar comandos!

**Atalho**: Adicione `alias spc='spotify-playlist'` para comandos mais rápidos!

---

Criado com ❤️ - Spotify Playlist Creator v2.0.0
