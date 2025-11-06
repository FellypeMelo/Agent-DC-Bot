# setup.py
# Sistema de configuração interativa via Discord

import discord
from discord.ext import commands
import asyncio
import json
import os
import logging
from typing import Dict, List, Any, Optional, Union, Callable

# Configuração do logger
logger = logging.getLogger(__name__)

class SetupWizard:
    """Assistente de configuração interativa para o bot via Discord"""
    
    def __init__(self, bot, config, command_handler, db):
        self.bot = bot
        self.config = config
        self.command_handler = command_handler
        self.db = db
        self.active_setups = {}
        self.timeout = 120
        
        # Etapas de configuração disponíveis
        self.setup_steps = [
            {
                "name": "bot_name_keyword",
                "title": "Nome do Bot e Palavra-Chave",
                "description": "Define o nome do bot e a palavra-chave que servirá como gatilho para respostas.",
                "handler": self._setup_bot_name_keyword
            },
            {
                "name": "command_prefix",
                "title": "Prefixo de Comandos",
                "description": "Permite alterar o prefixo usado para comandos.",
                "handler": self._setup_command_prefix
            },
            {
                "name": "memory_settings",
                "title": "Memória Permanente",
                "description": "Configura o armazenamento de mensagens importantes.",
                "handler": self._setup_memory_settings
            },
            {
                "name": "search_settings",
                "title": "Sistema de Busca",
                "description": "Configura o sistema de busca usando DuckDuckGo.",
                "handler": self._setup_search_settings
            },
            {
                "name": "moderation_settings",
                "title": "Moderação Automática",
                "description": "Configura filtros para spam, flood e palavras proibidas.",
                "handler": self._setup_moderation_settings
            },
            {
                "name": "bot_personality",
                "title": "Personalidade do Bot",
                "description": "Escolha entre formal, casual e humorístico.",
                "handler": self._setup_bot_personality
            },
            {
                "name": "notification_settings",
                "title": "Notificações",
                "description": "Configura notificações via Telegram ou Webhook.",
                "handler": self._setup_notification_settings
            }
        ]
    
    async def start_setup(self, ctx):
        """Inicia o assistente de configuração interativo"""
        # Verifica se o usuário tem permissões de administrador
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("❌ Você precisa ter permissões de administrador para usar este comando.")
            return
        
        # Verifica se já existe uma configuração ativa para este canal
        if ctx.channel.id in self.active_setups:
            await ctx.send("⚠️ Já existe uma configuração em andamento neste canal. Conclua-a ou aguarde o timeout.")
            return
        
        # Registra esta configuração como ativa
        self.active_setups[ctx.channel.id] = {
            "user_id": ctx.author.id,
            "step": 0,
            "config": {}
        }
        
        # Envia mensagem de boas-vindas
        welcome_embed = discord.Embed(
            title="🔧 Assistente de Configuração do Bot",
            description="Bem-vindo ao assistente de configuração interativo! Vou guiá-lo através das etapas para configurar o bot.",
            color=discord.Color.blue()
        )
        welcome_embed.add_field(
            name="ℹ️ Instruções",
            value="- Responda às perguntas digitando no chat\n- Digite `cancelar` a qualquer momento para sair\n- Digite `pular` para usar as configurações padrão\n- O assistente expirará após 2 minutos de inatividade",
            inline=False
        )
        welcome_embed.add_field(
            name="📋 Etapas de Configuração",
            value="\n".join([f"{i+1}. {step['title']}" for i, step in enumerate(self.setup_steps)]),
            inline=False
        )
        
        await ctx.send(embed=welcome_embed)
        
        # Inicia a primeira etapa
        await self._process_next_step(ctx)
        
    async def _process_next_step(self, ctx):
        """Processa a próxima etapa da configuração"""
        # Obtém os dados da configuração atual
        setup_data = self.active_setups.get(ctx.channel.id)
        if not setup_data:
            return
        
        # Verifica se todas as etapas foram concluídas
        if setup_data["step"] >= len(self.setup_steps):
            await self._finish_setup(ctx)
            return
        
        # Obtém a etapa atual
        current_step = self.setup_steps[setup_data["step"]]
        
        # Chama o handler da etapa atual
        await current_step["handler"](ctx)
    
    async def _wait_for_response(self, ctx, timeout=None):
        """Aguarda uma resposta do usuário"""
        if timeout is None:
            timeout = self.timeout
            
        setup_data = self.active_setups.get(ctx.channel.id)
        if not setup_data:
            return None
            
        def check(message):
            # Verifica se a mensagem é do usuário correto e no canal correto
            return (
                message.author.id == setup_data["user_id"] and 
                message.channel.id == ctx.channel.id
            )
        
        try:
            # Aguarda a resposta do usuário
            response = await self.bot.wait_for('message', check=check, timeout=timeout)
            
            # Verifica se o usuário deseja cancelar
            if response.content.lower() == "cancelar":
                await ctx.send("❌ Configuração cancelada pelo usuário.")
                del self.active_setups[ctx.channel.id]
                return None
                
            return response
        except asyncio.TimeoutError:
            await ctx.send("⏱️ Tempo esgotado. A configuração foi cancelada.")
            del self.active_setups[ctx.channel.id]
            return None
    
    async def _finish_setup(self, ctx):
        """Finaliza o assistente de configuração e aplica as configurações"""
        setup_data = self.active_setups.get(ctx.channel.id)
        if not setup_data:
            return
            
        # Aplica todas as configurações
        user_config = setup_data["config"]
        
        # Atualiza as configurações no objeto config
        for key, value in user_config.items():
            self.config.set_config_value(key, value)
        
        # Cria um embed com o resumo das configurações
        summary_embed = discord.Embed(
            title="✅ Configuração Concluída",
            description="As configurações foram aplicadas com sucesso!",
            color=discord.Color.green()
        )
        
        # Adiciona cada configuração ao resumo
        for key, value in user_config.items():
            # Formata o nome da configuração para exibição
            display_name = key.replace("_", " ").title()
            
            # Formata o valor para exibição
            if isinstance(value, bool):
                display_value = "Ativado" if value else "Desativado"
            elif value == "":
                display_value = "Não definido"
            else:
                display_value = str(value)
                
            summary_embed.add_field(
                name=display_name,
                value=display_value,
                inline=True
            )
        
        # Adiciona instruções para ajustes futuros
        prefix = self.config.get_prefix()
        summary_embed.add_field(
            name="🔄 Ajustes Futuros",
            value=f"Para modificar configurações específicas, use `{prefix}config [parâmetro] [valor]`.",
            inline=False
        )
        
        await ctx.send(embed=summary_embed)
        
        # Remove esta configuração da lista de configurações ativas
        del self.active_setups[ctx.channel.id]
    
    # Handlers para cada etapa de configuração
    
    async def _setup_bot_name_keyword(self, ctx):
        """Configura o nome do bot e a palavra-chave"""
        setup_data = self.active_setups.get(ctx.channel.id)
        
        # Cria o embed para esta etapa
        embed = discord.Embed(
            title="🤖 Nome do Bot e Palavra-Chave",
            description="Esta configuração define como o bot será chamado e a palavra-chave que ativará o bot.",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="📝 Palavra-Chave",
            value="Digite a palavra-chave que ativará o bot (ex: 'bot', 'assistente')\nOu digite `pular` para usar apenas menções.",
            inline=False
        )
        
        await ctx.send(embed=embed)
        
        # Aguarda a resposta do usuário
        response = await self._wait_for_response(ctx)
        if response is None:
            return
            
        # Processa a resposta
        if response.content.lower() != "pular":
            setup_data["config"]["bot_keyword"] = response.content.lower()
            await ctx.send(f"✅ Palavra-chave definida como: **{response.content}**")
        else:
            setup_data["config"]["bot_keyword"] = ""
            await ctx.send("ℹ️ O bot responderá apenas a menções.")
        
        # Avança para a próxima etapa
        setup_data["step"] += 1
        await self._process_next_step(ctx)
    
    async def _setup_command_prefix(self, ctx):
        """Configura o prefixo de comandos"""
        setup_data = self.active_setups.get(ctx.channel.id)
        
        # Cria o embed para esta etapa
        current_prefix = self.config.get_prefix()
        embed = discord.Embed(
            title="⌨️ Prefixo de Comandos",
            description=f"Esta configuração define o símbolo usado antes dos comandos.\nO prefixo atual é: **{current_prefix}**",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="📝 Novo Prefixo",
            value="Digite o novo prefixo para comandos (ex: '!', '/', '.')\nOu digite `pular` para manter o prefixo atual.",
            inline=False
        )
        
        await ctx.send(embed=embed)
        
        # Aguarda a resposta do usuário
        response = await self._wait_for_response(ctx)
        if response is None:
            return
            
        # Processa a resposta
        if response.content.lower() != "pular":
            new_prefix = response.content
            setup_data["config"]["prefix"] = new_prefix
            await ctx.send(f"✅ Prefixo definido como: **{new_prefix}**")
        else:
            await ctx.send(f"ℹ️ Mantendo o prefixo atual: **{current_prefix}**")
        
        # Avança para a próxima etapa
        setup_data["step"] += 1
        await self._process_next_step(ctx)
    
    async def _setup_memory_settings(self, ctx):
        """Configura as definições de memória"""
        setup_data = self.active_setups.get(ctx.channel.id)
        
        # Cria o embed para esta etapa
        current_limit = self.config.get_memory_limit()
        current_persistence = self.config.get_config_value("memory_persistence")
        
        embed = discord.Embed(
            title="🧠 Memória Permanente",
            description="Esta configuração define como o bot armazena o histórico de conversas.",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="📝 Limite de Memória",
            value=f"Digite o número de mensagens que o bot deve lembrar (atual: {current_limit})\nOu digite `pular` para manter o valor atual.",
            inline=False
        )
        
        await ctx.send(embed=embed)
        
        # Aguarda a resposta do usuário para o limite de memória
        response = await self._wait_for_response(ctx)
        if response is None:
            return
            
        # Processa a resposta do limite de memória
        if response.content.lower() != "pular":
            try:
                memory_limit = int(response.content)
                if memory_limit < 1:
                    await ctx.send("⚠️ O limite deve ser pelo menos 1. Definindo como 1.")
                    memory_limit = 1
                elif memory_limit > 100:
                    await ctx.send("⚠️ O limite não pode exceder 100. Definindo como 100.")
                    memory_limit = 100
                    
                setup_data["config"]["memory_limit"] = memory_limit
                await ctx.send(f"✅ Limite de memória definido como: **{memory_limit}** mensagens")
            except ValueError:
                await ctx.send("⚠️ Valor inválido. Mantendo o limite atual.")
                
        # Pergunta sobre a persistência de memória
        embed = discord.Embed(
            title="🧠 Memória Permanente",
            description="A persistência de memória permite que o bot lembre das conversas mesmo após ser reiniciado.",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="📝 Persistência",
            value=f"A persistência está atualmente **{'ativada' if current_persistence else 'desativada'}**\nDigite `ativar` ou `desativar` para alterar\nOu digite `pular` para manter o valor atual.",
            inline=False
        )
        
        await ctx.send(embed=embed)
        
        # Aguarda a resposta do usuário para a persistência
        response = await self._wait_for_response(ctx)
        if response is None:
            return
            
        # Processa a resposta da persistência
        if response.content.lower() != "pular":
            if response.content.lower() == "ativar":
                setup_data["config"]["memory_persistence"] = True
                await ctx.send("✅ Persistência de memória **ativada**")
            elif response.content.lower() == "desativar":
                setup_data["config"]["memory_persistence"] = False
                await ctx.send("✅ Persistência de memória **desativada**")
            else:
                await ctx.send("⚠️ Opção inválida. Mantendo a configuração atual.")
        
        # Avança para a próxima etapa
        setup_data["step"] += 1
        await self._process_next_step(ctx)
    
    async def _setup_search_settings(self, ctx):
        """Configura o sistema de busca"""
        setup_data = self.active_setups.get(ctx.channel.id)
        
        # Cria o embed para esta etapa
        current_search_enabled = self.config.get_config_value("search_enabled")
        
        embed = discord.Embed(
            title="🔍 Sistema de Busca",
            description="Esta configuração define como o bot realizará buscas na web.",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="📝 Busca na Web",
            value=f"A busca na web está atualmente **{'ativada' if current_search_enabled else 'desativada'}**\nDigite `ativar` ou `desativar` para alterar\nOu digite `pular` para manter o valor atual.",
            inline=False
        )
        
        await ctx.send(embed=embed)
        
        # Aguarda a resposta do usuário para ativar/desativar busca
        response = await self._wait_for_response(ctx)
        if response is None:
            return
            
        # Processa a resposta da busca
        if response.content.lower() != "pular":
            if response.content.lower() == "ativar":
                setup_data["config"]["search_enabled"] = True
                await ctx.send("✅ Busca na web **ativada**")
                
                # Pergunta sobre as configurações de busca
                embed = discord.Embed(
                    title="🔍 Configurações de Busca",
                    description="Configure as opções de busca usando a API DuckDuckGo.",
                    color=discord.Color.blue()
                )
                embed.add_field(
                    name="📝 Configurações de Busca",
                    value="Digite `1` para configurar a região de busca\nDigite `2` para configurar o nível de filtro de conteúdo\nDigite `3` para configurar o cache de busca\nOu digite `pular` para usar as configurações padrão.",
                    inline=False
                )
                
                await ctx.send(embed=embed)
                
                # Aguarda a resposta do usuário para as configurações de busca
                response = await self._wait_for_response(ctx)
                if response is None:
                    return
                    
                # Processa a resposta das configurações de busca
                if response.content.lower() != "pular":
                    # Configuração de região
                    if response.content == "1":
                        region_embed = discord.Embed(
                            title="🌎 Região de Busca",
                            description="Esta configuração define a região e idioma dos resultados de busca.",
                            color=discord.Color.blue()
                        )
                        region_embed.add_field(
                            name="📝 Região",
                            value="Digite `br-pt` para Brasil/Português\nDigite `us-en` para EUA/Inglês\nDigite `es-es` para Espanha/Espanhol\nOu digite outra região no formato `país-idioma`.",
                            inline=False
                        )
                        
                        await ctx.send(embed=region_embed)
                        
                        # Aguarda a resposta do usuário para a região
                        region_response = await self._wait_for_response(ctx)
                        if region_response is None:
                            return
                            
                        setup_data["config"]["SEARCH_REGION"] = region_response.content.lower()
                        await ctx.send(f"✅ Região de busca definida como: **{region_response.content.lower()}**")
                    
                    # Configuração de filtro de conteúdo
                    elif response.content == "2":
                        safesearch_embed = discord.Embed(
                            title="🔒 Filtro de Conteúdo",
                            description="Esta configuração define o nível de filtragem de conteúdo adulto ou sensível.",
                            color=discord.Color.blue()
                        )
                        safesearch_embed.add_field(
                            name="📝 Nível de Filtro",
                            value="Digite `off` para desativar o filtro\nDigite `moderate` para filtro moderado\nDigite `strict` para filtro rigoroso",
                            inline=False
                        )
                        
                        await ctx.send(embed=safesearch_embed)
                        
                        # Aguarda a resposta do usuário para o filtro
                        safesearch_response = await self._wait_for_response(ctx)
                        if safesearch_response is None:
                            return
                            
                        if safesearch_response.content.lower() in ["off", "moderate", "strict"]:
                            setup_data["config"]["SEARCH_SAFESEARCH"] = safesearch_response.content.lower()
                            await ctx.send(f"✅ Filtro de conteúdo definido como: **{safesearch_response.content.lower()}**")
                        else:
                            await ctx.send("⚠️ Opção inválida. Usando o filtro moderado.")
                            setup_data["config"]["SEARCH_SAFESEARCH"] = "moderate"
                    
                    # Configuração de cache
                    elif response.content == "3":
                        cache_embed = discord.Embed(
                            title="💾 Cache de Busca",
                            description="Esta configuração define se os resultados de busca serão armazenados em cache para melhorar o desempenho.",
                            color=discord.Color.blue()
                        )
                        cache_embed.add_field(
                            name="📝 Cache",
                            value="Digite `ativar` para ativar o cache\nDigite `desativar` para desativar o cache",
                            inline=False
                        )
                        
                        await ctx.send(embed=cache_embed)
                        
                        # Aguarda a resposta do usuário para o cache
                        cache_response = await self._wait_for_response(ctx)
                        if cache_response is None:
                            return
                            
                        if cache_response.content.lower() == "ativar":
                            setup_data["config"]["CACHE_ENABLED"] = True
                            await ctx.send("✅ Cache de busca **ativado**")
                            
                            # Pergunta sobre o tempo de expiração do cache
                            cache_expiry_embed = discord.Embed(
                                title="⏱️ Tempo de Expiração do Cache",
                                description="Esta configuração define por quanto tempo os resultados de busca serão mantidos em cache.",
                                color=discord.Color.blue()
                            )
                            cache_expiry_embed.add_field(
                                name="📝 Tempo (em horas)",
                                value="Digite o número de horas (1-72)\nOu digite `pular` para usar o padrão (24 horas).",
                                inline=False
                            )
                            
                            await ctx.send(embed=cache_expiry_embed)
                            
                            # Aguarda a resposta do usuário para o tempo de expiração
                            cache_expiry_response = await self._wait_for_response(ctx)
                            if cache_expiry_response is None:
                                return
                                
                            if cache_expiry_response.content.lower() != "pular":
                                try:
                                    expiry_hours = int(cache_expiry_response.content)
                                    if expiry_hours < 1:
                                        await ctx.send("⚠️ O tempo mínimo é 1 hora. Definindo como 1 hora.")
                                        expiry_hours = 1
                                    elif expiry_hours > 72:
                                        await ctx.send("⚠️ O tempo máximo é 72 horas. Definindo como 72 horas.")
                                        expiry_hours = 72
                                        
                                    setup_data["config"]["CACHE_EXPIRY"] = expiry_hours
                                    await ctx.send(f"✅ Tempo de expiração do cache definido como: **{expiry_hours} horas**")
                                except ValueError:
                                    await ctx.send("⚠️ Valor inválido. Usando o tempo padrão de 24 horas.")
                                    setup_data["config"]["CACHE_EXPIRY"] = 24
                        elif cache_response.content.lower() == "desativar":
                            setup_data["config"]["CACHE_ENABLED"] = False
                            await ctx.send("✅ Cache de busca **desativado**")
                        else:
                            await ctx.send("⚠️ Opção inválida. Usando as configurações padrão.")
                            setup_data["config"]["CACHE_ENABLED"] = True
                            setup_data["config"]["CACHE_EXPIRY"] = 24
            elif response.content.lower() == "desativar":
                setup_data["config"]["search_enabled"] = False
                await ctx.send("✅ Busca na web **desativada**")
            else:
                await ctx.send("⚠️ Opção inválida. Mantendo a configuração atual.")
        
        # Avança para a próxima etapa
        setup_data["step"] += 1
        await self._process_next_step(ctx)
    
    async def _setup_moderation_settings(self, ctx):
        """Configura as definições de moderação automática"""
        setup_data = self.active_setups.get(ctx.channel.id)
        
        # Cria o embed para esta etapa
        current_moderation = self.config.get_config_value("moderation_enabled", False)
        
        embed = discord.Embed(
            title="🛡️ Moderação Automática",
            description="Esta configuração define como o bot moderará mensagens automaticamente.",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="📝 Moderação Automática",
            value=f"A moderação automática está atualmente **{'ativada' if current_moderation else 'desativada'}**\nDigite `ativar` ou `desativar` para alterar\nOu digite `pular` para manter o valor atual.",
            inline=False
        )
        
        await ctx.send(embed=embed)
        
        # Aguarda a resposta do usuário para ativar/desativar moderação
        response = await self._wait_for_response(ctx)
        if response is None:
            return
            
        # Processa a resposta da moderação
        if response.content.lower() != "pular":
            if response.content.lower() == "ativar":
                setup_data["config"]["moderation_enabled"] = True
                
                # Configurações adicionais de moderação
                embed = discord.Embed(
                    title="🛡️ Opções de Moderação",
                    description="Selecione quais tipos de moderação você deseja ativar.",
                    color=discord.Color.blue()
                )
                embed.add_field(
                    name="📝 Filtros Disponíveis",
                    value="Digite os números dos filtros que deseja ativar, separados por vírgula:\n1. Anti-spam\n2. Anti-flood\n3. Filtro de palavras proibidas\nOu digite `todos` para ativar todos os filtros\nOu digite `pular` para não ativar nenhum filtro.",
                    inline=False
                )
                
                await ctx.send(embed=embed)
                
                # Aguarda a resposta do usuário para os filtros
                response = await self._wait_for_response(ctx)
                if response is None:
                    return
                    
                # Processa a resposta dos filtros
                if response.content.lower() != "pular":
                    if response.content.lower() == "todos":
                        setup_data["config"]["mod_antispam"] = True
                        setup_data["config"]["mod_antiflood"] = True
                        setup_data["config"]["mod_wordfilter"] = True
                        await ctx.send("✅ Todos os filtros de moderação foram **ativados**")
                    else:
                        # Processa os números informados
                        try:
                            selected_filters = [int(f.strip()) for f in response.content.split(',')]
                            
                            # Configura cada filtro selecionado
                            if 1 in selected_filters:
                                setup_data["config"]["mod_antispam"] = True
                            if 2 in selected_filters:
                                setup_data["config"]["mod_antiflood"] = True
                            if 3 in selected_filters:
                                setup_data["config"]["mod_wordfilter"] = True
                                
                            await ctx.send("✅ Filtros selecionados foram **ativados**")
                        except ValueError:
                            await ctx.send("⚠️ Formato inválido. Nenhum filtro foi ativado.")
                
                # Se o filtro de palavras foi ativado, perguntar sobre palavras proibidas
                if setup_data["config"].get("mod_wordfilter", False):
                    embed = discord.Embed(
                        title="🔤 Palavras Proibidas",
                        description="Configure a lista de palavras que serão filtradas pelo bot.",
                        color=discord.Color.blue()
                    )
                    embed.add_field(
                        name="📝 Lista de Palavras",
                        value="Digite as palavras proibidas separadas por vírgula\nOu digite `pular` para usar a lista padrão.",
                        inline=False
                    )
                    
                    await ctx.send(embed=embed)
                    
                    # Aguarda a resposta do usuário para as palavras proibidas
                    response = await self._wait_for_response(ctx)
                    if response is None:
                        return
                        
                    # Processa a resposta das palavras proibidas
                    if response.content.lower() != "pular":
                        banned_words = [word.strip().lower() for word in response.content.split(',')]
                        setup_data["config"]["banned_words"] = banned_words
                        await ctx.send(f"✅ Lista de {len(banned_words)} palavras proibidas configurada")
                
            elif response.content.lower() == "desativar":
                setup_data["config"]["moderation_enabled"] = False
                await ctx.send("✅ Moderação automática **desativada**")
            else:
                await ctx.send("⚠️ Opção inválida. Mantendo a configuração atual.")
        
        # Avança para a próxima etapa
        setup_data["step"] += 1
        await self._process_next_step(ctx)
    
    async def _setup_bot_personality(self, ctx):
        """Configura a personalidade do bot"""
        setup_data = self.active_setups.get(ctx.channel.id)
        
        # Cria o embed para esta etapa
        current_personality = self.config.get_config_value("bot_personality", "assistente amigável")
        
        embed = discord.Embed(
            title="🎭 Personalidade do Bot",
            description="Esta configuração define como o bot se comportará nas interações.",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="📝 Personalidade",
            value="Escolha uma das personalidades abaixo:\n1. Formal e profissional\n2. Casual e amigável\n3. Humorístico e descontraído\nOu digite uma personalidade personalizada\nOu digite `pular` para manter a personalidade atual.",
            inline=False
        )
        
        await ctx.send(embed=embed)
        
        # Aguarda a resposta do usuário para a personalidade
        response = await self._wait_for_response(ctx)
        if response is None:
            return
            
        # Processa a resposta da personalidade
        if response.content.lower() != "pular":
            if response.content == "1":
                setup_data["config"]["bot_personality"] = "formal e profissional"
                await ctx.send("✅ Personalidade definida como: **Formal e profissional**")
            elif response.content == "2":
                setup_data["config"]["bot_personality"] = "casual e amigável"
                await ctx.send("✅ Personalidade definida como: **Casual e amigável**")
            elif response.content == "3":
                setup_data["config"]["bot_personality"] = "humorístico e descontraído"
                await ctx.send("✅ Personalidade definida como: **Humorístico e descontraído**")
            else:
                setup_data["config"]["bot_personality"] = response.content
                await ctx.send(f"✅ Personalidade personalizada definida como: **{response.content}**")
        
        # Avança para a próxima etapa
        setup_data["step"] += 1
        await self._process_next_step(ctx)
    
    async def _setup_notification_settings(self, ctx):
        """Configura as notificações do bot"""
        setup_data = self.active_setups.get(ctx.channel.id)
        
        # Cria o embed para esta etapa
        current_notifications = self.config.get_config_value("notifications_enabled", False)
        
        embed = discord.Embed(
            title="🔔 Notificações",
            description="Esta configuração define como o bot enviará notificações sobre seu status.",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="📝 Notificações",
            value=f"As notificações estão atualmente **{'ativadas' if current_notifications else 'desativadas'}**\nDigite `ativar` ou `desativar` para alterar\nOu digite `pular` para manter o valor atual.",
            inline=False
        )
        
        await ctx.send(embed=embed)
        
        # Aguarda a resposta do usuário para ativar/desativar notificações
        response = await self._wait_for_response(ctx)
        if response is None:
            return
            
        # Processa a resposta das notificações
        if response.content.lower() != "pular":
            if response.content.lower() == "ativar":
                setup_data["config"]["notifications_enabled"] = True
                
                # Pergunta sobre o método de notificação
                embed = discord.Embed(
                    title="🔔 Método de Notificação",
                    description="Escolha como o bot enviará notificações.",
                    color=discord.Color.blue()
                )
                embed.add_field(
                    name="📝 Método",
                    value="Digite `telegram` para usar o Telegram\nDigite `webhook` para usar Webhook\nOu digite `pular` para usar o padrão (Webhook).",
                    inline=False
                )
                
                await ctx.send(embed=embed)
                
                # Aguarda a resposta do usuário para o método de notificação
                response = await self._wait_for_response(ctx)
                if response is None:
                    return
                    
                # Processa a resposta do método de notificação
                if response.content.lower() != "pular":
                    if response.content.lower() == "telegram":
                        setup_data["config"]["notification_method"] = "telegram"
                        
                        # Pergunta sobre o token do bot do Telegram
                        embed = discord.Embed(
                            title="🔔 Token do Telegram",
                            description="Configure o token do bot do Telegram para receber notificações.",
                            color=discord.Color.blue()
                        )
                        embed.add_field(
                            name="📝 Token",
                            value="Digite o token do seu bot do Telegram\nOu digite `pular` para configurar depois.",
                            inline=False
                        )
                        
                        await ctx.send(embed=embed)
                        
                        # Aguarda a resposta do usuário para o token do Telegram
                        response = await self._wait_for_response(ctx)
                        if response is None:
                            return
                            
                        # Processa a resposta do token do Telegram
                        if response.content.lower() != "pular":
                            setup_data["config"]["telegram_token"] = response.content
                            await ctx.send("✅ Token do Telegram configurado")
                            
                            # Pergunta sobre o chat ID do Telegram
                            embed = discord.Embed(
                                title="🔔 Chat ID do Telegram",
                                description="Configure o ID do chat para onde as notificações serão enviadas.",
                                color=discord.Color.blue()
                            )
                            embed.add_field(
                                name="📝 Chat ID",
                                value="Digite o ID do chat do Telegram\nOu digite `pular` para configurar depois.",
                                inline=False
                            )
                            
                            await ctx.send(embed=embed)
                            
                            # Aguarda a resposta do usuário para o chat ID do Telegram
                            response = await self._wait_for_response(ctx)
                            if response is None:
                                return
                                
                            # Processa a resposta do chat ID do Telegram
                            if response.content.lower() != "pular":
                                setup_data["config"]["telegram_chat_id"] = response.content
                                await ctx.send("✅ Chat ID do Telegram configurado")
                    
                    elif response.content.lower() == "webhook":
                        setup_data["config"]["notification_method"] = "webhook"
                        
                        # Pergunta sobre a URL do webhook
                        embed = discord.Embed(
                            title="🔔 URL do Webhook",
                            description="Configure a URL do webhook para receber notificações.",
                            color=discord.Color.blue()
                        )
                        embed.add_field(
                            name="📝 URL",
                            value="Digite a URL completa do webhook\nOu digite `pular` para configurar depois.",
                            inline=False
                        )
                        
                        await ctx.send(embed=embed)
                        
                        # Aguarda a resposta do usuário para a URL do webhook
                        response = await self._wait_for_response(ctx)
                        if response is None:
                            return
                            
                        # Processa a resposta da URL do webhook
                        if response.content.lower() != "pular":
                            setup_data["config"]["webhook_url"] = response.content
                            await ctx.send("✅ URL do webhook configurada")
                    else:
                        await ctx.send("⚠️ Opção inválida. Usando o método padrão (Webhook).")
                        setup_data["config"]["notification_method"] = "webhook"
                else:
                    setup_data["config"]["notification_method"] = "webhook"
                    
            elif response.content.lower() == "desativar":
                setup_data["config"]["notifications_enabled"] = False
                await ctx.send("✅ Notificações **desativadas**")
            else:
                await ctx.send("⚠️ Opção inválida. Mantendo a configuração atual.")
        
        # Avança para a próxima etapa
        setup_data["step"] += 1
        await self._process_next_step(ctx)