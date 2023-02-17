import bs4
from dotenv import load_dotenv
import os

import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, ConversationHandler, MessageHandler, filters
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes
from re import match
from urllib.parse import quote
import urllib.request
from html_table_parser.parser import HTMLTableParser
import datetime
import pytz

from bs4 import BeautifulSoup
import requests

import platform

platform.python_version()

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

global a, s, schdl2, url, dt_current, names_dict, studying_days, groups, urls_dict, btn_lable

# Клавиатура
reply_keyboard = [["Расписание на сегодня", "Выбрать день", 'Выбрать группу/изменить'], ['Регистрация']]
markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)

url = 'https://online.i-klgtu.ru/fulltime/current/10/' + quote(f'20-ИЭ-2.html')

names_dict = {}
studying_days = []
dt_current = []
groups = []

CHOOSING, CHOOSEINST, CHOOSEGROUPE, LAST_STEP = range(4)


def groupe_chooser():  # функция выбора группы типа как парсер работает
    global a, s, schdl2, url, dt_current, names_dict, studying_days, groups, urls_dict
    murl = "https://i-klgtu.ru/current/"
    html_content = requests.get(murl).text
    soup = BeautifulSoup(html_content, "html5lib")

    for link in soup.find_all("h4"):
        groups.append(format(link.text))

    MAIN_LIST = []
    for i in groups:
        list_words = i.split()

        final_acro = ""
        for i in list_words:
            final_acro += i[0].upper()
        MAIN_LIST.append(final_acro)

    groups = MAIN_LIST[:-2]

    # for el in range(len(groups))
    values_of_urls = list(range(10, len(groups) * 10 + 10, 10))
    urls_dict = dict(zip(groups, values_of_urls))


def pacer():  # Функция собирающая данные с расписания
    global a, s, schdl2, url, dt_current, names_dict, studying_days, groups
    names_dict = {}
    req = urllib.request.Request(url=url)
    f = urllib.request.urlopen(req)
    xhtml = f.read().decode('utf-8')
    p = HTMLTableParser()
    p.feed(xhtml)
    s = (p.tables[0])

    # print(s)

    def search_matrix(matrix, word):
        for i, row in enumerate(matrix):
            for j, text in enumerate(row):
                z = text.find(word)
                if z == -1:
                    continue
                return i, j, z
        return -1, -1, -1

    a = search_matrix(s, dt_current)
    b = [a for b in s for a in b]
    studying_days = list(filter(lambda v: match('\d\d\.\d\d\.\d{4}', v), b))
    # print('Это Б', studying_days)
    # Проверка на воскресенье
    if a != (-1, -1, -1):
        schdl = [i for i in s[int(a[0]):int(a[0]) + 12]]
        schdl2 = schdl[::2]
        count = 0
        firsts = [x[1] + ' ' + x[2] + ' ауд.' for x in schdl2]
        firsts[0] = schdl2[0][2] + ' ' + schdl2[0][3] + ' ауд.'

        names_dict = {}
        for i, name in enumerate(firsts, 1):
            names_dict[i] = name

        names_dict = {key: val for key, val in names_dict.items() if val != '  ауд.'}
        for i in range(len(firsts)):
            if firsts[i] == '':
                count += 1


def btn_lst():
    global a, s, schdl2, url, dt_current, names_dict, studying_days, groups, urls_dict, new_url, btn_lable

    res = requests.get(f"{new_url}")
    soup = bs4.BeautifulSoup(res.text, 'html5lib')
    btn_lable = []
    for link in soup.find_all("a"):
        btn_lable.append(format(link.text))

    btn_lable = btn_lable[1:]


def build_menu(buttons, n_cols, header_buttons=None, footer_buttons=None):
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)
    return menu


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global a, s, schdl2, url, answer, dt_current, names_dict, studying_days

    await update.message.reply_text("Hello", reply_markup=markup)
    return CHOOSING


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global a, s, schdl2, url, dt_current, names_dict, studying_days

    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query
    dt_current = query.data[0:10]
    pacer()

    await query.answer()
    if names_dict:
        await query.edit_message_text(text=f"Расписание на: {query.data}" + '\n\n' + '\n'.join(
            "{}. {}".format(k, v) for k, v in names_dict.items()))
    else:
        await query.edit_message_text(text=f"В этот день пар нет")


async def choose_schedule(update: Update,
                          context: ContextTypes.DEFAULT_TYPE):  # Функция выбора расписания на текущих неделях
    global a, s, schdl2, url, dt_current, names_dict, studying_days

    tz_klgd = pytz.timezone("Europe/Kaliningrad")
    dt_obj = datetime.datetime.now(tz_klgd)
    dt_current = dt_obj.strftime("%d.%m.%Y")
    pacer()
    button_list = []
    for each in studying_days:
        button_list.append(InlineKeyboardButton(each, callback_data=each))
    reply_markup = InlineKeyboardMarkup(
        build_menu(button_list, n_cols=2))  # n_cols = 1 is for single column and mutliple rows

    await update.message.reply_text("Please choose:", reply_markup=reply_markup)


async def schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):  # Функция расписания на текущий день
    global a, s, schdl2, url, dt_current, names_dict, studying_days

    tz_klgd = pytz.timezone("Europe/Kaliningrad")
    dt_obj = datetime.datetime.now(tz_klgd)
    dt_current = dt_obj.strftime("%d.%m.%Y")
    pacer()

    if names_dict:
        await update.message.reply_text(text=f"Расписание на:" + '\n\n' + '\n'.join(
            "{}. {}".format(k, v) for k, v in names_dict.items()))
    else:
        await update.message.reply_text(text=f"Сегодня пар нет")


async def choose_group(update: Update, context: ContextTypes.DEFAULT_TYPE):  # Функция выбора группы
    global a, s, schdl2, url, dt_current, names_dict, studying_days, groups

    groupe_chooser()
    button_list = []
    for eachs in groups:
        button_list.append(InlineKeyboardButton(eachs, callback_data=eachs))
    reply_markup = InlineKeyboardMarkup(
        build_menu(button_list, n_cols=1))  # n_cols = 1 is for single column and mutliple rows
    groups = []
    await update.message.reply_text("Выберете группу:", reply_markup=reply_markup)

    return CHOOSEINST


async def registration(update: Update, context: ContextTypes.DEFAULT_TYPE):  # Функция выбора группы
    global a, s, schdl2, url, dt_current, names_dict, studying_days, groups, urls_dict

    groupe_chooser()
    button_list = []
    for eachs in groups:
        button_list.append(InlineKeyboardButton(eachs, callback_data=eachs))
    reply_markup = InlineKeyboardMarkup(
        build_menu(button_list, n_cols=1))  # n_cols = 1 is for single column and mutliple rows
    groups = []

    await update.message.reply_text(
        "Здравствуйте, первичная регистрация занесёт вас в базу пользователей.\n\nВыберете свой институт:",
        reply_markup=reply_markup)

    return CHOOSEINST


async def inst_maker(update: Update, context: ContextTypes.DEFAULT_TYPE):  # Функция выбора группы
    global a, s, schdl2, url, dt_current, names_dict, studying_days, groups, urls_dict, new_url, btn_lable

    query = update.callback_query
    new_url = 'http://online.i-klgtu.ru/fulltime/current/' + quote(f'{urls_dict[query.data]}')

    # print(new_url)
    btn_lst()
    button_list = []
    for eachs in btn_lable:
        button_list.append(InlineKeyboardButton(eachs, callback_data=eachs))
    reply_markup = InlineKeyboardMarkup(
        build_menu(button_list, n_cols=4))  # n_cols = 1 is for single column and mutliple rows
    await query.edit_message_text(
        text="Выберите группу", reply_markup=reply_markup
    )
    return CHOOSEGROUPE


async def groupe_maker(update: Update, context: ContextTypes.DEFAULT_TYPE):  # Функция выбора группы
    global a, s, schdl2, url, dt_current, names_dict, studying_days, groups, urls_dict, new_url, btn_lable
    query = update.callback_query
    last_url = new_url + '/' + quote(f'{query.data}') + '.html'

    req = urllib.request.Request(url=last_url)
    f = urllib.request.urlopen(req)
    xhtml = f.read().decode('utf-8')
    p = HTMLTableParser()
    p.feed(xhtml)
    s = (p.tables[0])
    last_btn = []

    if s[7][2]:
        last_btn.extend((s[7][2], s[7][4]))
        button_list = []
        for eachs in last_btn:
            button_list.append(InlineKeyboardButton(eachs, callback_data=eachs))
        reply_markup = InlineKeyboardMarkup(
            build_menu(button_list, n_cols=4))  # n_cols = 1 is for single column and mutliple rows
        await query.edit_message_text(
            text="Выберите подгруппу", reply_markup=reply_markup
        )
    else:
        chat_id = query.message.chat_id
        print(chat_id)
        await query.edit_message_text(
            text="Группа установлена")
        return CHOOSING

    return LAST_STEP


async def last_step(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:  # Функция выбора группы
    global a, s, schdl2, url, dt_current, names_dict, studying_days, groups, urls_dict, new_url, btn_lable

    query = update.callback_query

    chat_id = query.message.chat_id
    print(chat_id)

    await query.edit_message_text(
        text="Группа установлена")

    return CHOOSING


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Привет, нужна помощь?")


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    await update.message.reply_text(
        "Bye! I hope we can talk again some day."
    )

    return ConversationHandler.END


if __name__ == '__main__':
    application = ApplicationBuilder().token(os.getenv('TOKEN')).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING: [MessageHandler(filters.Regex("^(Выбрать день)$"), choose_schedule),
                       CallbackQueryHandler(button),
                       MessageHandler(filters.Regex("^(Выбрать группу/изменить)$"), choose_group),
                       MessageHandler(filters.Regex("^(Расписание на сегодня)$"), schedule),
                       MessageHandler(filters.Regex("^(Регистрация)$"), registration)],

            CHOOSEINST: [CallbackQueryHandler(inst_maker)],
            CHOOSEGROUPE: [CallbackQueryHandler(groupe_maker)],
            LAST_STEP: [CallbackQueryHandler(last_step)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler('start', start))
    # application.add_handler(CallbackQueryHandler(reg_button))
    application.add_handler(CommandHandler('help', help))
    application.run_polling()
