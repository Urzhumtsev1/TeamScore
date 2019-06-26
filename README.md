# TeamScore
Team performance Telegram bot. With this bot, you can make your team more efficient boosting the competitive spirits. Set goals, reward team, and team members. 
Stimulate your colleagues and keep them motivated. Just appreciate little things in work life, reward regular success, and celebrate the milestones.

**If you are the developer, you can deploy this bot on your server. Just read guide bellow.** 

3 simple steps to get a free demo:
1. Go to https://t.me/TeamScore_bot or search for TeamScore_bot in Telegram
2. Take a super-quick registration
3. Add bot to the chat and text "/new"

That is all. Now you can use this bot to reward and penalty your team members or the whole team. 
(if they registered in bot and members of a chat) 

Please, check a short manual for all bot commands. https://telegra.ph/Manual-10-19

## Technical specification

1.  Unix-like OS:

	My choice is Debian 9. 

	Telegram is banned in several countries, so you should use VPS where you can run your bot.

	I use this [Hoster](https://m.do.co/c/8ec134b091f9)

2. Python 3.5+

3. Postgresql 9.6+

4. Nginx/1.10.3

## Installation

### Python dependencies:

>mkdir ~/ProjectName 

>cd ~/ProjectName

>python3 -m venv envname

>source envname/bin/activate

>pip3 install pyTelegramBotAPI aiohttp psycopg2 google-api-python-client
 

### Web server:

1. Add new DNS record for your bot on your domain name (Type - A, Name - botname, Server IP - IP, TTL - 600sec.)

2. Use [Certbot](https://certbot.eff.org/) to set free SSL certificates (Don't forget to set renewal with Cron)

3. Configure Nginx web server:

>sudo apt-get install nginx

Create your own config file.

>cd /etc/nginx/sites-available ; sudo touch botname

Your config file 'botname' should contains something like this:
```
server {
        listen 80;
        listen [::]:80;
        server_name botname.domainname.com;
        return 301 https://$server_name$request_uri;
}

server {
        listen 443 ssl http2;
        server_name botname.domainname.com;
        ssl on;
        ssl_certificate /etc/letsencrypt/live/botname.domainname.com/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/botname.domainname.com/privkey.pem;
        ssl_session_timeout 5m;
        ssl_protocols TLSv1 TLSv1.1 TLSv1.2;
        access_log /var/log/nginx/botname-access.log;
        error_log /var/log/nginx/botname-error.log;
        location ~ /.well-known {
            allow all;
        }


        #add_header Strict-Transport-Security "max-age=15768000; includeSubDomains; preload";


        location /{
                proxy_pass http://127.0.0.1:7127;
                proxy_set_header Host $http_host;
                proxy_redirect off;
                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                proxy_set_header X-Real-IP $remote_addr;
                proxy_set_header X-Forwarded-Host $server_name;
        }
}
```
Open port 7127 or any other

>sudo iptables -I INPUT 1 -p tcp --dport 7127 -j ACCEPT

>iptables-save 
(won't work after reboot)

Create a symbolic link
>sudo ln -s /etc/nginx/sites-available/botname /etc/nginx/sites-enabled/botname

>sudo service nginx restart

Create file constants.py in your Project directory.

>cd ~/ProjectName

>touch constants.py

>vi constants.py

Paste this code:
```
#!/usr/bin/python3.5
# -*- coding: utf-8 -*-
TOKEN = 'put here Telegam bot token from BotFather'
WEBHOOK_HOST = 'botname.domainname.com'
WEBHOOK_PORT = 7127
WEBHOOK_LISTEN = '0.0.0.0'
DATABASE = 'dbname'
USER = 'dbuser'
PASSWORD = 'strongpassword'
HOST = 'localhost'
PORT = 5432
```

### Database

1. Install PostgreSQL.

>sudo apt-get install postgresql

2. Run sql scripts

>sudo service postgresql start

>cd ~/ProjectName

>psql -U postgres 

>create role dbuser with login password 'strongpassword';

>create database dbname ;

I know it is horrible database structure. **# TODO: redesign database**
>\ir dbconfig.sql


### Google credentials

**# TODO - branch with CSV**

1. Got to https://console.developers.google.com 
2. Generate private key as json. [Instruction](https://developers.google.com/identity/protocols/OAuth2ServiceAccount#creatinganaccount)
3. Touch up path to private key in google_credentials.py


### Run bot

>cd /etc/systemd/system

>touch botname.service

Add this code and change to your values:

```
[Unit]
Description=Telegram bot 'botname'
After=syslog.target
After=network.target

[Service]
Type=simple
User=YourUsername
WorkingDirectory=/ProjectPath
ExecStart=/usr/bin/python3.5 /ProjectPath/main.py
RestartSec=10
Restart=always
 
[Install]
WantedBy=multi-user.target
```

>systemctl daemon-reload

>systemctl enable botname

>systemctl start botname

>systemctl status botname

##  How to use bot?

"/new" - if you are the manager of a team - firstly add TeamScore_bot to the group chat and set him as an admin. Then write /new in the group chat. After that, you can use other commands of the bot in this group chat.

"/reward @username 10 reason why" - if you want to reward someone from your team in group chat. Firstly, write '/reward', then '@username', then 'quantity' and 'reason' at the end. Please, always keep ONE space between all statements.

"/penalty @username 10 reason why" - if you want to penalty someone from your team in group chat. Firstly, write '/penalty', then '@username', then 'quantity' and 'reason' at the end. Please, always keep ONE space between all statements.

"/rewardteam 100 reason why" - if you are the manager of the team - you can reward all members of the team in group chat. Firstly write '/rewardteam', then 'quantity' and 'reason' at the end. NOTE: The quantity will be divided between all members of the group chat, except managers.   

"/penaltyteam 100 reason why" - if you are the manager of the team - you can penalty all members of the team in group chat. Firstly write '/penaltyteam', then 'quantity' and 'reason' at the end. NOTE: The quantity will be divided between all members of the group chat, except managers.  

"/kill" - all your data will be deleted.
