import discord
from discord.ext import commands
import json
import psutil
import os
from core.logger import setup_logger

logger = setup_logger("modules.commands")

class CommandHandler(commands.Cog):
    def __init__(self, bot, config, memory, ai_handler):
        self.bot = bot
        self.config = config
        self.memory = memory
        self.ai = ai_handler

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

        backend = await self.config.get_config_db("llm_backend", "lm_studio")
        ai_status = f"Backend: {backend}"

        if backend == "llama_cpp":
            # Access LlamaServerManager via bot instance if available
            # self.bot.owner_instance refers to the DiscordBot class instance which holds llama_server
            if hasattr(self.bot, 'owner_instance') and hasattr(self.bot.owner_instance, 'llama_server'):
                mgr = self.bot.owner_instance.llama_server
                if mgr.is_running():
                    ai_status += f"\n✅ Llama Server (PID: {mgr.process.pid})"
                else:
                    ai_status += "\n❌ Llama Server Parado"
            else:
                 ai_status += " (Ext)"

        embed = discord.Embed(title="📊 Status do Bot", color=discord.Color.green())
        embed.add_field(name="💻 CPU", value=f"{cpu}%")
        embed.add_field(name="🧠 RAM", value=f"{ram}%")
        embed.add_field(name="🔊 TTS", value=tts_status)
        embed.add_field(name="🤖 AI", value=ai_status, inline=False)
        await ctx.send(embed=embed)

    @commands.command(name='llm_restart')
    @commands.is_owner()
    async def llm_restart(self, ctx):
        """Reinicia o servidor Llama.cpp (Apenas Owner)"""
        backend = await self.config.get_config_db("llm_backend", "lm_studio")
        if backend != "llama_cpp":
            return await ctx.send("⚠️ Este comando só funciona com o backend `llama_cpp`.")

        msg = await ctx.send("🔄 Reiniciando Llama Server...")

        if hasattr(self.bot, 'owner_instance') and hasattr(self.bot.owner_instance, 'llama_server'):
            mgr = self.bot.owner_instance.llama_server
            try:
                mgr.stop()
                mgr.start()
                if await mgr.wait_for_ready(timeout=30):
                    await msg.edit(content="✅ Llama Server reiniciado com sucesso!")
                else:
                    await msg.edit(content="❌ Falha ao reiniciar Llama Server. Verifique os logs.")
            except Exception as e:
                await msg.edit(content=f"❌ Erro crítico: {e}")
        else:
            await msg.edit(content="❌ Gerenciador não encontrado.")

    @commands.command(name='llm_logs')
    @commands.is_owner()
    async def llm_logs(self, ctx, lines: int = 15):
        """Mostra as últimas linhas do log do Llama Server"""
        log_path = "llama_server.log"
        if not os.path.exists(log_path):
            return await ctx.send("⚠️ Arquivo de log não encontrado.")

        try:
            with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.readlines()
                if not content:
                    return await ctx.send("📄 Log vazio.")

                last_lines = "".join(content[-lines:])
                if len(last_lines) > 1900:
                    last_lines = last_lines[-1900:]

                await ctx.send(f"📄 **Llama Server Logs (Últimas {lines} linhas):**\n```log\n{last_lines}```")
        except Exception as e:
            await ctx.send(f"❌ Erro ao ler log: {e}")

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
