# news_feed_telegram
news feed telegram (teleton client)

Ubuntu 20.04:
1. install teleton (https://github.com/LonamiWebs/Telethon)
2. clone this repository: git clone https://github.com/yakamoto16/news_feed_telegram.git
3. register telegram app (https://my.telegram.org)
4. change newsfeed.py: api_id and api_hash
5. run: 
```
   python3 newsfeed.py
```
6. telegram: send to chat /invite_ and forward open channels
7. added other user: send to chat /invite_{your username}

Create deamon:
```
sudo nano /etc/systemd/system/newsfeed.service
```

```
[Unit]
Description=news_feed_telegram
After=syslog.target

[Service]
Type=simple
User=user
Group=user
WorkingDirectory=/home/user/news_feed_telegram/
ExecStart=/usr/bin/python3 newsfeed.py

[Install]
WantedBy=multi-user.target
```

```
sudo systemctl enable newsfeed
sudo systemctl start newsfeed
```

WARNING! First start no deamon
