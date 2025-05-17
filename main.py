import discord
from discord.ext import commands
from discord import app_commands

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree  # Pour les slash commands

# Stocke les compteurs dans un dict (mémoire temporaire)
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
        await message.edit(content=f"{message.content.splitlines()[0]}\n\nNombre de personnes qui ont cliqué : **{count}**", view=self)
        await interaction.response.send_message("Merci pour ton clic ! ✅", ephemeral=True)

# Slash command réservée aux membres ayant un rôle "Staff"
@tree.command(name="sendmessage", description="Envoyer un message avec bouton interactif")
@app_commands.describe(channel="Salon où envoyer le message", content="Contenu du message")
async def sendmessage(interaction: discord.Interaction, channel: discord.TextChannel, content: str):
    staff_role = discord.utils.get(interaction.guild.roles, name="Staff")
    if staff_role not in interaction.user.roles:
        await interaction.response.send_message("⛔ Tu n'as pas la permission d'utiliser cette commande.", ephemeral=True)
        return

    # Envoie le message avec bouton
    message = await channel.send(
        content=f"{content}\n\nNombre de personnes qui ont cliqué : **0**",
        view=ClickButton(message_id=interaction.id)
    )
    click_counters[interaction.id] = 0
    await interaction.response.send_message(f"✅ Message envoyé dans {channel.mention} !", ephemeral=True)

@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ Connecté en tant que {bot.user}")

