import threading
from src.Client import Player
import random
import time

gamepin=input("gamepin? ")
file="names.txt"

threads=[]

with open(file,"r") as f:
    content=f.read()
    f.close()
names=content.splitlines()

def create_bot(name,gamepin):
    print(f"bot with name: {name} joining {gamepin}")
    bot=Player(AuthBruteForce=True)
    
    @bot.EventListener(Ltype="Joined")
    def joined(data):
        print(f"{name} joined {gamepin}")
    
    @bot.EventListener(Ltype="Disconnected")
    def disconnected(data):
        print(f"{name} disconnected because {data.get("Reason")}")
        
    @bot.EventListener(Ltype="QuestionStarted")
    def question(data):
        bot.RandomAnswer(random.randint(5,10)/10)
        if data.get("QuestionType")=="brainstorming":
            time.sleep(2)
            bot.FinishBrainstorming()
        
    @bot.EventListener(Ltype="BrainstormVoting")
    def brainstorm(data):
        bot.RandomBrainstormVote(random.randint(5,10)/10)
    
    @bot.EventListener(Ltype="AuthLogin")
    def authfinished(data):
        print(f"{name} has finished the 2-step-join and is in the game!")
        
    @bot.EventListener(Ltype="QuizEnded")
    def ended(data):
        print(f"{name} ended at {data.get("Rank")} place and had {data.get("PlayerStatistics").get("TotalScore")} points \n")
    
    bot.Start(gamepin)
    bot.Join(name)


for name in names:
    t=threading.Thread(target=create_bot,args=(name,gamepin))
    threads.append(t)

for thread in threads:
    thread.start()
    time.sleep(random.randint(10,15)/10)

for thread in threads:
    thread.join()
