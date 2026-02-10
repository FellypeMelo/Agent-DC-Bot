# Requisitos Funcionais (RF)

Este documento lista todas as funcionalidades que o sistema oferece, baseadas na análise do código fonte.

## 1. Inteligência Artificial e Personalidade

| ID | Requisito | Descrição |
| :--- | :--- | :--- |
| **RF01** | Geração de Resposta (LLM) | O bot deve gerar respostas contextuais e coerentes utilizando um LLM conectado via **LM Studio** (API Local). |
| **RF02** | Gestão de Contexto | O sistema deve manter um histórico recente da conversa (limitado a ~14 mensagens) para manter a coerência do diálogo. |
| **RF03** | Personalidade Configurável | O usuário deve poder definir e alterar a personalidade do bot (System Prompt) através de comandos ou configuração. |
| **RF04** | Detecção de Sentimento | O bot deve analisar o texto gerado para identificar emoções (ex: [HAPPY], [ANGRY]) para influenciar futuras interações. |

## 2. Memória e Persistência

| ID | Requisito | Descrição |
| :--- | :--- | :--- |
| **RF05** | Memória de Longo Prazo | O bot deve extrair e salvar fatos importantes sobre o usuário (ex: gostos, nomes) em um banco de dados SQLite. |
| **RF06** | Recuperação Semântica (RAG) | O sistema deve buscar memórias relevantes ao contexto atual usando similaridade de vetores (Embeddings). |
| **RF07** | Diário Automático (Summarization) | Conversas longas devem ser periodicamente resumidas e salvas como "Resumos" no banco de dados para não perder o histórico antigo. |
| **RF08** | Persistência de Perfil de Usuário | O sistema deve salvar dados do usuário como nome, afinidade, humor atual e contagem de interações. |
| **RF09** | Limpeza de Histórico | O usuário deve ter a opção de limpar sua memória de curto prazo (histórico de chat) via comando `!limpar`. |

## 3. Comandos e Controle

| ID | Requisito | Descrição |
| :--- | :--- | :--- |
| **RF10** | Menu de Ajuda | O comando `!ajuda` deve exibir um painel interativo com todos os comandos disponíveis. |
| **RF11** | Status do Sistema | O comando `!status` deve exibir o uso de CPU, RAM, e o estado dos motores de IA (Modelo LLM). |
| **RF12** | Consulta de Memórias | O comando `!memorias` deve listar o que o bot "sabe" sobre o usuário que executou o comando. |
| **RF13** | Configuração de Setup | O comando `!setup_ai` deve guiar o usuário na criação de uma nova identidade para o bot. |
