from Pyhoot.Client import Player
import time
import string
import random

characters=string.ascii_letters + string.digits + string.punctuation

bot=Player(Auth_Brute_Force=True,closeafterdisconnect=True)
    
# your listener functions here

gameid=input("gamepin?")
name=input("name?")
bot.start(gameid)
bot.join(name)

# nothing works here after the WS is closed (working on fixing this)
