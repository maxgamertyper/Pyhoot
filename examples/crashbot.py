from Pyhoot.Client import Player

bot=Player(Auth_Brute_Force=True,closeafterdisconnect=True)
    
@bot.event_listener(Ltype="question_started")
def question(data):
    bot.answer_crash() # or could do a profile_crash() somewhere else if wanted

gameid=input("gamepin?")
name=input("name?")
bot.start(gameid)
bot.join(name) # or bot.join_crash(name)

# nothing works here after the WS is closed (working on fixing this)
