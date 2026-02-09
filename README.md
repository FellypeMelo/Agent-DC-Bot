# Agent-DC-Bot: Assistente de IA de Alta Performance

Um agente de IA sofisticado para Discord, projetado para rodar localmente com foco em privacidade e alta performance (especialmente em GPUs Intel Arc). Este bot combina conversação natural por voz, memória persistente e uma personalidade dinâmica.

---

## 📚 Documentação Completa

A documentação detalhada do sistema está organizada na pasta `docs/`. Abaixo está o índice para navegação rápida:

### 🔹 Para Usuários
- **[Guia do Usuário](docs/USER_GUIDE.md)**: Passo-a-passo de como instalar, configurar e conversar com o bot.
- **[Casos de Uso (UC)](docs/UC.md)**: Exemplos práticos de interações e o que esperar de cada comando.

### 🔹 Para Desenvolvedores e Arquitetos
- **[Guia do Desenvolvedor](docs/DEVELOPER_GUIDE.md)**: Como o código funciona, estrutura de pastas e como contribuir.
- **[Arquitetura do Sistema](docs/ARCHITECTURE.md)**: Diagramas UML (Mermaid) e explicação dos componentes internos.
- **[Requisitos Funcionais (RF)](docs/RF.md)**: Lista completa do que o sistema faz.
- **[Requisitos Não Funcionais (RNF)](docs/RNF.md)**: Performance, segurança e restrições técnicas.
- **[Regras de Negócio (RN)](docs/RN.md)**: Lógicas internas de memória, afinidade e emoção.

---

## 🚀 Destaques do Projeto

### 🗣️ Conversa em Tempo Real
Utiliza **Whisper (Tiny)** para ouvir e **Kokoro V1.0** para falar, garantindo uma latência extremamente baixa para conversas fluidas.

### 🧠 Memória Semântica (RAG)
O bot "lembra" de você. Ele extrai fatos das conversas e os armazena em um banco de dados vetorial local, recuperando-os quando relevante para o contexto atual.

### 🎭 Personalidade Dinâmica
Crie personas únicas com "DNA de Voz" gerado por IA. O bot ajusta seu tom de voz e estilo de fala com base na descrição que você fornecer.

### 🔒 100% Local e Privado
Tudo roda na sua máquina. Nenhuma conversa é enviada para a nuvem. Seus dados são seus.

---

## 🛠️ Instalação Rápida

1. **Clone o Repositório:**
   ```bash
   git clone https://github.com/seu-usuario/agent-dc-bot.git
   ```

2. **Instale Dependências:**
   ```bash
   pip install -r requirements.txt
   ```
   *(Usuários Intel Arc: executem `tools/setup_arc.bat`)*

3. **Inicie o LM Studio:**
   Configure o servidor local na porta `1234`.

4. **Rode o Bot:**
   ```bash
   run_bot.bat
   ```

---

*Desenvolvido com foco em simplicidade e poder.*
