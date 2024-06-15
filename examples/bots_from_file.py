import threading
from Pyhoot.Client import Player
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
    bot=Player()
    
    @bot.event_listener(Ltype="joined")
    def joined(data):
        print(f"{name} joined {gamepin}")
    
    @bot.event_listener(Ltype="disconnected")
    def disconnected(data):
        print(f"{name} disconnected because {data.get("Reason")}")
        
    @bot.event_listener(Ltype="question_started")
    def question(data):
        bot.random_answer(random.randint(5,10)/10)
        if data.get("QuestionType")=="brainstorming":
            time.sleep(2)
            bot.FinishBrainstorming()
        
    @bot.event_listener(Ltype="brainstorm_voting")
    def brainstorm(data):
        bot.RandomBrainstormVote(random.randint(5,10)/10)
        
    @bot.event_listener(Ltype="quiz_ended")
    def ended(data):
        print(f"{name} ended at {data.get("Rank")} place and had {data.get("PlayerStatistics").get("TotalScore")} points \n")
    
    bot.start(gamepin)
    bot.join(name)


for name in names:
    t=threading.Thread(target=create_bot,args=(name,gamepin))
    threads.append(t)

for thread in threads:
    thread.start()
    time.sleep(random.randint(10,15)/10)

for thread in threads:
    thread.join()
