import json
import discord
from discord.ext import commands
from discord import Embed, app_commands
import mysql.connector
import discord.utils
import settings

class Level(commands.Cog):
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
    async def on_message(self, message:discord.Message):
        if not isinstance(message.channel, discord.channel.DMChannel):
            await self.add_experience(message)

    async def add_experience(self, data:discord.Message):
        if not data.author.bot:
            self.db_connect()
            self.leveldb_connect()
            user_cursor = self.leveldb.cursor()
            guild_cursor = self.db.cursor()
            try:
                user_cursor.execute(f"SELECT COUNT(*) FROM {data.guild.id}_server WHERE user_id = %s", (data.author.id,))
                user = user_cursor.fetchone()
                user = self.clean_request(user)
                user = int(user)
            except:
                user_cursor.execute(f"CREATE TABLE IF NOT EXISTS {data.guild.id}_server (user_id BIGINT(20), lvl INT(11), exp INT(11))")
                guild_cursor.execute("INSERT INTO server_settings(server_id, language, exp_1, exp_2, exp_3, exp_4, exp_5, lvl_1, lvl_2, lvl_3, lvl_4, lvl_5, exp_per_message) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (data.guild.id, "notset", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0"))
                self.db.commit()
                return None
            guild_cursor.execute(f"SELECT exp_per_message FROM server_settings WHERE server_id = %s", (data.guild.id,))
            rate = guild_cursor.fetchone()
            rate = self.clean_request(rate)
            rate = int(rate)
            if user != 0:
                user_cursor.execute(f"SELECT * FROM {data.guild.id}_server WHERE user_id = %s", (data.author.id,))
                user_data = user_cursor.fetchall()
                level = int(user_data[0][1])
                exp = int(user_data[0][2] + rate)
                guild_cursor = self.db.cursor()
                try:
                    guild_cursor.execute(f"SELECT exp_{level+1} FROM server_settings WHERE server_id = %s", (data.guild.id,))
                    server_data = guild_cursor.fetchone()
                    server_data = int(self.clean_request(server_data))
                except:
                    server_data = 0
                    level = 5
                if exp >= server_data and level < 5:
                    user_cursor.execute(f"UPDATE {data.guild.id}_server SET lvl = %s, exp = %s WHERE user_id = %s", (level+1, exp, data.author.id))
                    self.leveldb.commit()
                    guild_cursor.execute(f"SELECT lvl_{level+1} FROM server_settings WHERE server_id = %s", (data.guild.id,))
                    role_id = guild_cursor.fetchone()
                    role_id = self.clean_request(role_id)
                    role_id = int(role_id)
                    if role_id != 0:
                        self.db_connect()
                        cursor = self.db.cursor()
                        cursor.execute("SELECT language FROM server_settings WHERE server_id = %s", (data.guild.id,))
                        language = cursor.fetchone()
                        language = self.clean_request(language)
                        if language == "notset":
                            language = "us"
                        role = discord.utils.get(data.guild.roles, id=role_id)
                        await data.author.add_roles(role, reason="Level up")
                        await data.channel.send(f"{self.language[language]['congrats']} {level+1} {self.language[language]['on']} **{data.guild.name}**!")
                elif server_data != 0:
                    user_cursor.execute(f"UPDATE {data.guild.id}_server SET exp = %s WHERE user_id = %s", (exp, data.author.id))
                    self.leveldb.commit()
            else:
                user_cursor.execute(f"INSERT INTO {data.guild.id}_server VALUES(%s, %s, %s)", (data.author.id, 0, rate))
                self.leveldb.commit()

    @app_commands.command(name="rank", description="Se your rank")
    @app_commands.describe(user="The user")
    @app_commands.guild_only()
    async def rank(self, interaction:discord.Interaction, user:discord.Member=None):
            await interaction.response.defer()
            self.db_connect()
            cursor = self.db.cursor()
            cursor.execute("SELECT language FROM server_settings WHERE server_id = %s", (interaction.guild.id,))
            language = cursor.fetchone()
            language = self.clean_request(language)
            if language == "notset":
                language = "us"
            if user != None:
                user = user
            else:
                user = interaction.user
            if not user.bot:
                try:
                    self.leveldb_connect()
                    cursor = self.leveldb.cursor()
                    cursor.execute(f"SELECT * FROM {interaction.guild.id}_server WHERE user_id = %s", (user.id,))
                    info = cursor.fetchall()
                    self.db_connect()
                    cursor = self.db.cursor()
                    try:
                        cursor.execute("SELECT * FROM user_settings WHERE user_id = %s", (user.id,))
                        badge = cursor.fetchall()
                        dev_badge = badge[0][1]
                        upvote_badge = badge[0][2]

                        if int(dev_badge) == 1:
                            dev_badge = discord.utils.get(self.bot.emojis, name="dev_badge")
                        else:
                            dev_badge = ""

                        if int(upvote_badge) == 1:
                            upvote_badge = discord.utils.get(self.bot.emojis, name="upvote_badge")
                            view = None
                        else:
                            upvote_badge = ""
                            button = discord.ui.Button(style=discord.ButtonStyle.link, label="Get the upvote badge", emoji="🗳", url="https://top.gg/bot/869721469964394537")
                            view = discord.ui.View()
                            view.add_item(button)


                    except:                       
                        dev_badge = self.language[language]['no_badges']
                        upvote_badge = ""
                        button = discord.ui.Button(style=discord.ButtonStyle.link, label="Get the upvote badge", emoji="🗳", url="https://top.gg/bot/869721469964394537")
                        view = discord.ui.View()
                        view.add_item(button)
                    if info[0][1] != 5:
                        cursor.execute(f"SELECT exp_{int(info[0][1]+1)} FROM server_settings WHERE server_id = %s", (interaction.guild.id,))
                        exp = cursor.fetchone()
                        exp = self.clean_request(exp)
                        exp = int(exp)
                        remaining_exp = exp - info[0][2]
                    else:
                        remaining_exp = f"{self.language[language]['finished']}"
                    embed = discord.Embed(color=discord.Color.blurple(), title=f"{self.language[language]['rank_of']} {user.name}#{user.discriminator}")
                    embed.set_thumbnail(url=f"{user.avatar}")
                    embed.add_field(name=f"{self.language[language]['level']}", value=f"{info[0][1]}", inline=True)
                    embed.add_field(name=f"{self.language[language]['exp']}", value=f"{info[0][2]}", inline=True)
                    embed.add_field(name=f"{self.language[language]['before_next_level']}", value=f"{remaining_exp}", inline=True)
                    embed.add_field(name=f"Badges", value=f"{dev_badge}{upvote_badge}")
                    if view is not None:
                        await interaction.followup.send(embed=embed, view=view)
                    else:
                        await interaction.followup.send(embed=embed)
                except:
                    try:
                        self.leveldb_connect()
                        cursor = self.leveldb.cursor()
                        cursor.execute(f"INSERT INTO {interaction.guild.id}_server VALUES(%s, %s, %s)", (interaction.user.id, 0, 0))
                        self.leveldb.commit()
                    except:
                        pass
                    await interaction.followup.send(self.language[language]['no_user_info'])
            else:
                await interaction.followup.send(self.language[language]['no_user_info'])

    @app_commands.command(name="leaderboard", description="View the top 5 users of the server")
    @app_commands.guild_only()
    async def leaderboard(self, interaction:discord.Interaction):
        self.db_connect()
        cursor = self.db.cursor()
        cursor.execute("SELECT language FROM server_settings WHERE server_id = %s", (interaction.guild.id,))
        language = cursor.fetchone()
        language = self.clean_request(language)
        if language == "notset":
            language = "us"
        self.leveldb_connect()
        cursor = self.leveldb.cursor()
        cursor.execute(f"SELECT user_id, exp FROM {interaction.guild.id}_server ORDER BY exp DESC")
        users = cursor.fetchmany(5)
        embed = Embed(title=f"Leaderboard {self.language[language]['of']} **{interaction.guild.name}**", color=discord.Color.blurple())
        i:int = 0
        for user in users:
            if i < 5:
                embed.add_field(name=f"{self.bot.get_user(user[0]).name}#{self.bot.get_user(user[0]).discriminator}", value=f"{user[1]} EXP", inline=False)
                i += 1
        await interaction.response.send_message(embed=embed)

async def setup(bot:commands.Bot):
    await bot.add_cog(Level(bot))