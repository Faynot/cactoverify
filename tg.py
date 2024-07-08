import telebot
import random
import string
import requests
import json
import time
from telebot import types
from threading import Thread

API_TOKEN = '7350646532:AAGCJesf_S_s8sBwZEbTEFqp5PLB15T9v88'
CHANNEL_ID = '-1002198186948'
DISCORD_BOT_URL = 'https://f4bc-185-9-186-241.ngrok-free.app/verify'
DISCORD_REMOVE_USER_URL = 'https://f4bc-185-9-186-241.ngrok-free.app/remove_user'

bot = telebot.TeleBot(API_TOKEN)

# Загрузка данных о пользователях из файла JSON
try:
    with open('linked_users.json', 'r') as f:
        linked_users = json.load(f)
except FileNotFoundError:
    linked_users = {}

# Генерация случайного кода
def generate_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

# Сохранение данных о пользователях в файл JSON
def save_linked_users():
    with open('linked_users.json', 'w') as f:
        json.dump(linked_users, f, indent=4)

# Проверка, находится ли пользователь в канале
def is_user_in_channel(user_id):
    try:
        chat_member = bot.get_chat_member(CHANNEL_ID, user_id)
        if chat_member.status in ['member', 'administrator', 'creator']:
            return True
        else:
            print(f"Пользователь {user_id} не является участником канала.")
            return False
    except Exception as e:
        print(f"Ошибка проверки пользователя в канале: {e}")
        return False

# Функция для отправки запроса на верификацию в Discord
def send_verification_request_to_discord(user_id, discord_username, code):
    try:
        response = requests.post(DISCORD_BOT_URL, json={'telegram_id': user_id, 'discord_username': discord_username, 'code': code})
        if response.status_code == 200:
            print("HTTP запрос успешно отправлен в Discord бот.")
        else:
            print(f"Ошибка при отправке HTTP запроса в Discord бот. Код ошибки: {response.status_code}")
    except Exception as e:
        print(f"Ошибка при выполнении HTTP запроса в Discord бот: {e}")

# Функция для отправки уведомления об удалении пользователя в Discord
def send_user_removal_notification_to_discord(user_id, discord_username):
    try:
        response = requests.post(DISCORD_REMOVE_USER_URL, json={'telegram_id': user_id, 'discord_username': discord_username})
        if response.status_code == 200:
            print("HTTP запрос об удалении пользователя успешно отправлен в Discord бот.")
        else:
            print(f"Ошибка при отправке HTTP запроса об удалении пользователя в Discord бот. Код ошибки: {response.status_code}")
    except Exception as e:
        print(f"Ошибка при выполнении HTTP запроса об удалении пользователя в Discord бот: {e}")

# Функция для проверки пользователя и отправки запроса, если необходимо
def check_and_send_verification(user_id, discord_username):
    if is_user_in_channel(user_id):
        code = generate_code()
        bot.send_message(user_id, f"🤓 Твой код верификации: {code}.\nОтправь его боту в Discord: VerifyToCacto0o#4557.")

        linked_users[user_id] = {
            'discord_username': discord_username,
            'verification_code': code
        }
        save_linked_users()

        send_verification_request_to_discord(user_id, discord_username, code)
        bot.send_message(user_id, "✨ Информация отправлена боту в Discord.\nПожалуйста, введите свой код в Discord бота.")
    else:
        bot.send_message(user_id, "😭 Вас нет в канале. Невозможно выполнить верификацию.")

# Функция для проверки привязанных пользователей и отправки запроса на Discord в случае отсутствия
def check_linked_users():
    while True:
        for user_id in list(linked_users.keys()):
            if not is_user_in_channel(user_id):
                discord_username = linked_users[user_id]['discord_username']
                send_verification_request_to_discord(user_id, discord_username, "")
                # Удаление пользователя из списка, так как он не привязан к каналу
                del linked_users[user_id]
                save_linked_users()
                print(f"Пользователь {user_id} удален из списка привязанных пользователей.")
                send_user_removal_notification_to_discord(user_id, discord_username)
        time.sleep(5)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "🌵 Добро пожаловать в бота приватки cacto0o! Пропишите /link , чтобы связать ваш Telegram с вашим Discord аккаунтом.")

@bot.message_handler(commands=['link'])
def ask_discord_username(message):
    bot.send_message(message.chat.id, "🔧 Введите ваш Discord юзернейм:")

@bot.message_handler(func=lambda message: True)
def process_discord_username(message):
    user_id = message.from_user.id
    discord_username = message.text

    if is_user_in_channel(user_id):
        code = generate_code()
        bot.send_message(message.chat.id, f"🤓 Твой код верификации: {code}.\nОтправь его боту в Discord: VerifyToCacto0o#4557.")

        linked_users[user_id] = {
            'discord_username': discord_username,
            'verification_code': code
        }
        save_linked_users()

        response = requests.post(DISCORD_BOT_URL, json={'telegram_id': user_id, 'discord_username': discord_username, 'code': code})
        if response.status_code == 200:
            bot.send_message(message.chat.id, "✨ Информация отправлена боту в Discord.\nПожалуйста, введите свой код в Discord бота.")
        else:
            bot.send_message(message.chat.id, f"Ошибка верификации. Код ошибки: {response.status_code}")
    else:
        bot.send_message(message.chat.id, "😭 Вас нет в канале. Невозможно выполнить верификацию.")

if __name__ == "__main__":
    Thread(target=check_linked_users, daemon=True).start()
    bot.polling()
