from urllib.request import urlopen
import discord
from discord.ext import commands
from discord import app_commands
import json
import mysql.connector
import settings

class ServerModeration(commands.Cog):
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

    @app_commands.command(name="give", description="Give EXP to an user")
    @app_commands.guild_only()
    async def give_exp(self, interaction:discord.Interaction, user:discord.Member, exp:int):
        self.db_connect()
        cursor = self.db.cursor()
        cursor.execute("SELECT language FROM server_settings WHERE server_id = %s", (interaction.guild.id,))
        language = cursor.fetchone()
        language = self.clean_request(language)
        if language == "notset":
            language = "us"

        if interaction.user.guild_permissions.manage_guild:
            exp = str(exp).replace("-", "")
            exp = int(exp)
            self.leveldb_connect()
            cursor = self.leveldb.cursor()
            try:
                cursor.execute(f"SELECT exp FROM {interaction.guild.id}_server WHERE user_id = %s", (user.id,))
                user_exp = cursor.fetchone()
                user_exp = self.clean_request(user_exp)
                user_exp = int(user_exp)
            except:
                try:
                    self.leveldb_connect()
                    user_cursor = self.leveldb.cursor()
                    user_cursor.execute(f"INSERT INTO {interaction.guild.id}_server VALUES(%s, %s, %s)", (user.id, 0, exp))
                    self.leveldb.commit()
                    await interaction.response.send_message(f"{user.mention} {self.language[language]['exp_granted']} {exp} EXP")
                    return None
                except:
                    await interaction.response.send_message(self.language[language]['not_configured'])
                    return None
            cursor.execute(f"UPDATE {interaction.guild.id}_server SET exp = %s WHERE user_id = %s", (user_exp+exp, user.id))
            self.leveldb.commit()
            await interaction.response.send_message(f"{user.mention} {self.language[language]['exp_granted']} {exp} EXP")

        else:
            await interaction.response.send_message(self.language[language]['doesnt_have_perms'])

    @app_commands.command(name="remove", description="Remove EXP from an user")
    @app_commands.guild_only()
    async def remove_exp(self, interaction:discord.Interaction, user:discord.Member, exp:int):
        self.db_connect()
        cursor = self.db.cursor()
        cursor.execute("SELECT language FROM server_settings WHERE server_id = %s", (interaction.guild.id,))
        language = cursor.fetchone()
        language = self.clean_request(language)
        if language == "notset":
            language = "us"

        if interaction.user.guild_permissions.manage_guild:
            self.leveldb_connect()
            cursor = self.leveldb.cursor()
            try:
                cursor.execute(f"SELECT exp FROM {interaction.guild.id}_server WHERE user_id = %s", (user.id,))
                user_exp = cursor.fetchone()
                user_exp = self.clean_request(user_exp)
                user_exp = int(user_exp)
            except:
                await interaction.response.send_message(self.language[language]['not_configured'])
                return None
            if user_exp == 0:
                await interaction.response.send_message(self.language[language]['not_negative'])
            else:
                cursor.execute(f"UPDATE {interaction.guild.id}_server SET exp = %s WHERE user_id = %s", (user_exp-exp, user.id))
                self.leveldb.commit()
                await interaction.response.send_message(f"{user.mention} {self.language[language]['exp_removed']} {exp} EXP")

        else:
            await interaction.response.send_message(self.language[language]['doesnt_have_perms'])


async def setup(bot:commands.Bot):
    await bot.add_cog(ServerModeration(bot))