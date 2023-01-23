import random
import time
from typing import List, Any
import requests
import json
from aiogram import Bot, Dispatcher, executor, types
from datetime import datetime
import asyncio

api_bot_token = 'your bot token'
bot = Bot(token=api_bot_token)
dp = Dispatcher(bot)

headers = {'PRIVATE-TOKEN': 'your gitlab autorization token'}

time_to_send_message = {
    '10:00',
    '12:00',
    '14:00',
    '16:00',
}

developers = {
    'gitlab developer username': '@user telegram name'
}

# One love =)
german_motivation = [
    'Fahr zur Hölle!',
    'Halt die Fotze!',
    'Leck mich am Arsch!',
    'Du gehst mir auf den Sack!',
    'Ein Scheißdreck werde ich tun!',
    'Verpiss dich!',
    'der Mistkerl!',
    'der Fotzenlecker!',
    'der Wichser!',
    'Alter Muschi!',
    'Ah du Schwein!',
    'Scheiß drauf!',
    'Mir ist es scheißegal!'
]

work_days = list(range(5))
approved_data: {'web_url': [{str: str}]} = {}
need_approve_data: {'web_url': [str]} = {}


def get_telegram_name(users_from_description: [str]) -> [str]:
    to_telegram_names: list[str] = []
    for user in users_from_description:
        to_telegram_names.append(developers[user.removeprefix('@')])

    return to_telegram_names


def get_not_in_draft_mrs() -> []:
    url = 'https://gitlab.com/api/v4/projects/your project number/merge_requests?state=opened'
    response = requests.get(url, headers=headers).text
    opened_merge_requests = json.loads(response)

    return filter(lambda item: item['draft'] is False, opened_merge_requests)


def load_mr_data():
    not_in_draft = get_not_in_draft_mrs()

    for mr in not_in_draft:
        iid = str(mr['iid'])
        web_url = str(mr['web_url'])

        url = 'https://gitlab.com/api/v4/projects/your project number/merge_requests/' + iid + '/approvals'
        get_approved_mrs = requests.get(url, headers=headers).text
        approved_mrs_dict = json.loads(get_approved_mrs)
        approved_developers = approved_mrs_dict['approved_by']

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
        for merge_request in approved_data:
            approved_developers = get_approved_developers(approved_data[merge_request])
            need_send_message_developers = list(set(need_approve_data[merge_request]) - set(approved_developers))
            web_url = str(merge_request)
            to_readable_view = ''

            for i in need_send_message_developers:
                to_readable_view += (i + ' ')

            motivation = random.choice(german_motivation) + ' 💅'
            new_message = to_readable_view + web_url + ' МР ждёт ревью' + ', ' + motivation
            await bot.send_message(message.from_user.id, new_message)

        await asyncio.sleep(60)
    else:
        await asyncio.sleep(60)


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply('🔪 Мать мр-ов в деле 💄\n✅ Ушла искать нарушителей 💅')
    while True:
        await send_message_if_needed(message)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
