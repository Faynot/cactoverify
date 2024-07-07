import disnake
from disnake.ext import commands
from aiohttp import web

intents = disnake.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

verification_requests = {}

GUILD_ID = '1259211841238994944'  # ID вашего сервера
ROLE_ID = '1259212461119242270'  # ID роли, которую необходимо выдать


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    user_id = message.author.id
    if user_id in verification_requests:
        code = verification_requests.pop(user_id)
        if message.content.strip() == code:
            guild = bot.get_guild(int(GUILD_ID))
            if guild:
                member = guild.get_member(user_id)
                if member:
                    role = disnake.utils.get(guild.roles, id=int(ROLE_ID))
                    await member.add_roles(role)
                    await message.channel.send("Роль выдана!")
                else:
                    await message.channel.send("Пользователь не найден.")
            else:
                await message.channel.send("Сервер не найден.")
        else:
            await message.channel.send("Не верный код, пожалуйста, попробуйте ещё раз или обратитесь в поддержку: \n Discord - faynot \n Telegram - @faynotobglotish.")
    await bot.process_commands(message)


async def handle_verification(request):
    data = await request.json()
    telegram_id = data['telegram_id']
    discord_username = data['discord_username']
    code = data['code']

    guild = bot.get_guild(int(GUILD_ID))
    member = disnake.utils.get(guild.members,
                               name=discord_username)  # Убедитесь, что имя пользователя уникально и существует

    if member:
        verification_requests[member.id] = code
        await member.send("Введите код:")
        return web.Response(text="Verification request received.")
    else:
        return web.Response(text="User not found.")


app = web.Application()
app.router.add_post('/verify', handle_verification)

if __name__ == "__main__":
    bot.loop.create_task(web._run_app(app, port=8080))
    bot.run('MTE1NDMxNDI0Nzg0OTkxODQ4NA.GKFDR4.600OVnhPDSuoZiQPRSzB4aiV9mWD6LCXvogT_Y')
