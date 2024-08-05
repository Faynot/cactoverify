import disnake
from disnake.ext import commands
from aiohttp import web

intents = disnake.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

verification_requests = {}

GUILD_ID = ''  # server ID
ROLE_ID = ''  # role ID

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if isinstance(message.channel, disnake.DMChannel) and message.author in verification_requests:
        verification_code = message.content.strip().upper()
        if verification_code == verification_requests[message.author]['code']:
            guild = bot.get_guild(int(GUILD_ID))
            member = guild.get_member(message.author.id)
            role = guild.get_role(int(ROLE_ID))
            await member.add_roles(role)
            await message.author.send("🎉 Verification successful! You have been given a role.")
            del verification_requests[message.author]
        else:
            await message.author.send("❌ Incorrect code. Please try again.")

async def handle_verification_request(request):
    data = await request.json()
    telegram_id = data['telegram_id']
    discord_username = data['discord_username']
    code = data['code']

    for guild in bot.guilds:
        for member in guild.members:
            if member.name == discord_username or member.display_name == discord_username:
                verification_requests[member] = {'telegram_id': telegram_id, 'code': code}
                await member.send(f"🤖 Hello! Please enter verification code: ")
                return web.Response(text="Verification request sent to user.")
    return web.Response(text="Discord user not found.", status=404)

async def handle_remove_user(request):
    data = await request.json()
    telegram_id = data['telegram_id']
    discord_username = data['discord_username']

    for guild in bot.guilds:
        for member in guild.members:
            if member.name == discord_username or member.display_name == discord_username:
                role = guild.get_role(int(ROLE_ID))
                await member.remove_roles(role)
                return web.Response(text="User removed from role.")
    return web.Response(text="Discord user not found.", status=404)

async def handle_return_user(request):
    data = await request.json()
    telegram_id = data['telegram_id']
    discord_username = data['discord_username']

    for guild in bot.guilds:
        for member in guild.members:
            if member.name == discord_username or member.display_name == discord_username:
                role = guild.get_role(int(ROLE_ID))
                await member.add_roles(role)
                return web.Response(text="User returned to role.")
    return web.Response(text="Discord user not found.", status=404)

app = web.Application()
app.add_routes([
    web.post('/verify', handle_verification_request),
    web.post('/remove_user', handle_remove_user),
    web.post('/return_user', handle_return_user)
])

bot.loop.create_task(web._run_app(app, host='localhost', port=7070))
bot.run('BOT_TOKEN')
