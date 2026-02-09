# Regras de Negócio (RN)

Este documento define as lógicas, políticas e regras que regem o comportamento e as decisões automáticas do sistema.

## 1. Regras de Personalidade e Emoção

| ID | Regra | Descrição |
| :--- | :--- | :--- |
| **RN01** | Mudança de Humor | O humor do bot ('mood') deve ser atualizado dinamicamente com base na análise de sentimento da resposta gerada. Sentimentos como [HAPPY] ou [ANGRY] alteram o estado armazenado no banco. |
| **RN02** | Afinidade do Usuário | A afinidade (`affinity`) é um valor numérico que deve aumentar (+0.1) a cada interação positiva e diminuir (-0.5) em caso de interrupções frequentes ou hostilidade detectada. |
| **RN03** | Reset de Humor | O humor deve tender ao estado 'neutral' após um período de inatividade (ex: 1 hora sem interação), simulando "esfriamento" emocional. |
| **RN04** | Influência na Voz | O estado emocional atual deve influenciar a velocidade e o tom da voz (Kokoro), tornando a fala mais rápida se [ANGRY] ou mais lenta se [SAD]. |

## 2. Regras de Memória e Retenção

| ID | Regra | Descrição |
| :--- | :--- | :--- |
| **RN05** | Extração de Fatos | O sistema deve processar cada mensagem do usuário para extrair fatos novos. Se um fato já existe na memória (similaridade > 0.9), ele deve ser ignorado ou reforçado, não duplicado. |
| **RN06** | Importância da Memória | Fatos extraídos devem receber um grau de "importância" (1-10). Apenas fatos com importância > 3 devem ser mantidos no Long-Term Memory para evitar poluição. |
| **RN07** | Sumarização Automática | Quando o histórico de conversa atingir 20 mensagens, o sistema deve gerar um resumo das 10 mais antigas, salvar na tabela `summaries` e remover as mensagens originais do contexto imediato. |
| **RN08** | Limite de Contexto | O prompt enviado ao LLM nunca deve exceder 12.000 tokens. O sistema deve cortar mensagens antigas (`_trim_context`) priorizando manter a System Message e as últimas 10 interações. |

## 3. Regras de Voz e Interação

| ID | Regra | Descrição |
| :--- | :--- | :--- |
| **RN09** | Prioridade de Interrupção | Se o usuário falar por mais de 0.5s enquanto o bot fala, o bot deve cessar a fala imediatamente (Barge-In). O bot deve pedir desculpas ou reconhecer a interrupção na próxima fala. |
| **RN10** | Modo de Fala | O sistema utiliza o motor **Kokoro** como padrão para todas as gerações, otimizando tanto a velocidade quanto a qualidade da síntese de fala. |
| **RN11** | Timeout de Silêncio | Se o bot estiver em um canal de voz sozinho ou em silêncio absoluto por mais de 5 minutos, ele deve sair automaticamente para economizar recursos. |
| **RN12** | Formato de Áudio | Todo áudio enviado ao Discord deve ser estritamente Stereo 48kHz PCM16LE. Qualquer outro formato deve ser convertido antes do envio. |

## 4. Regras de Sistema e Segurança

| ID | Regra | Descrição |
| :--- | :--- | :--- |
| **RN13** | Acesso ao Setup | O comando `!setup_ai` só pode ser executado pelo dono do bot (verificado via ID no `.env` ou permissão de Admin). |
| **RN14** | Rate Limiting | O bot deve ignorar comandos de um mesmo usuário se enviados em intervalos menores que 0.5s para evitar spam/abuso de API. |
