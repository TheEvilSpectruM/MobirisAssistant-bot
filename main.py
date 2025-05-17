import discord
from discord.ext import commands
from discord import app_commands

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

class MessageModal(discord.ui.Modal, title="Envoyer un message avec bouton"):

    channel = discord.ui.TextInput(label="ID du salon (channel id)", placeholder="Ex: 123456789012345678")
    message_content = discord.ui.TextInput(label="Message à envoyer", style=discord.TextStyle.paragraph)

    def __init__(self, interaction):
        super().__init__()
        self.interaction = interaction

    async def on_submit(self, interaction: discord.Interaction):
        # Récupère le salon
        channel_id = int(self.channel.value)
        channel = self.interaction.guild.get_channel(channel_id)
        if channel is None:
            await interaction.response.send_message("Salon invalide.", ephemeral=True)
            return
        
        # Envoie le message avec bouton et compteur
        message = await channel.send(
            content=f"{self.message_content.value}\n\nNombre de personnes qui ont cliqué : **0**",
            view=ClickButton(message.id)
        )
        click_counters[message.id] = 0
        await interaction.response.send_message(f"Message envoyé dans {channel.mention} !", ephemeral=True)


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

click_counters = {}

@tree.command(name="sendmessage", description="Commande pour envoyer un message avec bouton")
async def sendmessage(interaction: discord.Interaction):
    staff_role = discord.utils.get(interaction.guild.roles, name="Staff")
    if staff_role not in interaction.user.roles:
        await interaction.response.send_message("⛔ Tu n'as pas la permission d'utiliser cette commande.", ephemeral=True)
        return
    modal = MessageModal(interaction)
    await interaction.response.send_modal(modal)

@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ Connecté en tant que {bot.user}")
