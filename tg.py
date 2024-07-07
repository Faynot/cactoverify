import telebot
import random
import string
import requests
from telebot import types


API_TOKEN = '7350646532:AAGCJesf_S_s8sBwZEbTEFqp5PLB15T9v88'
PRIVATE_CHAT_ID = '-1002184246668'
DISCORD_BOT_URL = 'https://3a49-185-9-186-241.ngrok-free.app/verify'

bot = telebot.TeleBot(API_TOKEN)

# Генерация случайного кода
def generate_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

# Проверка, находится ли пользователь в приватном чате
def is_user_in_private_chat(user_id):
    try:
        chat_member = bot.get_chat_member(PRIVATE_CHAT_ID, user_id)
        return chat_member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        print(f"Ошибка проверки пользователя в приватном чате: {e}")
        return False

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, " 🌵 Добро пожаловать в бота приватки cacto0o! \n \n 💫 Пропишите /link , чтобы всязать вас с вашим Discord аккаунтом\n \n \n 🛠 Поддержка - @faynotobglotish (Telegram) / faynot (Discord)")

@bot.message_handler(commands=['link'])
def ask_discord_username(message):
    bot.send_message(message.chat.id, " 🔧 Введите свой discord юзернейм:")

@bot.message_handler(func=lambda message: True)
def process_discord_username(message):
    user_id = message.from_user.id
    discord_username = message.text

    if is_user_in_private_chat(user_id):
        code = generate_code()
        bot.send_message(message.chat.id, f" 🤓 Твой код верификации, отправь его дискорд боту: {code} \n ЛС бота - VerifyToCacto0o#4557")

        # Отправка запроса на верификацию в Дискорд-бот
        response = requests.post(DISCORD_BOT_URL, json={'telegram_id': user_id, 'discord_username': discord_username, 'code': code})
        if response.status_code == 200:
            bot.send_message(message.chat.id, " ✨ Я отправил информацию о вас боту! Пожалуйста, напишите ему свой код.")
        else:
            bot.send_message(message.chat.id, f"Ошибка в верификации. Ошибка: {response.status_code}")
    else:
        bot.send_message(message.chat.id, " 😭 Вас нет в приватном чате.")

if __name__ == "__main__":
    bot.polling()