# setup.py
import discord
from discord.ext import commands
import json
import asyncio
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class CharacterWizard(commands.Cog):
    """
    Interactive wizard for creating AI personas using the '7 Pillars' framework.
    """
    def __init__(self, bot, db, ai_handler, memory):
        """
        Initializes the wizard.
        
        Big (O): O(1).
        """
        self.bot = bot
        self.db = db
        self.ai = ai_handler
        self.memory = memory

    @commands.command(name="create_character", aliases=["setup_ai"])
    @commands.has_permissions(administrator=True)
    async def create_character(self, ctx):
        """
        Starts the step-by-step character creation process.
        
        Big (O): O(1) per step - Bound by user input speed and network latency.
        """
        
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        results = {}
        steps = [
            ("identity", "🎨 **Identidade (1/7)**\nQual o **Nome** e **Apelido** do bot?", lambda x: {"name": x, "language": "Portuguese"}),
            ("personality", "🧠 **Personalidade (2/7)**\nComo ele deve ser? (Ex: Sarcástico, fofo, lógico?)", lambda x: {"traits": x, "empathy": 0.5}),
            ("history", "📖 **História (3/7)**\nQual a origem dele? Por que ele existe?", lambda x: {"backstory": x}),
            ("emotions", "🎭 **Emoções (4/7)**\nEle é reativo e intenso ou frio e calculista?", lambda x: {"sensitivity": x}),
            ("social", "🤝 **Relação Social (5/7)**\nEle é um assistente, um mestre, um amigo ou um rival?", lambda x: {"role": x}),
            ("interaction", "💬 **Interação (6/7)**\nEle fala muito ou é direto? Como ele conversa?", lambda x: {"style": x}),
            ("technical", "⚙️ **Técnica (7/7)**\nNível de criatividade? (0.1 a 1.5 - recomendado 0.7)", lambda x: {"temperature": float(x)})
        ]
        
        try:
            for key, prompt, formatter in steps:
                await ctx.send(prompt)
                msg = await self.bot.wait_for('message', check=check, timeout=120.0)
                results[key] = formatter(msg.content)

            # Finalize: Save to DB
            status_msg = await ctx.send("⌛ **Salvando perfil...**")
            await self.save_profile(results)
            await status_msg.edit(content=f"✨ **Sucesso!** O personagem **{results['identity']['name']}** foi ativado!")
            
        except asyncio.TimeoutError:
            await ctx.send("❌ Tempo esgotado. Processo cancelado.")
        except Exception as e:
            await ctx.send(f"❌ Erro crítico: {e}")
            logger.error(f"Wizard Error: {e}", exc_info=True)

    async def save_profile(self, r: Dict[str, Any]) -> None:
        """
        Persists the character profile to the database and activates it.
        
        Args:
            r: Dictionary containing all 7 pillars data.
            
        Big (O): O(1) - Single transaction with fixed number of fields.
        """
        # Deactivate previous profiles in one step
        await self.db._db.execute("UPDATE character_profiles SET is_active = 0")
        
        query = """
            INSERT INTO character_profiles 
            (identity_json, personality_json, history_json, emotions_json, social_json, interaction_json, technical_json, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1)
        """
        
        # Serialize all components to JSON (O(1) given small fixed keys)
        await self.db._db.execute(query, (
            json.dumps(r['identity']),
            json.dumps(r['personality']),
            json.dumps(r['history']),
            json.dumps(r['emotions']),
            json.dumps(r['social']),
            json.dumps(r['interaction']),
            json.dumps(r['technical'])
        ))
        await self.db._db.commit()

async def setup(bot):
    # Cog loading handled via bot.py
    pass