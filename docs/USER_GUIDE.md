# Guia do Usuário

Bem-vindo ao manual de operação do Agent-DC-Bot. Siga este guia passo-a-passo para interagir com seu assistente de IA.

## 1. Instalação e Configuração Inicial

Antes de começar, certifique-se de que o administrador do bot já realizou a instalação técnica (`setup_arc.bat`).

### Passo 1: Ligar os Motores
1. Abra o **LM Studio** e carregue um modelo (ex: `Ministral-3B`).
2. Inicie o Servidor Local (Start Server) na porta `1234`.
3. Execute o bot clicando duas vezes em `run_bot.bat`.
4. Aguarde a mensagem "Bot is ready!" no console.

---

## 2. Primeiros Passos (Conversa por Texto)

Você pode conversar com o bot em qualquer canal de texto onde ele tenha permissão.

1. Digite `!ajuda` para ver o menu de comandos.
2. O bot responderá com um painel interativo.
3. Use `!status` para verificar se os sistemas de IA estão online.

---

## 3. Conversa por Voz (Real-Time)

A principal funcionalidade deste bot é a conversa natural por voz.

### Como Iniciar
1. Entre em um canal de voz no seu servidor Discord.
2. No chat de texto desse canal (ou qualquer canal de texto), digite:
   ```
   !join
   ```
3. O bot entrará no canal e dirá algo como "Estou ouvindo".
4. **Fale normalmente!** Não precisa de comando para ativar. O bot detecta quando você para de falar e responde.

### Durante a Conversa
- **Interrupção:** Se o bot estiver falando e você quiser interromper, basta começar a falar. O bot vai parar imediatamente para te ouvir.
- **Latência:** A resposta pode levar de 1 a 3 segundos dependendo da velocidade do seu computador.

### Como Parar
1. Digite o comando:
   ```
   !leave
   ```
2. O bot se desconectará do canal e liberará a memória do computador.

---

## 4. Gerenciando a Memória do Bot

O bot lembra de coisas que você conta para ele.

- **Ver o que ele sabe:**
  Digite `!memorias` para ver uma lista de fatos que ele salvou sobre você.

- **Esquecer tudo (Curto Prazo):**
  Se a conversa ficar confusa, digite `!limpar` para apagar o histórico recente e começar do zero.

---

## 5. Personalizando o Bot (Admin)

Se você tem permissão, pode mudar a personalidade e a voz do bot.

1. Digite `!setup_ai`.
2. O bot vai perguntar o **Nome** da nova persona. Responda no chat.
3. O bot vai pedir uma **Descrição**. Descreva como ele deve agir e falar.
   *Exemplo: "Você é um robô sarcástico do futuro que odeia humanos, mas é obrigado a ajudar."*
4. O bot irá gerar uma nova voz baseada na sua descrição e salvar tudo automaticamente.

---

## 6. Solução de Problemas Comuns

| Problema | Solução |
| :--- | :--- |
| **Bot entra mas não fala nada.** | Verifique se o volume do bot no Discord não está em 0%. |
| **Bot não responde aos comandos.** | Verifique se o console (`run_bot.bat`) mostra erros. Reinicie o bot. |
| **Voz do bot está "picotando".** | Seu computador pode estar sobrecarregado. Feche outros programas pesados. |
| **Erro "Connection Refused".** | O LM Studio não está rodando ou o servidor local não foi iniciado na porta 1234. |
