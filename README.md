# 🤖 Agent-DC-Bot: Conversational AI Agent

Um agente de IA de alta performance para Discord, otimizado para **Intel Arc GPUs (SYCL)**, com memória semântica, consciência emocional e voz em tempo real.

---

## 🚀 Principais Características

### 🧠 Cérebro & Memória
- **LLM Flexível**: Suporta LM Studio (API) ou Llama-cpp (Local) com aceleração SYCL.
- **RAG-Lite (Memória Semântica)**: Usa `all-MiniLM-L6-v2` para lembrar de fatos importantes via similaridade de cosseno ($O(\log N)$ no DB, $O(1)$ em Python via Numpy).
- **Jornal de Longo Prazo**: O bot resume automaticamente conversas longas e as armazena, prevenindo o esquecimento e mantendo o contexto limpo e rápido.

### ❤️ Dinâmica Social & Emoções
- **Sistema de Afinidade**: A amizade evolui baseada nas interações.
- **Estado Emocional (Mood)**: O bot detecta sentimentos (Feliz, Irritado, Neutro) e muda o comportamento e a voz dinamicamente.
- **Consciência Temporal**: O bot sabe quanto tempo passou desde a última conversa ("Faz tempo que não nos falamos!").

### 🎙️ Voz & Ouvido
- **Kokoro TTS (S-Tier)**: Vozes ultra-realistas locais de apenas 80MB.
- **Streaming Audio**: O bot começa a falar enquanto ainda está processando a resposta (baixa latência).
- **Faster-Whisper STT**: Transcrição rápida para ouvir usuários no canal de voz.

---

## 🛠️ Arquitetura Técnica

| Componente | Tecnologia | Complexidade (Big O) |
| :--- | :--- | :--- |
| **Banco de Dados** | SQLite + Indexing | $O(\log N)$ |
| **Busca Semântica** | Numpy Vectorization | $O(M)$ (C-Level optimization) |
| **Inferência LLM** | Llama-cpp (SYCL) | Dependente de Hardware (Arc B580) |
| **Sumarização** | AI Logic | $O(N)$ mensagens |

---

## 📦 Instalação (Windows + Intel Arc)

### 1. Requisitos de Sistema
- Python 3.10+
- **Intel oneAPI Base Toolkit** (Obrigatório para aceleração SYCL na B580)
- FFMPEG instalado no PATH (Para áudio no Discord)

### 2. Setup Automatizado
Execute o script de setup especializado:
```powershell
setup_arc.bat
```
Este script irá:
- Criar o ambiente virtual (`venv`).
- Instalar **Intel Extension for PyTorch (IPEX)**.
- Compilar o `llama-cpp-python` especificamente para sua GPU Intel.
- Criar o arquivo `.env`.

### 3. Modelos Necessários
Baixe e coloque na pasta `bot_discord/data/`:
- `kokoro-v0_19.onnx` (HuggingFace)
- `voices.json` (HuggingFace)
- Seu modelo `.gguf` preferido.

---

## 🎮 Comandos Principais

- `!join`: O bot entra no seu canal de voz e ativa o modo "Real-Time".
- `!leave`: O bot sai do canal de voz.
- `!limpar`: Limpa o histórico de conversa (memória de curto prazo).
- `!memorias`: Lista os fatos que o bot lembra sobre você.
- `!personalidade [descrição]`: Muda a personalidade global do bot.

---

## 🛡️ Segurança & Produção
- **Privacidade Local**: Todos os dados, memórias e interações são processados 100% no seu computador. Nada é enviado para nuvens de terceiros.
- **Sanidade de Dados**: Todas as queries SQL são parametrizadas contra injeção.
- **Observabilidade**: Logs detalhados em `logs/YYYY-MM-DD.log`.

---

## 📈 Roadmap de Upgrades
- [ ] **Interrupção Duplex**: Parar a fala do bot instantaneamente quando o usuário começar a falar.
- [ ] **Visão Agentica**: Capacidade de processar imagens postadas no chat.
- [ ] **Backup em Nuvem**: Enviar cópias criptografadas do `bot_database.db` para segurança.

---
*Desenvolvido com foco em performance e simplicidade (KISS).*
