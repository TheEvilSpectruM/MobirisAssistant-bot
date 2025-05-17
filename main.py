import os
import discord
from discord.ext import commands
from discord import app_commands

token = os.getenv("TOKEN")
print(f"Token récupéré : {token is not None}")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

click_counters = {}

class MessageModal(discord.ui.Modal, title="Envoyer un message avec bouton"):
    channel = discord.ui.TextInput(label="ID du salon (channel id)", placeholder="Ex: 123456789012345678")
    message_content = discord.ui.TextInput(label="Message à envoyer", style=discord.TextStyle.paragraph)
    button_text = discord.ui.TextInput(label="Texte du bouton", placeholder="Ex: Cliquer ici !", max_length=50)
    button_color = discord.ui.TextInput(label="Couleur du bouton (hexadécimal)", placeholder="#5865F2", max_length=9)

    def __init__(self, interaction: discord.Interaction):
        super().__init__()
        self.interaction = interaction

    async def on_submit(self, interaction: discord.Interaction):
        try:
            channel_id = int(self.channel.value.strip())
        except ValueError:
            await interaction.response.send_message("ID du salon invalide.", ephemeral=True)
            return

        channel = self.interaction.guild.get_channel(channel_id)
        if channel is None:
            await interaction.response.send_message("Salon introuvable.", ephemeral=True)
            return

        label = self.button_text.value.strip() or "Clique ici"
        # Note : Discord n'autorise pas les couleurs personnalisées sur les boutons (limité aux styles prédéfinis)
        # Donc on ignore la couleur dans le style, toujours style=primary

        view = ClickButton(message_id=0, label=label)
        sent_message = await channel.send(
            content=f"{self.message_content.value}\n\nNombre de personnes qui ont cliqué : **0**",
            view=view
        )
        view.message_id = sent_message.id
        click_counters[sent_message.id] = 0

        await interaction.response.send_message(f"Message envoyé dans {channel.mention} !", ephemeral=True)


class ClickButton(discord.ui.View):
    def __init__(self, message_id: int, label: str = "Clique ici"):
        super().__init__(timeout=None)
        self.message_id = message_id
        self.button = discord.ui.Button(label=label, style=discord.ButtonStyle.primary)
        self.add_item(self.button)
        self.button.callback = self.click_callback

    async def click_callback(self, interaction: discord.Interaction):
        click_counters[self.message_id] = click_counters.get(self.message_id, 0) + 1
        count = click_counters[self.message_id]
        message = interaction.message
        lines = message.content.splitlines()
        if lines:
            new_content = lines[0] + f"\n\nNombre de personnes qui ont cliqué : **{count}**"
            await message.edit(content=new_content, view=self)
        await interaction.response.send_message("Merci pour ton clic ! ✅", ephemeral=True)


# Commande /sendmessage
@tree.command(name="sendmessage", description="Envoyer un message avec bouton personnalisé")
async def sendmessage(interaction: discord.Interaction):
    admin_role = discord.utils.get(interaction.guild.roles, name="Administrateur")
    if admin_role not in interaction.user.roles:
        await interaction.response.send_message("⛔ Tu n'as pas la permission d'utiliser cette commande.", ephemeral=True)
        return
    modal = MessageModal(interaction)
    await interaction.response.send_modal(modal)


# Commande /session
@tree.command(name="session", description="Créer une session dans #⫻session")
@app_commands.describe(
    start_time="Heure de début (format HH:MM, ex: 14:30)",
    duration="Durée de la session"
)
@app_commands.choices(duration=[
    app_commands.Choice(name="10 minutes", value="10min"),
    app_commands.Choice(name="20 minutes", value="20min"),
    app_commands.Choice(name="30 minutes", value="30min"),
    app_commands.Choice(name="40 minutes", value="40min"),
    app_commands.Choice(name="50 minutes", value="50min"),
    app_commands.Choice(name="1 heure", value="1h"),
    app_commands.Choice(name="2 heures", value="2h"),
])
async def session(interaction: discord.Interaction, start_time: str, duration: app_commands.Choice[str]):
    admin_role = discord.utils.get(interaction.guild.roles, name="Administrateur")
    if admin_role not in interaction.user.roles:
        await interaction.response.send_message("⛔ Tu n'as pas la permission d'utiliser cette commande.", ephemeral=True)
        return

    channel = discord.utils.get(interaction.guild.text_channels, name="⫻session")
    if channel is None:
        await interaction.response.send_message("Le salon #⫻session n'existe pas.", ephemeral=True)
        return

    organizer_mention = interaction.user.mention
    session_msg = (f"📢 **Nouvelle session** 📢\n"
               f"Organisateur : {organizer_mention}\n"
               f"Heure de début : {start_time}\n"
               f"Durée : {duration.name}\n\n"
               f"@session")

    await channel.send(session_msg)
    await interaction.response.send_message(f"Session créée dans {channel.mention}.", ephemeral=True)


@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ Connecté en tant que {bot.user} - Commandes synchronisées")

bot.run(token)
