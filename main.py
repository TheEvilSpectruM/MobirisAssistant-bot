import os
import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Modal, TextInput, View, Button

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# === CONFIGURATION ===
PSEUDO_CHANNEL_ID = 1373624458862002250  # Remplace par l'ID du salon #pseudo-roblox
SESSION_CHANNEL_ID = 1373221920685948969  # Remplace par l'ID du salon #⫻session
TICKETS_CHANNEL_ID = 1356145309574758481  # Remplace par l'ID du salon #tickets
THE_EVIL_SPECTRUM_ID = 1075319939306639412  # Ton ID Discord (theevilspectrum)

# === Données pour la liste des pseudos Roblox ===
roblox_links = {}
roblox_embed_message = None

# --- Fonction pour mettre à jour l'embed persistant des pseudos ---
async def update_roblox_embed(client: discord.Client):
    global roblox_embed_message
    channel = client.get_channel(PSEUDO_CHANNEL_ID)
    if not channel:
        return

    embed = discord.Embed(
        title="📋 Liste des pseudos Roblox enregistrés",
        color=discord.Color.blue()
    )
    if roblox_links:
        for user_id, pseudo in roblox_links.items():
            try:
                user = await client.fetch_user(user_id)
                embed.add_field(name=user.name, value=pseudo, inline=False)
            except:
                continue
    else:
        embed.description = "Aucune donnée enregistrée."

    if roblox_embed_message:
        try:
            await roblox_embed_message.edit(embed=embed)
        except discord.NotFound:
            roblox_embed_message = await channel.send(embed=embed)
    else:
        roblox_embed_message = await channel.send(embed=embed)

# === Commande /pseudo-roblox avec validation manuelle ===
class PseudoVerificationView(View):
    def __init__(self, user: discord.User, pseudo: str):
        super().__init__(timeout=None)
        self.user = user
        self.pseudo = pseudo

    @discord.ui.button(label="N'existe pas", style=discord.ButtonStyle.danger)
    async def does_not_exist(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message(
            f"❌ Le pseudo **{self.pseudo}** n'existe pas. Ping de {self.user.mention}.", ephemeral=False)
        await self.user.send(f"⛔ Le pseudo que tu as soumis (**{self.pseudo}**) n'existe pas selon la vérification manuelle.")
        self.stop()

    @discord.ui.button(label="Existe", style=discord.ButtonStyle.success)
    async def exists(self, interaction: discord.Interaction, button: Button):
        roblox_links[self.user.id] = self.pseudo
        await update_roblox_embed(interaction.client)
        await interaction.response.send_message(
            f"✅ Ajouté: {self.user.name} → {self.pseudo}", ephemeral=False)
        await self.user.send(f"🎉 Ton pseudo Roblox **{self.pseudo}** a été validé et ajouté à la liste.")
        self.stop()

@tree.command(name="pseudo-roblox", description="Lier ton pseudo Roblox")
@app_commands.describe(pseudo="Ton pseudo Roblox")
async def pseudo_roblox(interaction: discord.Interaction, pseudo: str):
    await interaction.response.send_message("🔍 Ton pseudo est en cours de vérification...", ephemeral=True)
    admin_user = await interaction.client.fetch_user(THE_EVIL_SPECTRUM_ID)
    await admin_user.send(
        content=f"Veuillez vérifier si ce pseudo existe: **{pseudo}**",
        view=PseudoVerificationView(interaction.user, pseudo)
    )

# === Commande /sendmessage avec bouton personnalisable ===
class ClickButton(View):
    def __init__(self, message_id):
        super().__init__(timeout=None)
        self.message_id = message_id
        self.count = 0

    @discord.ui.button(label="📥 Je clique !", style=discord.ButtonStyle.primary)
    async def click(self, interaction: discord.Interaction, button: Button):
        self.count += 1
        content = interaction.message.content.split("\n\n")[0]
        await interaction.message.edit(content=f"{content}\n\nNombre de personnes qui ont cliqué : **{self.count}**", view=self)
        await interaction.response.send_message("Merci pour ton clic ! ✅", ephemeral=True)

class MessageModal(Modal, title="Envoyer un message avec bouton"):
    channel = TextInput(label="ID du salon", placeholder="123456789012345678")
    message_content = TextInput(label="Message", style=discord.TextStyle.paragraph)
    button_label = TextInput(label="Texte du bouton", default="📥 Je clique !")
    button_color = TextInput(label="Couleur du bouton (primary/danger/success)", default="primary")

    def __init__(self, interaction):
        super().__init__()
        self.interaction = interaction

    async def on_submit(self, interaction: discord.Interaction):
        try:
            channel_id = int(self.channel.value)
        except ValueError:
            await interaction.response.send_message("ID de salon invalide.", ephemeral=True)
            return

        channel = self.interaction.guild.get_channel(channel_id)
        if not channel:
            await interaction.response.send_message("Salon invalide ou introuvable.", ephemeral=True)
            return

        style_map = {
            "primary": discord.ButtonStyle.primary,
            "danger": discord.ButtonStyle.danger,
            "success": discord.ButtonStyle.success
        }
        style = style_map.get(self.button_color.value.lower(), discord.ButtonStyle.primary)

        view = ClickButton(message_id=0)
        # Modifie le texte et style du bouton
        view.children[0].label = self.button_label.value
        view.children[0].style = style

        message = await channel.send(content=f"{self.message_content.value}\n\nNombre de personnes qui ont cliqué : **0**", view=view)
        view.message_id = message.id

        await interaction.response.send_message(f"Message envoyé dans {channel.mention}", ephemeral=True)

@tree.command(name="sendmessage", description="Envoyer un message avec bouton")
async def sendmessage(interaction: discord.Interaction):
    if not any(role.name == "Administrateur" for role in interaction.user.roles):
        await interaction.response.send_message("⛔ Tu n'as pas la permission.", ephemeral=True)
        return
    await interaction.response.send_modal(MessageModal(interaction))

# === Commande /session ===
class SessionModal(Modal, title="Créer une session"):
    heure = TextInput(label="Heure de début (HH:MM)", placeholder="15:30")
    duree = TextInput(label="Durée (ex: 10min, 1h)", placeholder="30min")

    async def on_submit(self, interaction: discord.Interaction):
        channel = interaction.guild.get_channel(SESSION_CHANNEL_ID)
        if not channel:
            await interaction.response.send_message("Salon de session introuvable.", ephemeral=True)
            return

        embed = discord.Embed(
            title="📢 Nouvelle session",
            description=f"@ping session\n**Heure de début** : {self.heure.value}\n**Durée** : {self.duree.value}\n**Organisateur** : {interaction.user.mention}",
            color=discord.Color.green()
        )
        await channel.send(embed=embed)
        await interaction.response.send_message("✅ Session créée avec succès !", ephemeral=True)

@tree.command(name="session", description="Créer une session dans #⫻session")
async def session(interaction: discord.Interaction):
    await interaction.response.send_modal(SessionModal())

# === Système de tickets ===
class TicketModal(Modal, title="Créer un ticket"):
    raison = TextInput(label="Raison du ticket", placeholder="Choisis une raison", max_length=100)
    message = TextInput(label="Décris ton problème", style=discord.TextStyle.paragraph)

    def __init__(self, user):
        super().__init__()
        self.user = user

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            self.user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            guild.get_member(THE_EVIL_SPECTRUM_ID): discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }
        channel = await guild.create_text_channel(name=f"{self.user.name}-ticket", overwrites=overwrites)

        embed = discord.Embed(title="🎫 Ticket Ouvert", description=self.message.value, color=discord.Color.blurple())
        await channel.send(content=f"Ticket pour {self.user.mention} — <@{THE_EVIL_SPECTRUM_ID}>", embed=embed, view=TicketControlView(channel))
        await interaction.response.send_message("✅ Ticket créé !", ephemeral=True)

class TicketControlView(View):
    def __init__(self, channel):
        super().__init__(timeout=None)
        self.channel = channel

    @discord.ui.button(label="Fermer le ticket", style=discord.ButtonStyle.danger)
    async def close(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != THE_EVIL_SPECTRUM_ID:
            await interaction.response.send_message("⛔ Seul le staff peut fermer ce ticket.", ephemeral=True)
            return
        await interaction.response.send_message("🔒 Ticket fermé.", ephemeral=True)
        await self.channel.delete()

@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ Connecté en tant que {bot.user}")

    # Récupérer le message embed existant dans #pseudo-roblox s'il existe
    global roblox_embed_message
    channel = bot.get_channel(PSEUDO_CHANNEL_ID)
    if channel:
        async for message in channel.history(limit=50):
            if message.author == bot.user and message.embeds:
                roblox_embed_message = message
                break

    # Envoyer le message bouton pour ouvrir un ticket dans #tickets
    ticket_channel = bot.get_channel(TICKETS_CHANNEL_ID)
    if ticket_channel:
        embed = discord.Embed(title="📩 Ouvrir un ticket", description="Clique ci-dessous pour ouvrir un ticket.", color=discord.Color.orange())
        view = View()

        async def callback(interaction: discord.Interaction):
            await interaction.response.send_modal(TicketModal(interaction.user))

        button = Button(label="Créer un ticket", style=discord.ButtonStyle.primary)
        button.callback = callback
        view.add_item(button)
        await ticket_channel.send(embed=embed, view=view)

token = os.getenv("TOKEN")
bot.run(token)
