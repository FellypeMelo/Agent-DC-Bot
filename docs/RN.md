# Regras de Negócio (RN)

Este documento define as lógicas, políticas e regras que regem o comportamento e as decisões automáticas do sistema.

## 1. Regras de Personalidade e Emoção

| ID | Regra | Descrição |
| :--- | :--- | :--- |
| **RN01** | Mudança de Humor | O humor do bot ('mood') deve ser atualizado dinamicamente com base na análise de sentimento da resposta gerada. Sentimentos como [HAPPY] ou [ANGRY] alteram o estado armazenado no banco. |
| **RN02** | Afinidade do Usuário | A afinidade (`affinity`) é um valor numérico que deve aumentar (+0.1) a cada interação positiva e diminuir (-0.5) em caso de hostilidade detectada. |
| **RN03** | Reset de Humor | O humor deve tender ao estado 'neutral' após um período de inatividade (ex: 1 hora sem interação), simulando "esfriamento" emocional. |

## 2. Regras de Memória e Retenção

| ID | Regra | Descrição |
| :--- | :--- | :--- |
| **RN05** | Extração de Fatos | O sistema deve processar cada mensagem do usuário para extrair fatos novos. Se um fato já existe na memória (similaridade > 0.9), ele deve ser ignorado ou reforçado, não duplicado. |
| **RN06** | Importância da Memória | Fatos extraídos devem receber um grau de "importância" (1-10). Apenas fatos com importância > 3 devem ser mantidos no Long-Term Memory para evitar poluição. |
| **RN07** | Sumarização Automática | Quando o histórico de conversa atingir 20 mensagens, o sistema deve gerar um resumo das 10 mais antigas, salvar na tabela `summaries` e remover as mensagens originais do contexto imediato. |
| **RN08** | Limite de Contexto | O prompt enviado ao LLM nunca deve exceder 12.000 tokens. O sistema deve cortar mensagens antigas (`_trim_context`) priorizando manter a System Message e as últimas 10 interações. |

## 3. Regras de Sistema e Segurança

| ID | Regra | Descrição |
| :--- | :--- | :--- |
| **RN13** | Acesso ao Setup | O comando `!setup_ai` só pode ser executado pelo dono do bot (verificado via ID no `.env` ou permissão de Admin). |
| **RN14** | Rate Limiting | O bot deve ignorar comandos de um mesmo usuário se enviados em intervalos menores que 0.5s para evitar spam/abuso de API. |