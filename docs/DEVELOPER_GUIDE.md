# Guia do Desenvolvedor

Este manual detalha como configurar o ambiente de desenvolvimento, entender o código e contribuir para o projeto.

## 1. Configuração do Ambiente (Dev)

### Pré-requisitos
- Python 3.10+
- FFmpeg (Adicionado ao PATH)
- Driver Intel Arc (Se usar GPU Intel) ou CUDA (Nvidia)
- Git

### Instalação
1. Clone o repositório:
   ```bash
   git clone https://github.com/seu-usuario/agent-dc-bot.git
   cd agent-dc-bot
   ```

2. Crie um ambiente virtual:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Linux/Mac
   .\venv\Scripts\activate   # Windows
   ```

3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   # Se tiver Intel Arc, execute o script de setup:
   .\tools\setup_arc.bat
   ```

4. Configure o `.env`:
   Copie o `example.env` para `.env` e preencha o token do Discord.

---

## 2. Estrutura do Código

O projeto segue o padrão **Modular Monolith**:

```
bot_discord/
├── core/              # Componentes fundamentais
│   ├── bot.py         # Entrypoint e loop principal
│   ├── database.py    # Abstração do SQLite (Async)
│   ├── voice_engine.py# Gerenciador de TTS/STT (Kokoro, Whisper)
│   └── llm_provider.py# Cliente HTTP para LM Studio
├── modules/           # Funcionalidades de alto nível (Cogs)
│   ├── ai_handler.py  # Lógica de prompts e memória
│   ├── voice_client.py# Lógica de conexão com Discord Voice
│   └── commands.py    # Comandos de usuário (!help, etc)
└── data/              # Arquivos persistentes
    ├── bot_database.db# SQLite DB
    └── models/        # Pesos de modelos locais
```

## 3. Fluxo de Execução (Life Cycle)

1. **Start:** `run_bot.bat` chama `python -m bot_discord.core.bot`.
2. **Init:** O `DiscordBot` carrega o `config.py` e inicializa o `DatabaseManager`.
3. **Connect:** O bot se conecta ao Gateway do Discord.
4. **Load Cogs:** Os módulos em `modules/` são carregados como extensões.
   - `VoiceHandler` inicializa o `VoiceEngine` (mas não carrega modelos pesados na VRAM ainda).
5. **Wait:** O bot aguarda comandos ou eventos de voz.

## 4. Estendendo o Bot

### Adicionando um Novo Comando
Edite `bot_discord/modules/commands.py`:

```python
@commands.command(name='novo_comando')
async def novo_comando(self, ctx):
    # Sua lógica aqui
    await ctx.send("Olá mundo!")
```

### Modificando a Lógica de IA
Edite `bot_discord/modules/ai_handler.py`. A função `generate_response` controla o que é enviado ao LLM. Você pode adicionar novos passos ao pipeline, como buscar dados na web antes de responder.

### Adicionando um Novo Motor de TTS
1. Implemente a classe do motor em `bot_discord/core/voice_engine.py`.
2. Adicione a lógica de carregamento em `load_engine`.
3. Atualize o método `generate_speech` para usar seu novo motor.

---

## 5. Banco de Dados

O banco SQLite é gerenciado automaticamente pelo `DatabaseManager`.
- **Migrations:** Não há sistema de migração automática complexo. As tabelas são criadas em `_create_tables` se não existirem.
- **Para alterar o Schema:** Você deve editar `_create_tables` e, se já houver dados em produção, criar um script de migração manual em `tools/`.

## 6. Testes

Para rodar os testes unitários:
```bash
pytest bot_discord/tests/
```
