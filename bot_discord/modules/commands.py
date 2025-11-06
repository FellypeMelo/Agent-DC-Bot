# commands.py
# Comandos customizados do bot

import discord
from discord.ext import commands
import logging
import os
import json

logger = logging.getLogger(__name__)

class CommandHandler:
    def __init__(self, bot, config, memory, ai_handler, db):
        self.bot = bot
        self.config = config
        self.memory = memory
        self.ai_handler = ai_handler
        self.db = db
        self.custom_commands = {}
        from modules.setup import SetupWizard
        self.setup_wizard = SetupWizard(bot, config, self, db)
        self.register_commands()
        self._load_custom_commands()

    def register_commands(self):
        @self.bot.command(name='ajuda')
        async def help_command(ctx):
            prefix = self.config.get_prefix()
            embed = discord.Embed(
                title="📚 Guia de Comandos do Bot",
                description="Um bot com memória avançada e personalidades dinâmicas.",
                color=discord.Color.blue()
            )

            # Comandos Gerais
            embed.add_field(
                name="🔧 Comandos Gerais",
                value=f"""
                `{prefix}ajuda`: Exibe esta mensagem.
                `{prefix}config [param] [valor]`: Ajusta configurações. Ex: `memory_limit 50`.
                `{prefix}setup`: Inicia o assistente de configuração interativo.
                """,
                inline=False
            )

            # Comandos de Memória
            embed.add_field(
                name="🧠 Comandos de Memória",
                value=f"""
                `{prefix}limpar`: Limpa a memória de curto prazo da conversa atual.
                `{prefix}lembrar [termo]`: Busca na memória de longo prazo usando IA.
                `{prefix}memorias`: Lista todos os fatos e resumos na memória de longo prazo.
                """,
                inline=False
            )

            # Comandos de Personalidade
            embed.add_field(
                name="🎭 Comandos de Personalidade",
                value=f"""
                `{prefix}personalidade_criar <nome> | <descrição> | <memória principal>`: Cria uma nova persona.
                `{prefix}personalidades`: Lista todas as personalidades salvas.
                `{prefix}personalidade_usar <nome>`: Ativa uma personalidade existente.
                `{prefix}personalidade_deletar <nome>`: Remove uma personalidade.
                """,
                inline=False
            )

            # Comandos Personalizados
            embed.add_field(
                name="🤖 Comandos Personalizados",
                value=f"""
                `{prefix}comando_add <nome> <resposta>`: Cria um comando simples.
                `{prefix}comando_remove <nome>`: Remove um comando personalizado.
                `{prefix}comandos`: Lista todos os comandos personalizados.
                """,
                inline=False
            )
            
            embed.set_footer(text="Converse comigo me mencionando!")
            await ctx.send(embed=embed)

        @self.bot.command(name='config')
        async def config_command(ctx, param=None, value=None):
            if not param:
                embed = discord.Embed(title="Configuração Atual", color=discord.Color.green())
                embed.add_field(name="Prefixo", value=f"`{self.config.get_prefix()}`")
                embed.add_field(name="Limite de Memória", value=f"`{self.config.get_memory_limit()}`")
                embed.add_field(name="Personalidade Ativa", value=f"`{self.config.get_config_value('active_personality_name')}`")
                await ctx.send(embed=embed)
                return
            if param.lower() == 'memory_limit':
                try:
                    self.config.set_memory_limit(int(value))
                    self.memory.memory_limit = int(value)
                    await ctx.send(f"✅ Limite de memória definido para `{value}`.")
                except ValueError:
                    await ctx.send("❌ O limite de memória deve ser um número.")
            else:
                await ctx.send("❌ Parâmetro não reconhecido.")

        @self.bot.command(name='setup')
        async def setup_command(ctx):
            await self.setup_wizard.start_setup(ctx)

        @self.bot.command(name='limpar')
        async def clear_memory_command(ctx):
            if self.memory.clear_short_term():
                await ctx.send("✅ Memória de curto prazo limpa.")
            else:
                await ctx.send("❌ Erro ao limpar a memória.")

        @self.bot.command(name='lembrar')
        async def remember_command(ctx, *, query: str):
            memories = self.memory.find_relevant_memories(query)
            if not memories:
                await ctx.send("Não encontrei nada relevante na memória.")
                return
            embed = discord.Embed(title=f"Lembranças sobre: {query}", color=discord.Color.green())
            for mem in memories:
                embed.add_field(name=mem['key'], value=mem['value'], inline=False)
            await ctx.send(embed=embed)

        @self.bot.command(name='memorias')
        async def list_memories_command(ctx):
            memories = self.memory.get_all_permanent_info()
            if not memories:
                await ctx.send("Nenhuma memória de longo prazo encontrada.")
                return
            embed = discord.Embed(title="Memórias Armazenadas", color=discord.Color.blue())
            for mem in memories:
                embed.add_field(name=mem['key'], value=mem['value'], inline=False)
            await ctx.send(embed=embed)

        # --- Comandos de Personalidade ---
        @self.bot.command(name='personalidade_criar')
        async def personality_create(ctx, *, args):
            try:
                name, description, core_memory = [arg.strip() for arg in args.split('|', 2)]
                if self.db.create_personality(name, description, core_memory, str(ctx.author.id)):
                    await ctx.send(f"✅ Personalidade '{name}' criada.")
                else:
                    await ctx.send(f"❌ Personalidade '{name}' já existe.")
            except ValueError:
                await ctx.send("❌ Formato: `!personalidade_criar <nome> | <descrição> | <memória central>`")

        @self.bot.command(name='personalidades')
        async def personality_list(ctx):
            personalities = self.db.get_all_personalities()
            if not personalities:
                await ctx.send("Não há personalidades salvas.")
                return
            embed = discord.Embed(title="Personalidades Disponíveis", color=discord.Color.purple())
            for p in personalities:
                embed.add_field(name=p['name'], value=p['description'][:250], inline=False)
            await ctx.send(embed=embed)

        @self.bot.command(name='personalidade_usar')
        async def personality_use(ctx, *, name):
            if self.db.get_personality(name):
                self.config.set_config_value('active_personality_name', name)
                await ctx.send(f"✅ Personalidade ativa: '{name}'.")
            else:
                await ctx.send(f"❌ Personalidade '{name}' não encontrada.")

        @self.bot.command(name='personalidade_deletar')
        async def personality_delete(ctx, *, name):
            if name == 'default':
                await ctx.send("❌ A personalidade 'default' não pode ser deletada.")
                return
            if self.db.delete_personality(name):
                if self.config.get_config_value('active_personality_name') == name:
                    self.config.set_config_value('active_personality_name', 'default')
                    await ctx.send(f"✅ Personalidade '{name}' deletada. Ativa revertida para 'default'.")
                else:
                    await ctx.send(f"✅ Personalidade '{name}' deletada.")
            else:
                await ctx.send(f"❌ Personalidade '{name}' não encontrada.")
    
    # --- Comandos Personalizados ---
    @self.bot.command(name='comando_add')
    async def add_custom_command(self, ctx, name: str, *, response: str):
        if name in self.bot.commands:
            await ctx.send(f"❌ Comando '{name}' já existe.")
            return
        self.custom_commands[name] = response
        self._save_custom_commands()
        self.bot.add_command(commands.Command(self._create_custom_command_callback(name), name=name))
        await ctx.send(f"✅ Comando `!{name}` adicionado.")

    @self.bot.command(name='comando_remove')
    async def remove_custom_command(self, ctx, name: str):
        if name not in self.custom_commands:
            await ctx.send(f"❌ Comando '{name}' não encontrado.")
            return
        del self.custom_commands[name]
        self._save_custom_commands()
        self.bot.remove_command(name)
        await ctx.send(f"✅ Comando `!{name}` removido.")

    @self.bot.command(name='comandos')
    async def list_custom_commands(self, ctx):
        if not self.custom_commands:
            await ctx.send("Não há comandos personalizados.")
            return
        embed = discord.Embed(title="Comandos Personalizados", color=discord.Color.orange())
        for name, response in self.custom_commands.items():
            embed.add_field(name=name, value=response, inline=False)
        await ctx.send(embed=embed)

    def _create_custom_command_callback(self, name):
        async def command_callback(ctx):
            await ctx.send(self.custom_commands[name])
        return command_callback

    def _save_custom_commands(self):
        path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'custom_commands.json')
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self.custom_commands, f, indent=4)
        except IOError as e:
            logger.error(f"Erro ao salvar comandos personalizados: {e}")

    def _load_custom_commands(self):
        path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'custom_commands.json')
        if not os.path.exists(path):
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                self.custom_commands = json.load(f)
            for name in self.custom_commands:
                self.bot.add_command(commands.Command(self._create_custom_command_callback(name), name=name))
        except (IOError, json.JSONDecodeError) as e:
            logger.error(f"Erro ao carregar comandos personalizados: {e}")
