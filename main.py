#!/usr/bin/python3.5
# -*- coding: utf-8 -*-

import telebot
from aiohttp import web
from telebot import types

import dbconn
import google_credentials
import my_conn

gg = google_credentials.GgCredits()
conn = my_conn.MyConn()


# Process webhook calls
async def handle(request):
    if request.match_info.get('token') == conn.bot.token:
        request_body_dict = await request.json()
        update = telebot.types.Update.de_json(request_body_dict)
        conn.bot.process_new_updates([update])
        return web.Response()
    else:
        return web.Response(status=403)

conn.app.router.add_post('/{token}/', handle)


# Frequently repeatable keyboard
def keyboards():
    user_markup = telebot.types.ReplyKeyboardMarkup(True, True)
    user_markup.row('Balance')
    user_markup.row('Store')
    user_markup.row('Settings'u'\U00002699', 'Help')
    return user_markup


# Frequently repeatable back button
def keyboard_back_button():
    user_markup = telebot.types.ReplyKeyboardMarkup(True, True)
    user_markup.row('Back')
    return user_markup


KEYBOARD = keyboards()
BACK_BUTTON = keyboard_back_button()


# First command which user can send to telegram bot
@conn.bot.message_handler(commands=['start'])
def handle_start(message):
    # Checks if user is new or in our db
    uid = message.from_user.id
    db = dbconn.PGadmin()
    telegram_id = db.select_single('*', 'users', 'telegram_id={0}'.format(uid))
    db.close()
    if telegram_id is not None:
        reg_key = telegram_id[3]
    else:
        reg_key = 1
        conn.bot.send_message(uid, 'Welcome to MyKPI_bot, TeamScore clone! \nSign up, please!')
    if reg_key == 1:
        # If user is new
        keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        button_contact = types.KeyboardButton(text="Sign up", request_contact=False)
        keyboard.add(button_contact)
        conn.bot.send_message(uid,
                              'NOTE! You should have a @username (Settings ---> Edit Profile). '
                              'Also, in case you use a VPN/Proxy-conection, registration may fail! '
                              'After registration you may use VPN/Proxy unhindered',
                              reply_markup=keyboard)
    else:
        conn.bot.send_message(uid, 'You are at the main menu.', reply_markup=KEYBOARD)


# if it is necessary you can delete all your data from db
@conn.bot.message_handler(commands=['kill'])
def handle_new_chat(message):
    uid = message.from_user.id
    inline_keyboard = types.InlineKeyboardMarkup()
    kill = types.InlineKeyboardButton(text='Yes', callback_data=' kill')
    inline_keyboard.add(kill)
    
    conn.bot.send_message(uid, 'This command will delete all your data.', reply_markup=KEYBOARD)
    conn.bot.send_message(uid, 'Are you sure?', reply_markup=inline_keyboard)


# Manager must register bot in chat if we want our users not to cheat
# Otherwise user can create chat, add bot and reward yourself with another account.
@conn.bot.message_handler(commands=['new'])
def handle_new_chat(message):
    uid = message.from_user.id
    user_name = '@' + message.from_user.username.lower()
    db = dbconn.PGadmin()
    manager = db.select_single('*', 'managers', "user_name='{0}'".format(user_name))
    chat = db.select_single('*', 'chats', "user_name='{0}'".format(user_name))
    chat2 = db.select_single('*', 'chats', 'chat_id={0}'.format(message.chat.id))
    man = db.select_single('*', 'users', 'telegram_id={0}'.format(uid))
    db.close()
    if message.chat.id == uid:
        conn.bot.send_message(uid, "ERROR: You are in bot interface. You can't register bot in the bot.")
    else:
        if chat is None or chat2 is None:
            if manager is None:
                conn.bot.send_message(uid,
                                      'ERROR: Sorry! But you are not in the list of managers or bot is not paid yet. '
                                      'Please, contact us: @Max_Urzhumtsev')
            elif manager[0].lower() == user_name.lower():
                db = dbconn.PGadmin()
                db.insert('chats (telegram_id,user_name,chat_id,company)', (uid,
                                                                            user_name,
                                                                            message.chat.id,
                                                                            man[6]))
                db.close()
                conn.bot.send_message(uid, 'Thank you! Bot is registered in this chat now')
            else:
                conn.bot.send_message(uid,
                                      'ERROR: Sorry! But you are not in the list of managers or bot is not paid yet. '
                                      'Please, contact us: @Max_Urzhumtsev')
        else:
            conn.bot.send_message(uid, 'ERROR: Bot is already registered in this chat.')


@conn.bot.message_handler(commands=['reward', 'penalty'])
def handle_com(message):
    uid = message.from_user.id
    # Trying to figure out if user want to reward/penalty: yourself, in bot interface or in chat.
    # We will use this data also in insertion of operation.
    db = dbconn.PGadmin()
    yourself = db.select_single('*', 'users', 'telegram_id={0}'.format(uid))
    chat = db.select_single('*', 'chats', 'chat_id={}'.format(message.chat.id))
    db.close()
    if chat is None:
        if message.chat.id == uid:
            conn.bot.send_message(uid,
                                  "Please reward/penalty in group chats, not in bot interface, "
                                  "so the Team could see your decisions.")
        else:
            conn.bot.send_message(message.chat.id,
                                  "Bot is not registered in this chat. "
                                  "If you are manager and bot is paid, please, push /new to register it. "
                                  "Else you will get an ERROR.")
    elif chat[2] == message.chat.id:
        # Split message into components
        data_to_split = format(message.text)
        data_for_add = data_to_split.split(' ')
        reason_len = len(data_for_add)
        reason1 = data_for_add[3:reason_len]
        reason_finish1 = ' '.join(reason1)
        # Finding the user to reward/penalty from message
        db = dbconn.PGadmin()
        user = db.select_single('*',
                                'users',
                                "user_name='{}'".format(data_for_add[1].lower()))
        db.close()
        quantity = data_for_add[2].isdigit()
        # Define if the user allowed to be rewarded in chat
        status = conn.bot.get_chat_member(chat_id=message.chat.id, user_id=user[1])
        if user is None:
            conn.bot.send_message(message.chat.id, "Invalid username")
            return 0
        if data_for_add[1].lower() == yourself[5]:
            conn.bot.send_message(uid, "You can't reward yourself")
            return 0
        if data_for_add[2] == '':
            conn.bot.send_message(message.chat.id, "Too much spaces between @username and quantity. Should be only one.")
            return 0
        if quantity is False:
            conn.bot.send_message(message.chat.id, "Unknown quantity: " + data_for_add[2])
            return 0
        if reason_len <= 3:
            conn.bot.send_message(message.chat.id, "Please specify the reason.")
            return 0
        if status.status == 'restricted' or status.status == 'left' or status.status == 'kicked':
            conn.bot.send_message(message.chat.id, "Invalid username for this chat")
            return 0
        else:
            if data_for_add[0] == '/reward':
                db = dbconn.PGadmin()
                db.update('users',
                          'sum=sum +{}'.format(data_for_add[2]),
                          "user_name='{}'".format(data_for_add[1].lower()))
                conn.bot.send_message(uid,
                                      'You rewarded '
                                      + data_for_add[1]
                                      + ' quantity: '
                                      + data_for_add[2]
                                      + ' reason: '
                                      + reason_finish1)
            elif data_for_add[0] == '/penalty':
                db = dbconn.PGadmin()
                db.update('users',
                          'sum=sum -{}'.format(data_for_add[2].lower()),
                          "user_name='{}'".format(data_for_add[1].lower()))
                conn.bot.send_message(uid,
                                      'You are fined '
                                      + data_for_add[1]
                                      + ' quantity: '
                                      + data_for_add[2]
                                      + ' reason: '
                                      + reason_finish1)
            # Insertion to the history of operations
            cur_date = db.select('CURRENT_DATE')
            db.insert('operations (who,to_whom,date,command,sum,reason,company)',
                      (yourself[5],
                       data_for_add[1].lower(),
                       format(cur_date[0]),
                       data_for_add[0],
                       data_for_add[2],
                       reason_finish1,
                       yourself[6]))
            db.close()


@conn.bot.message_handler(commands=['rewardteam'])
def handle_com_team(message):
    global data_to_add_finish, reason_finish
    uid = message.from_user.id
    db = dbconn.PGadmin()
    chat = db.select_single('*', 'chats', 'chat_id={}'.format(message.chat.id))
    db.close()
    if chat is None:
        conn.bot.send_message(message.chat.id, "Bot is not registered in this chat. "
                                               "If you are manager and bot is paid, please, push /new to register it. "
                                               "Else you will get an ERROR.")
    else:
        if message.chat.id == uid:
            conn.bot.send_message(uid, "Please reward/penalty in group chats, not in bot interface, "
                                       "so the Team could see your decisions.")
        else:
            db = dbconn.PGadmin()
            manager = db.select_single('*', 'users', 'telegram_id={0}'.format(uid))  # Двойная фунция. 1 определение на менеджера 2 определение компании
            chat_members = db.select_all1('*', 'users', "company='{0}'".format(manager[6]))
            db.close()
            status = conn.bot.get_chat_member(chat_id=message.chat.id, user_id=uid)
            if manager[9] == 1 and status.status == 'creator' or manager[9] == 1 and status.status == 'administrator':
                for c in range(len(chat_members)):
                    status = conn.bot.get_chat_member(chat_id=message.chat.id, user_id=chat_members[c][1])
                    if status.status == 'member':
                        if chat_members[c][9] == 1:
                            db = dbconn.PGadmin()
                            db.update('users', 'quantity=quantity-{}'.format(1), 'telegram_id={}'.format(uid))
                            db.close()
                        else:
                            db = dbconn.PGadmin()
                            db.update('users', 'quantity=quantity+{}'.format(1), 'telegram_id={}'.format(uid))
                            db.close()
                    else:
                        continue
                db = dbconn.PGadmin()
                count = db.select_single('*', 'users', 'telegram_id={}'.format(uid))
                db.close()
                if count[10] <= 1:
                    conn.bot.send_message(uid,
                                          'ERROR: Less than 2 members (except managers) '
                                          'in this group chat or all members are administrators.')
                    db = dbconn.PGadmin()
                    db.update('users', 'quantity=0', 'telegram_id={}'.format(uid))
                    db.close()
                    return
                else:
                    count = count[10]
                for i in range(len(chat_members)):
                    status = conn.bot.get_chat_member(chat_id=message.chat.id, user_id=chat_members[i][1])
                    if status.status == 'member' or status.status == 'creator' or status.status == 'administrator':
                        if chat_members[i][9] == 1:
                            x = 0
                            print(x)
                        else:
                            data_to_split = format(message.text)
                            data_for_add = data_to_split.split(' ')
                            is_digit = data_for_add[1].isdigit()
                            if is_digit is True:
                                data_to_add_finish = int(data_for_add[1]) // count
                                reason_len = len(data_for_add)
                                if reason_len <= 2:
                                    db = dbconn.PGadmin()
                                    db.update('users', 'quantity=0', 'telegram_id={}'.format(uid))
                                    db.close()
                                    conn.bot.send_message(message.chat.id, "Please specify the reason.")
                                    return None
                                else:
                                    reason1 = data_for_add[2:reason_len]
                                    reason_finish = ' '.join(reason1)
                                    db = dbconn.PGadmin()
                                    cur_date = db.select('CURRENT_DATE')
                                    db.update('users',
                                              'sum=sum +{}'.format(data_to_add_finish),
                                              "user_name='{}'".format(chat_members[i][5]))
                                    db.insert('operations (who,to_whom,date,command,sum,reason,company)', (manager[5],
                                                                                                           chat_members[i][5],
                                                                                                           format(cur_date[0]),
                                                                                                           data_for_add[0],
                                                                                                           data_to_add_finish,
                                                                                                           reason_finish,
                                                                                                           manager[6]))
                                    db.update('users', 'quantity=0', 'telegram_id={}'.format(uid))
                                    db.close()
                            else:
                                db = dbconn.PGadmin()
                                db.update('users', 'quantity=0', 'telegram_id={}'.format(uid))
                                db.close()
                                conn.bot.send_message(message.chat.id, "Undefined quantity: " + data_for_add[1])
                                return None
                    else:
                        i = 0
                        print(i)
                conn.bot.send_message(uid,
                                      'You rewarded team. Chat: '
                                      + message.chat.title
                                      + '\nquantity (each): '
                                      + str(data_to_add_finish)
                                      + '\nReason: '
                                      + reason_finish)
            else:
                conn.bot.send_message(uid, 'ERROR: You are not a manager of this group chat.'
                                           ' \nPS.: Manager must have admin rights in group chat for rewarding team.')


@conn.bot.message_handler(commands=['penaltyteam'])
def handle_com_team(message):
    global data_to_add_finish, reason_finish
    uid = message.from_user.id
    db = dbconn.PGadmin()
    chat = db.select_single('*', 'chats', 'chat_id={}'.format(message.chat.id))
    db.close()
    if chat is None:
        conn.bot.send_message(message.chat.id, "Bot is not registered in this chat. "
                                               "If you are manager and bot is paid, please, push /new to register it. "
                                               "Else you will get an ERROR.")
    else:
        if message.chat.id == uid:
            conn.bot.send_message(uid,
                                  "Please reward/penalty in group chats, "
                                  "not in bot interface, "
                                  "so the Team could see your decisions.")
        else:
            db = dbconn.PGadmin()
            manager = db.select_single('*', 'users', 'telegram_id={0}'.format(uid))  # Двойная фунция. 1 определение на менеджера 2 определение компании
            chat_members = db.select_all1('*', 'users', "company='{0}'".format(manager[6]))
            db.close()
            status = conn.bot.get_chat_member(chat_id=message.chat.id, user_id=uid)
            if manager[9] == 1 and status.status == 'creator' or manager[9] == 1 and status.status == 'administrator':
                for c in range(len(chat_members)):
                    status = conn.bot.get_chat_member(chat_id=message.chat.id, user_id=chat_members[c][1])
                    if status.status == 'member':
                        if chat_members[c][9] == 1:
                            db = dbconn.PGadmin()
                            db.update('users', 'quantity=quantity-{}'.format(1), 'telegram_id={}'.format(uid))
                            db.close()
                        else:
                            db = dbconn.PGadmin()
                            db.update('users', 'quantity=quantity+{}'.format(1), 'telegram_id={}'.format(uid))
                            db.close()
                    else:
                        continue
                db = dbconn.PGadmin()
                count = db.select_single('*', 'users', 'telegram_id={}'.format(uid))
                db.close()
                if count[10] <= 1:
                    conn.bot.send_message(uid,
                                          'ERROR: Less than 2 members (except managers) '
                                          'in this group chat or all members are administrators.')
                    db = dbconn.PGadmin()
                    db.update('users', 'quantity=0', 'telegram_id={}'.format(uid))
                    db.close()
                    return
                else:
                    count = count[10]
                for i in range(len(chat_members)):
                    status = conn.bot.get_chat_member(chat_id=message.chat.id, user_id=chat_members[i][1])
                    if status.status == 'member' or status.status == 'creator' or status.status == 'administrator':
                        if chat_members[i][9] == 1:
                            x = 0
                            print(x)
                        else:
                            data_to_split = format(message.text)
                            data_for_add = data_to_split.split(' ')
                            is_digit = data_for_add[1].isdigit()
                            if is_digit is True:
                                data_to_add_finish = int(data_for_add[1]) // count
                                reason_len = len(data_for_add)
                                if reason_len <= 2:
                                    db = dbconn.PGadmin()
                                    db.update('users', 'quantity=0', 'telegram_id={}'.format(uid))
                                    db.close()
                                    conn.bot.send_message(message.chat.id, "Please specify the reason.")
                                    return None
                                else:
                                    reason1 = data_for_add[2:reason_len]
                                    reason_finish = ' '.join(reason1)
                                    db = dbconn.PGadmin()
                                    cur_date = db.select('CURRENT_DATE')
                                    db.update('users',
                                              'sum=sum -{}'.format(data_to_add_finish),
                                              "user_name='{}'".format(chat_members[i][5]))
                                    db.insert('operations (who,to_whom,date,command,sum,reason,company)', (manager[5],
                                                                                                           chat_members[i][5],
                                                                                                           format(cur_date[0]),
                                                                                                           data_for_add[0],
                                                                                                           data_to_add_finish,
                                                                                                           reason_finish,
                                                                                                           manager[6]))
                                    db.update('users', 'quantity=0', 'telegram_id={}'.format(uid))
                                    db.close()
                            else:
                                db = dbconn.PGadmin()
                                db.update('users', 'quantity=0', 'telegram_id={}'.format(uid))
                                db.close()
                                conn.bot.send_message(message.chat.id, "Undefined quantity: " + data_for_add[1])
                                return None
                    else:
                        i = 0
                        print(i)
                conn.bot.send_message(uid,
                                      'You are fined team. Chat: '
                                      + message.chat.title
                                      + '\nquantity (each): '
                                      + str(data_to_add_finish)
                                      + '\nReason: '
                                      + reason_finish)
            else:
                conn.bot.send_message(uid, 'ERROR: You are not a manager of this group chat. '
                                           '\nPS.: Also Manager must have admin rights in group chat.')


@conn.bot.message_handler(content_types=['text'])
def handle_contact(message):
    uid = message.from_user.id
    db = dbconn.PGadmin()
    user_position = db.select_single('*', 'users', 'telegram_id={0}'.format(uid))
    db.close()
    if message.text == 'Sign up':
        uid = message.from_user.id
        user_name = '@' + message.from_user.username
        if message.from_user.last_name is None:
            name = format(message.from_user.first_name)
        else:
            name = format(message.from_user.first_name + ' ' + message.from_user.last_name)
        db = dbconn.PGadmin()
        account = db.select_single('*', 'users', 'telegram_id={0}'.format(uid))
        db.close()
        if account is not None:
            conn.bot.send_message(uid, 'You are already registered', reply_markup=KEYBOARD)
        else:
            db = dbconn.PGadmin()
            db.insert('users (telegram_id,name,reg_key,user_position,user_name)', (uid,
                                                                                   name,
                                                                                   0,
                                                                                   1,
                                                                                   user_name.lower()))
            db.close()
            hide_keyboard = telebot.types.ReplyKeyboardRemove()
            conn.bot.send_message(uid,
                                  'Write the name of your company/team, please. '
                                  'If a match would not found a new company will be created.',
                                  reply_markup=hide_keyboard)
    elif message.text == 'Help':
        user_markup = telebot.types.ReplyKeyboardMarkup(True, True)
        user_markup.row('Contact us'u'\U00002709')
        user_markup.row('Back')
        inline_keyboard = types.InlineKeyboardMarkup()
        help_button = types.InlineKeyboardButton(text='Open', callback_game='t.me/MyKPI_bot?game=Manual')
        inline_keyboard.add(help_button)
        conn.bot.send_message(uid, "Help", reply_markup=user_markup)
        conn.bot.send_game(chat_id=message.chat.id, game_short_name='Manual', reply_markup=inline_keyboard)
    elif message.text == 'Back':
        db = dbconn.PGadmin()
        db.update('users', 'user_position=0', 'telegram_id={}'.format(uid))
        db.close()
        
        conn.bot.send_message(uid, 'Main menu', reply_markup=KEYBOARD)
    elif message.text == 'Settings'u'\U00002699':
        user_markup = telebot.types.ReplyKeyboardMarkup(True, True)
        user_markup.row('Full statement')
        user_markup.row('Manage store')
        user_markup.row('Reassigning Manager')
        user_markup.row('Back')
        conn.bot.send_message(uid, 'Settings', reply_markup=user_markup)
    elif message.text == 'Full statement':
        global url
        db = dbconn.PGadmin()
        manager = db.select_single('*', 'users', 'telegram_id={}'.format(uid))
        db.close()
        if manager[9] == 1:
            db = dbconn.PGadmin()
            statement = db.select_all1('*', 'operations', "company='{0}'".format(manager[6]))
            db.close()
            conn.bot.send_message(uid, 'Please wait...', reply_markup=BACK_BUTTON)
            spreadsheet = gg.service.spreadsheets().create(body={'properties': {'title': manager[5],
                                                                                'locale': 'ru_RU'},
                                                                 'sheets': [{'properties': {'sheetType': 'GRID',
                                                                                            'sheetId': 0, 'title': manager[5],
                                                                                            'gridProperties': {'rowCount': 1000,
                                                                                                               'columnCount': 6
                                                                                                               }
                                                                                            }
                                                                             }]
                                                                 }
                                                           ).execute()
            service1 = google_credentials.apiclient.discovery.build('drive', 'v3', http=gg.httpAuth)
            service1.permissions().create(fileId=spreadsheet['spreadsheetId'],
                                          body={'type': 'anyone', 'role': 'reader'},
                                          fields='id').execute()
            for i in range(len(statement)):
                db = dbconn.PGadmin()
                cell = db.select_single('*', 'operations', "company='{}'".format(manager[6]))
                db.close()
                results = gg.service.spreadsheets().values().batchUpdate(spreadsheetId=spreadsheet['spreadsheetId'],
                                                                         body={"valueInputOption": "USER_ENTERED",
                                                                               "data": [{"range": manager[5]
                                                                                                  + "!A"
                                                                                                  + str(cell[6])
                                                                                                  + ":F" + str(cell[6]),
                                                                                         "majorDimension": "ROWS",
                                                                                         "values": [[statement[i][0],
                                                                                                     statement[i][1],
                                                                                                     statement[i][2],
                                                                                                     statement[i][3],
                                                                                                     statement[i][4],
                                                                                                     statement[i][5]
                                                                                                     ]]
                                                                                         }]
                                                                               }
                                                                         ).execute()
                db = dbconn.PGadmin()
                db.update('operations', 'num=num+1', "company='{}'".format(manager[6]))
                db.close()
                url = 'https://docs.google.com/spreadsheets/d/' + results['spreadsheetId']
            db = dbconn.PGadmin()
            db.update('operations', 'num=1', "company='{}'".format(manager[6]))
            db.close()
            conn.bot.send_message(uid, url, reply_markup=BACK_BUTTON)
        else:
            conn.bot.send_message(uid, 'ERROR: You are not in the managers list.', reply_markup=BACK_BUTTON)
    elif message.text == 'Balance':
        db = dbconn.PGadmin()
        balance = db.select_single('*', 'users', 'telegram_id={}'.format(uid))
        db.close()
        if balance is not None:
            inline_keyboard = types.InlineKeyboardMarkup()
            statement = types.InlineKeyboardButton(text='Statement', callback_data=balance[5] + ' statement')
            inline_keyboard.add(statement)
            conn.bot.send_message(uid, 'Your balance: ', reply_markup=BACK_BUTTON)
            conn.bot.send_message(uid, str(balance[8]), reply_markup=inline_keyboard)
        else:
            user_markup = telebot.types.ReplyKeyboardMarkup(True, True)
            user_markup.row('Sign up')
            conn.bot.send_message(uid, 'Sign up, please', reply_markup=user_markup)
    elif message.text == 'Reassigning Manager':
        db = dbconn.PGadmin()
        manager = db.select_single('*', 'managers', "user_name='{}'".format('@' + message.from_user.username.lower()))
        db.close()
        if manager is not None:
            db = dbconn.PGadmin()
            db.update('users', 'user_position=3', 'telegram_id={}'.format(uid))
            db.close()
            conn.bot.send_message(uid, "Please specify @username of the colleague.", reply_markup=BACK_BUTTON)
        else:
            conn.bot.send_message(uid,
                                  'ERROR: You are not in the managers list, who can set another managers.',
                                  reply_markup=BACK_BUTTON)
    elif message.text == 'Manage store':
        db = dbconn.PGadmin()
        manager = db.select_single('*', 'managers', "user_name='{}'".format('@' + message.from_user.username.lower()))
        db.close()
        if manager is not None:
            db = dbconn.PGadmin()
            store = db.select_all1('*', 'store', 'manager={}'.format(uid))
            db.close()
            if len(store) == 0:
                conn.bot.send_message(uid, 'No items.')
                db = dbconn.PGadmin()
                db.update('users', 'user_position=4', 'telegram_id={}'.format(uid))
                db.close()
                conn.bot.send_message(uid, 'Please, specify an item.', reply_markup=BACK_BUTTON)
            else:
                for i in range(len(store)):
                    db = dbconn.PGadmin()
                    db.update('users', 'user_position=4', 'telegram_id={}'.format(uid))
                    db.close()
                    inline_keyboard = types.InlineKeyboardMarkup()
                    delete = types.InlineKeyboardButton(text='Delete', callback_data=store[i][0] + '_item')
                    inline_keyboard.add(delete)
                    conn.bot.send_message(uid, store[i][0] + '\n' + str(store[i][1]), reply_markup=inline_keyboard)
                    conn.bot.send_message(uid, 'Please, specify an item.', reply_markup=BACK_BUTTON)
        else:
            conn.bot.send_message(uid, 'ERROR: You are not in the managers list.', reply_markup=BACK_BUTTON)
    elif message.text == 'Store':
        db = dbconn.PGadmin()
        manager = db.select_single('*', 'users', 'telegram_id={}'.format(uid))
        store = db.select_all1('*', 'store', "manager='{}'".format(manager[11]))
        db.close()
        if len(store) == 0:
            conn.bot.send_message(uid, 'No items.', reply_markup=BACK_BUTTON)
        else:
            for i in range(len(store)):
                inline_keyboard = types.InlineKeyboardMarkup()
                buy = types.InlineKeyboardButton(text='Buy', callback_data=str(store[i][0]) + '_buy')
                inline_keyboard.add(buy)
                conn.bot.send_message(uid, store[i][0] + '\n' + str(store[i][1]), reply_markup=inline_keyboard)
            conn.bot.send_message(uid, 'Choose an item.', reply_markup=BACK_BUTTON)
    elif message.text == 'Contact us'u'\U00002709':
        conn.bot.send_message(uid,
                              'We are always happy to help you in any situation. '
                              'Please, contact: \n@Max_Urzhumtsev',
                              reply_markup=BACK_BUTTON)
    elif user_position[4] == 1:
        if message.text:
            db = dbconn.PGadmin()
            company = db.select_single('*', 'companies', "name='{}'".format(message.text))
            db.close()
            if company is None:
                db = dbconn.PGadmin()
                db.insert('managers (user_name,num)', ('@' + message.from_user.username.lower(), 0))
                db.insert('companies (name, manager)', (message.text, '@' + message.from_user.username.lower()))
                db.update('users', 'manager=1', 'telegram_id={}'.format(uid))
                db.close()
                inline_keyboard = types.InlineKeyboardMarkup()
                abort = types.InlineKeyboardButton(text='Abort', callback_data=message.text + ' abort')
                go = types.InlineKeyboardButton(text='Go', callback_data=' go')
                inline_keyboard.add(abort, go)
                conn.bot.send_message(uid,
                                      'New company/team created and you have been set as a manager. '
                                      'Push "abort" to delete company/team.',
                                      reply_markup=inline_keyboard)
            elif message.text == company[1]:
                db = dbconn.PGadmin()
                db.update('users', "company='{}'".format(company[1]), 'telegram_id={}'.format(uid))
                manager = db.select_all1('*', 'users', "manager=1 AND company='{}'".format(company[1]))
                db.close()
                conn.bot.send_message(uid, 'Please choose your manager.')
                for i in range(len(manager)):
                    inline_keyboard = types.InlineKeyboardMarkup()
                    choose = types.InlineKeyboardButton(text='Choose', callback_data=str(manager[i][1]) + ' choose')
                    inline_keyboard.add(choose)
                    conn.bot.send_message(uid, manager[i][2], reply_markup=inline_keyboard)
            else:
                conn.bot.send_message(uid, 'Error. Try more.')

    elif user_position[4] == 3:  # Reassigning Manager
        if message.text:
            db = dbconn.PGadmin()
            manager = db.select_single('*', 'users', "user_name='{}'".format(message.text.lower()))
            db.close()
            if manager[5] == message.text.lower():
                db = dbconn.PGadmin()
                db.update('users', 'manager=1', "user_name='{}'".format(message.text.lower()))
                db.update('users', 'user_position=0', 'telegram_id={}'.format(uid))
                db.close()
                inline_keyboard = types.InlineKeyboardMarkup()
                save = types.InlineKeyboardButton(text='Hold', callback_data=' save')
                delegate = types.InlineKeyboardButton(text='Delegate', callback_data=message.text.lower() + ' delegate')
                cancel = types.InlineKeyboardButton(text='Cancel', callback_data=message.text.lower() + ' cancel')
                inline_keyboard.add(save, delegate, cancel)
                conn.bot.send_message(uid,
                                      message.text
                                      + ' - assigned. '
                                      'Would you like to hold your managers rights or delegate it fully to  '
                                      + message.text + ' ?',
                                      reply_markup=inline_keyboard)
            else:
                conn.bot.send_message(uid,
                                      "User "
                                      + message.text
                                      + " not found. Don't you forget to put '@' before 'username'?",
                                      reply_markup=BACK_BUTTON)
    elif user_position[4] == 4:  # Добавление наименования нового товара
        if message.text:
            db = dbconn.PGadmin()
            db.insert('store (item,manager,price)', (message.text, uid, 0))
            db.update('users', 'user_position=5', 'telegram_id={}'.format(uid))
            db.close()
            conn.bot.send_message(uid,
                                  'Added. Please specify cost of the item.',
                                  reply_markup=BACK_BUTTON)
    elif user_position[4] == 5:  # Добавление стоимости нового товара
        if message.text:
            db = dbconn.PGadmin()
            db.update('store', 'price={}'.format(message.text), 'price=0')
            store = db.select_all1('*', 'store', 'manager={}'.format(uid))
            db.close()
            conn.bot.send_message(uid, 'Done.', reply_markup=BACK_BUTTON)
            for i in range(len(store)):
                db = dbconn.PGadmin()
                db.update('users', 'user_position=4', 'telegram_id={}'.format(uid))
                db.close()
                inline_keyboard = types.InlineKeyboardMarkup()
                delete = types.InlineKeyboardButton(text='Delete', callback_data=store[i][0] + '_item')
                inline_keyboard.add(delete)
                conn.bot.send_message(uid, store[i][0] + '\n' + str(store[i][1]), reply_markup=inline_keyboard)
            conn.bot.send_message(uid, 'Please specify new item.', reply_markup=BACK_BUTTON)


@conn.bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    uid = call.from_user.id
    if call.message:
        if call.data is not None:
            if 'save' in call.data:
                db = dbconn.PGadmin()
                db.update('users', 'user_position=0', 'telegram_id={}'.format(uid))
                db.close()
                
                conn.bot.send_message(uid,
                                      "Done. Please don't forget to set admins rights for a new manager in group chat.",
                                      reply_markup=KEYBOARD)
            elif 'kill' in call.data:
                db = dbconn.PGadmin()
                db.delete_single('companies', 'manager', "'@" + call.from_user.username.lower() + "'")
                db.delete_single('managers', 'user_name', "'@" + call.from_user.username.lower() + "'")
                db.delete_single('users', 'telegram_id', uid)
                db.close()
                hide_keyboard = telebot.types.ReplyKeyboardRemove()
                conn.bot.send_message(uid, 'Deleted.')
                conn.bot.send_message(uid,
                                      'Write the name of your company/team, please. '
                                      'If a match would not found a new company will be created.',
                                      reply_markup=hide_keyboard)
            elif 'abort' in call.data:
                db = dbconn.PGadmin()
                db.delete_single('companies', 'manager', "'@" + call.from_user.username.lower() + "'")
                db.delete_single('managers', 'user_name', "'@" + call.from_user.username.lower() + "'")
                db.update('users', 'manager=0', 'telegram_id={}'.format(uid))
                db.close()
                conn.bot.send_message(uid, 'Deleted.')
                conn.bot.send_message(uid, 'Write the name of your company/team, please. '
                                           'If a match would not found a new company will be created.')
            elif 'go' in call.data:
                db = dbconn.PGadmin()
                db.update('users',
                          'user_position=0, my_manager={}'.format(call.from_user.id),
                          'telegram_id={}'.format(uid))
                db.close()
                inline_keyboard = types.InlineKeyboardMarkup()
                help_button = types.InlineKeyboardButton(text='Open',
                                                         callback_game='t.me/MyKPI_bot?game=Manual')
                inline_keyboard.add(help_button)
                conn.bot.send_game(chat_id=call.message.chat.id,
                                   game_short_name='Manual',
                                   reply_markup=inline_keyboard)
                conn.bot.send_message(uid, 'You are in the main menu.', reply_markup=KEYBOARD)
            elif 'item' in call.data:
                call_data_to_split = format(call.data)
                call_data = call_data_to_split.split('_')
                db = dbconn.PGadmin()
                db.delete_single('store', 'item', "'" + call_data[0] + "'")
                db.close()
                conn.bot.send_message(uid, "Deleted", reply_markup=KEYBOARD)
            elif 'buy' in call.data:
                call_data_to_split = format(call.data)
                call_data = call_data_to_split.split('_')
                db = dbconn.PGadmin()
                store = db.select_single('*', 'store', "item='{}'".format(call_data[0]))
                yourself = db.select_single('*', 'users', 'telegram_id={0}'.format(uid))
                cur_date = db.select('CURRENT_DATE')
                db.update('users', 'sum=sum-{}'.format(int(store[1])), 'telegram_id={}'.format(uid))
                db.insert('operations (who,to_whom,date,command,sum,reason,company)', ('Store',
                                                                                       '@' + call.from_user.username.lower(),
                                                                                       format(cur_date[0]),
                                                                                       '/penalty',
                                                                                       int(store[1]),
                                                                                       store[0],
                                                                                       yourself[6]))
                db.close()
                conn.bot.send_message(uid, "Done.", reply_markup=KEYBOARD)
            elif 'delegate' in call.data:
                call_data_to_split = format(call.data)
                call_data = call_data_to_split.split(' ')
                user_name = '@' + call.from_user.username.lower()
                db = dbconn.PGadmin()
                telegram_id = db.select_single('*', 'users', "user_name='{}'".format(call_data[0]))
                db.update('users', 'manager=0, user_position=0', 'telegram_id={}'.format(uid))
                db.update('chats', "telegram_id={}, user_name='{}'".format(telegram_id[1],
                                                                           call_data[0]), 'telegram_id={}'.format(uid))
                db.delete_single('managers', 'user_name', "'" + user_name + "'")
                db.insert('managers (user_name, num)', (call_data[0], 0))
                db.close()
                conn.bot.send_message(uid,
                                      "All rights have been delegated. "
                                      "You can't send /rewardteam and /penaltyteam commands anymore.",
                                      reply_markup=KEYBOARD)
            elif 'cancel' in call.data:
                call_data_to_split = format(call.data)
                call_data = call_data_to_split.split(' ')
                db = dbconn.PGadmin()
                db.update('users', 'user_position=0', 'telegram_id={}'.format(uid))
                db.update('users', 'manager=0', "user_name='{}'".format(call_data[0]))
                db.close()
                conn.bot.send_message(uid, 'Canceled.', reply_markup=KEYBOARD)
            elif 'choose' in call.data:
                call_data_to_split = format(call.data)
                call_data = call_data_to_split.split(' ')
                db = dbconn.PGadmin()
                db.update('users', 'my_manager={}'.format(call_data[0]), 'telegram_id={}'.format(uid))
                db.update('users', 'user_position=0', 'telegram_id={}'.format(uid))
                db.close()
                conn.bot.send_message(uid, 'You are in the main menu.', reply_markup=KEYBOARD)
            elif 'statement' in call.data:
                global url
                call_data_to_split = format(call.data)
                call_data = call_data_to_split.split(' ')
                db = dbconn.PGadmin()
                statement = db.select_all1('*', 'operations', "to_whom='{0}'".format(call_data[0]))
                db.close()
                if len(statement) == 0:
                    conn.bot.send_message(uid, 'No transactions found.', reply_markup=KEYBOARD)
                else:
                    conn.bot.send_message(uid, 'Please wait...')
                    spreadsheet = gg.service.spreadsheets().create(body={'properties': {'title': call_data[0],
                                                                                        'locale': 'ru_RU'},
                                                                         'sheets': [{'properties': {'sheetType': 'GRID',
                                                                                                    'sheetId': 0,
                                                                                                    'title': call_data[0],
                                                                                                    'gridProperties': {'rowCount': 20,
                                                                                                                       'columnCount': 5}
                                                                                                    }
                                                                                     }]
                                                                         }
                                                                   ).execute()
                    service1 = google_credentials.apiclient.discovery.build('drive', 'v3', http=gg.httpAuth)
                    service1.permissions().create(fileId=spreadsheet['spreadsheetId'],
                                                  body={'type': 'anyone', 'role': 'reader'},
                                                  fields='id').execute()
                    for i in range(len(statement)):
                        db = dbconn.PGadmin()
                        cell = db.select_single('*', 'operations', "to_whom='{}'".format(call_data[0]))
                        db.close()
                        results = gg.service.spreadsheets().values().batchUpdate(spreadsheetId=spreadsheet['spreadsheetId'],
                                                                                 body={"valueInputOption": "USER_ENTERED",
                                                                                       "data": [{"range": statement[i][1]
                                                                                                          + "!A" + str(cell[6])
                                                                                                          + ":E" + str(cell[6]),
                                                                                                 "majorDimension": "ROWS",
                                                                                                 "values": [[statement[i][0],
                                                                                                             statement[i][2],
                                                                                                             statement[i][3],
                                                                                                             statement[i][4],
                                                                                                             statement[i][5]
                                                                                                             ]]
                                                                                                 }]
                                                                                       }
                                                                                 ).execute()
                        db = dbconn.PGadmin()
                        db.update('operations', 'num=num+1', "to_whom='{}'".format(call_data[0]))
                        db.close()
                        url = 'https://docs.google.com/spreadsheets/d/' + results['spreadsheetId']
                    db = dbconn.PGadmin()
                    db.update('operations', 'num=1', "to_whom='{}'".format(call_data[0]))
                    db.close()
                    conn.bot.send_message(uid, url, reply_markup=KEYBOARD)
        else:
            if call.message.game.description == 'Manual':
                conn.bot.answer_callback_query(callback_query_id=call.id,
                                               url='http://telegra.ph/MyKPI-bot-manual-07-09')


conn.bot.remove_webhook()
conn.bot.set_webhook(url=conn.WEBHOOK_URL_BASE+conn.WEBHOOK_URL_PATH,)
web.run_app(
    conn.app,
    host=conn.WEBHOOK_LISTEN,
    port=conn.WEBHOOK_PORT,
)

# TODO - make functions for other commands instead "content_types=['text']"
