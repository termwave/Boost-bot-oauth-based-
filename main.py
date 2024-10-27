import discord
from discord.ext import commands
from discord import app_commands
import tls_client
import threading
import os
import requests
from base64 import b64encode
import json

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Constants and configurations
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
BUILD_NUMBER = 165486
CV = "108.0.0.0"
BOT_TOKEN = "Your Bot Token"
CLIENT_SECRET = "Your Bot Secret"
CLIENT_ID = "cLIENT ID"
REDIRECT_URI = "http://localhost:8080"
API_ENDPOINT = 'https://canary.discord.com/api/v9'
AUTH_URL = f"https://canary.discord.com/api/oauth2/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope=identify%20guilds.join"

SUPER_PROPERTIES = b64encode(
    json.dumps(
        {
            "os": "Windows",
            "browser": "Chrome",
            "device": "PC",
            "system_locale": "en-GB",
            "browser_user_agent": USER_AGENT,
            "browser_version": CV,
            "os_version": "10",
            "referrer": "https://discord.com/channels/@me",
            "referring_domain": "discord.com",
            "referrer_current": "",
            "referring_domain_current": "",
            "release_channel": "stable",
            "client_build_number": BUILD_NUMBER,
            "client_event_source": None
        },
        separators=(',', ':')).encode()).decode()

def get_headers(token):
    return {
        "Authorization": token,
        "Origin": "https://canary.discord.com",
        "Accept": "*/*",
        "X-Discord-Locale": "en-GB",
        "X-Super-Properties": SUPER_PROPERTIES,
        "User-Agent": USER_AGENT,
        "Referer": "https://canary.discord.com/channels/@me",
        "X-Debug-Options": "bugReporterEnabled",
        "Content-Type": "application/json"
    }

def exchange_code(code):
    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    response = requests.post(f"{API_ENDPOINT}/oauth2/token", data=data, headers=headers)
    if response.status_code in (200, 201, 204):
        return response.json()
    else:
        print(f"Error exchanging code: {response.status_code} - {response.text}")
        return False

def add_to_guild(access_token, user_id, guild_id):
    url = f"{API_ENDPOINT}/guilds/{guild_id}/members/{user_id}"
    bot_token = BOT_TOKEN
    data = {"access_token": access_token}
    headers = {"Authorization": f"Bot {bot_token}", 'Content-Type': 'application/json'}
    response = requests.put(url=url, headers=headers, json=data)
    return response.status_code

def rename(token, guild_id, nickname):
    if nickname:
        headers = get_headers(token)
        client = tls_client.Session(client_identifier="firefox_102")
        client.headers.update(headers)
        response = client.patch(
            f"https://canary.discord.com/api/v9/guilds/{guild_id}/members/@me",
            json={"nick": nickname}
        )
        if response.status_code in (200, 201, 204):
            print(f"[+] Nickname changed to {nickname}")
            return "ok"
        else:
            print(f"[-] Failed to change nickname: {response.status_code} - {response.text}")
            return "error"

def update_pfp(token, image_path):
    if image_path and os.path.isfile(image_path):
        headers = get_headers(token)
        with open(image_path, "rb") as f:
            image_data = f.read()
        image_base64 = b64encode(image_data).decode('utf-8')
        response = requests.patch(
            f"{API_ENDPOINT}/users/@me",
            headers=headers,
            json={"avatar": f"data:image/png;base64,{image_base64}"}
        )
        if response.status_code in (200, 201, 204):
            print("[+] Profile picture updated")
            return "ok"
        else:
            print(f"[-] Failed to update profile picture: {response.status_code} - {response.text}")
            return "error"

def get_user(access_token):
    response = requests.get(
        f"{API_ENDPOINT}/users/@me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    if response.status_code == 200:
        response_json = response.json()
        return response_json['id']
    else:
        print(f"[-] Failed to get user info: {response.status_code} - {response.text}")
        return None

def authorize(token, guild_id, nickname, pfp_path):
    headers = get_headers(token)
    response = requests.post(AUTH_URL, headers=headers, json={"authorize": "true"})
    if response.status_code in (200, 201, 204):
        location = response.json().get('location')
        code = location.replace("http://localhost:8080?code=", "")
        exchange = exchange_code(code)
        if exchange:
            access_token = exchange['access_token']
            user_id = get_user(access_token)
            if user_id:
                add_to_guild(access_token, user_id, guild_id)
                if nickname:
                    threading.Thread(target=rename, args=(token, guild_id, nickname)).start()
                if pfp_path:
                    threading.Thread(target=update_pfp, args=(token, pfp_path)).start()
                return "ok"
    print("[-] Authorization failed")
    return "error"

def main(token, guild_id, nickname=None, pfp_path=None):
    authorization_result = authorize(token, guild_id, nickname, pfp_path)
    if authorization_result == "ok":
        headers = get_headers(token)
        client = tls_client.Session(client_identifier="firefox_102")
        client.headers.update(headers)
        response = client.get(f"{API_ENDPOINT}/users/@me/guilds/premium/subscription-slots")
        
        try:
            slots = response.json()
            if isinstance(slots, list):
                for slot in slots:
                    if isinstance(slot, dict) and 'id' in slot:
                        slot_id = slot['id']
                        payload = {"user_premium_guild_subscription_slot_ids": [slot_id]}
                        response = client.put(
                            f"{API_ENDPOINT}/guilds/{guild_id}/premium/subscriptions",
                            json=payload
                        )
                        if response.status_code in (200, 201, 204):
                            print(f"[+] Boosted {guild_id}")
                        else:
                            print(f"[-] Failed to boost: {response.status_code} - {response.text}")
                    else:
                        print(f"[-] Unexpected slot format: {slot}")
            else:
                print(f"[-] Unexpected response format: {slots}")
        except json.JSONDecodeError as e:
            print(f"[-] Failed to parse JSON response: {e}")
    else:
        print("[-] Authorization failed")

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)
    
    activity = discord.Activity(type=discord.ActivityType.watching, name=".gg/dreamboostz")
    await bot.change_presence(activity=activity)

ALLOWED_USER_IDS = [894929372648189952, 1101773091245391913]  # Replace with the actual user IDs

def is_allowed_user():
    async def predicate(interaction: discord.Interaction):
        if interaction.user.id in ALLOWED_USER_IDS:
            return True
        embed = discord.Embed(title="Permission Denied", description="You are not allowed to use this command.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return False
    return app_commands.check(predicate)

@bot.tree.command(name="operate")
@is_allowed_user()
@app_commands.describe(guild_id="The ID of the guild", nickname="The nickname to use", pfp_path="The path to the profile picture file")
async def operate(interaction: discord.Interaction, guild_id: str, nickname: str = None, pfp_path: str = None):
    if not guild_id:
        embed = discord.Embed(title="Missing Arguments", description="Please provide the guild ID.", color=discord.Color.red())
        embed.add_field(name="Command Usage", value="/operate <guild_id> [nickname] [pfp_path]")
        await interaction.response.send_message(embed=embed)
        return

    await interaction.response.send_message(f"Starting operation for guild ID: {guild_id} with nickname: {nickname} and profile picture: {pfp_path}")
    with open("boost-tokens.txt", "r") as f:
        tokens = f.readlines()
    for token in tokens:
        token = token.strip()
        if ":" in token:
            try:
                token = token.split(":")[2]
            except IndexError:
                await interaction.followup.send(f"Invalid token format: {token}")
                continue
        threading.Thread(target=main, args=(token, guild_id, nickname, pfp_path)).start()
    await interaction.followup.send(f"Operation completed for guild ID: {guild_id}")

@bot.tree.command(name="add_token")
@is_allowed_user()
@app_commands.describe(token="The token to add")
async def add_token(interaction: discord.Interaction, token: str):
    if not token:
        embed = discord.Embed(title="Missing Arguments", description="Please provide the required token.", color=discord.Color.red())
        embed.add_field(name="Command Usage", value="/add_token <token>")
        await interaction.response.send_message(embed=embed)
        return

    with open("boost-tokens.txt", "a") as f:
        f.write(f"{token}\n")
    await interaction.response.send_message(f"Token added: {token}")

@bot.tree.command(name="remove_token")
@is_allowed_user()
@app_commands.describe(token="The token to remove")
async def remove_token(interaction: discord.Interaction, token: str):
    if not token:
        embed = discord.Embed(title="Missing Arguments", description="Please provide the required token.", color=discord.Color.red())
        embed.add_field(name="Command Usage", value="/remove_token <token>")
        await interaction.response.send_message(embed=embed)
        return

    with open("boost-tokens.txt", "r") as f:
        tokens = f.readlines()
    tokens = [t.strip() for t in tokens if t.strip() != token]
    with open("boost-tokens.txt", "w") as f:
        f.write("\n".join(tokens) + "\n")
    await interaction.response.send_message(f"Token removed: {token}")

@bot.tree.command(name="list_tokens")
@is_allowed_user()
async def list_tokens(interaction: discord.Interaction):
    with open("boost-tokens.txt", "r") as f:
        tokens = f.readlines()
    if tokens:
        embed = discord.Embed(title="Boost Tokens", description="\n".join(tokens), color=discord.Color.blue())
    else:
        embed = discord.Embed(title="Boost Tokens", description="No boost tokens found.", color=discord.Color.blue())
    await interaction.response.send_message(embed=embed)
    
bot.run(BOT_TOKEN)