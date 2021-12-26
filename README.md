# Clash of Clans Discord Bot (CoC Bot)

This bot is used to fetch in-game player data by using the official [Clash of Clans API](https://developer.clashofclans.com/#/documentation). CoC Bot is still under testing and some features have yet to be implemented. Suggestions are encouraged!

## Commands

Currently, eight commands are able to be used.

### coc verify

When ran, the bot will DM the user and prompt their in-game player tag and API token (also found in-game). This command allows the user's data to be saved to the database, and therefore, the user will be able to run other commands. The experience with this bot is much better when the user has verified.

### coc stats

When ran without verification, the bot requires a player tag argument to be entered after the command. <br />
```
coc stats #GY2GJLCP
```
When ran, and the user has already been verified, no additional arguments are required.

<img src='https://raw.githubusercontent.com/CodingPenguin/clashofclans-bot/main/images/cocstats.png' width="500" height="500"/>

### coc clan

This command requires user verification before use. If the user does not have a default clan saved, the user will need to input a clan tag: <br />
```
coc clan #2PGJUGPR
```

At this point, the bot will prompt if the user would like to save the inputted clan tag as their default clan. If so, the next instance of `coc clan` will not need a clan tag; instead, it will fetch the clan data from the saved clan tag: <br />
```
coc clan
```

And if you're curious what metrics are shown, here are some images! <br />

<img src='https://raw.githubusercontent.com/CodingPenguin/clashofclans-bot/main/images/cocclan1.png' width="500"/> <br />
<img src='https://raw.githubusercontent.com/CodingPenguin/clashofclans-bot/main/images/cocclan2.png' width="500"/>

### coc graph

This command requires user verification before use. The user's saved trophy data will be plotted (via matplotlib) on a line graph. New data can only be saved once daily, but the graph can be seen as many times as prompted. 

<img src='https://raw.githubusercontent.com/CodingPenguin/clashofclans-bot/main/images/cocgraph.png' width="600" height="500" />

### coc hero

This command fetches the hero levels of each hero the player has. In the future, this should include how far the player is from maxing out their heroes for their Town Hall level. Requires verification.

<img src='https://raw.githubusercontent.com/CodingPenguin/clashofclans-bot/main/images/cochero.png' width="600" height="700" />

### coc zap

Tells the player how many lightning spells are required to destroy an air defense.
This command requires two parameters: the air defense level and your lightning spell level. <br />
```
coc zap [air defense level] [lightning spell level]
```

### coc zapquake

Tells the player how many lightning spells and earthquake spells are required to destroy an air defense.
This command requires three parameters: the air defense level and a lightning spell level, and an earthquake spell level <br />
```
coc zapquake [air defense level] [lightning spell level] [earthquake spell level]
```

### coc help

Sends the command list!

## Contribute & Support

Want to add the bot to your server? Use this [link](https://discord.com/api/oauth2/authorize?client_id=870085172136149002&permissions=2147544128&scope=bot)! <br />Need more support? Join the support [server](https://discord.gg/6MXVXxK7pb) and ask me directly! <br />Want to support? [Buy me a coffee!](https://www.buymeacoffee.com/danmaruchi)

