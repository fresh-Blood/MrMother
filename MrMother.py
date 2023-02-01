import random
import requests
import json
import asyncio
from aiogram import Bot, Dispatcher, executor, types
from datetime import datetime
from aiogram.utils.exceptions import BotBlocked
from aiogram.utils.exceptions import BadRequest
from typing import Any

api_bot_token = 'YOUR_TELEGRAM_BOT_TOKEN'
bot = Bot(token=api_bot_token)
dp = Dispatcher(bot)

headers = {'PRIVATE-TOKEN': 'YOUR_GITLAB_PRIVATE_TOKEN'}

# Set time to get message to your team chat
time_to_send_message = {
    '10:00',
    '13:00',
    '16:00'
}

# Set developers names
developers = {
    'gitlab_nickname': '@telegram_nickname',
}

# Set bot start messages
start_messages = [
    'Как прикажете',
    'Уже ушла',
    'Мать мр-в в деле',
    'Нормально же общались',
    'Хотела денег попросить, но приказали идти работать',
    'Слушаюсь',
    'Как раз получила чёрный пояс по карате',
    'Повинуюсь',
    'Wie sie befohlen haben',
    'Schon weg',
    'Mr-ins Mutter in aktion',
    'Wir haben normal kommuniziert',
    'Ich wollte geld bitten, aber sie befahlen mir, zur arbeit zu gehen',
    'Ich höre',
    "Habe gerade einen schwarzen gürtel im karate bekommen",
    'Ich gehorche',
    'Euer wort ist gesetz, mylord',
    'Endlich arbeiten',
    'Die Rakete ist weg!',
    'После 20 лет в шахтах с углём это - проще простого',
    'После взлома сервера пентагона это кажется лёгкой прогулкой'
]

# If no merge requests to approve, this is Mayakovsky's perfect spell to send 
mayakovskiy = 'Magst du Rosen?\nIch scheiß drauf!\nDas Land braucht Lokomotiven,\nwir brauchen ' \
              'Metall!\nGenosse!\nStöhne nicht,' \
              '\nNicht keuchen!\nZieh nicht am Zaum!\nWenn du den Plan abgeschlossen hast,\nschick alle zu ' \
              '\nf*ck\nhabe ihn nicht abgeschlossen - \nf*ck dich selbst.'

# Set workdays number 
work_days = list(range(7))
approved_data: {str: [{str: str}]} = {}
need_approve_data: {str: [str]} = {}


def get_telegram_name(users_from_description: [str]) -> [str]:
    to_telegram_names: list[str] = []
    for user in users_from_description:
        to_telegram_names.append(developers[user.removeprefix('@')])

    return to_telegram_names


def get_not_in_draft_mrs() -> []:
    url = 'https://gitlab.com/api/v4/projects/YOUR_PROJECT_GIRLAB_NUMBER/merge_requests?state=opened'
    response = requests.get(url, headers=headers).text
    opened_merge_requests = json.loads(response)

    return filter(lambda item: item['draft'] is False, opened_merge_requests)


def clear_data():
    need_approve_data.clear()
    approved_data.clear()


def load_mr_data():
    not_in_draft = get_not_in_draft_mrs()

    for mr in not_in_draft:
        iid = str(mr['iid'])
        web_url = str(mr['web_url'])

        url = 'https://gitlab.com/api/v4/projects/YOUR_PROJECT_GIRLAB_NUMBER/merge_requests/' + iid + '/approvals'
        get_approved_mrs = requests.get(url, headers=headers).text
        approved_mrs_dict = json.loads(get_approved_mrs)
        approved_developers = approved_mrs_dict['approved_by']

        # Set needed approves number 
        if len(approved_developers) < 3:
            mr_data = {web_url: approved_developers}

            assignee = str((mr['assignee'])['username'])
            users_from_description_str = str(mr['description'])
            users_from_description_with_task = users_from_description_str.split()
            users_from_description_filtered = filter(lambda word: '@' in word, users_from_description_with_task)
            users_from_description = list(users_from_description_filtered)

            to_telegram_names = get_telegram_name(users_from_description)

            to_telegram_names.append(developers[assignee])
            need_approve_developers = {web_url: to_telegram_names}

            need_approve_data.update(need_approve_developers)
            approved_data.update(mr_data)


def get_approved_developers(all_developers: Any) -> []:
    approved_developers = []
    for user in all_developers:
        current_user = user['user']
        username = current_user['username']
        approved_developers.append(developers[username])

    return approved_developers


async def send_message_if_needed(message: types.Message):
    now = datetime.now()
    weekday = now.weekday()
    current_time = now.strftime('%H:%M')

    if weekday in work_days and current_time in time_to_send_message:
        load_mr_data()
        common_message = ''

        for merge_request in approved_data:
            approved_developers = get_approved_developers(approved_data[merge_request])
            need_send_message_developers = list(set(need_approve_data[merge_request]) - set(approved_developers))
            web_url = str(merge_request)
            developers_str = ''

            for i in need_send_message_developers:
                developers_str += ('👨‍💻 ' + i + '\n')

            common_message += ('{0}\n➡️ {1}\n\n\n'.format(developers_str[: -1], web_url))

            # Complete message  
        if len(common_message) != 0:
            new_message = common_message + '👮🏻 МР-ы ждут ревью 🚔'
            print('---> I am ok, message successfully sent: ' + current_time)
        else:
            # Or if nothing to sent, send Spell, also print in Windows cmd line for debugging and bot state monitoring
            thoughts = 'С мр-ами порядок 💅, и я вдруг вспомнила:\n\n' + mayakovskiy
            new_message = thoughts
            print('---> I am ok, Mayakovskiy successfully sent: ' + current_time)

        clear_data()
        await bot.send_message(message.chat.id, new_message, disable_web_page_preview=True)
        await asyncio.sleep(60)
    else:
        # If not time and not day to sent message, just sleep for another 60 sec check 
        print('---> I am ok, having 60 seconds rest: ' + current_time)
        await asyncio.sleep(60)


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply(random.choice(start_messages) + ' 💁🏻‍♀️')
    while True:
        try:
            await send_message_if_needed(message)
            # Handle possible errors
        except BotBlocked as error:
            print('!!! BotBlocked error: ' + error.text)
            pass
        except BadRequest as error:
            print('!!! BadRequest error: ' + error.text)
            pass


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
