from Pyhoot.Client import Player

bot=Player(AuthBruteForce=True,CloseAfterDisconnect=True)
    
# your listener functions here

gameid=input("gamepin?")
name=input("name?")
bot.Start(gameid)
bot.Join(name)

# nothing works here after the WS is closed (working on fixing this)
