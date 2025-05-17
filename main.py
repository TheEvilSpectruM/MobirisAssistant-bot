import os
import discord
from discord.ext import commands
from discord import app_commands
from discord.app_commands import Choice

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
        count = click_counters.get(self.message_id, 0) + 1
        click_counters[self.message_id] = count

        message = interaction.message
        # On récupère uniquement la première ligne du message (le message d'origine)
        original_message = message.content.splitlines()[0]

        await message.edit(content=f"{original_message}\n\nNombre de personnes qui ont cliqué : **{count}**", view=self)
        await interaction.response.send_message("Merci pour ton clic ! ✅", ephemeral=True)

@tree.command(name="sendmessage", description="Envoyer un message avec bouton")
@app_commands.describe(
    channel="Le salon où envoyer le message",
    message="Le contenu du message à envoyer"
)
@app_commands.checks.has_role("Staff")  # Restreint aux utilisateurs avec rôle Staff
async def sendmessage(interaction: discord.Interaction, channel: discord.TextChannel, message: str):
    # Envoie le message avec bouton et compteur à 0
    sent_msg = await channel.send(
        content=f"{message}\n\nNombre de personnes qui ont cliqué : **0**",
        view=ClickButton(0)  # temporaire, on mettra à jour juste après
    )
    # Met à jour la vue avec le bon message id
    sent_msg_view = ClickButton(sent_msg.id)
    await sent_msg.edit(view=sent_msg_view)

    click_counters[sent_msg.id] = 0
    await interaction.response.send_message(f"Message envoyé dans {channel.mention} !", ephemeral=True)

@sendmessage.error
async def sendmessage_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.errors.MissingRole):
        await interaction.response.send_message("⛔ Tu n'as pas la permission d'utiliser cette commande.", ephemeral=True)
    else:
        await interaction.response.send_message(f"Erreur: {error}", ephemeral=True)

@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ Connecté en tant que {bot.user}")

token = os.getenv("TOKEN")
print(f"Token récupéré : {token is not None}")

bot.run(token)
