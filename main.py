# discord-mc-bot/main.py
#
# Update a specific Discord message with the status of a Minecraft server
# every 10 seconds to display a live status without spamming new messages.

import os
from dotenv import load_dotenv
import discord
from mcstatus import JavaServer
from discord.ext import tasks
from datetime import datetime

load_dotenv()

# --- Configuration ---
# You only need the bot token and the channel ID now.
DISCORD_BOT_SECRET = os.getenv("DISCORD_BOT_SECRET")
DISCORD_CHANNEL_ID = os.getenv("DISCORD_CHANNEL_ID")

MINECRAFT_SERVER_IP = "185.55.240.150"
CHECK_INTERVAL = 10 # seconds
# --------------------

intents = discord.Intents.default()
client = discord.Client(intents=intents)

# This global variable will hold the message object after it's sent.
status_message = None

def get_mc_server_status():
    """Queries the Minecraft server and returns a formatted status string."""
    try:
        server = JavaServer.lookup(MINECRAFT_SERVER_IP)
        status = server.status()
        # The 'players.sample' can sometimes be None, so we handle that case.
        player_names = [player.name for player in status.players.sample] if status.players.sample else []
        
        player_list_str = f"**Players:** {', '.join(player_names)}" if player_names else "**Players:** No one is online"

        return (
            f"**Minecraft Server Status**\n"
            f"IP: `{MINECRAFT_SERVER_IP}`\n"
            f":green_circle: **Online**\n"
            f"**Players Online:** {status.players.online}/{status.players.max}\n"
            f"{player_list_str}\n"
            f"*Last updated: <t:{int(datetime.now().timestamp())}:R>*"
        )
    except Exception as e:
        print(f"Could not connect to the Minecraft server: {e}")
        return (
            f"**Minecraft Server Status**\n"
            f"IP: `{MINECRAFT_SERVER_IP}`\n"
            f":red_circle: **Offline**\n"
            f"*Could not retrieve server details.*\n"
            f"*Last updated: <t:{int(datetime.now().timestamp())}:R>*"
        )


@client.event
async def on_ready():
    """Event handler for when the bot logs in and is ready."""
    print(f'Logged in as {client.user}')
    # Start the background task to update the status.
    update_status.start()
    

@tasks.loop(seconds=CHECK_INTERVAL)
async def update_status():
    """A background task that runs every CHECK_INTERVAL seconds to update the status message."""
    global status_message # Use the global variable to store the message

    # Get the channel object from the ID provided.
    channel = client.get_channel(int(DISCORD_CHANNEL_ID))
    
    # Stop the task if the channel ID is invalid or the bot isn't in the server.
    if not channel:
        print(f"Error: Channel with ID {DISCORD_CHANNEL_ID} not found. Stopping task.")
        update_status.stop()
        return

    # Get the latest server status content.
    new_content = get_mc_server_status()

    try:
        if status_message is None:
            # If the bot has just started, it sends a new message.
            status_message = await channel.send(new_content)
            print(f"Initial status message sent with ID: {status_message.id}")
        else:
            # Otherwise, it edits the existing message.
            await status_message.edit(content=new_content)
            print("Status message updated.")
            
    except discord.errors.NotFound:
        # This happens if the original message was deleted by a user.
        print("Message not found. It was likely deleted. Sending a new one.")
        status_message = await channel.send(new_content)
        
    except Exception as e:
        print(f"Failed to update message: {e}")


client.run(DISCORD_BOT_SECRET)