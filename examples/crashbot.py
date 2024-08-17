from Pyhoot.Client import Player

bot=Player(Auth_Brute_Force=True,closeafterdisconnect=True)
    
@bot.EventListener(Ltype="question_started")
def question(data):
    bot.AnswerCrash() # or could do a profile_crash() somewhere else if wanted

gameid=input("gamepin?")
name=input("name?")
bot.Start(gameid)
bot.Join(name) # or bot.join_crash(name)

# nothing works here after the WS is closed (working on fixing this)
