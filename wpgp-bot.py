import os
import discord
import json
import datetime
import requests
import base64
from discord.ext import tasks
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
# Discord related
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('GUILD')
HEARTBEAT = os.getenv('HEARTBEAT')
PACKALERT = os.getenv('PACKALERT')
STATUS = os.getenv('STATUS')

# Pack forum related
PACKFORUM = os.getenv('PACKFORUM')
PACKTAG = os.getenv('PACKTAG')
PACKLIVETAG = os.getenv('PACKLIVETAG')
PACKDEADTAG = os.getenv('PACKDEADTAG')

# GitHub related
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_USER = os.getenv('GITHUB_USER')
GITHUB_REPO = os.getenv('GITHUB_REPO')
GITHUB_FILEPATH = os.getenv('GITHUB_FILEPATH')

# Commit to GitHub
async def update_github():
    # Get all active friend codes
    fcs = []
    for user in data:
        if data[user]['status']:
            fcs.append(data[user]['fc'])
    text = '\r\n'.join(fcs)

    # Get the sha of the ids.txt file
    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{GITHUB_FILEPATH}"
    headers = { 'Authorization': f'token {GITHUB_TOKEN}' }
    response = requests.get(url, headers=headers)
    sha = response.json()['sha']

    # Update the ids.txt file
    commitData = {
        'message': 'Updated ids.txt from Discord',
        'content': base64.b64encode(text.encode()).decode(),
        'sha': sha
    }
    response = requests.put(url, headers=headers, json=commitData)
    print('Updated GitHub!')

# Update internal friend code status
async def update_fcids(guild):
    roleActive = discord.utils.get(guild.roles, name="Active")
    roleInactive = discord.utils.get(guild.roles, name="Inactive")
    for user in data:
        member = guild.get_member(int(user))
        if data[user]['status']:
            # Check if last heartbeat was too long ago
            now = datetime.datetime.now()
            last_on = datetime.datetime.strptime(data[user]['last_on'], "%Y-%m-%d %H:%M:%S.%f")
            if (now - last_on).total_seconds() > 60 * 33: # 33 minutes for extra buffer
                data[user]['status'] = False
                await member.add_roles(roleInactive)
                await member.remove_roles(roleActive)
                print(f"{member.display_name} is offline!")
            else:
                await member.add_roles(roleActive)
                await member.remove_roles(roleInactive)
        else:
            await member.add_roles(roleInactive)
            await member.remove_roles(roleActive)
    
    # Update logged data
    json_file = open('data.json', 'w')
    json.dump(data, json_file)
    json_file.close()

# Generate online info
def generate_online_info(guild):
    message_part = []
    instances = 0
    width = 40
    for user in data:
        if data[user]['status']:
            member_name = guild.get_member(int(user)).display_name
            instance_str = f"{data[user]['instances']} Instance(s)" if 'instances' in data[user] else "N/A Instances"
            if len(member_name) + len(instance_str) > width - 5:
                member_name = member_name[0:(width - 8)] + "..."
            
            rate = '(N/A packs/min)'
            if ('run_time' in data[user] and not data[user]['run_time'] == 0):
                rate = f"({round(data[user]['packs']['cur'] / data[user]['run_time'] / 60, 2)} packs/min)"
            message_part.append(f"[{'2;32m' if len(data[user]['offline']) == 0 else '0;33m'}{member_name} [2;37m{' '*(width - 1 - len(member_name) - len(instance_str))}[2;37m{instance_str}\n[2;30m{data[user]['packs']['cur']} packs in {data[user]['run_time'] if 'run_time' in data[user] else 'N/A'}h {rate}")
            instances += data[user]['instances'] if 'instances' in data[user] else 0
    return f"```ansi\n[1;34mTotal instances:{' '*(width - 19 - len(str(instances)))} [1;45m[1;37m {instances} [0m\n\n" + '\n'.join(message_part) + "\n```"

# Update status channel
async def update_status(guild):
    status_channel = guild.get_channel(int(STATUS))
    if not 'online_message' in serverdata:

        online_message = await status_channel.send(generate_online_info(guild))
        serverdata['online_message'] = int(online_message.id)

        # Update logged data
        json_file = open('serverdata.json', 'w')
        json.dump(serverdata, json_file)
        json_file.close()
    else:
        online_message = await status_channel.fetch_message(serverdata['online_message'])
        await online_message.edit(content=generate_online_info(guild))
    
# Bot stuff
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = discord.Bot(intents=intents)

# Initialize data
if os.path.isfile('data.json'):
    json_file = open('data.json')
    data = json.load(json_file)
    json_file.close()
else:
    data = {}

if os.path.isfile('serverdata.json'):
    json_file = open('serverdata.json')
    serverdata = json.load(json_file)
    json_file.close()
else:
    serverdata = {}

profile = bot.create_group("profile", "Manage Profile")

# Command: Link friend code to user's Discord ID
@profile.command(description="Set your PTCGP friend code")
async def set(ctx, friend_code: str):
    if len(friend_code) != 16:
        await ctx.respond("Please enter your PTCGP friend code without hyphens.")
    else:
        author_id_str = str(ctx.author.id)
        if not author_id_str in data:
            data[author_id_str] = {}
        
        data[author_id_str]['fc'] = friend_code
        data[author_id_str]['status'] = False

        # Update logged data
        json_file = open('data.json', 'w')
        json.dump(data, json_file)
        json_file.close()

        await ctx.respond(f"Friend code set to {friend_code}!")
        await update_fcids(ctx.guild)

# Command: Get user's profile / information
@profile.command(description="Get user's profile / information")
async def get(ctx, discord_id: str):
    if discord_id in data:
        if 'last_on' in data[discord_id]:
            now = datetime.datetime.now()
            last_on = datetime.datetime.strptime(data[discord_id]['last_on'], "%Y-%m-%d %H:%M:%S.%f")
            days_ago = (now - last_on).days
            hours_ago = round(((now - last_on).seconds / 3600)%24, 1)
        else:
            days_ago = 'N/A'
            hours_ago = 'N/A'
        if 'run_time' in data[discord_id]:
            run_time = round(data[discord_id]['run_time'],1)
        else:
            run_time = 'N/A'
        status = f'Online, running for {run_time}h' if data[discord_id]['status'] else f'Offline, last seen {days_ago} days and {hours_ago} hours ago'#{data[discord_id]['run_time'] if 'run_time' in data[discord_id] else 'N/A'}
        name = await bot.fetch_user(int(discord_id))
        hours = data[discord_id]['hours'] if 'hours' in data[discord_id] else 0
        packs = data[discord_id]['packs']['total'] + data[discord_id]['packs']['cur'] if 'packs' in data[discord_id] else "N/A"
        instances = data[discord_id]['instances'] if 'instances' in data[discord_id] else "N/A"
        await ctx.respond(f"**{name}**\nFriend code: {data[discord_id]['fc']}\nStatus: {status}\nHours farmed: {hours}\nPacks farmed: {packs}\nInstances: {instances}")
    else:
        await ctx.respond("User not found.")

# Admin command: Edit user's profile
@profile.command(description="Edit user's profile (Admin)")
@discord.option("param",choices=["fc","status","hours",])
@discord.option("value",description="Value to update (true/false for status)")
async def manage(ctx, discord_id: str, param: str, value: str):
    if not ctx.author.guild_permissions.administrator:
        await ctx.respond("You do not have permission to use this command.", ephemeral=True)
        return

    if discord_id not in data:
        await ctx.respond("User not found.", ephemeral=True)
        return
    
    value_update = value if param == "fc" else (round(float(value)*2,0)/2 if param == "hours" else (True if value == "true" else False))
    data[discord_id][param] = value_update
    if param == "status" and value_update:
        data[discord_id]['last_on'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

    json_file = open('data.json', 'w')
    json.dump(data, json_file)
    json_file.close()

    await ctx.respond(f"✅ {param} updated!")
    await update_fcids(ctx.guild)

stats = bot.create_group("stats", "View server statistics")

# Command: Get stats of inactive rerollers
@stats.command(description="Get stats of inactive rerollers")
async def inactive(ctx):
    message_part = []
    for user in data:
        if not data[user]['status']:
            member = ctx.guild.get_member(int(user))
            if 'last_on' in data[user]:
                now = datetime.datetime.now()
                last_on = datetime.datetime.strptime(data[user]['last_on'], "%Y-%m-%d %H:%M:%S.%f")
                days_ago = round((now - last_on).days,1)
            else:
                days_ago = 'N/A'
            message_part.append(f"**{member.display_name}**\tLast on: **{days_ago}** days ago")
    await ctx.respond('\n'.join(message_part))

# Command: Generate usernames.txt for self
@bot.command(description="Generate usernames.txt for yourself")
async def usernames(ctx):
    author = ctx.author.display_name
    if len(author) > 11:
        author = author[0:11]
    usernames = []
    for num in range(1, 201):
        usernames.append(f"{author}{num}")
    
    user_file = open('usernames.txt', 'w')
    user_file.write('\n'.join(usernames))
    user_file.close()
    discord_file = discord.File('usernames.txt')
    await ctx.respond(file=discord_file)

# Command: Update god pack thread status
@bot.command(description="Update god pack thread status")
@discord.option("status",choices=["Live","Dead"])
async def gp_status(ctx, status: str):
    if not str(ctx.channel.type) == "public_thread":
        await ctx.respond(f"This command can only be used in a pack thread.", ephemeral=True)
        return
    
    pack_forum = ctx.guild.get_channel(int(PACKFORUM))
    tag = pack_forum.get_tag(int(PACKLIVETAG)) if status == "Live" else pack_forum.get_tag(int(PACKDEADTAG))
    await ctx.channel.edit(applied_tags=[tag])
    await ctx.respond("✅ Status updated!")

# Command: Set own status to offline manually
@bot.command(description="Set your status to offline")
async def offline(ctx):
    if str(ctx.author.id) not in data:
        await ctx.respond("Please set your friend code first.", ephemeral=True)
        return
    
    data[str(ctx.author.id)]['status'] = False

    json_file = open('data.json', 'w')
    json.dump(data, json_file)
    json_file.close()

    await ctx.respond("✅ Status set to offline!")
    await update_fcids(ctx.guild)
    await update_status(ctx.guild)


# Admin command: Get full user data (for debug)
@bot.command(description="Get full user data (Admin)")
async def get_json(ctx, discord_id: str):
    if not ctx.author.guild_permissions.administrator:
        await ctx.respond("You do not have permission to use this command.", ephemeral=True)
        return
    
    if discord_id in data:
        await ctx.respond(f"```\n{json.dumps(data[discord_id], indent=4)}\n```")
    else:
        await ctx.respond("User not found.")

# Events for reading messages
@bot.event
async def on_message(message):
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return
    
    # Heartbeat channel
    if message.channel.id == int(HEARTBEAT):
        # Ensure message is from webhook
        if message.webhook_id:
            lines = message.content.split('\n')
            online_id = lines[0]

            # Ensure user has set their friend code
            if online_id not in data:
                await message.add_reaction("❓")
                await update_fcids(message.guild)
                return
            
            # Update user status / last online time
            data[online_id]['status'] = True
            if 'hours' in data[online_id]:
                now = datetime.datetime.now()
                last_on = datetime.datetime.strptime(data[online_id]['last_on'], "%Y-%m-%d %H:%M:%S.%f")
                if (now - last_on).total_seconds() > 60 * 29:
                    data[online_id]['hours'] = data[online_id]['hours'] + 0.5
            else:
                data[online_id]['hours'] = 0.5
            data[online_id]['last_on'] = message.created_at.strftime("%Y-%m-%d %H:%M:%S.%f")

            # Update user instance count
            data[online_id]['instances'] = len(lines[1].split(',')) - 1

            # Update current roll time
            data[online_id]['run_time'] = round(int(lines[3].split('Time: ')[1].split('m')[0])/60.0,1)

            # Update user pack count
            if 'packs' not in data[online_id]:
                data[online_id]['packs'] = {
                    'total': 0,
                    'cur': 0
                }
            cur_packs = int(lines[3].split('Packs: ')[1])
            if cur_packs == 0:
                data[online_id]['packs']['total'] += data[online_id]['packs']['cur']
                data[online_id]['packs']['cur'] = 0
            else:
                data[online_id]['packs']['cur'] = cur_packs

            # Check for offline instances
            if lines[2] == "Offline: none.":
                data[online_id]['offline'] = []
            else:
                if 'offline' not in data[online_id]:
                    data[online_id]['offline'] = []
                r_offset = -1 if lines[2].endswith('.') else -2
                offlines = lines[2][9:r_offset].split(', ')
                if not len(offlines) == len(data[online_id]['offline']):
                    offlines_str = ', '.join(offlines)
                    await message.channel.send(f"<@{online_id}> Instance(s) offline: {offlines_str}")

            # Update logged data
            json_file = open('data.json', 'w')
            json.dump(data, json_file)
            json_file.close()

            print(f"{message.guild.get_member(int(online_id)).display_name} is online!")
            await message.add_reaction("❤️")
            await update_fcids(message.guild)
            await update_status(message.guild)


    # Pack alert channel
    elif message.channel.id == int(PACKALERT):
        # Ensure message is from webhook
        if message.webhook_id:
            lines = message.content.split('\n')
            # Ignore other alerts in the channel
            if len(lines) < 3:
                return
            if lines[2].startswith("Found a God Pack"):
                acc_name = lines[1].split('(')[0]
                acc_fc = lines[1].split('(')[1][0:16]
                packs_num = lines[2].split('(')[1][0]
                file = message.attachments[0].url
                roleActive = discord.utils.get(message.guild.roles, name="Active")
                pack_forum = message.guild.get_channel(int(PACKFORUM))
                tag = pack_forum.get_tag(int(PACKTAG))
                packnumdata = [(1,1),(5,9),(8,15),(11,21)]
                await pack_forum.create_thread(name=f"{acc_name} [{packs_num}P]", content=f"{roleActive.mention}\nClear your friends list and check your wonder pick!\nFriend code: `{acc_fc}`\nUse `/gp_status` to update thread tag\nOther packs needed for 95% confidence of dud: **{packnumdata[int(packs_num)-1][0]}**\nOther packs needed for 99.7% confidence of dud: **{packnumdata[int(packs_num)-1][1]}**\n{file}", applied_tags=[tag])

# Event on bot startup
@bot.event
async def on_ready():
    print('---------------------')
    print(f'Started bot at {datetime.datetime.now()}')
    print('---------------------\n')
    
    # Set bot status
    await bot.change_presence(activity=discord.Game(name="v1.2b"))

    # Begin auto update loop
    auto_update.start()
    guild = bot.get_guild(int(GUILD))
    await update_fcids(guild)
    await update_status(guild)

# Auto update loop
@tasks.loop(minutes=2)
async def auto_update():
    await update_github()

bot.run(DISCORD_TOKEN)