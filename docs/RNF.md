# Requisitos Não Funcionais (RNF)

Este documento especifica os requisitos técnicos, restrições e padrões de qualidade do sistema, baseados na análise do código fonte e hardware alvo.

## 1. Performance e Latência

| ID | Requisito | Descrição |
| :--- | :--- | :--- |
| **RNF02** | Processamento de Texto | A geração de tokens pelo LLM deve ocorrer em streaming (chunk-by-chunk) para reduzir a percepção de latência. |
| **RNF04** | Aceleração de Hardware | O sistema deve priorizar o uso de GPU (Intel Arc via SYCL ou CUDA) para inferência de LLM. |

## 2. Segurança e Privacidade

| ID | Requisito | Descrição |
| :--- | :--- | :--- |
| **RNF05** | Privacidade de Dados | Todos os dados de conversas, embeddings e perfis de usuário devem ser armazenados localmente em SQLite (`bot_database.db`). |
| **RNF06** | Sem Dependência de Nuvem | O sistema não deve enviar texto para APIs de terceiros na nuvem (exceto a API local do LM Studio). |
| **RNF07** | Sanitização de Entrada | Comandos e inputs de texto devem ser sanitizados antes de interagir com o banco de dados (SQL Injection). |

## 3. Compatibilidade e Ambiente

| ID | Requisito | Descrição |
| :--- | :--- | :--- |
| **RNF08** | Sistema Operacional | O sistema deve ser compatível com Windows (com suporte a drivers Intel Arc) e Linux. |
| **RNF09** | Python | O código deve ser executável em Python 3.10 ou superior. |
| **RNF10** | Dependências Externas | O sistema requer instalação prévia do **LM Studio** (para LLM). |

## 4. Manutenibilidade e Código

| ID | Requisito | Descrição |
| :--- | :--- | :--- |
| **RNF11** | Estrutura Modular | O código deve seguir a arquitetura modular: Core (Lógica base), Modules (Funcionalidades) e Data (Persistência). |
| **RNF12** | Logging Detalhado | O sistema deve gerar logs detalhados (INFO/DEBUG) para facilitar o diagnóstico de falhas em conexões e API. |
| **RNF13** | Tratamento de Erros | O bot não deve crashar completamente em caso de falha de um módulo específico. |

## 5. Escalabilidade (Local)

| ID | Requisito | Descrição |
| :--- | :--- | :--- |
| **RNF14** | Gerenciamento de Memória | O histórico de conversas deve ser truncado automaticamente (~14 msgs) para evitar estouro de contexto do LLM. |
| **RNF15** | Otimização de Banco | O banco de dados SQLite deve usar índices (`idx_memories_user`, `idx_history_user_time`) para buscas rápidas. |