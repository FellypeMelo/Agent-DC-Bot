# Casos de Uso (UC)

Este documento descreve as interações práticas entre o usuário e o sistema, detalhando o fluxo de uso.

## 1. UC01 - Entrar em Canal de Voz e Iniciar Conversa

| Etapa | Ação | Descrição |
| :--- | :--- | :--- |
| **Ator** | Usuário | Usuário |
| **Pré-requisitos** | O usuário deve estar em um canal de voz no servidor. |
| **Gatilho** | O usuário digita `!join`. |
| **Fluxo Principal** | 1. O bot verifica se o usuário está em um canal de voz. <br> 2. O bot entra no canal de voz do usuário. <br> 3. O bot carrega o modelo Kokoro e Whisper na memória. <br> 4. O bot anuncia via voz ou texto: "Conectado. Estou ouvindo." <br> 5. O sistema inicia o loop de captura de áudio. |
| **Fluxo Alternativo** | (Se usuário não estiver em voz) O bot responde com mensagem de erro: "Você precisa estar em um canal de voz." |
| **Pós-condições** | O bot está no canal, ouvindo e pronto para transcrever fala em tempo real. |

## 2. UC02 - Conversar com o Bot e Receber Resposta (Voz)

| Etapa | Ação | Descrição |
| :--- | :--- | :--- |
| **Ator** | Usuário | Usuário |
| **Pré-requisitos** | O bot deve estar conectado ao canal de voz (UC01). |
| **Gatilho** | O usuário fala no microfone. |
| **Fluxo Principal** | 1. O sistema detecta atividade de voz (VAD). <br> 2. O sistema grava o áudio até detectar silêncio. <br> 3. O Whisper transcreve o áudio para texto. <br> 4. O texto é enviado ao `AIHandler` com o contexto da conversa. <br> 5. O LLM gera uma resposta textual. <br> 6. O TTS converte a resposta em áudio. <br> 7. O áudio é reproduzido no canal de voz. |
| **Fluxo Alternativo** | (Interrupção) Se o usuário falar durante o passo 7, o bot para o áudio imediatamente e reinicia o processo no passo 1. |
| **Pós-condições** | A resposta foi entregue e o bot volta a ouvir. |

## 3. UC03 - Configurar Nova Personalidade

| Etapa | Ação | Descrição |
| :--- | :--- | :--- |
| **Ator** | Admin / Usuário | Admin / Usuário Autorizado |
| **Pré-requisitos** | O bot deve estar online. |
| **Gatilho** | O usuário digita `!setup_ai`. |
| **Fluxo Principal** | 1. O bot inicia um diálogo interativo. <br> 2. O bot pergunta o nome da nova persona. <br> 3. O usuário responde. <br> 4. O bot pergunta a descrição da personalidade ("Como eu devo agir?"). <br> 5. O usuário fornece a descrição. <br> 6. O bot configura a nova personalidade no banco de dados e a ativa. |
| **Pós-condições** | O bot agora responde com a nova personalidade e voz configuradas. |

## 4. UC04 - Consultar Memórias Salvas

| Etapa | Ação | Descrição |
| :--- | :--- | :--- |
| **Ator** | Usuário | Usuário |
| **Pré-requisitos** | O usuário já deve ter interagido com o bot anteriormente. |
| **Gatilho** | O usuário digita `!memorias`. |
| **Fluxo Principal** | 1. O sistema consulta a tabela `memories` filtrando pelo ID do usuário. <br> 2. O sistema formata a lista de fatos encontrados. <br> 3. O bot envia uma mensagem de texto (Embed) com a lista: "Isso é o que eu sei sobre você: [Lista]". |
| **Fluxo Alternativo** | (Se não houver memórias) O bot responde: "Ainda não sei nada sobre você." |
| **Pós-condições** | O usuário visualiza seus dados persistidos. |

## 5. UC05 - Limpar Histórico de Conversa

| Etapa | Ação | Descrição |
| :--- | :--- | :--- |
| **Ator** | Usuário | Usuário |
| **Pré-requisitos** | N/A |
| **Gatilho** | O usuário digita `!limpar`. |
| **Fluxo Principal** | 1. O sistema deleta todas as entradas na tabela `conversation_history` associadas ao ID do usuário. <br> 2. O bot confirma: "Minha memória de curto prazo foi apagada." |
| **Pós-condições** | O contexto da conversa é resetado (mas memórias de longo prazo e perfil são mantidos). |
