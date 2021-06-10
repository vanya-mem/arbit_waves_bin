import telebot
import time


TOKEN = '1707285125:AAHl8X_r-DCGnLoM1hyHt3TZYWZCft9JKm8'
TIME_SLEEP = 15
ARBITRAGE_MESSAGES = []

sol_array = []
waves_array = []
usdn_array = []
bot_spam = []

bot = telebot.TeleBot(TOKEN)


def get_logs():
    with open('solana_arbit_log.txt', 'r', encoding='utf8') as sol_file:
        for line in sol_file:
            sol_array.append(line)

    with open('arbit_log.txt', 'r', encoding='utf8') as waves_file:
        for line in waves_file:
            waves_array.append(line)

    with open('price_deflect.txt', 'r', encoding='utf8') as usdn_file:
        for line in usdn_file:
            usdn_array.append(line)


def start_arbitrage():
    get_logs()
    sol_len = len(sol_array)
    waves_len = len(waves_array)
    usdn_len = len(usdn_array)
    sol_array.clear()
    waves_array.clear()
    usdn_array.clear()
    while True:
        if '/stop' in bot_spam:
            break
        else:
            get_logs()
            if len(sol_array) > sol_len:
                sol_arbitrage_name = 'SOLANA ARBITRAGE'
                sol_arbit_mess = sol_arbitrage_name + '\n' '\n' + f'{str(sol_array[-1])}'
                ARBITRAGE_MESSAGES.append(sol_arbit_mess)
            elif len(waves_array) > waves_len:
                waves_arbitrage_name = 'WAVES ARBITRAGE'
                waves_arbit_mess = waves_arbitrage_name + '\n' + '\n' + f'{str(waves_array[-1])}'
                ARBITRAGE_MESSAGES.append(waves_arbit_mess)
            elif len(usdn_array) > usdn_len:
                usdn_arbitrage_name = 'USDN ARBITRAGE'
                usdn_arbit_mess = usdn_arbitrage_name + '\n' + '\n' + f'{str(usdn_array[-1])}'
                ARBITRAGE_MESSAGES.append(usdn_arbit_mess)

            if len(ARBITRAGE_MESSAGES) > 0:
                @bot.message_handler()
                def send_arbit_message(message):
                    for arbitrage_message in ARBITRAGE_MESSAGES:
                        bot.send_message(chat_id=message.from_user.id, text=arbitrage_message)
            sol_len, waves_len, usdn_len = len(sol_array), len(waves_array), len(usdn_array)
            sol_array.clear()
            waves_array.clear()
            usdn_array.clear()
            time.sleep(TIME_SLEEP)


@bot.message_handler(commands=['start'])
def start_conversation(message):
    first_mess = f'Привет, {message.from_user.first_name}! Выбери команду /go, чтобы начать ;)'
    bot.send_message(chat_id=message.from_user.id, text=first_mess)


@bot.message_handler(content_types=['text'])
def messages(message):
    new_message = message.text.strip().lower()

    if new_message == '/go':
        if len(bot_spam) > 2:
            bot_spam.clear()
            bot_spam.append(new_message)
        bot_spam.append(new_message)
        start_process_mess = ('Скрипт начал работу...' + '\n' + '\n' + 'Если вы хотите прекратить работу, то выберите' +
        ' ' + 'команду /stop')
        bot.send_message(chat_id=message.from_user.id, text=start_process_mess)
        start_arbitrage()

    elif new_message == '/stop':
        bot_spam.append(new_message)
        if len(ARBITRAGE_MESSAGES) > 0:
            for arbit_mess in ARBITRAGE_MESSAGES:
                bot.send_message(chat_id=message.from_user.id, text=arbit_mess)
        bot.send_message(chat_id=message.from_user.id, text='Скрипт прекратил свою работу...' + '\n' + '\n' +
        'Чтобы возобновить работу, выберите команду /go')


bot.polling(none_stop=True)












