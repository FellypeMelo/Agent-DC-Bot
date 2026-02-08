# setup.py
import discord
from discord.ext import commands
import json
import asyncio
import logging

logger = logging.getLogger(__name__)

class CharacterWizard(commands.Cog):
    """
    Wizard interativo para criação de personagens (7 Pilares).
    """
    def __init__(self, bot, db, ai_handler, voice_engine, memory):
        self.bot = bot
        self.db = db
        self.ai = ai_handler
        self.voice = voice_engine
        self.memory = memory

    @commands.command(name="create_character", aliases=["setup_ai"])
    @commands.has_permissions(administrator=True)
    async def create_character(self, ctx):
        """Inicia o processo de criação de um novo personagem."""
        
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        results = {}
        
        try:
            await ctx.send("🎨 **Iniciando Arquiteto de Personagem (1/7)**\nQual o **Nome** e **Apelido** do bot?")
            msg = await self.bot.wait_for('message', check=check, timeout=120.0)
            results['identity'] = {"name": msg.content, "language": "Portuguese"}

            await ctx.send("🧠 **Personalidade (2/7)**\nComo ele deve ser? (Ex: Sarcástico, fofo, lógico, caótico?)")
            msg = await self.bot.wait_for('message', check=check, timeout=120.0)
            results['personality'] = {"traits": msg.content, "empathy": 0.5}

            await ctx.send("📖 **História (3/7)**\nQual a origem dele? Por que ele existe?")
            msg = await self.bot.wait_for('message', check=check, timeout=120.0)
            results['history'] = {"backstory": msg.content}

            await ctx.send("🎭 **Emoções (4/7)**\nEle é reativo e intenso ou frio e calculista?")
            msg = await self.bot.wait_for('message', check=check, timeout=120.0)
            results['emotions'] = {"sensitivity": msg.content}

            await ctx.send("🤝 **Relação Social (5/7)**\nEle é um assistente, um mestre, um amigo ou um rival?")
            msg = await self.bot.wait_for('message', check=check, timeout=120.0)
            results['social'] = {"role": msg.content}

            await ctx.send("💬 **Interação (6/7)**\nEle fala muito (textão) ou é direto? Ele interrompe as pessoas?")
            msg = await self.bot.wait_for('message', check=check, timeout=120.0)
            results['interaction'] = {"style": msg.content}

            await ctx.send("⚙️ **Técnica (7/7)**\nQual o nível de criatividade? (0.1 a 1.5 - recomendado 0.7)")
            msg = await self.bot.wait_for('message', check=check, timeout=120.0)
            results['technical'] = {"temperature": float(msg.content)}

            # --- Finalização e Síntese ---
            status_msg = await ctx.send("⌛ **Processando Persona e Gerando DNA de Voz...** (Isso pode levar de 30 a 60 segundos na Intel ARC)")
            
            # 1. Gera Instrução Acústica via LLM
            persona_desc = f"{results['personality']['traits']} - {results['social']['role']}"
            acoustic_instruct = await self.ai.generate_voice_dna_instruction(persona_desc)
            await status_msg.edit(content=f"⌛ **Instrução de voz gerada:** `{acoustic_instruct}`\nAgora carregando o modelo VoiceDesign...")
            
            # 2. Gera DNA de Voz (VoiceDesign)
            voice_dna_prompt = await self.voice.design_and_cache_voice("active_dna", acoustic_instruct)
            await status_msg.edit(content="⌛ **DNA de Voz capturado com sucesso!** Salvando perfil no banco de dados...")
            
            # 3. Salva no Banco de Dados
            import pickle
            voice_dna_blob = pickle.dumps(voice_dna_prompt) if voice_dna_prompt else None
            await self.save_profile(results, voice_dna_blob)
            
            await status_msg.edit(content=f"✨ **Sucesso!** O personagem **{results['identity']['name']}** nasceu e sua voz foi calibrada!")
            
        except asyncio.TimeoutError:
            await ctx.send("❌ Tempo esgotado. Processo cancelado.")
        except Exception as e:
            await ctx.send(f"❌ Erro crítico: {e}")
            logger.error(f"Wizard Error: {e}")

    async def save_profile(self, r, voice_dna_blob):
        # Desativa perfis antigos
        await self.db._db.execute("UPDATE character_profiles SET is_active = 0")
        
        query = """
            INSERT INTO character_profiles 
            (identity_json, personality_json, history_json, emotions_json, social_json, interaction_json, technical_json, voice_dna, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
        """
        await self.db._db.execute(query, (
            json.dumps(r['identity']),
            json.dumps(r['personality']),
            json.dumps(r['history']),
            json.dumps(r['emotions']),
            json.dumps(r['social']),
            json.dumps(r['interaction']),
            json.dumps(r['technical']),
            voice_dna_blob
        ))
        await self.db._db.commit()

async def setup(bot):
    # Nota: Este setup será chamado pelo bot.py
    pass
