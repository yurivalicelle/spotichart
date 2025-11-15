# 🔧 Troubleshooting Guide

Soluções para problemas comuns no Spotify Playlist Creator.

---

## ✅ Problema Resolvido: Cache Warnings

### Sintoma
```
Couldn't read cache at: .cache
Couldn't write token to cache at: .cache
```

### Causa
O Spotipy tentava usar `.cache` como arquivo, mas agora é um diretório.

### Solução ✅ (Já Aplicada)
O código foi atualizado para usar `.cache/spotify_token.cache` como arquivo de cache.

**Status**: ✅ **RESOLVIDO** - Funciona perfeitamente agora!

---

## 🆘 Problemas Comuns

### 1. Erro de Autenticação

#### Sintoma
```
SpotifyAuthError: Authentication failed
```

#### Soluções

**a) Verificar credenciais**
```bash
spotify-playlist config
cat .env
```

Certifique-se que `.env` tem:
```env
SPOTIFY_CLIENT_ID=seu_client_id
SPOTIFY_CLIENT_SECRET=seu_client_secret
REDIRECT_URI=http://localhost:8888/callback
```

**b) Limpar cache e tentar novamente**
```bash
rm -rf .cache/
spotify-playlist create --region brazil --limit 10
```

**c) Verificar redirect URI**
- Deve ser exatamente `http://localhost:8888/callback`
- Deve estar configurado no Spotify Developer Dashboard

---

### 2. Comando Não Encontrado

#### Sintoma
```bash
spotify-playlist: command not found
```

#### Soluções

**a) Reinstalar o pacote**
```bash
pip install -e .
```

**b) Verificar se está no ambiente virtual correto**
```bash
which python
which spotify-playlist
```

**c) Ativar ambiente virtual**
```bash
source venv/bin/activate  # macOS/Linux
# ou
venv\Scripts\activate  # Windows
```

---

### 3. Erro ao Importar Módulos

#### Sintoma
```python
ModuleNotFoundError: No module named 'spotify_playlist_creator'
```

#### Soluções

**a) Instalar dependências**
```bash
pip install -e .
```

**b) Verificar PYTHONPATH**
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

**c) Reinstalar em modo desenvolvimento**
```bash
pip uninstall spotify-playlist-creator
pip install -e ".[dev]"
```

---

### 4. Scraping Falha

#### Sintoma
```
ScrapingError: Table not found
```

#### Soluções

**a) Verificar conexão internet**
```bash
ping kworb.net
```

**b) Testar preview primeiro**
```bash
spotify-playlist preview --region brazil --limit 5
```

**c) Ver logs detalhados**
```bash
spotify-playlist --debug preview --region brazil --limit 5
tail -50 logs/spotify_playlist.log
```

**d) Tentar outra região**
```bash
spotify-playlist preview --region global --limit 5
```

---

### 5. Tracks Não Encontrados

#### Sintoma
```
Tracks not found: 50
```

#### Causas
- Track IDs do Kworb podem estar incorretos
- Tracks removidos do Spotify
- Restrições regionais

#### Soluções

**a) Normal ter alguns tracks falhando**
- 5-10% de falha é normal
- Spotify remove tracks ocasionalmente

**b) Ver logs para detalhes**
```bash
grep "not found" logs/spotify_playlist.log
```

**c) Tentar com menos tracks**
```bash
spotify-playlist create --region brazil --limit 100
```

---

### 6. Docker Problemas

#### Sintoma
```
docker: command not found
```

#### Soluções

**a) Instalar Docker**
- macOS: Docker Desktop
- Linux: `sudo apt-get install docker.io docker-compose`
- Windows: Docker Desktop

**b) Verificar se Docker está rodando**
```bash
docker --version
docker-compose --version
```

**c) Build da imagem**
```bash
make docker-build
# ou
docker-compose build
```

---

### 7. Permissões Negadas

#### Sintoma
```
Permission denied: /Users/.../logs/spotify_playlist.log
```

#### Soluções

**a) Criar diretório de logs**
```bash
mkdir -p logs
chmod 755 logs
```

**b) Verificar permissões**
```bash
ls -la logs/
```

**c) Rodar com sudo (não recomendado)**
```bash
sudo spotify-playlist create --region brazil
```

---

### 8. Erro ao Criar Playlist

#### Sintoma
```
PlaylistCreationError: Playlist creation failed
```

#### Soluções

**a) Verificar autenticação**
```bash
rm -rf .cache/
spotify-playlist config
```

**b) Verificar escopo OAuth**
- Deve ter `playlist-modify-private`

**c) Ver logs**
```bash
tail -50 logs/spotify_playlist.log
```

**d) Testar com playlist pequena**
```bash
spotify-playlist create --region brazil --limit 10 --name "Teste"
```

---

### 9. Rate Limiting

#### Sintoma
```
Too many requests
```

#### Soluções

**a) Aguardar alguns minutos**
- Spotify tem rate limits
- Código já tem delays automáticos

**b) Reduzir número de tracks**
```bash
spotify-playlist create --region brazil --limit 100
```

**c) Usar batch processing menor**
- Já configurado automaticamente

---

### 10. Browser Não Abre (OAuth)

#### Sintoma
Browser não abre automaticamente para autenticação

#### Soluções

**a) Copiar URL manualmente**
```
1. Comando mostra URL
2. Copie a URL
3. Cole no browser
4. Autorize
5. Copie URL de callback
6. Cole no terminal
```

**b) Verificar redirect URI**
```bash
echo $REDIRECT_URI
# Deve ser: http://localhost:8888/callback
```

---

## 🔍 Comandos de Debug

### Ver Logs em Tempo Real
```bash
tail -f logs/spotify_playlist.log
```

### Ver Últimas Linhas
```bash
tail -50 logs/spotify_playlist.log
```

### Buscar Erros
```bash
grep ERROR logs/spotify_playlist.log
grep -i "failed" logs/spotify_playlist.log
```

### Debug Mode
```bash
spotify-playlist --debug create --region brazil --limit 10
```

### Verificar Configuração
```bash
spotify-playlist config
cat .env
```

### Verificar Instalação
```bash
which spotify-playlist
pip show spotify-playlist-creator
```

### Ver Versão
```bash
spotify-playlist --version
```

---

## 🧹 Comandos de Limpeza

### Limpar Cache
```bash
rm -rf .cache/
rm -rf __pycache__/
```

### Limpar Logs
```bash
rm -rf logs/*.log
```

### Limpar Tudo
```bash
make clean
```

### Reinstalar
```bash
pip uninstall spotify-playlist-creator
pip install -e .
```

---

## 📊 Verificação de Saúde

Execute estes comandos para verificar se tudo está OK:

```bash
# 1. Configuração
spotify-playlist config

# 2. Regiões
spotify-playlist regions

# 3. Preview (sem criar playlist)
spotify-playlist preview --region brazil --limit 5

# 4. Criar playlist teste
spotify-playlist create --region brazil --limit 10 --name "Teste"

# ✅ Se todos funcionarem, está tudo OK!
```

---

## 🆘 Ainda com Problemas?

### 1. Ver Issues no GitHub
```bash
# Pesquisar issues similares
https://github.com/yourusername/spotify-playlist-creator/issues
```

### 2. Criar Nova Issue
Inclua:
- Comando executado
- Erro completo
- Output de `spotify-playlist config`
- Últimas 50 linhas do log
- Sistema operacional e versão Python

### 3. Verificar Documentação
- `START_HERE.md` - Início rápido
- `QUICKSTART.md` - Setup detalhado
- `COMMANDS_CHEATSHEET.md` - Todos os comandos
- `README_NEW.md` - Guia completo

---

## ✅ Checklist de Resolução

Antes de reportar um problema, verifique:

- [ ] `.env` está configurado corretamente
- [ ] Credenciais do Spotify estão corretas
- [ ] Redirect URI está configurado no Spotify Dashboard
- [ ] Ambiente virtual está ativado
- [ ] Pacote está instalado (`pip install -e .`)
- [ ] Internet está funcionando
- [ ] Logs foram verificados
- [ ] Tentou limpar cache
- [ ] Tentou reinstalar

---

## 💡 Dicas de Prevenção

1. **Sempre use ambiente virtual**
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

2. **Mantenha credenciais seguras**
   - Nunca commite `.env`
   - Use `.env.example` como template

3. **Verifique logs regularmente**
   ```bash
   tail -f logs/spotify_playlist.log
   ```

4. **Teste com playlists pequenas primeiro**
   ```bash
   spotify-playlist create --region brazil --limit 10
   ```

5. **Use debug mode quando tiver problemas**
   ```bash
   spotify-playlist --debug create --region brazil
   ```

---

## 📞 Suporte

- **Documentação**: Ver arquivos `.md` na raiz
- **Issues**: GitHub Issues
- **Logs**: `logs/spotify_playlist.log`
- **Debug**: `spotify-playlist --debug COMMAND`

---

**Última atualização**: Janeiro 2025
**Versão**: 2.0.0
