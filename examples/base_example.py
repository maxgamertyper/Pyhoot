from Pyhoot.Client import Player

bot=Player(Auth_Brute_Force=True,closeafterdisconnect=True)
    
# your listener functions here

gameid=input("gamepin?")
name=input("name?")
bot.Start(gameid)
bot.Join(name)

# nothing works here after the WS is closed (working on fixing this)
