import discord
from discord import Embed, app_commands
from discord.ext import commands
from discord import ui
import settings

class BugReport(ui.Modal, title='Report a bug'):
    bug_title = ui.TextInput(label='Title', placeholder="What's your bug about?")
    bug = ui.TextInput(label="Problem", style=discord.TextStyle.paragraph, placeholder="What does the bug do?")
    steps = ui.TextInput(label='Steps', style=discord.TextStyle.paragraph, placeholder="How to reproduce it?")

    async def on_submit(self, interaction: discord.Interaction):
        embed = Embed(color=discord.Color.red(), title="New bug report", description=f"From {interaction.user.name}#{interaction.user.discriminator} (user ID {interaction.user.id})")
        embed.add_field(name="Title", value=self.bug_title, inline=False)
        embed.add_field(name="What does the bug do?", value=self.bug, inline=False)
        embed.add_field(name="How to reproduce it", value=self.steps, inline=False)
        channel = discord.utils.get(interaction.guild.channels, id=settings.report_channel)
        await channel.send(embed=embed)
        await interaction.response.send_message(f'Thanks for your help, {interaction.user.mention}!', ephemeral=True)

class HelpServer(commands.Cog):
    def __init__(self, bot:commands.Bot):
        self.bot = bot

    @app_commands.command(name="bug", description="Report a bug")
    async def bug_report(self, interaction:discord.Interaction):
        await interaction.response.send_modal(BugReport())

async def setup(bot:commands.Bot):
    await bot.add_cog(HelpServer(bot), guilds=[discord.Object(id=settings.SUPPORT_GUILD)])