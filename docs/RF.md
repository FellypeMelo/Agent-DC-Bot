# Requisitos Funcionais (RF)

Este documento lista todas as funcionalidades que o sistema oferece, baseadas na análise do código fonte.

## 1. Interação por Voz (Voice & Audio)

| ID | Requisito | Descrição |
| :--- | :--- | :--- |
| **RF01** | Entrada em Canal de Voz | O bot deve ser capaz de entrar em um canal de voz mediante comando (`!join`) e iniciar a captura de áudio. |
| **RF02** | Saída do Canal de Voz | O bot deve sair do canal de voz e liberar recursos ao receber o comando `!leave`. |
| **RF03** | Detecção de Atividade de Voz (VAD) | O sistema deve detectar quando um usuário está falando e ignorar silêncio ou ruído de fundo (Threshold 0.6). |
| **RF04** | Transcrição de Áudio (STT) | O áudio capturado dos usuários deve ser convertido em texto usando o modelo **Whisper (Tiny)** para baixa latência. |
| **RF05** | Síntese de Fala (TTS) | O bot deve converter suas respostas textuais em áudio usando dois motores: **Kokoro** (Modo Rápido) ou **Qwen-TTS** (Modo Qualidade). |
| **RF06** | Interrupção (Barge-In) | O bot deve parar de falar imediatamente se detectar que o usuário começou a falar enquanto ele ainda está reproduzindo áudio. |
| **RF07** | Reprodução Stereo 48kHz | O áudio gerado deve ser processado e enviado ao Discord no formato Stereo 48kHz (padrão de alta qualidade). |

## 2. Inteligência Artificial e Personalidade

| ID | Requisito | Descrição |
| :--- | :--- | :--- |
| **RF08** | Geração de Resposta (LLM) | O bot deve gerar respostas contextuais e coerentes utilizando um LLM conectado via **LM Studio** (API Local). |
| **RF09** | Gestão de Contexto | O sistema deve manter um histórico recente da conversa (limitado a ~14 mensagens) para manter a coerência do diálogo. |
| **RF10** | Personalidade Configurável | O usuário deve poder definir e alterar a personalidade do bot (System Prompt) através de comandos ou configuração. |
| **RF11** | Detecção de Sentimento | O bot deve analisar o texto gerado para identificar emoções (ex: [HAPPY], [ANGRY]) e ajustar o tom da voz de acordo. |
| **RF12** | DNA de Voz (Voice Design) | O sistema deve ser capaz de criar um "DNA de voz" único baseado na descrição textual da personalidade (usando Qwen-TTS). |

## 3. Memória e Persistência

| ID | Requisito | Descrição |
| :--- | :--- | :--- |
| **RF13** | Memória de Longo Prazo | O bot deve extrair e salvar fatos importantes sobre o usuário (ex: gostos, nomes) em um banco de dados SQLite. |
| **RF14** | Recuperação Semântica (RAG) | O sistema deve buscar memórias relevantes ao contexto atual usando similaridade de vetores (Embeddings). |
| **RF15** | Diário Automático (Summarization) | Conversas longas devem ser periodicamente resumidas e salvas como "Resumos" no banco de dados para não perder o histórico antigo. |
| **RF16** | Persistência de Perfil de Usuário | O sistema deve salvar dados do usuário como nome, afinidade, humor atual e contagem de interações. |
| **RF17** | Limpeza de Histórico | O usuário deve ter a opção de limpar sua memória de curto prazo (histórico de chat) via comando `!limpar`. |

## 4. Comandos e Controle

| ID | Requisito | Descrição |
| :--- | :--- | :--- |
| **RF18** | Menu de Ajuda | O comando `!ajuda` deve exibir um painel interativo com todos os comandos disponíveis. |
| **RF19** | Status do Sistema | O comando `!status` deve exibir o uso de CPU, RAM, e o estado dos motores de IA (TTS carregado, Modelo LLM). |
| **RF20** | Consulta de Memórias | O comando `!memorias` deve listar o que o bot "sabe" sobre o usuário que executou o comando. |
| **RF21** | Configuração de Setup | O comando `!setup_ai` deve guiar o usuário na criação de uma nova identidade para o bot. |
