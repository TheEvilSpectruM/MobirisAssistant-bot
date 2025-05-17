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

def hex_to_button_style(hex_color: str) -> discord.ButtonStyle:
    """
    Map une couleur hex vers un ButtonStyle Discord.
    Discord ne supporte que quelques styles, donc on approxime :
    - bleu foncé (#0000ff) -> primary
    - gris (#808080) -> secondary
    - vert (#00ff00) -> success
    - rouge (#ff0000) -> danger
    Sinon fallback sur primary.
    """
    hex_color = hex_color.lower()
    mapping = {
        "#0000ff": discord.ButtonStyle.primary,
        "#000080": discord.ButtonStyle.primary,
        "#808080": discord.ButtonStyle.secondary,
        "#00ff00": discord.ButtonStyle.success,
        "#008000": discord.ButtonStyle.success,
        "#ff0000": discord.ButtonStyle.danger,
        "#800000": discord.ButtonStyle.danger,
        "#000000": discord.ButtonStyle.secondary,
    }
    # recherche approximative par couleur la plus proche
    # ici simple égalité ou fallback
    return mapping.get(hex_color, discord.ButtonStyle.primary)

class ClickButton(discord.ui.View):
    def __init__(self, message_id, button_label="📥 Je clique !", button_style=discord.ButtonStyle.primary):
        super().__init__(timeout=None)
        self.message_id = message_id
        # On crée le bouton dynamique
        self.button = discord.ui.Button(label=button_label, style=button_style)
        self.button.callback = self.click
        self.add_item(self.button)

    async def click(self, interaction: discord.Interaction):
        message = interaction.message
        click_counters[self.message_id] = click_counters.get(self.message_id, 0) + 1
        count = click_counters[self.message_id]
        original_lines = message.content.splitlines()
        new_content = original_lines[0] + f"\n\nNombre de personnes qui ont cliqué : **{count}**"
        await message.edit(content=new_content, view=self)
        await interaction.response.send_message("Merci pour ton clic ! ✅", ephemeral=True)


@tree.command(
    name="sendmessage",
    description="Envoyer un message avec bouton personnalisé"
)
@app_commands.describe(
    channel="Le salon où envoyer le message",
    message="Le contenu du message à envoyer",
    button_text="Texte du bouton",
    button_color="Couleur du bouton en hex (ex: #544de2)"
)
@app_commands.checks.has_role("Administrateurs")
async def sendmessage(
    interaction: discord.Interaction,
    channel: discord.TextChannel,
    message: str,
    button_text: str = "📥 Je clique !",
    button_color: str = "#0000ff"
):
    # Validation simple du format hex
    if not button_color.startswith("#") or len(button_color) != 7:
        await interaction.response.send_message("❌ Couleur invalide. Utilise un code hex comme #544de2.", ephemeral=True)
        return
    
    style = hex_to_button_style(button_color)
    view = ClickButton(message_id=0, button_label=button_text, button_style=style)
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
