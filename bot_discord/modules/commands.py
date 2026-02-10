# commands.py
import discord
from discord.ext import commands
import json
import psutil
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class CommandHandler(commands.Cog):
    def __init__(self, bot, config, memory, ai_handler):
        """
        Initializes command handlers.
        
        Big (O): O(1).
        """
        self.bot = bot
        self.config = config
        self.memory = memory
        self.ai = ai_handler

    @commands.command(name='ajuda', aliases=['help'])
    async def ajuda(self, ctx):
        """
        Displays the help menu.
        
        Big (O): O(1) - Constant time response with static content.
        """
        prefix = self.bot.command_prefix
        embed = discord.Embed(
            title="🤖 Central de Comando",
            color=discord.Color.blue(),
            description="Interface de controle do Agente DC."
        )
        
        embed.add_field(
            name="✨ Configuração",
            value=f"`{prefix}setup_ai` - Configura a personalidade.",
            inline=False
        )
        
        embed.add_field(
            name="🧠 Memória",
            value=f"`{prefix}memorias` - Consulta fatos salvos.\n`{prefix}limpar` - Reseta o chat.",
            inline=False
        )
        
        embed.add_field(
            name="📊 Sistema",
            value=f"`{prefix}status` - Saúde do bot.",
            inline=False
        )
        
        await ctx.send(embed=embed)

    @commands.command(name='status')
    async def status(self, ctx):
        """
        Displays system resource usage and AI backend status.
        
        Big (O): O(1) - Rapid syscalls for CPU/RAM and single DB lookup.
        """
        # psutil calls are efficient C-level lookups
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        
        backend = await self.config.get_config_db("llm_backend", "lm_studio")
        ai_status = f"Backend: {backend}"

        # Llama Server check if applicable
        if backend == "llama_cpp":
            if hasattr(self.bot, 'owner_instance') and hasattr(self.bot.owner_instance, 'llama_server'):
                mgr = self.bot.owner_instance.llama_server
                if mgr.is_running():
                    ai_status += f"\n✅ Online (PID: {mgr.process.pid})"
                else:
                    ai_status += "\n❌ Offline"

        embed = discord.Embed(title="📊 Status do Sistema", color=discord.Color.green())
        embed.add_field(name="💻 CPU", value=f"{cpu}%")
        embed.add_field(name="🧠 RAM", value=f"{ram}%")
        embed.add_field(name="🤖 AI", value=ai_status, inline=False)
        await ctx.send(embed=embed)

    @commands.command(name='limpar')
    async def limpar(self, ctx):
        """
        Clears the short-term conversation history for the user.
        
        Big (O): O(1) - Targeted SQL deletion.
        """
        await self.memory.db.clear_history(ctx.author.id)
        await ctx.send("🧹 Histórico de conversa limpo!")

    @commands.command(name='memorias')
    async def memorias(self, ctx):
        """
        Lists stored permanent facts about the user.
        
        Big (O): O(M) - M is number of memories (formatting for display).
        """
        async with self.memory.db._db.execute(
            "SELECT content FROM memories WHERE user_id = ? LIMIT 10", (str(ctx.author.id),)
        ) as cursor:
            rows = await cursor.fetchall()
            
        if rows:
            # Efficient join for string building
            res = "\n".join([f"• {r[0]}" for r in rows])
            await ctx.send(f"🧠 **O que eu lembro sobre você:**\n{res}")
        else:
            await ctx.send("📭 Ainda não tenho memórias salvas.")

    @commands.command(name='perfil')
    async def perfil(self, ctx):
        """
        Shows the currently active character profile.
        
        Big (O): O(1) - Single SQL lookup.
        """
        async with self.memory.db._db.execute("SELECT identity_json FROM character_profiles WHERE is_active = 1") as cursor:
            row = await cursor.fetchone()
            if not row: 
                return await ctx.send("⚠️ Sem perfil ativo. Use `!setup_ai`.")
            
            data = json.loads(row[0])
            await ctx.send(f"👤 **Persona Ativa:** {data.get('name')}")

async def setup(bot):
    # This Cog is loaded manually in bot.py
    pass