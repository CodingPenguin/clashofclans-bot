# Clash of Clans Discord Bot (CoC Bot)

This bot is used to fetch in-game player data by using the official [Clash of Clans API](https://developer.clashofclans.com/#/documentation). CoC Bot is still under testing and some features have yet to be implemented. Suggestions are encouraged!

## Commands

Currently, three commands are able to be used.

### coc verify

When ran, the bot will DM the user and prompt their in-game player tag and API token (also found in-game). This command allows the user's data to be saved to the MongoDB database, and therefore, the user will be able to run the other two commands.

### coc stats

When ran without verification, the bot requires a player tag argument to be entered after the command. <br />
```
coc stats #GY2GJLCP
```
When ran, and the user has already been verified, no additional arguments are required.

![Picture of coc stats](https://user-images.githubusercontent.com/11476519/128583213-a3e8eeb6-d76f-49bd-b142-e89e2a2d2825.png)

### coc graph

This command requires user verification before use. The user's saved trophy data will be plotted (via matplotlib) on a line graph. New data can only be saved once daily, but the graph can be seen as many times as prompted. 

![Picture of coc graph](https://user-images.githubusercontent.com/11476519/128583210-8a603e61-7512-4c85-afd1-5c429ba740b2.png)

## Contribute & Test

Want to add the bot to your server? Join the testing server and ask me!  [Discord Invite](https://discord.gg/6MXVXxK7pb)

