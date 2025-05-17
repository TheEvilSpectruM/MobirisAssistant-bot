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

# ----- Classes pour /sendmessage -----

class MessageModal(discord.ui.Modal, title="Envoyer un message avec bouton"):
    channel = discord.ui.TextInput(label="ID du salon (channel id)", placeholder="Ex: 123456789012345678")
    message_content = discord.ui.TextInput(label="Message à envoyer", style=discord.TextStyle.paragraph)
    button_label = discord.ui.TextInput(label="Texte du bouton", default="📥 Je clique !")
    button_color = discord.ui.TextInput(label="Couleur du bouton (#RRGGBB ou name)", default="primary")

    def __init__(self, interaction):
        super().__init__()
        self.interaction = interaction

    async def on_submit(self, interaction: discord.Interaction):
        try:
            channel_id = int(self.channel.value)
            channel = self.interaction.guild.get_channel(channel_id)
            if channel is None:
                await interaction.response.send_message("Salon invalide.", ephemeral=True)
                return
        except ValueError:
            await interaction.response.send_message("ID de salon invalide.", ephemeral=True)
            return

        # Couleurs possibles pour ButtonStyle
        color_map = {
            "primary": discord.ButtonStyle.primary,
            "secondary": discord.ButtonStyle.secondary,
            "success": discord.ButtonStyle.success,
            "danger": discord.ButtonStyle.danger,
        }

        # Essayer d'analyser la couleur
        color_input = self.button_color.value.strip().lower()
        if color_input.startswith("#") and len(color_input) == 7:
            # Discord.py ne supporte pas les couleurs hex direct dans ButtonStyle, fallback sur primary
            button_style = discord.ButtonStyle.primary
        else:
            button_style = color_map.get(color_input, discord.ButtonStyle.primary)

        class ClickButton(discord.ui.View):
            def __init__(self, message_id):
                super().__init__(timeout=None)
                self.message_id = message_id

            @discord.ui.button(label=self.button_label.value, style=button_style)
            async def click(self, interaction: discord.Interaction, button: discord.ui.Button):
                message = interaction.message
                click_counters[self.message_id] = click_counters.get(self.message_id, 0) + 1
                count = click_counters[self.message_id]
                await message.edit(content=f"{message.content.splitlines()[0]}\n\nNombre de personnes qui ont cliqué : **{count}**", view=self)
                await interaction.response.send_message("Merci pour ton clic ! ✅", ephemeral=True)

        # Envoyer le message avec le bouton
        message = await channel.send(
            content=f"{self.message_content.value}\n\nNombre de personnes qui ont cliqué : **0**",
            view=ClickButton(0)  # message.id pas encore disponible
        )
        # Mettre à jour le message_id du bouton
        message.view.message_id = message.id
        click_counters[message.id] = 0

        await interaction.response.send_message(f"Message envoyé dans {channel.mention} !", ephemeral=True)

@tree.command(name="sendmessage", description="Commande pour envoyer un message avec bouton personnalisé")
async def sendmessage(interaction: discord.Interaction):
    admin_role = discord.utils.get(interaction.guild.roles, name="Administrateur")
    if admin_role not in interaction.user.roles:
        await interaction.response.send_message("⛔ Tu n'as pas la permission d'utiliser cette commande.", ephemeral=True)
        return
    modal = MessageModal(interaction)
    await interaction.response.send_modal(modal)


# ----- Commande /session -----

durations_choices = [
    app_commands.Choice(name="10 minutes", value="10min"),
    app_commands.Choice(name="20 minutes", value="20min"),
    app_commands.Choice(name="30 minutes", value="30min"),
    app_commands.Choice(name="40 minutes", value="40min"),
    app_commands.Choice(name="50 minutes", value="50min"),
    app_commands.Choice(name="1 heure", value="1h"),
    app_commands.Choice(name="2 heures", value="2h"),
]

@tree.command(name="session", description="Créer une session dans #⫻session")
@app_commands.describe(
    start_time="Heure de début (format HH:MM, ex: 14:30)",
    duration="Durée de la session"
)
@app_commands.choices(duration=durations_choices)
async def session(interaction: discord.Interaction, start_time: str, duration: app_commands.Choice[str]):
    # Vérifier rôle administrateur
    admin_role = discord.utils.get(interaction.guild.roles, name="Administrateur")
    if admin_role not in interaction.user.roles:
        await interaction.response.send_message("⛔ Tu n'as pas la permission d'utiliser cette commande.", ephemeral=True)
        return

    # Valider format HH:MM
    try:
        h, m = start_time.split(":")
        h = int(h)
        m = int(m)
        if not (0 <= h <= 23 and 0 <= m <= 59):
            raise ValueError
    except:
        await interaction.response.send_message("❌ Format d'heure invalide. Utilise HH:MM, ex: 14:30", ephemeral=True)
        return

    # Trouver le salon #⫻session
    session_channel = discord.utils.get(interaction.guild.text_channels, name="⫻session")
    if session_channel is None:
        await interaction.response.send_message("❌ Salon #⫻session introuvable.", ephemeral=True)
        return

    organizer_mention = interaction.user.mention
    message = (
        f"📢 **Session organisée par {organizer_mention}**\n"
        f"⏰ Début : {start_time}\n"
        f"⏳ Durée : {duration.name}\n"
        f"Merci de bien vouloir vous organiser en conséquence !"
    )

    await session_channel.send(message)
    await interaction.response.send_message(f"Session annoncée dans {session_channel.mention} !", ephemeral=True)


@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ Connecté en tant que {bot.user}")


bot.run(token)
