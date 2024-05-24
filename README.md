# Pyhoot
This is a library made by MaxGamerTyper to interface with the Kahoot API.

New Release in 1996?

# Installation
https://pypi.org/project/Pyhoot/

pip install Pyhoot

New release in 1996?

## documentation (will improve later):
``` 
Client(gamepin:optional,name:optional) used to define the bot 
.start(gamepin:gamepin) starts the websocket
.join(gamepin:optional) joins the bot to the game
```



```@bot.event_listener(type=...)```

types:
* "pinged"
* "handshake_1"
* "handshake_2"
* "avatar_updated" 
* "disconnected"
* "question_started" 
* "question_ended"
* "question_awaited"
* "quiz_started" 
* "quiz_ended
* "unknown_message"
* "joined"

put this decorator above a function with an argument allowing for data to be sent

```
bot.random_answer(delay:optional) #sends a random answer

bot.submit_answer(answer:,delay:optional(in seconds))

bot.kill() #instantly stops the bot
bot.close() #safley closes the bot
```

## current V1.3 Plans:
* V1.3.1 will improve the documentation and the event listener outputs
* V1.3.2 will add the Host class allowing you to host a game (hopefully) or it will fix the auth bypass
* V1.3.3 will be whatever doesnt get added in V1.3.2

