from urllib.request import urlopen
import mysql.connector
import discord
import json
from discord.ext import commands
from discord import app_commands
from discord.app_commands import Choice
from discord.ui import Button, View
import settings

class ServerConfig(commands.Cog):
    def __init__(self, bot:commands.Bot):
        self.bot = bot
        with open(f'{settings.PATH}cogs', 'r') as f:
            self.language = json.load(f)

    def db_connect(self):
        self.db = mysql.connector.connect(
            host=settings.USER_DATA_HOST,
            port=settings.USER_DATA_PORT,
            user=settings.USER_DATA_USERNAME,
            password=settings.USER_DATA_PASSWORD,
            database=settings.USER_DATA_DATABASE
        )

    def leveldb_connect(self):
        self.leveldb = mysql.connector.connect(
            host=settings.LEVELS_DATA_HOST,
            port=settings.LEVELS_DATA_PORT,
            user=settings.LEVELS_DATA_USERNAME,
            password=settings.LEVELS_DATA_PASSWORD,
            database=settings.LEVELS_DATA_DATABASE
        )
    
    def clean_request(self, value):
        value = str(value).replace("(", "")
        value = str(value).replace(")", "")
        value = str(value).replace(",", "")
        value = str(value).replace("'", "")
        return value

    @commands.Cog.listener()
    async def on_guild_join(self, guild:discord.Guild):
        self.db_connect()
        cursor = self.db.cursor()
        cursor.execute("INSERT INTO server_settings(server_id, language, exp_1, exp_2, exp_3, exp_4, exp_5, lvl_1, lvl_2, lvl_3, lvl_4, lvl_5, exp_per_message) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (guild.id, "notset", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0"))
        self.db.commit()
        self.leveldb_connect()
        level_cursor = self.leveldb.cursor()
        level_cursor.execute(f"CREATE TABLE IF NOT EXISTS {guild.id}_server (user_id BIGINT(20), lvl INT(11), exp INT(11))")
        user = guild.owner
        await user.send(":flag_us: Thank you for inviting me on the server!\nTo start the configuration of the bot, do /help moderation on your server\n\n:flag_fr: Merci de m'avoir invité sur le serveur !\nPour commencer la configuration du bot, faites /help moderation sur votre serveur")

    @app_commands.command(name="language", description="Change server language")
    @app_commands.guild_only()
    async def language(self, interaction:discord.Interaction):
        if interaction.user.guild_permissions.manage_guild:
            button1 = Button(label="Français", style=discord.ButtonStyle.primary, emoji="🇫🇷")
            button2 = Button(label="English (US)", style=discord.ButtonStyle.primary, emoji="🇺🇸")
            async def french_callback(interaction:discord.Interaction):
                self.db_connect()
                cursor = self.db.cursor()
                cursor.execute("UPDATE server_settings SET language = %s WHERE server_id = %s", ("fr", interaction.message.guild.id))
                self.db.commit()
                await interaction.response.edit_message(content=self.language['fr']['server_language_changed'], view=None)
            async def english_callback(interaction:discord.Interaction):
                interaction_message = await get_interaction()
                if interaction_message.user.id == interaction.user.id:
                    self.db_connect()
                    cursor = self.db.cursor()
                    cursor.execute("UPDATE server_settings SET language = %s WHERE server_id = %s", ("us", interaction.message.guild.id))
                    self.db.commit()
                    await interaction.response.edit_message(content=self.language['us']['server_language_changed'], view=None)
                else:
                    pass
            async def get_interaction():
                return interaction
            button1.callback = french_callback
            button2.callback = english_callback
            view = View()
            view.add_item(button1)
            view.add_item(button2)
            await interaction.response.send_message(f":flag_fr: Choisissez votre langue\n:flag_us: Select your language", view=view)
        else:
            self.db_connect()
            cursor = self.db.cursor()
            cursor.execute("SELECT language FROM server_settings WHERE server_id = %s", (interaction.message.guild.id,))
            language = cursor.fetchone()
            language = self.clean_request(language)
            if language == "notset":
                language = "us"
            await interaction.response.send_message(self.language[language]['doesnt_have_perms'])

    @commands.hybrid_group(name="settings")
    @app_commands.guild_only()
    async def settings_base(self, interaction:discord.Interaction):
        pass

    @settings_base.command(name="view", description="View actuals EXP settings")
    @app_commands.guild_only()
    async def settings_view(self, ctx:commands.Context):
        if ctx.author.guild_permissions.manage_guild:
            self.db_connect()
            cursor = self.db.cursor()
            cursor.execute("SELECT language FROM server_settings WHERE server_id = %s", (ctx.guild.id,))
            language_ = cursor.fetchone()
            language = self.clean_request(str(language_))
            if language == "notset":
                language = "us"
            cursor.execute("SELECT * FROM server_settings WHERE server_id = %s", (ctx.guild.id,))
            exp = cursor.fetchall()
            await ctx.send(f"{self.language[language]['exp_view']} 1, 2, 3, 4 {self.language[language]['and']} 5:\n{exp[0][2]} EXP {self.language[language]['for_the_role']} <@&{exp[0][7]}>\n{exp[0][3]} EXP {self.language[language]['for_the_role']} <@&{exp[0][8]}>\n{exp[0][4]} EXP {self.language[language]['for_the_role']} <@&{exp[0][9]}>\n{exp[0][5]} EXP {self.language[language]['for_the_role']} <@&{exp[0][10]}>\n{exp[0][6]} EXP {self.language[language]['for_the_role']} <@&{exp[0][11]}>\n{self.language[language]['exp_rate']}: {exp[0][12]}")
        else:
            self.db_connect()
            cursor = self.db.cursor()
            cursor.execute("SELECT language FROM server_settings WHERE server_id = %s", (ctx.guild.id,))
            language = cursor.fetchone()
            language = self.clean_request(language)
            if language == "notset":
                language = "us"
            await ctx.send(self.language[language]['doesnt_have_perms'])

    @settings_base.command(name="change", description="Change server settings")
    @app_commands.choices(setting=[
    Choice(name='role', value=1),
    Choice(name='exp', value=2)
    ])
    @app_commands.describe(setting="The setting to change", level="For which level", exp="EXP required for this level", role="The role to set for this level")
    @app_commands.guild_only()
    async def settings_change(self, ctx:commands.Context, setting:int, level:int, exp:int=None, role:discord.Role=None):
        if ctx.author.guild_permissions.manage_guild:
            self.db_connect()
            cursor = self.db.cursor()
            self.db_connect()
            cursor = self.db.cursor()
            cursor.execute("SELECT language FROM server_settings WHERE server_id = %s", (ctx.guild.id,))
            language = cursor.fetchone()
            language = self.clean_request(language)
            if language == "notset":
                language = "us"
            if setting == 1:
                if role != None:
                    cursor.execute(f"UPDATE server_settings SET lvl_{level} = %s WHERE server_id = %s", (role.id, ctx.guild.id))
                else:
                    await ctx.send(f"{self.language[language]['field_missing']}: `role`")
                    return None
            else:
                if exp != None:
                    cursor.execute(f"UPDATE server_settings SET exp_{level} = %s WHERE server_id = %s", (exp, ctx.guild.id))
                else:
                    await ctx.send(f"{self.language[language]['field_missing']}: `exp`")
                    return None

            self.db.commit()
            await ctx.send(self.language[language]['setting_changed'])
        else:
            self.db_connect()
            cursor = self.db.cursor()
            cursor.execute("SELECT language FROM server_settings WHERE server_id = %s", (ctx.guild.id,))
            language = cursor.fetchone()
            language = self.clean_request(language)
            if language == "notset":
                language = "us"
            await ctx.send(self.language[language]['doesnt_have_perms'])
        
    @settings_base.command(name="rate", description="Change earned EXP per message")
    @app_commands.describe(rate="The EXP earned by message")
    @app_commands.guild_only()
    async def settings_rate(self, ctx:commands.Context, rate:int):
        if ctx.author.guild_permissions.manage_guild:
            self.db_connect()
            cursor = self.db.cursor()
            cursor.execute(f"UPDATE server_settings SET exp_per_message = %s WHERE server_id = %s", (rate, ctx.guild.id))
            self.db.commit()
            cursor.execute("SELECT language FROM server_settings WHERE server_id = %s", (ctx.guild.id,))
            language = cursor.fetchone()
            language = self.clean_request(language)
            if language == "notset":
                language = "us"
            await ctx.send(self.language[language]['exp_rate_changed'])
        else:
            self.db_connect()
            cursor = self.db.cursor()
            cursor.execute("SELECT language FROM server_settings WHERE server_id = %s", (ctx.guild.id,))
            language = cursor.fetchone()
            language = self.clean_request(language)
            if language == "notset":
                language = "us"
            await ctx.send(self.language[language]['doesnt_have_perms'])

    @commands.hybrid_group(name="help", guild=True)
    @app_commands.guild_only()
    async def help_base(self, interaction:discord.Interaction):
        pass

    @help_base.command(name="user", description="Users commands")
    @app_commands.guild_only()
    async def help_user(self, ctx:commands.Context):
        self.db_connect()
        cursor = self.db.cursor()
        cursor.execute("SELECT language FROM server_settings WHERE server_id = %s", (ctx.author.guild.id,))
        language = cursor.fetchone()
        language = self.clean_request(language)
        if language == "notset":
            language = "us"
        await ctx.send(self.language[language]['help_user'])

    @help_base.command(name="moderation", description="A little guide on how to start with the bot")
    @app_commands.guild_only()
    async def help_moderation(self, ctx:commands.Context):
        if ctx.author.guild_permissions.manage_guild:
            self.db_connect()
            cursor = self.db.cursor()
            cursor.execute("SELECT language FROM server_settings WHERE server_id = %s", (ctx.author.guild.id,))
            language = cursor.fetchone()
            language = self.clean_request(language)
            if language == "notset":
                language = "us"
                await ctx.send(":flag_fr: Premirement, changez la langue du serveur avec `/language`\nApres cela, creez 5 nouveaux roles qui vont etre utilises pour le systeme de niveau ou utilisez des roles existants (mettez le role du bot au dessus de ces roles pour la hierarchie)\n*Utilisez `/settings change` avec les arguments suivants:\n`setting`: exp ou role, utilisez exp pour changer l'EXP requis pour un des niveau, role pour changer le role gagne pour un des niveaux\n`level`: pour le niveau suivant\n`exp` (a utiliser avec le parametre exp): le montant d'EXP pour ce niveau\n`role` (a utiliser avec le parametre role): le role donne quand un utilisateur atteint ce niveau\nExemple: `/settings change setting:role level:1 role:@Level 1`         Cette commande change le role donne au niveau 1 au role @Level 1\n                  `/settings change setting:exp level:1 exp:3000`         Ce role change l'EXP requis pour le niveau 1\n`/settings rate`: change l'EXP gagne pour un message\n`/settings view`: voir les parametres actuels\n\nC'est tout pour les commandes, bon usage !\n**Note :** pour utiliser ces commandes, vous avez besoin de la permission **Gerer le serveur**")
            await ctx.send(self.language[language]['help_moderation'])

async def setup(bot):
    await bot.add_cog(ServerConfig(bot))