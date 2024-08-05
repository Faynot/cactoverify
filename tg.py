import telebot
import random
import string
import requests
import sqlite3
import json
import time
from telebot import types
from threading import Thread

API_TOKEN = 'BOT_TOKEN'
CHANNEL_ID = 'ID'
DISCORD_BOT_URL = 'http://localhost:7070/verify'
DISCORD_REMOVE_USER_URL = 'http://localhost:7070/remove_user'
DISCORD_RETURN_USER_URL = 'http://localhost:7070/return_user'
ADMIN_USER_ID = user_id

bot = telebot.TeleBot(API_TOKEN)
maintenance_mode = False

# Initializing the Database
conn = sqlite3.connect('linked_users.db', check_same_thread=False)
cursor = conn.cursor()

# Creating a user table if it doesn't exist
cursor.execute('''
CREATE TABLE IF NOT EXISTS linked_users (
    user_id INTEGER PRIMARY KEY,
    discord_username TEXT,
    verification_code TEXT,
    in_channel INTEGER DEFAULT 1
)
''')
conn.commit()

# Loading data from JSON and transferring it to the database
def migrate_json_to_db():
    try:
        with open('linked_users.json', 'r') as f:
            json_data = json.load(f)
        for user_id, data in json_data.items():
            cursor.execute('''
                INSERT OR IGNORE INTO linked_users (user_id, discord_username, verification_code, in_channel)
                VALUES (?, ?, ?, ?)
            ''', (int(user_id), data['discord_username'], data['verification_code'], 1))
        conn.commit()
        print("Data from JSON was successfully transferred to the database.")
    except FileNotFoundError:
        print("JSON file not found. Skip data transfer.")
    except Exception as e:
        print(f"Error when transferring data from JSON to database: {e}")

# Perform data transfer on initialization
migrate_json_to_db()

# Генерация случайного кода
def generate_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

# Saving user data to the database
def save_linked_user(user_id, discord_username, code):
    cursor.execute('''
        INSERT OR REPLACE INTO linked_users (user_id, discord_username, verification_code, in_channel)
        VALUES (?, ?, ?, ?)
    ''', (user_id, discord_username, code, 1))
    conn.commit()

# Update user status in database
def update_user_status(user_id, in_channel):
    cursor.execute('''
        UPDATE linked_users SET in_channel = ? WHERE user_id = ?
    ''', (in_channel, user_id))
    conn.commit()

# Removing a user from the database
def delete_linked_user(user_id):
    cursor.execute('DELETE FROM linked_users WHERE user_id = ?', (user_id,))
    conn.commit()

# Check if the user is in the channel
def is_user_in_channel(user_id):
    try:
        chat_member = bot.get_chat_member(CHANNEL_ID, user_id)
        if chat_member.status in ['member', 'administrator', 'creator']:
            return True
        else:
            return False
    except Exception as e:
        print(f"user verification error in channel: {e}")
        return False

# Function for sending a verification request to Discord
def send_verification_request_to_discord(user_id, discord_username, code):
    try:
        response = requests.post(DISCORD_BOT_URL, json={'telegram_id': user_id, 'discord_username': discord_username, 'code': code})
        if response.status_code == 200:
            print("HTTP request successfully sent to Discord.")
        else:
            print(f"Error sending HTTP request to Discord bot. Error code {response.status_code}")
    except Exception as e:
        print(f"Error when making an HTTP request in Discord bot: {e}")

# Function to send notification of user deletion in Discord
def send_user_removal_notification_to_discord(user_id, discord_username):
    try:
        response = requests.post(DISCORD_REMOVE_USER_URL, json={'telegram_id': user_id, 'discord_username': discord_username})
        if response.status_code == 200:
            print("An HTTP request to delete a user was successfully sent to the Discord bot.")
        else:
            print(f"Error when sending an HTTP request to delete a user in a Discord bot. Error code: {response.status_code}")
    except Exception as e:
        print(f"Error when executing an HTTP request to delete a user in a Discord bot: {e}")

# Function to send a notification when a user returns to Discord
def send_user_return_notification_to_discord(user_id, discord_username):
    try:
        response = requests.post(DISCORD_RETURN_USER_URL, json={'telegram_id': user_id, 'discord_username': discord_username})
        if response.status_code == 200:
            print("HTTP request to return user successfully sent to Discord bot.")
        else:
            print(f"Error when sending an HTTP request to return a user to the Discord bot. Error code: {response.status_code}")
    except Exception as e:
        print(f"Error when making an HTTP request to return a user to a Discord bot: {e}")

# Function to verify the user and send a request if necessary
def check_and_send_verification(user_id, discord_username):
    if is_user_in_channel(user_id):
        code = generate_code()
        bot.send_message(user_id, f"🤓 Your verification code: {code}.\nSend it to the bot on Discord: YOURE_BOT#0000.")

        save_linked_user(user_id, discord_username, code)

        send_verification_request_to_discord(user_id, discord_username, code)
        bot.send_message(user_id, "✨ Information has been sent to the bot in Discord.\nPlease enter your code in the bot's Discord.")
    else:
        bot.send_message(user_id, "😭 You are not in the channel. Unable to verify.")

# Function to check linked users and update their status
def check_linked_users():
    while True:
        cursor.execute('SELECT user_id, discord_username, in_channel FROM linked_users')
        linked_users = cursor.fetchall()
        for user_id, discord_username, in_channel in linked_users:
            if is_user_in_channel(user_id):
                if in_channel == 0:
                    update_user_status(user_id, 1)
                    send_user_return_notification_to_discord(user_id, discord_username)
                    print(f"User {user_id} (Discord: {discord_username}) is back in the channel.")
            else:
                if in_channel == 1:
                    update_user_status(user_id, 0)
                    send_user_removal_notification_to_discord(user_id, discord_username)
                    print(f"User {user_id} (Discord: {discord_username}) is no longer in the channel, a Discord notification has been sent.")
        time.sleep(5)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    if maintenance_mode and message.from_user.id != ADMIN_USER_ID:
        bot.reply_to(message, "Sorry, maintenance is currently underway.")
        return
    bot.reply_to(message, "🌵 Welcome to the verification bot! Type /link to link your Telegram with your Discord account.")

@bot.message_handler(commands=['link'])
def ask_discord_username(message):
    if maintenance_mode and message.from_user.id != ADMIN_USER_ID:
        bot.send_message(message.chat.id, "Sorry, maintenance is currently underway.")
        return
    bot.send_message(message.chat.id, "🔧 Enter your Discord username:")

@bot.message_handler(commands=['techon'])
def enable_maintenance(message):
    global maintenance_mode
    if message.from_user.id == ADMIN_USER_ID:
        maintenance_mode = True
        bot.send_message(message.chat.id, "Maintenance enabled.")

@bot.message_handler(commands=['techoff'])
def disable_maintenance(message):
    global maintenance_mode
    if message.from_user.id == ADMIN_USER_ID:
        maintenance_mode = False
        bot.send_message(message.chat.id, "Maintenance disabled.")

@bot.message_handler(commands=['adduser'])
def add_user(message):
    if message.from_user.id == ADMIN_USER_ID:
        try:
            command, user_id, discord_username = message.text.split(maxsplit=2)
            user_id = int(user_id)
            code = generate_code()
            save_linked_user(user_id, discord_username, code)
            bot.send_message(message.chat.id, f"A user with ID {user_id} and username {discord_username} has been added to the database.")
        except ValueError:
            bot.send_message(message.chat.id, "⚠️ Invalid command format. Use /adduser <user_id> <discord_username>.")
    else:
        bot.send_message(message.chat.id, "⚠️ You do not have permission to run this command.")

@bot.message_handler(func=lambda message: True)
def process_discord_username(message):
    if maintenance_mode and message.from_user.id != ADMIN_USER_ID:
        bot.send_message(message.chat.id, "Sorry, maintenance is currently underway.")
        return
    user_id = message.from_user.id
    discord_username = message.text

    if is_user_in_channel(user_id):
        code = generate_code()
        bot.send_message(message.chat.id, f"🤓 Your verification code: {code}.\nSend it to the bot in Discord: YOURE_BOT#0000.")

        save_linked_user(user_id, discord_username, code)

        response = requests.post(DISCORD_BOT_URL, json={'telegram_id': user_id, 'discord_username': discord_username, 'code': code})
        if response.status_code == 200:
            bot.send_message(message.chat.id, "✨ Information sent to the bot in Discord.\nPlease enter your code in the bot's Discord.")
        else:
            bot.send_message(message.chat.id, "⚠️ Error when sending data to the bot in Discord.")
    else:
        bot.send_message(message.chat.id, "😭 You are not in the channel. Unable to verify.")

# Run user verification in a separate thread
Thread(target=check_linked_users).start()
bot.polling(none_stop=True)
