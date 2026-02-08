# commands.py
import discord
from discord.ext import commands
import os
import json
import time
import psutil
from core.logger import setup_logger

logger = setup_logger("modules.commands")

class CommandHandler(commands.Cog):
    def __init__(self, bot, config, memory, ai_handler):
        self.bot = bot
        self.config = config
        self.memory = memory
        self.ai = ai_handler
        self.start_time = time.time()

    @commands.command(name='ajuda', aliases=['help'])
    async def ajuda(self, ctx):
        """Menu de Ajuda Central"""
        prefix = self.bot.command_prefix
        embed = discord.Embed(
            title="🤖 Central de Comando Blepp",
            color=discord.Color.blue(),
            description="Aqui estão as ferramentas de configuração e interação."
        )
        
        embed.add_field(
            name="✨ Configuração (Passo a Passo)",
            value=f"`{prefix}setup_ai` - Cria sua personalidade e voz do zero.",
            inline=False
        )
        
        embed.add_field(
            name="🔊 Conversa por Voz",
            value=f"`{prefix}join` - Entra no canal e ativa Whisper.\n`{prefix}leave` - Sai do canal.",
            inline=False
        )
        
        embed.add_field(
            name="🎭 Persona & IA",
            value=f"`{prefix}perfil` - Status da persona ativa.\n`{prefix}status` - Saúde do sistema.",
            inline=False
        )
        
        embed.add_field(
            name="🧠 Memória",
            value=f"`{prefix}memorias` - O que eu sei sobre você.\n`{prefix}limpar` - Reseta o chat.",
            inline=False
        )
        
        await ctx.send(embed=embed)

    @commands.command(name='status')
    async def status(self, ctx):
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        
        voice_cog = self.bot.get_cog("VoiceHandler")
        tts_status = "Inativo"
        if voice_cog:
            if voice_cog.voice_engine.kokoro:
                tts_status = "Kokoro (Fast Mode)"
            elif voice_cog.voice_engine.model:
                tts_status = "Qwen (Quality Mode)"
            else:
                tts_status = "Aguardando"

        embed = discord.Embed(title="📊 Status do Bot", color=discord.Color.green())
        embed.add_field(name="💻 CPU", value=f"{cpu}%")
        embed.add_field(name="🧠 RAM", value=f"{ram}%")
        embed.add_field(name="🔊 TTS", value=tts_status)
        embed.add_field(name="🤖 AI", value="LM-STUDIO (Online)", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name='limpar')
    async def limpar(self, ctx):
        await self.memory.db.clear_history(ctx.author.id)
        await ctx.send("🧹 Histórico de conversa limpo!")

    @commands.command(name='memorias')
    async def memorias(self, ctx):
        async with self.memory.db._db.execute(
            "SELECT content FROM memories WHERE user_id = ?", (str(ctx.author.id),)
        ) as cursor:
            rows = await cursor.fetchall()
        if rows:
            res = "\n".join([f"• {r[0]}" for r in rows])
            await ctx.send(f"🧠 **Fatos salvos:**\n{res}")
        else:
            await ctx.send("📭 Sem memórias por enquanto.")

    @commands.command(name='perfil')
    async def perfil(self, ctx):
        async with self.memory.db._db.execute("SELECT identity_json FROM character_profiles WHERE is_active = 1") as cursor:
            row = await cursor.fetchone()
            if not row: return await ctx.send("⚠️ Sem perfil ativo. Use `!setup_ai`.")
            data = json.loads(row[0])
            await ctx.send(f"👤 **Perfil Ativo:** {data.get('name')}")

async def setup(bot):
    pass