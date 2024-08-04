import disnake
from disnake.ext import commands, tasks
import os
import random
import json
from dotenv import load_dotenv
from flask import Flask
from threading import Thread
import asyncio
from datetime import datetime, timedelta
import re
import requests

BUMPING_ROLE_ID = 1269374629047173214
BUMPING_CHANNEL_ID = 1269355523522953317
ROLE_ID = 1251588659015192607
CHANNEL_ID = 1269366021576200374
ANSWER_ROLE_ID = 1269365019208843314
ANIME_VOTE_CHANNEL_ID = 1269613048944132116
PING_ANIME_VOTE_ROLE_ID = 1269617965100306494


intents = disnake.Intents.default()
intents.members = True
intents.presences = True
intents.guilds = True
intents.message_content = True

with open("Json/anime.json", "r") as f:
    anime_list = json.load(f)

with open('Json/question.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    questions = [item['question'] for item in data]  

BIO = os.getenv('BIO')
STATUE = os.getenv('STATUE')
bot = commands.Bot(command_prefix="w!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}.")
    await bot.change_presence(status=disnake.Status.do_not_disturb, activity=disnake.Activity(type=disnake.ActivityType.watching, name=f"{STATUE}"))
    check_status.start()
    send_random_question.start()
    remind_bumping.start()
    anime_vote_task.start()

@tasks.loop(hours=2)
async def remind_bumping():
    channel = bot.get_channel(BUMPING_CHANNEL_ID)
    role = disnake.utils.get(channel.guild.roles, id=BUMPING_ROLE_ID)
    if channel is not None and role is not None:
        embed = disnake.Embed(
            title="Rappel de Bump",
            description=f"Il est temps de bump le serveur ! {role.mention}",
            color=0xFF5733
        )
        await channel.send(embed=embed)

def get_anime_image(anime_name):
    url = f"https://api.jikan.moe/v4/anime?q={anime_name}&limit=1"
    response = requests.get(url)
    data = response.json()
    if data['data']:
        return data['data'][0]['images']['jpg']['large_image_url']
    return None

@bot.event
async def on_button_click(interaction: disnake.MessageInteraction):
    if interaction.custom_id == "accept":
        await interaction.response.send_message("Vous avez accepté cet anime!", ephemeral=True)
    elif interaction.custom_id == "pass":
        await interaction.response.send_message("Vous avez passé cet anime!", ephemeral=True)

@tasks.loop(hours=1)
async def anime_vote_task():
    channel = bot.get_channel(int(ANIME_VOTE_CHANNEL_ID))
    anime = random.choice(anime_list)
    anime_name = anime["name"]
    image_url = get_anime_image(anime_name)
    
    if image_url:
        embed = disnake.Embed(title="Vote pour l'anime", description=f"Proposition d'anime : {anime_name}")
        embed.set_image(url=image_url)
        
        view = disnake.ui.View()
        view.add_item(disnake.ui.Button(label="Accepter", style=disnake.ButtonStyle.success, custom_id="accept"))
        view.add_item(disnake.ui.Button(label="Passer", style=disnake.ButtonStyle.danger, custom_id="pass"))

        await channel.send(content=f"<@&{PING_ANIME_VOTE_ROLE_ID}>", embed=embed, view=view)
    else:
        await channel.send(content=f"Je n'ai pas pu trouver une image pour l'anime '{anime_name}'.")

@tasks.loop(hours=24)
async def send_random_question():
    channel = bot.get_channel(CHANNEL_ID)
    role = disnake.utils.get(channel.guild.roles, id=ANSWER_ROLE_ID)
    if channel is not None and role is not None:
        question = random.choice(questions)
        embed = disnake.Embed(title="Question du jour", description=question, color=0x00ff00)
        embed.add_field(name='Hesitez pas a repondre dans:', value='https://discord.com/channels/1251476405112537148/1269373203650973726')
        await channel.send(content=role.mention, embed=embed)

async def wait_until_8am():
    now = datetime.now()
    future = datetime.combine(now.date(), datetime.min.time()) + timedelta(hours=8)
    if now >= future:
        future += timedelta(days=1)
    await asyncio.sleep((future - now).total_seconds())

@tasks.loop(seconds=5)
async def check_status():
    for guild in bot.guilds:
        role = guild.get_role(ROLE_ID)
        if role is None:
            print(f"Role with ID {ROLE_ID} not found in guild {guild.name}.")
            continue

        for member in guild.members:
            if member.bot:
                continue  

            if member.status == disnake.Status.offline:
                continue  

            has_custom_status = any(
                activity.type == disnake.ActivityType.custom and activity.state and f'{BIO}' in activity.state
                for activity in member.activities
            )

            if has_custom_status:
                if role not in member.roles:
                    await member.add_roles(role)
                    print(f'Role added to {member.display_name} in guild {guild.name}')
            else:
                if role in member.roles:
                    await member.remove_roles(role)
                    try:
                        print(f'Role removed from {member.display_name} in guild {guild.name}')
                    except disnake.Forbidden:
                        print(f'Could not send DM to {member.display_name}')
                    print(f'Role removed from {member.display_name} in guild {guild.name}')

@bot.slash_command(description="Affiche le nombre de messages envoyés par un membre")
async def count_messages(inter, member: disnake.Member):
    await inter.response.defer()  

    total_messages = 0

    for channel in inter.guild.text_channels:
        try:
            async for message in channel.history(limit=None):
                if message.author == member:
                    total_messages += 1
        except disnake.Forbidden:
            pass

    embed = disnake.Embed(title="Nombre de messages envoyés", color=disnake.Color.blue())
    embed.add_field(name="Membre", value=member.display_name, inline=True)
    embed.add_field(name="Messages", value=str(total_messages), inline=True)
    embed.set_thumbnail(url=member.avatar.url)
    
    await inter.edit_original_response(embed=embed) 

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if re.search(r'discord\.gg|discord\.com|discord\.me|discord\.app|discord\.io|discord|gg|discord\.gg/|discord\.gg', message.content, re.IGNORECASE):
            await message.delete()
            warning_message = await message.channel.send(f"{message.author.mention}, les liens Discord ne sont pas autorisés dans ce serveur. Cordialement équipe La Taverne")
            await asyncio.sleep(5)
            await warning_message.delete()
            return

    await bot.process_commands(message)

@bot.slash_command(description="Affiche la photo de profil d'un membre")
async def pdp(inter, member: disnake.Member):
    embed = disnake.Embed(title=f"Voici l'avatar de {member.display_name}", color=disnake.Color.blue())
    embed.set_image(url=member.avatar.url)
    embed.set_footer(text=f"Demandé par {inter.author.display_name}", icon_url=inter.author.avatar.url)
    
    await inter.response.send_message(embed=embed)

@bot.slash_command(name='anime_vote')
@commands.has_permissions(administrator=True)
async def anime_vote(ctx):
    anime_vote_task.start()

app = Flask('')

@app.route('/')
def main():
    return f"Logged in as {bot.user}."

def run():
    app.run(host="0.0.0.0", port=5000)

def keep_alive():
    server = Thread(target=run)
    server.start()

keep_alive()
bot.run(os.getenv('TOKEN'))
