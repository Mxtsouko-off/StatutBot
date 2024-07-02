import disnake
from disnake.ext import commands, tasks
import os
from flask import Flask
from threading import Thread

ROLE_ID = 1257351412401180752
intents = disnake.Intents.default()
intents.members = True
intents.presences = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}.")
    await bot.change_presence(status=disnake.Status.idle,
                              activity=disnake.Activity(
                                  type=disnake.ActivityType.watching,
                                  name=f"/z7shop to unlock sponsor roles"))
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
                    continue  # Ignore les bots et les membres hors ligne

            has_custom_status = any(
                activity.type == disnake.ActivityType.custom and activity.state and '/z7shop'  in activity.state
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
                        await member.send('Vous avez perdu le rôle car vous avez retiré "/z7shop" de votre statut.')
                    except disnake.Forbidden:
                        print(f'Could not send DM to {member.display_name}')
                    print(f'Role removed from {member.display_name} in guild {guild.name}')

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
