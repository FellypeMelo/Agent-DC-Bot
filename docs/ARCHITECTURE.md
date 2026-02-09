# Arquitetura do Sistema

Este documento descreve a estrutura técnica do projeto utilizando diagramas UML (Mermaid) para ilustrar os componentes e fluxos.

## 1. Visão Geral (Diagrama de Classes)

O sistema é dividido em três camadas principais: **Core**, **Modules** e **Data**.

```mermaid
classDiagram
    class DiscordBot {
        +run()
        +on_ready()
        +on_message()
    }
    class DatabaseManager {
        +connect()
        +get_user()
        +add_memory()
        +get_history()
    }
    class VoiceEngine {
        +load_engine()
        +transcribe(audio)
        +generate_speech(text)
    }
    class AIHandler {
        +generate_response()
        +detect_memory_triggers()
        +summarize_history()
    }
    class CommandHandler {
        +ajuda()
        +status()
        +memorias()
    }
    class VoiceHandler {
        +join()
        +leave()
        +process_user_speech()
    }

    DiscordBot --> DatabaseManager : Uses
    DiscordBot --> VoiceHandler : Manages
    DiscordBot --> CommandHandler : Loads
    VoiceHandler --> VoiceEngine : Uses
    VoiceHandler --> AIHandler : Requests Response
    CommandHandler --> DatabaseManager : Reads/Writes
    AIHandler --> DatabaseManager : Stores/Retrieves Context
```

## 2. Fluxo de Conversa por Voz (Sequence Diagram)

O diagrama abaixo ilustra o fluxo de uma interação completa, desde o usuário falar até o bot responder com áudio.

```mermaid
sequenceDiagram
    participant User as Usuário (Discord)
    participant VH as VoiceHandler
    participant VE as VoiceEngine
    participant AI as AIHandler
    participant DB as DatabaseManager

    User->>VH: Fala (Audio Stream)
    VH->>VE: process_audio(chunks)
    VE-->>VH: VAD Detected? (Yes)
    VH->>VE: transcribe(audio_buffer)
    VE-->>VH: "Olá, bot!" (Text)

    VH->>AI: generate_response("Olá, bot!")
    AI->>DB: get_history(user_id)
    DB-->>AI: history_context
    AI->>DB: get_semantic_memories(user_id)
    DB-->>AI: relevant_facts

    AI-->>VH: "Olá! Como posso ajudar?" (Response)

    VH->>VE: generate_speech("Olá! Como posso ajudar?")
    VE-->>VH: audio_bytes (PCM)
    VH->>User: Reproduz Áudio (Voice Channel)

    Note over VH, User: Se o usuário falar agora, o bot interrompe (Barge-In)
```

## 3. Estrutura de Pastas e Componentes

### **Core (`bot_discord/core/`)**
*   **`bot.py`**: Ponto de entrada. Gerencia eventos do Discord e carrega extensões.
*   **`database.py`**: Abstração do SQLite (`aiosqlite`). Gerencia todas as queries e conexões.
*   **`voice_engine.py`**: Wrapper para modelos de IA de áudio (Whisper, Kokoro, Qwen). Gerencia carregamento/descarregamento de VRAM.
*   **`llm_provider.py`**: Cliente para API do LM Studio.

### **Modules (`bot_discord/modules/`)**
*   **`voice_client.py` (`VoiceHandler`)**: Lógica de interação com canais de voz do Discord. Implementa o Sink de áudio e o loop de reprodução.
*   **`ai_handler.py`**: Lógica de "cérebro". Monta o prompt, chama o LLM, extrai memórias e sentimentos.
*   **`commands.py`**: Comandos de texto (`!ajuda`, `!status`, etc.).

### **Data (`bot_discord/data/`)**
*   **`bot_database.db`**: Arquivo SQLite contendo tabelas de usuários, histórico e memórias.
*   **`models/`**: Pasta onde residem os modelos `.onnx` (Kokoro) e `.gguf` (opcional).

## 4. Integrações Externas

*   **LM Studio (Local API)**: O sistema se comunica via HTTP (localhost:1234) para inferência de texto.
*   **Discord Gateway**: Websocket para eventos de tempo real e transmissão de voz (UDP).
