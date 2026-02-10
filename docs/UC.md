# Casos de Uso (UC)

Este documento descreve as interações práticas entre o usuário e o sistema, detalhando o fluxo de uso.

## 1. UC01 - Conversar com o Bot via Texto

| Etapa | Ação | Descrição |
| :--- | :--- | :--- |
| **Ator** | Usuário | Usuário |
| **Pré-requisitos** | O bot deve estar online. |
| **Gatilho** | O usuário envia uma mensagem mencionando o bot ou usando a palavra-chave. |
| **Fluxo Principal** | 1. O sistema recebe a mensagem de texto. <br> 2. O texto é enviado ao `AIHandler` com o contexto da conversa. <br> 3. O LLM gera uma resposta textual. <br> 4. O bot envia a resposta no canal de texto. |
| **Pós-condições** | A resposta foi entregue e o bot aguarda nova interação. |

## 2. UC02 - Configurar Nova Personalidade

| Etapa | Ação | Descrição |
| :--- | :--- | :--- |
| **Ator** | Admin / Usuário | Admin / Usuário Autorizado |
| **Pré-requisitos** | O bot deve estar online. |
| **Gatilho** | O usuário digita `!setup_ai`. |
| **Fluxo Principal** | 1. O bot inicia um diálogo interativo. <br> 2. O bot faz uma série de perguntas sobre a identidade e personalidade da persona. <br> 3. O usuário responde a cada etapa. <br> 4. O bot configura a nova personalidade no banco de dados e a ativa. |
| **Pós-condições** | O bot agora responde com a nova personalidade configurada. |

## 3. UC03 - Consultar Memórias Salvas

| Etapa | Ação | Descrição |
| :--- | :--- | :--- |
| **Ator** | Usuário | Usuário |
| **Pré-requisitos** | O usuário já deve ter interagido com o bot anteriormente. |
| **Gatilho** | O usuário digita `!memorias`. |
| **Fluxo Principal** | 1. O sistema consulta a tabela `memories` filtrando pelo ID do usuário. <br> 2. O sistema formata a lista de fatos encontrados. <br> 3. O bot envia uma mensagem de texto (Embed) com a lista: "Isso é o que eu sei sobre você: [Lista]". |
| **Fluxo Alternativo** | (Se não houver memórias) O bot responde: "Ainda não sei nada sobre você." |
| **Pós-condições** | O usuário visualiza seus dados persistidos. |

## 4. UC04 - Limpar Histórico de Conversa

| Etapa | Ação | Descrição |
| :--- | :--- | :--- |
| **Ator** | Usuário | Usuário |
| **Pré-requisitos** | N/A |
| **Gatilho** | O usuário digita `!limpar`. |
| **Fluxo Principal** | 1. O sistema deleta todas as entradas na tabela `conversation_history` associadas ao ID do usuário. <br> 2. O bot confirma: "Minha memória de curto prazo foi apagada." |
| **Pós-condições** | O contexto da conversa é resetado (mas memórias de longo prazo e perfil são mantidos). |