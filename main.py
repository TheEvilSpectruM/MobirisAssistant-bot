import os
import discord
from discord.ext import commands
from discord import app_commands

intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # pour accéder aux membres

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# Dictionnaire pour stocker les pseudos Roblox validés
roblox_links = {}
roblox_embed_message = None
PSEUDO_CHANNEL_ID = 1373624458862002250  # Remplace avec l'ID de #pseudo-roblox
THE_EVIL_SPECTRUM_ID = 1075319939306639412  # Ton ID d'utilisateur (theevilspectrum)

class PseudoVerificationView(discord.ui.View):
    def __init__(self, user: discord.User, pseudo: str):
        super().__init__(timeout=None)
        self.user = user
        self.pseudo = pseudo

    @discord.ui.button(label="N'existe pas", style=discord.ButtonStyle.danger)
    async def does_not_exist(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(f"❌ Le pseudo **{self.pseudo}** n'existe pas. Ping de {self.user.mention}.", ephemeral=False)
        await self.user.send(f"⛔ Le pseudo que tu as soumis (**{self.pseudo}**) n'existe pas selon la vérification manuelle.")
        self.stop()

    @discord.ui.button(label="Existe", style=discord.ButtonStyle.success)
    async def exists(self, interaction: discord.Interaction, button: discord.ui.Button):
        roblox_links[self.user.id] = self.pseudo
        await update_roblox_embed(interaction.client)
        await interaction.response.send_message(f"✅ Ajouté: {self.user.name} → {self.pseudo}", ephemeral=False)
        await self.user.send(f"🎉 Ton pseudo Roblox **{self.pseudo}** a été validé et ajouté à la liste.")
        self.stop()

async def update_roblox_embed(client: discord.Client):
    global roblox_embed_message

    channel = client.get_channel(PSEUDO_CHANNEL_ID)
    if channel is None:
        print("Salon #pseudo-roblox introuvable")
        return

    embed = discord.Embed(
        title="📋 Liste des pseudos Roblox enregistrés",
        description="Voici les correspondances entre Discord et Roblox",
        color=discord.Color.blue()
    )

    if roblox_links:
        for uid, pseudo in roblox_links.items():
            user = await client.fetch_user(uid)
            embed.add_field(name=user.name, value=pseudo, inline=False)
    else:
        embed.description = "Aucune donnée enregistrée pour le moment."

    if roblox_embed_message:
        try:
            await roblox_embed_message.edit(embed=embed)
        except discord.NotFound:
            roblox_embed_message = await channel.send(embed=embed)
    else:
        roblox_embed_message = await channel.send(embed=embed)

@tree.command(name="pseudo-roblox", description="Lier ton pseudo Roblox")
@app_commands.describe(pseudo="Ton pseudo Roblox")
async def pseudo_roblox(interaction: discord.Interaction, pseudo: str):
    await interaction.response.send_message("🔍 Ton pseudo est en cours de vérification...", ephemeral=True)

    # Envoi du message privé à l'admin
    admin_user = await interaction.client.fetch_user(THE_EVIL_SPECTRUM_ID)
    view = PseudoVerificationView(interaction.user, pseudo)
    await admin_user.send(
        content=f"Veuillez vérifier si ce pseudo existe: **{pseudo}**",
        view=view
    )

@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ Connecté en tant que {bot.user}")
    # On essaye de récupérer le dernier embed si possible
    channel = bot.get_channel(PSEUDO_CHANNEL_ID)
    if channel:
        async for message in channel.history(limit=50):
            if message.author == bot.user and message.embeds:
                global roblox_embed_message
                roblox_embed_message = message
                break

# Ton token à la fin
token = os.getenv("TOKEN")
bot.run(token)
