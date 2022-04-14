from telethon import TelegramClient, events, utils
from telethon.tl.functions.channels import JoinChannelRequest, LeaveChannelRequest
from telethon.tl.types import PeerUser, PeerChat, PeerChannel
from telethon.tl.functions.users import GetFullUserRequest
import sqlite3

api_id = 00000000
api_hash = '00000000000000000000000000000000'
client = TelegramClient('news_feed', api_id, api_hash)

sqlite_connection = sqlite3.connect('news_feed.db')
cursor = sqlite_connection.cursor()
cursor.execute('create table if not exists channels (id integer not null, name text not null);')
cursor.execute('create table if not exists users (id integer not null, name text not null, admin integer not null);')
cursor.execute('create table if not exists channels_users (channel_id integer not null, user_id integer not null);')
sqlite_connection.commit()

@client.on(events.NewMessage)
async def my_event_handler(event):
    try:
        if hasattr(event.message, 'peer_id') and hasattr(event.message.peer_id, 'channel_id'):
            # forward channel post to users
            cursor.execute('select user_id from channels_users where channel_id=' + str(event.message.peer_id.channel_id) + ';')
            records = cursor.fetchall()
            for row in records:
                user_id = int(row[0])
                await event.message.forward_to(user_id)        
        if hasattr(event.message, 'peer_id') and hasattr(event.message.peer_id, 'user_id'):
            user_id = event.message.peer_id.user_id
            hasuser = False
            cursor.execute('select count(1) from users where id=' + str(user_id) + ';')
            records = cursor.fetchall()
            for row in records:
                hasuser = int(row[0]) > 0            
            if hasuser:
                if hasattr(event.message, 'fwd_from') and hasattr(event.message.fwd_from, 'from_id') and hasattr(event.message.fwd_from.from_id, 'channel_id'):
                    # added channel for forward to this user
                    channel_id = event.message.fwd_from.from_id.channel_id
                    haschannel = False
                    cursor.execute('select count(1) from channels where id=' + str(channel_id) + ';')
                    records = cursor.fetchall()
                    for row in records:
                        haschannel = int(row[0]) > 0
                    if haschannel == False:
                        channel = await client.get_entity(PeerChannel(event.message.fwd_from.from_id.channel_id))
                        channel_name = utils.get_display_name(channel)
                        await client(JoinChannelRequest(channel))
                        cursor.execute("insert into channels (id, name) values (" + str(channel_id) + ", '" + channel_name + "');")
                        sqlite_connection.commit() 
                    hasfollowuser = False
                    cursor.execute('select count(1) from channels_users where channel_id=' + str(channel_id) + ' and user_id=' + str(user_id) + ';')
                    records = cursor.fetchall()
                    for row in records:
                        hasfollowuser = int(row[0]) > 0
                    if hasfollowuser == False:
                        cursor.execute("insert into channels_users (channel_id, user_id) values (" + str(channel_id) + ", " + str(user_id) + ");")
                        sqlite_connection.commit()
                elif event.message.message == '/channels':
                    cursor.execute('select c.id, c.name from channels c inner join channels_users u on u.channel_id=c.id where u.user_id=' + str(user_id) + ';')
                    records = cursor.fetchall()
                    for row in records:
                        channel_id = row[0]
                        channel_name = row[1]
                        await client.send_message(user_id, channel_name + '\r\n/stop_' + str(channel_id))                        
                elif event.message.message.startswith('/stop_'):
                    channel_id = int(event.message.message.replace("/stop_", ""))
                    cursor.execute("delete from channels_users where channel_id=" + str(channel_id) + " and user_id=" + str(user_id) + ";")
                    sqlite_connection.commit()
                    count = 0
                    cursor.execute('select count(1) from channels_users where channel_id=' + str(channel_id) + ';')
                    records = cursor.fetchall()
                    for row in records:
                        count = int(row[0])
                    if count == 0:
                        channel = await client.get_entity(PeerChannel(channel_id))
                        await client(LeaveChannelRequest(channel))
                        cursor.execute("delete from channels where id=" + str(channel_id) + ";")
                        sqlite_connection.commit()
                elif event.message.message.startswith('/kick') or event.message.message == '/users' or event.message.message == '/':                    
                    isadmin = False
                    cursor.execute('select count(1) from users where admin=1 and id=' + str(user_id) + ';')
                    records = cursor.fetchall()
                    for row in records:
                        isadmin = int(row[0]) > 0
                    if isadmin:
                        if event.message.message == '/users':
                            cursor.execute('select id, name from users where id<>' + str(user_id) + ';')
                            records = cursor.fetchall()
                            for row in records:
                                item_id = row[0]
                                item_name = row[1]
                                await client.send_message(user_id, item_name + '\r\n/kick_' + str(item_id))
                        elif event.message.message.startswith('/kick_'):
                            item_id = int(event.message.message.replace("/kick_", ""))
                            if user_id != item_id:
                                cursor.execute("delete from users where id=" + str(item_id) + ";")
                                cursor.execute("delete from channels_users where user_id=" + str(item_id) + ";")
                                sqlite_connection.commit()                            
                                cursor.execute('select c.id from channels c where (select count(1) from channels_users cu where cu.channel_id=c.id)=0;')
                                records = cursor.fetchall()
                                for row in records:
                                    channel_id = int(row[0])
                                    channel = await client.get_entity(PeerChannel(channel_id))
                                    await client(LeaveChannelRequest(channel))
                                    cursor.execute("delete from channels where id=" + str(channel_id) + ";")
                                    sqlite_connection.commit()
                        elif event.message.message == '/':
                            await client.send_message(user_id, 'Commands:\r\n/channels\r\n/users')
                    else:
                        if event.message.message == '/':
                            await client.send_message(user_id, 'Commands:\r\n/channels')
            else:
                if event.message.message.startswith('/invite_'):
                    invite = event.message.message.replace("/invite_", "")
                    sender = await event.get_sender()
                    user_name = sender.username
                    hasallusers = False
                    cursor.execute('select count(1) from users;')
                    records = cursor.fetchall()
                    for row in records:
                        hasallusers = int(row[0]) > 0
                    if hasallusers:
                        hasinvite = False
                        cursor.execute("select count(1) from users where admin=1 and name='" + invite + "';")
                        records = cursor.fetchall()
                        for row in records:
                            hasinvite = int(row[0]) > 0
                        if hasinvite:
                            cursor.execute("insert into users (id, name, admin) values (" + str(user_id) + ", '" + user_name + "', 0);")
                            sqlite_connection.commit()
                    else:
                        cursor.execute("insert into users (id, name, admin) values (" + str(user_id) + ", '" + user_name + "', 1);")
                        sqlite_connection.commit()
    except Exception as e:
        print(str(event) + '\n**********\n' + str(e) + '\n**********\n')
client.start()
client.run_until_disconnected()
