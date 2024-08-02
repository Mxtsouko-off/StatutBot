import disnake
from disnake.ext import commands, tasks
import os
from flask import Flask
from threading import Thread

ROLE_ID = 1251588659015192607
intents = disnake.Intents.default()
intents.members = True
intents.presences = True
intents.guilds = True
intents.message_content = True

BIO = os.getenv('BIO')
STATUE = os.getenv('STATUE')
bot = commands.Bot(command_prefix="+", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}.")
    await bot.change_presence(status=disnake.Status.idle, activity=disnake.Activity(type=disnake.ActivityType.watching, name=f"{STATUE}"))
    check_status.start()

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

            if member.bot or member.status == disnake.Status.offline:
                    continue  

            has_custom_status = any(
                activity.type == disnake.ActivityType.custom and activity.state and f'{BIO}'  in activity.state
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

    if 'mxtsouko' or '@! MXTSOUKO' in message.content.lower():
        embed = disnake.Embed(
            title="My Link",
            description=(
                "**Mes Reseaux**:\n\n"
                "[**Instagram**](https://www.instagram.com/mxtsouko/)\n"
                "[**Snapchat**](https://www.snapchat.com/add/mxtsouko)\n"
                "[**Github**](https://github.com/mxtsouko-off)\n"
                "[**TikTok**](https://www.tiktok.com/@mxtsouko)\n\n"
                "**Me faire un dons**:\n\n"
                "[**Paypal**](https://www.paypal.com/paypalme/MxtsoukoYtSlmCommand)\n"
            ),
            color=disnake.Color.green()
        )
        embed.set_author(name=message.author.display_name, icon_url=message.author.avatar.url)
        embed.set_footer(text=f"Message ID: {message.id}")

        await message.channel.send(embed=embed)

    await bot.process_commands(message)

@bot.slash_command(description="Affiche la photo de profil d'un membre")
async def pdp(inter, member: disnake.Member):
    embed = disnake.Embed(title=f"Voici l'avatar de {member.display_name}", color=disnake.Color.blue())
    embed.set_image(url=member.avatar.url)
    embed.set_footer(text=f"Demandé par {inter.author.display_name}", icon_url=inter.author.avatar.url)
    
    await inter.response.send_message(embed=embed)



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
