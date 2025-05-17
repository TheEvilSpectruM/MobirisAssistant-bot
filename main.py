import os
import discord
from discord.ext import commands
from discord import app_commands

# Récupération token depuis variable d'environnement
token = os.getenv("TOKEN")
print(f"Token récupéré : {token is not None}")  # True si ok

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# Stockage des compteurs de clics par message ID
click_counters = {}

# ---- Modal pour envoyer un message avec bouton personnalisable ----
class MessageModal(discord.ui.Modal, title="Envoyer un message avec bouton"):
    channel = discord.ui.TextInput(label="ID du salon (channel id)", placeholder="Ex: 123456789012345678")
    message_content = discord.ui.TextInput(label="Message à envoyer", style=discord.TextStyle.paragraph)
    button_text = discord.ui.TextInput(label="Texte du bouton", placeholder="Ex: Cliquer ici !", max_length=50)
    button_color = discord.ui.TextInput(label="Couleur du bouton (hexadécimal)", placeholder="#544de2", max_length=9)

    def __init__(self, interaction: discord.Interaction):
        super().__init__()
        self.interaction = interaction

    async def on_submit(self, interaction: discord.Interaction):
        # Récupérer salon par ID
        try:
            channel_id = int(self.channel.value.strip())
        except ValueError:
            await interaction.response.send_message("ID du salon invalide.", ephemeral=True)
            return

        channel = self.interaction.guild.get_channel(channel_id)
        if channel is None:
            await interaction.response.send_message("Salon introuvable dans ce serveur.", ephemeral=True)
            return

        # Valider couleur hex (avec #)
        color_str = self.button_color.value.strip()
        if not color_str.startswith("#") or len(color_str) not in {4, 7, 9}:
            await interaction.response.send_message("Couleur hexadécimale invalide (ex: #544de2).", ephemeral=True)
            return

        # Créer une vue avec bouton personnalisé
        view = ClickButton(
            message_id=0,  # temporaire, sera mis à jour après envoi
            label=self.button_text.value.strip() or "Clique ici",
            color=color_str
        )

        # Envoyer message avec bouton
        sent_message = await channel.send(
            content=f"{self.message_content.value}\n\nNombre de personnes qui ont cliqué : **0**",
            view=view
        )
        # Update message_id dans la vue pour suivre ce message
        view.message_id = sent_message.id

        # Init compteur clics
        click_counters[sent_message.id] = 0

        await interaction.response.send_message(f"Message envoyé dans {channel.mention} !", ephemeral=True)


# ---- Vue personnalisée avec bouton dynamique ----
class ClickButton(discord.ui.View):
    def __init__(self, message_id: int, label: str = "Clique ici", color: str = "#5865F2"):
        super().__init__(timeout=None)
        self.message_id = message_id
        self.button = discord.ui.Button(label=label, style=discord.ButtonStyle.primary)
        # Essayer de convertir hex couleur en discord.ButtonStyle color (limité à 4 styles)
        # Discord ne supporte pas la couleur hex dans ButtonStyle directement
        # Donc on laisse primary (bleu), secondary (gris), success (vert), danger (rouge)
        # Ou on peut choisir style selon la couleur hex, sinon primary par défaut
        # Ici on laisse primary toujours pour la simplicité
        self.add_item(self.button)
        self.button.callback = self.click_callback

    async def click_callback(self, interaction: discord.Interaction):
        # Incrémenter compteur clics
        click_counters[self.message_id] = click_counters.get(self.message_id, 0) + 1
        count = click_counters[self.message_id]
        message = interaction.message
        # Editer contenu avec nouveau compteur
        lines = message.content.splitlines()
        if lines:
            new_content = lines[0] + f"\n\nNombre de personnes qui ont cliqué : **{count}**"
            await message.edit(content=new_content, view=self)
        await interaction.response.send_message("Merci pour ton clic ! ✅", ephemeral=True)


# ---- Commande /sendmessage ----
@tree.command(name="sendmessage", description="Envoyer un message avec bouton personnalisé")
async def sendmessage(interaction: discord.Interaction):
    # Rôle autorisé : Administrateur (nom exact)
    admin_role = discord.utils.get(interaction.guild.roles, name="Administrateur")
    if admin_role not in interaction.user.roles:
        await interaction.response.send_message("⛔ Tu n'as pas la permission d'utiliser cette commande.", ephemeral=True)
        return
    modal = MessageModal(interaction)
    await interaction.response.send_modal(modal)


# ---- Commande /session ----
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
    # Vérification rôle Administrateur
    admin_role = discord.utils.get(interaction.guild.roles, name="Administrateur")
    if admin_role not in interaction.user.roles:
        await interaction.response.send_message("⛔ Tu n'as pas la permission d'utiliser cette commande.", ephemeral=True)
        return

    # Trouver salon #⫻session (exactement ce nom)
    channel = discord.utils.get(interaction.guild.text_channels, name="⫻session")
    if channel is None:
        await interaction.response.send_message("Le salon #⫻session n'existe pas sur ce serveur.", ephemeral=True)
        return

    # Construire le message avec mention de l'organisateur
    organizer_mention = interaction.user.mention
    session_msg = (f"📢 **Nouvelle session** 📢\n"
                   f"Organisateur : {organizer_mention}\n"
                   f"Heure de début : {start_time}\n"
                   f"Durée : {duration.name}")

    # Envoyer message dans #⫻session
    await channel.send(session_msg)

    # Confirmer à l'utilisateur
    await interaction.response.send_message(f"Session créée dans {channel.mention}.", ephemeral=True)


# ---- Event on_ready ----
@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ Connecté en tant que {bot.user} - Commandes synchronisées")


# ---- Lancer le bot ----
bot.run(token)
