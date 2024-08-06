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
FONDATION_ID = 1251491671124738173
STAFF_ID = 1268728239010873395
HAUT_STAFF_ID = 1268895267382628383
BILAN_MSG_ID = 1269972458526478357
SUSPENSION_ID = 1269975815655915552
RÉUNION_ID = 1270027066934427700

intents = disnake.Intents.default()
intents.members = True
intents.presences = True
intents.guilds = True
intents.message_content = True

accept_count = 0
pass_count = 0
total_count = 0

Wiki = """
** Commandes de Modération et de Gestion des Niveaux

*** Commandes Administration

- **Réunion :**  
  Pour organisé une réunion, utilisez la commande suivante :  
  `/réunion date: heures:`

- **Plainte Bilan :**  
  Pour faire une plainte staff, utilisez la commande suivante :  
  `/bilan @membre: plainte:`

- **Suspensions Staff :**  
  Pour faire une Suspensions staff, utilisez la commande suivante :  
  `/suspension @membre: temps:`

- **Promouvoir Staff :**  
  Pour faire une Promotions staff, utilisez la commande suivante :  
  `/promouvoir @membre:`

*** Commandes de Modération

- **Avertissement :**  
  Pour avertir un membre, utilisez la commande suivante :  
  `/avertir @membre raison`

- **Bannissement :**  
  Pour bannir un utilisateur, utilisez la commande suivante :  
  `/ban @utilisateur raison`

- **Mute :**  
  Pour réduire au silence un membre temporairement, utilisez :  
  `/mute durée raison`

- **Expulsion :**  
  Pour expulser un membre, utilisez :  
  `/expulser @membre raison`

*** Commandes de Gestion des Niveaux

- **Ajouter des niveaux :**  
  Pour ajouter des niveaux à un membre, utilisez :  
  `/adminxp ajouter @membre niveaux`

- **Ajouter de l'expérience :**  
  Pour ajouter de l'expérience à un membre, utilisez :  
  `/adminxp ajouter @membre experience`

- **Retirer des niveaux :**  
  Pour retirer des niveaux à un membre, utilisez :  
  `/adminxp retirer @membre niveaux`

- **Retirer de l'expérience :**  
  Pour retirer de l'expérience à un membre, utilisez :  
  `/adminxp retirer @membre experience`

*** Sanctions d'Avertissement

- **1-2 Avertissements :**  
  Aucune sanction.

- **3 Avertissements :**  
  Exclusion temporaire de 24 heures.

- **4 Avertissements :**  
  Avertissement supplémentaire + exclusion de 48 heures.

- **5 Avertissements :**  
  Bannissement permanent.
"""

PROMOTION_ROLES = {
    "Manager": 1251840088032280668,
    "Responsable": 1268647331679440984,
    "Bot Manager": 1268649746797428808,
    "Administrateur": 1268649426470043738,
    "Super Modérateur": 1251840576651792417,
    "Moderateur": 1251839752886554666,
    "Helpeur": 1268649634725761117,
    "Periode Test": 1251840313891491881
}

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

@bot.event
async def on_interaction(interaction: disnake.Interaction):
    if interaction.type == disnake.InteractionType.component:
        custom_id = interaction.data.custom_id
    if custom_id == "accept":
            await interaction.response.send_message("Vous avez accepté cet anime!", ephemeral=True)
    elif custom_id == "pass":
            await interaction.response.send_message("Vous avez passé cet anime!", ephemeral=True)

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

@bot.slash_command(name='wiki', description='Permet de voir les commandes staff')
@commands.has_role(STAFF_ID)
async def wiki(ctx, salon):
    GET_ID = salon
    channel = bot.get_channel(GET_ID)
    if channel:
        em = disnake.Embed(title='Wiki staff', description=Wiki)
        em.set_image(url='https://i.ibb.co/zGv8w3k/Taverne-R-cup-r.png')
        em.set_footer(text='Équipe de la fondation')
        await salon.send(embed=em)
        await ctx.response.send_message(f"Message envoyé dans le salon {salon.mention}", ephemeral=True)
    else:
        await ctx.response.send_message("Le salon spécifié n'existe pas.", ephemeral=True)

@bot.slash_command(name='bilan', description='Soumettre une plainte envers un staff')
@commands.has_role(STAFF_ID)
async def bilan(ctx, membre: disnake.Member, plainte: str):
    channel = bot.get_channel(BILAN_MSG_ID)
    if channel:
        em = disnake.Embed(title=f"Une plainte a été déposée envers {membre.mention}", description=f"La plainte est : {plainte}")
        await channel.send(embed=em)
        await ctx.response.send_message(f"Plainte enregistrée concernant {membre.mention}.", ephemeral=True)
    else:
        await ctx.response.send_message("Le canal de bilan spécifié n'existe pas.", ephemeral=True)


@bot.slash_command(name='promouvoir', description='Permet de promouvoir une personne du staff')
@commands.has_role(FONDATION_ID)
async def promouvoir(ctx, membre: disnake.Member):
    options = [
        disnake.SelectOption(label=role_name, value=str(role_id))
        for role_name, role_id in PROMOTION_ROLES.items()
    ]
    
    select = disnake.ui.Select(placeholder="Choisissez le rôle à promouvoir", options=options)
    view = disnake.ui.View()
    view.add_item(select)
    
    async def on_select(interaction: disnake.Interaction):
        if interaction.user != ctx.author:
            await interaction.response.send_message("Vous n'êtes pas autorisé à utiliser ce menu.", ephemeral=True)
            return
        
        role_id = int(select.values[0])
        role = ctx.guild.get_role(role_id)
        if role:
            await membre.add_roles(role)
            await interaction.response.send_message(f"{membre.mention} a été promu au rôle {role.name}.", ephemeral=True)
            try:
                await membre.send(f"Félicitations ! Vous avez été promu au rôle {role.name} dans le serveur.")
            except disnake.Forbidden:
                await ctx.response.send_message("Impossible d'envoyer un message privé à ce membre.", ephemeral=True)
        else:
            await interaction.response.send_message("Rôle non trouvé.", ephemeral=True)
    
    select.callback = on_select
    await ctx.response.send_message("Sélectionnez le rôle pour la promotion :", view=view, ephemeral=True)


@bot.slash_command(name='suspension', description='Permet de suspendre un membre du staff')
@commands.has_role(FONDATION_ID)
async def suspension(ctx, membre: disnake.Member, temps: str):
    try:
        time_mapping = {
            "s": 1,  
            "m": 60, 
            "h": 3600, 
            "d": 86400 
        }
        
        if temps[-1] in time_mapping:
            duration = int(temps[:-1]) * time_mapping[temps[-1]]
        else:
            await ctx.response.send_message("Format de temps invalide. Utilisez `s` pour secondes, `m` pour minutes, `h` pour heures, `d` pour jours.", ephemeral=True)
            return
        
        suspension_role = ctx.guild.get_role(SUSPENSION_ID)
        if suspension_role:
            await membre.add_roles(suspension_role)
        else:
            await ctx.response.send_message("Rôle de suspension non trouvé.", ephemeral=True)
            return
        
        staff_roles = [ctx.guild.get_role(STAFF_ID), ctx.guild.get_role(HAUT_STAFF_ID)]
        for role in staff_roles:
            if role in membre.roles:
                await membre.remove_roles(role)
        
        try:
            await membre.send(f"Vous avez été suspendu pour {temps}. Votre rôle de staff a été temporairement retiré.")
        except disnake.Forbidden:
            await ctx.response.send_message("Impossible d'envoyer un message privé à ce membre.", ephemeral=True)
        
        await asyncio.sleep(duration)
        
        if suspension_role in membre.roles:
            await membre.remove_roles(suspension_role)
        
        if STAFF_ID in [role.id for role in staff_roles]:
            await membre.add_roles(ctx.guild.get_role(STAFF_ID))
        if HAUT_STAFF_ID in [role.id for role in staff_roles]:
            await membre.add_roles(ctx.guild.get_role(HAUT_STAFF_ID))
        
        await ctx.response.send_message(f"La suspension de {membre.mention} est terminée. Les rôles de staff ont été réattribués.", ephemeral=True)
    
    except Exception as e:
        await ctx.response.send_message(f"Une erreur est survenue : {str(e)}", ephemeral=True)

@bot.slash_command(name='réunion', description='Organiser une réunion staff')
@commands.has_any_role(FONDATION_ID, HAUT_STAFF_ID)
async def réunion(ctx, date: str, heures: str):
    channel = bot.get_channel(RÉUNION_ID)
    if channel:
        em = disnake.Embed(title='Annonce Réunions', description=f'Une Réunions aura lieux le {date} a {heures}') 
        em.set_image(url='https://i.ibb.co/zGv8w3k/Taverne-R-cup-r.png')
        await channel.send(embed=em)
    await ctx.response.send_message(f"Réunion organisée pour le {date} à {heures}.", ephemeral=True)


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
