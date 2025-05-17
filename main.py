import os
import discord
from discord.ext import commands
from discord import app_commands

token = os.getenv("TOKEN")
print(f"Token récupéré : {token is not None}")  # Affiche True si token bien récupéré

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

click_counters = {}

class ClickButton(discord.ui.View):
    def __init__(self, message_id):
        super().__init__(timeout=None)
        self.message_id = message_id

    @discord.ui.button(label="📥 Je clique !", style=discord.ButtonStyle.primary)
    async def click(self, interaction: discord.Interaction, button: discord.ui.Button):
        message = interaction.message
        click_counters[self.message_id] = click_counters.get(self.message_id, 0) + 1
        count = click_counters[self.message_id]
        # On met à jour le contenu du message avec le nouveau compteur
        original_lines = message.content.splitlines()
        # On garde la première ligne (le message) et on remplace la ligne compteur
        new_content = original_lines[0] + f"\n\nNombre de personnes qui ont cliqué : **{count}**"
        await message.edit(content=new_content, view=self)
        await interaction.response.send_message("Merci pour ton clic ! ✅", ephemeral=True)


@tree.command(
    name="sendmessage",
    description="Envoyer un message avec bouton"
)
@app_commands.describe(
    channel="Le salon où envoyer le message",
    message="Le contenu du message à envoyer"
)
@app_commands.checks.has_role("Administrateurs")
async def sendmessage(interaction: discord.Interaction, channel: discord.TextChannel, message: str):
    view = ClickButton(message_id=0)  # id temporaire
    sent_message = await channel.send(
        content=f"{message}\n\nNombre de personnes qui ont cliqué : **0**",
        view=view
    )
    view.message_id = sent_message.id
    click_counters[sent_message.id] = 0
    await interaction.response.send_message(f"Message envoyé dans {channel.mention} !", ephemeral=True)


@sendmessage.error
async def sendmessage_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.errors.MissingRole):
        await interaction.response.send_message("⛔ Tu n'as pas la permission d'utiliser cette commande.", ephemeral=True)
    else:
        await interaction.response.send_message(f"Une erreur est survenue: {error}", ephemeral=True)


@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ Connecté en tant que {bot.user}")

bot.run(token)
