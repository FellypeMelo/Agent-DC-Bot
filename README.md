# Bot de IA Avançado para Discord com Personalidades Dinâmicas

Este projeto implementa um bot de Discord de alta complexidade, inspirado em plataformas como o Character.AI. Ele utiliza modelos de linguagem locais (via LM Studio) e foi arquitetado para oferecer interações profundas, personalizadas e contextuais.

## ✨ Funcionalidades Avançadas

- **Gestão de Personalidades:** Crie, salve e alterne entre múltiplas personalidades. Cada personalidade tem sua própria descrição, "memória central" (fatos imutáveis) e pode ser ativada a qualquer momento.
- **Memória Estruturada e Automática:** A IA analisa as conversas e extrai fatos importantes (ex: `user_preference_color: blue`) de forma autônoma, salvando-os em uma memória de longo prazo para uso futuro.
- **Busca Semântica:** A memória de longo prazo é vetorial. O bot usa `sentence-transformers` para buscar informações com base no *significado* e não apenas em palavras-chave, garantindo que o contexto mais relevante seja sempre encontrado.
- **Rastreamento de Relacionamento:** O bot analisa o tom da conversa e ajusta seu relacionamento com cada usuário (de "Desconhecido" para "Amigável", por exemplo), adaptando suas respostas para uma experiência mais pessoal.
- **Arquitetura Robusta:** Todo o sistema de memória e personalidades é construído sobre um banco de dados **SQLite**, garantindo performance, estabilidade e persistência de dados.
- **Altamente Configurável:** Ajuste o prefixo dos comandos e o tamanho da janela de contexto (`memory_limit`) para se adaptar a diferentes modelos de IA.

## 🛠️ Instalação

1.  **Clone o repositório** e entre na pasta do projeto.
2.  **Crie um ambiente virtual e instale as dependências:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```
3.  **Configure as variáveis de ambiente:**
    - Vá para a pasta `bot_discord`.
    - Renomeie o arquivo `.env.example` para `.env`.
    - Edite o `.env` e adicione seu `DISCORD_TOKEN` e a `LM_STUDIO_API_URL`.

4.  **Execute o bot:**
    ```bash
    python run_bot.py
    ```

## 🚀 Guia de Comandos

### Comandos Gerais
| Comando | Descrição |
| --- | --- |
| `!ajuda` | Exibe a mensagem de ajuda completa. |
| `!setup` | Inicia um assistente interativo para configurar o bot. |
| `!config memory_limit [num]` | Ajusta o número de mensagens recentes a serem usadas como contexto. |

### Comandos de Memória
| Comando | Descrição |
| --- | --- |
| `!limpar` | Apaga o histórico da conversa atual (memória de curto prazo). |
| `!lembrar [termo]` | Realiza uma busca de IA na memória de longo prazo. |
| `!memorias` | Lista todos os fatos e resumos salvos na memória de longo prazo. |

### Comandos de Personalidade
| Comando | Descrição |
| --- | --- |
| `!personalidade_criar <nome> \| <descrição> \| <memória principal>` | Cria uma nova personalidade. Separe os argumentos com `|`. |
| `!personalidades` | Lista todas as personalidades salvas no banco de dados. |
| `!personalidade_usar <nome>` | Ativa uma personalidade para ser usada pelo bot. |
| `!personalidade_deletar <nome>` | Remove uma personalidade do banco de dados. |

### Comandos Personalizados
| Comando | Descrição |
| --- | --- |
| `!comando_add <nome> <resposta>` | Cria um comando de resposta simples. |
| `!comando_remove <nome>` | Deleta um comando personalizado. |
| `!comandos` | Lista todos os comandos personalizados criados. |

## 🏗️ Arquitetura Final

```
📂 bot_discord/
├── 📂 core/
│   ├── bot.py         # Lógica central do bot, eventos e integração dos módulos
│   ├── config.py      # Gestão do arquivo config.json
│   └── logger.py      # Configuração do sistema de logs
├── 📂 modules/
│   ├── memory.py      # Abstração da memória (curto e longo prazo)
│   ├── ai_handler.py  # Integração com a IA, extração de fatos e análise de relacionamento
│   ├── commands.py    # Implementação de todos os comandos de usuário
│   └── setup.py       # Lógica para o assistente de configuração interativo
├── 📂 data/
│   ├── memory.db      # Banco de dados SQLite
│   └── config.json    # Configurações do bot
└── database.py        # Módulo de baixo nível para todas as operações com o SQLite
```

Este projeto está licenciado sob a licença MIT.
