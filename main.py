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
from bs4 import BeautifulSoup

BUMPING_ROLE_ID = 1269374629047173214
BUMPING_CHANNEL_ID = 1269355523522953317
ROLE_ID = 1251588659015192607
CHANNEL_ID = 1269366021576200374
ANSWER_ROLE_ID = 1269365019208843314
ANIME_VOTE_CHANNEL_ID = 1269613048944132116
PING_ANIME_VOTE_ROLE_ID = 1269617965100306494
DEVINE_LE_PAYS_ID = 1269626318690189363
PING_DEVINE_LE_PAYS_ID = 1269627556601004104


intents = disnake.Intents.default()
intents.members = True
intents.presences = True
intents.guilds = True
intents.message_content = True

accept_count = 0
pass_count = 0
total_count = 0


countries = [
    "France", "Germany", "Italy", "Spain", "Japan", "Brazil", "Canada", "Australia", "China", "India",
    "United States", "United Kingdom", "Russia", "Mexico", "South Korea", "Turkey", "Saudi Arabia", "Argentina",
    "South Africa", "Egypt", "Nigeria", "Kenya", "Morocco", "Israel", "Greece", "Portugal", "Sweden", "Norway",
    "Denmark", "Finland", "Poland", "Netherlands", "Belgium", "Switzerland", "Austria", "Czech Republic",
    "Hungary", "Romania", "Bulgaria", "Croatia", "Serbia", "Slovakia", "Slovenia", "Lithuania", "Latvia", 
    "Estonia", "Ukraine", "Belarus", "Georgia", "Armenia", "Azerbaijan", "Kazakhstan", "Uzbekistan", "Pakistan",
    "Bangladesh", "Sri Lanka", "Nepal", "Bhutan", "Myanmar", "Thailand", "Vietnam", "Cambodia", "Laos", "Malaysia",
    "Singapore", "Indonesia", "Philippines", "New Zealand"
]


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



def get_country_image(country_name):
    search_query = f"{country_name} landmark"
    search_url = f"https://www.google.com/search?hl=en&tbm=isch&q={search_query}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"}
    
    response = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    image_elements = soup.find_all("img")
    if len(image_elements) > 1:
        img_tag = image_elements[1]
        if 'srcset' in img_tag.attrs:
            srcset = img_tag['srcset']
            urls = [url.split(' ')[0] for url in srcset.split(',')]
            return urls[-1]  # Retourner la meilleure résolution
        else:
            return img_tag['src']
    return None

# Créer un modal
class CountryGuessModal(disnake.ui.Modal):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_item(disnake.ui.TextInput(
            label="Quel est le pays?",
            placeholder="Entrez votre réponse ici...",
            custom_id="country_guess_input"
        ))

    async def callback(self, interaction: disnake.ModalInteraction):
        user_guess = self.children[0].value.strip().lower()
        correct_country = bot.guess_data["country"]
        channel_id = bot.guess_data["channel_id"]
        user_id = bot.guess_data["user_id"]
        
        if user_guess == correct_country:
            await interaction.response.send_message(f"Félicitations ! Vous avez deviné correctement. Le pays est {correct_country}.", ephemeral=True)
            channel = bot.get_channel(channel_id)
            await channel.send(f"Le gagnant est <@{user_id}> ! Nouvelle devinette en cours...")
            await country_guess_task()  # Redémarrer la devinette
        else:
            await interaction.response.send_message(f"Oops ! Ce n'est pas correct. Essayez encore !", ephemeral=True)

# Gérer les interactions avec les boutons
@bot.event
async def on_interaction(interaction: disnake.Interaction):
    if interaction.type == disnake.InteractionType.component:
        custom_id = interaction.data.custom_id
        if custom_id.startswith("guess_"):
            country = custom_id.split("_")[1]
            bot.guess_data = {
                "country": country.lower(),
                "channel_id": interaction.channel.id,
                "user_id": interaction.user.id
            }
            modal = CountryGuessModal(title="Devine le pays")
            await interaction.response.send_modal(modal)
    
    if custom_id == "accept":
            await interaction.response.send_message("Vous avez accepté cet anime!", ephemeral=True)
    elif custom_id == "pass":
            await interaction.response.send_message("Vous avez passé cet anime!", ephemeral=True)

@tasks.loop(hours=2)
async def country_guess_task():
    channel = bot.get_channel(int(DEVINE_LE_PAYS_ID))
    country = random.choice(countries)
    image_url = get_country_image(country)
    
    if image_url:
        embed = disnake.Embed(title="Devine le pays", description=f"Devinez de quel pays il s'agit ! Commencez à deviner par la première lettre : {country[0]}")
        embed.set_image(url=image_url)
        
        view = disnake.ui.View()
        view.add_item(disnake.ui.Button(label="Répondre", style=disnake.ButtonStyle.primary, custom_id=f"guess_{country}"))

        await channel.send(content=f"<@&{PING_DEVINE_LE_PAYS_ID}>", embed=embed, view=view)
    else:
        await channel.send(content="Je n'ai pas pu obtenir une image de pays. Réessayez plus tard.")



@tasks.loop(hours=1)
async def anime_vote_task():
    channel = bot.get_channel(int(ANIME_VOTE_CHANNEL_ID))
    
    if hasattr(anime_vote_task, "accept_count") and hasattr(anime_vote_task, "pass_count"):
        total_count = anime_vote_task.accept_count + anime_vote_task.pass_count
        if total_count > 0:
            accept_percentage = (anime_vote_task.accept_count / total_count) * 100
            pass_percentage = (anime_vote_task.pass_count / total_count) * 100
            results_embed = disnake.Embed(
                title="Résultats du vote anime",
                description=f"**Accepté**: {accept_percentage:.2f}%\n**Passé**: {pass_percentage:.2f}%",
                color=0x00ff00
            )
            await channel.send(embed=results_embed)

    anime_vote_task.accept_count = 0
    anime_vote_task.pass_count = 0

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

@tasks.loop(hours=8)
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
