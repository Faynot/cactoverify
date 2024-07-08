import disnake
from disnake.ext import commands
from aiohttp import web

intents = disnake.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

verification_requests = {}

GUILD_ID = '1168716887648112720'  # ID вашего сервера
ROLE_ID = '1259775538210541588'  # ID роли, которую необходимо выдать


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
            await message.channel.send(
                "Не верный код, пожалуйста, попробуйте ещё раз или обратитесь в поддержку: \n Discord - faynot \n Telegram - @faynotobglotish.")
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
        await member.send("Привет! Я бот приватки Cacto0o, если вы не получали никакой код, обратитесь в поддержку:  \n Discord - faynot \n Telegram - @faynotobglotish \nВведите код:")
        return web.Response(text="Verification request received.")
    else:
        return web.Response(text="User not found.")


# Новый эндпоинт для уведомления об удалении пользователя
async def handle_user_removal(request):
    data = await request.json()
    telegram_id = data['telegram_id']
    discord_username = data['discord_username']

    guild = bot.get_guild(int(GUILD_ID))
    member = disnake.utils.get(guild.members, name=discord_username)

    if member:
        role = disnake.utils.get(guild.roles, id=int(ROLE_ID))
        await member.remove_roles(role)
        print(f"Пользователя {telegram_id} больше нет, роль удалена у {discord_username}")

    return web.Response(text="User removal notification received.")


app = web.Application()
app.router.add_post('/verify', handle_verification)
app.router.add_post('/remove_user', handle_user_removal)

if __name__ == "__main__":
    bot.loop.create_task(web._run_app(app, port=8080))
    bot.run('MTE1NDMxNDI0Nzg0OTkxODQ4NA.Gde09C.TajMa-svq72lYX-k0Nob7Ojv2QuqKqRA7dUymQ')
