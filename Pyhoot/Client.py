import websocket
import time
import json as JSON
import threading
from fake_useragent import UserAgent as UA
from .Token import Token
from . import Exceptions
import inspect
import random
import itertools

class Client():
    def __init__(self, gamepin:str=None, name:str="bot",quizuuid:str="",random_text:str="",auth_bypass:bool=True):
        self.data = {}
        self.sent = {}
        self.auth_bypass=auth_bypass
        self.web_log=[]
        self.random_text="Hello, I am a bot and can not answer this question" if random_text=="" else random_text
        self.latest_listener_call=None
        self.previous_data={}
        self.WebSocket = None
        self.WebChannels={ "META_HANDSHAKE": "/meta/handshake", "META_CONNECT": "/meta/connect", "META_DISCONNECT": "/meta/disconnect", "SERVICE_CONTROLLER": "/service/controller", "SERVICE_PLAYER": "/service/player" }
        self.ClientData={"gamepin":gamepin,"clientId":None,"pong_count":1,"name":name,"messageId":1,"token":None}
        self.UserAgent = UA().random
        self.game_info = None
        self.connection_init = threading.Event()
        self.logged_in = threading.Event()
        self.quizuuid=quizuuid
        self.questionindex=1
        self.ListeningData={"functions":{},"types":["pinged","handshake_1","handshake_2","avatar_updated", "disconnected", "question_started", "question_ended", "question_awaited", "quiz_started", "quiz_ended", "unknown_message","joined","auth_reset","auth_correct","auth_incorrect"],"eventIds":{14:"handshake2",46:"avatar_updated",10:"disconnected",2:"question_awaited",8:"question_ended",9:"quiz_started",13:"quiz_ended",53:"auth_reset",52:"auth_correct",51:"auth_incorrect"}}
        self.question_data=None
        self.disconnected=False
        self.quiz_data={}
        self.auth_reset=threading.Event()
        self.auth_correct=threading.Event()
        self.stableid=None
        self.stepverified=False

    def on_open(self,ws):
        self.init_connection(ws)

    def on_message(self,ws, message):
        self.MessageReceiver(message)

    def exception_handler(self,exception,param1,param2=""):
        if self.logged_in.is_set():
            self.disconnect()
            time.sleep(1)
        self.close()
        if param2:
            raise exception(param1,param2)
        else:
            raise exception(param1)

    # websocket connection to kahoot's servers
    def init_connection(self, ws):
        try:
            self.WebSocket = ws
            firsthandshake = [{"id": "1", "version": "1.0", "minimumVersion": "1.0", "channel": self.WebChannels["META_HANDSHAKE"], "supportedConnectionTypes": ["websocket", "long-polling", "callback-polling"], "advice": {"timeout": 60000, "interval": 0}, "ext": {"ack": True, "timesync": {"tc": self.time(), "l": 0, "o": 0}}}]
            self.send(firsthandshake)
        except Exception as e:
            self.exception_handler(Exceptions.KahootInitException,e)

    # second part of the connection to kahoot
    def second_handshake(self):
        try:
            secondhandshake = [{"id": "2", "channel": self.WebChannels["META_CONNECT"], "connectionType": "websocket", "advice": {"timeout": 0}, "clientId": self.ClientData["clientId"], "ext": {"ack": 0, "timesync": {"tc": self.time(), "l": 0, "o": 0}}}]
            self.send(secondhandshake)
            self.connection_init.set()
        except Exception as e:
            self.exception_handler(Exceptions.KahootInitException,e)

    #used for reciving messages
    def MessageReceiver(self, msg):
        self.previous_data=self.data
        self.data = JSON.loads(msg)[0]
        self.web_log.append(JSON.loads(msg))
        self.MessageHandler()
    
    #used for handling information on messages
    def MessageHandler(self):
        func=None
        prev_func=None
        data=self.data.get("data",{})
        print("\n in \n",self.data)
        
        error = data.get("error") if data.get("error") is not None else self.data.get("error")

        if error is not None:
            reason = str(data.get("description"))
            if reason == "Duplicate name":
                self.exception_handler(Exceptions.NameTakenException,self.ClientData["name"])
            elif error=="402::session_unknown":
                self.exception_handler(Exceptions.UnknownSessionException,self.ClientData["clientId"],self.sent.get("clientId"))
            else:
                self.exception_handler(Exceptions.UnknownException,error,reason)
        
        ext=self.data.get("ext",{})
        ack=str(ext.get("ack"))

        if ack!="True" and ack !="None":
            if self.disconnected==True:
                return
            self.pong_count=int(ack)
            self.pong()
            if self.latest_listener_call=="question_awaited":
                prev_func=self.ListeningData["functions"].get("question_started")
            if self.latest_listener_call=="auth_correct":
                print("claaed")
                time.sleep(random.randint(50,100)/100)
                self.send([{"id":self.ClientData["messageId"],"channel":"/service/controller","data":{"id":16,"type":"message","gameid":self.ClientData["gamepin"],"host":"kahoot.it","content":JSON.dumps({"stableIdentifier":self.stableid,"usingNamerator":False})},"clientId":self.ClientData["clientId"],"ext":{}}])
                self.auth_correct.set()
            func=self.ListeningData["functions"].get("pinged")
        elif ack=="True":
            self.ClientData["clientId"] = self.data.get("clientId")
            self.second_handshake()
            func=self.ListeningData["functions"].get("handshake1")

        id=data.get("id")
        info=self.data
        del info["ext"]
        del info["channel"]
        
        if id==17:
            content=JSON.loads(self.data.get("data").get("content"))
            self.stableid=content.get("stableIdentifier")

        if id in list(self.ListeningData["eventIds"].keys()):
            if id==10:
                if info.get("data",{}).get("content")=='{"kickCode":1}':
                    del info["data"]["content"]
                    info["reason"]="kicked"
            elif id ==2:
                self.questionindex=int(JSON.loads(self.data.get("data").get("content")).get("gameBlockIndex"))
                self.question_data=self.data
            elif id==53:
                self.auth_reset.set()
                time.sleep(1)
                self.auth_reset.clear()
            elif id==52:
                pass
            event=self.ListeningData["eventIds"].get(id)
            func=self.ListeningData["functions"].get(event)
            self.latest_listener_call=event
        elif data.get("reason")=="disconnect":
            func=self.ListeningData["functions"].get("disconnected")
            info["reason"]='host left'
            del info["data"]["reason"]
            self.disconnected=True
        elif str(data.get("type"))=="loginResponse":
            self.latest_listener_call="joined"
            func=self.ListeningData["functions"].get("joined")
        else:
            func=self.ListeningData["functions"].get("unkown message")
            self.latest_listener_call="unknown message"
        
        if callable(func):
            func(info)
        if callable(prev_func):
            prev_func(self.previous_data)
            self.latest_listener_call="question_answered"
    
    #used for sending messages
    def send(self, msg):
        try:
            self.sent=msg[0]
            msg = JSON.dumps(msg)
            print("\n out \n",msg)
            self.web_log.append(msg)
            self.WebSocket.send(msg)
            self.ClientData["messageId"] += 1
            return "sent"
        except Exception as e:
            self.exception_handler(Exceptions.SendingException,e)
    
    #used to get the current time since epoch in miliseconds
    def time(self):
        return str(round(time.time() * 1000))

    #used to respond to the kahoot servers pinging the client
    def pong(self):
        packet=self.packet_factory("META_CONNECT",ext={"ack": self.pong_count, "timesync": {"tc": self.time(), "l": 0, "o": 0}})
        self.send(packet)
        return "ponged"
    
    def packet_factory(self,channel,data="",ext={}):
        packet=[{
            "channel":self.WebChannels[channel],
            "clientId":str(self.ClientData["clientId"]),
            "data":data,
            "id":self.ClientData["messageId"],
            "ext":ext,
            "connectionType": "websocket"
            }]
        if data=="":
            packet[0].pop("data")
        return packet
    
    def data_factory(self, content, type1: str, id_int: int = -1):
        data = {
            "gameid": self.ClientData["gamepin"],
            "host": "kahoot.it",
            "type": str(type1),
            "id": id_int,
            "content": JSON.dumps(content),
            "name": self.ClientData["name"]
        }
        if id_int==-1:
            data.pop("id")
        return data
    
    def question_content_factory(self,answer,lag):
        question_type=JSON.loads(self.question_data.get("data").get("content")).get("type")
        content={
            "type":question_type,
            "questionIndex":self.questionindex,
            "meta":{"lag":lag}
        }
        if question_type=="drop_pin":
            if type(answer) is dict:
                content["pin"]=answer
            else:
                self.exception_handler(Exceptions.InvalidAnswerException,answer)
        elif question_type=="jumble" or question_type=="multiple_select_poll" or question_type=="multiple_select_quiz":
            if type(answer) is list:
                content["choice"]=answer
            else:
                self.exception_handler(Exceptions.InvalidAnswerException,answer)
        elif question_type=="brainstorming" or question_type=="word_cloud" or question_type=="open_ended":
            if type(answer) is str:
                content["text"]=answer
            else:
                self.exception_handler(Exceptions.InvalidAnswerException,answer)
        elif question_type=="feedback":
            if type(answer) is str:
                content["text"]=answer
                content["textHighlightIndex"]=-1
            else:
                self.exception_handler(Exceptions.InvalidAnswerException,answer)
        elif question_type=="slider":
            if type(answer) is int:
                content["choice"]=answer
            else:
                self.exception_handler(Exceptions.InvalidAnswerException,answer)
        else:
            if JSON.loads(self.question_data.get("data").get("content")).get("layout")=="TRUE_FALSE":
                if answer=="blue" or answer==0:
                    answer=0
                elif answer=="red" or answer==1:
                    answer=1
                else:
                    self.exception_handler(Exceptions.InvalidAnswerException,answer)
            elif question_type=="quiz":
                if answer=="blue" or answer==0:
                    answer=0
                elif answer=="red" or answer==1:
                    answer=1
                elif answer=="yellow" or answer==2:
                    answer=2
                elif answer=="green" or answer==3:
                    answer=3
                else:
                    self.exception_handler(Exceptions.InvalidAnswerException,answer)
            content["choice"]=answer
        return content

    def question_packet_factory(self,answer,lag):
        packet=[{
            "id":self.ClientData["messageId"],
            "channel": self.WebChannels["SERVICE_CONTROLLER"],
            "data":{
                "id":45,
                "type":"message",
                "gameid":self.ClientData["gamepin"],
                "host":"kahoot.it",
                "content":JSON.dumps(self.question_content_factory(answer,lag))
                },
            "clientId":str(self.ClientData["clientId"]),
            "ext":{}
        }]
        return packet
    


    #used by user and not websocket/generator only



    def start(self,gamepin:str=None):
        self.ClientData["gamepin"]=gamepin if gamepin is not None else self.ClientData["gamepin"]
        gamepin=self.ClientData["gamepin"]
        if gamepin==None:
            self.exception_handler(Exceptions.GamePinException,"")
        if self.ClientData["token"]==None:
            a=Token(self.ClientData["gamepin"],self.UserAgent)
            self.ClientData["token"]=a["Token"]
            self.game_info=a["info"]
        try:
            ws = websocket.WebSocketApp(f'wss://kahoot.it/cometd/{self.ClientData["gamepin"]}/{self.ClientData["token"]}/', on_message=self.on_message, on_open=self.on_open)
            wst=threading.Thread(target=ws.run_forever)
            wst.start()
        except Exception as e:
            self.exception_handler(Exceptions.WebSocketInitException,e)
    
    def kill(self):
        if self.WebSocket:
            self.WebSocket.close()
        
        for thread in threading.enumerate():
            if thread.name == "Thread-WebSocketApp":
                thread.terminate()
        return "killed"

    def close(self):
        if self.WebSocket:
            self.WebSocket.close()
        return "closed"

    #the decorator for functions that calls them on use
    def event_listener(self, listening_type:str):
        def custom_decorator(func):
            if not callable(func):
                self.exception_handler(Exceptions.ListenerFunctionNotCallableException,listening_type)
            parameters = inspect.signature(func).parameters
            has_parameters = any(p.kind == p.POSITIONAL_OR_KEYWORD for p in parameters.values())
            if not has_parameters:
                self.exception_handler(Exceptions.ListenerFunctionParametersException,listening_type)
            if listening_type in self.ListeningData["types"]:
                self.ListeningData["functions"][listening_type] = func
            else:
                self.exception_handler(Exceptions.UnknownListenerException,listening_type)
        return custom_decorator

    # used to generate the information on a profile
    def profile_generator(self,avatar:str,cosmetic:str):
        avatar_map={'WHITE_BEAR': 2350,'PENGUIN': 2300,'REINDEER': 5373,'CHRISTMAS_TREE': 5374,'COOKIE': 5375,'BROWN_RAT': 1800,'GROUNDHOG': 1600,'GRAY_RAT': 4000,'MOOSE': 1500,'PUG': 1700,'DOG': 1700, 'CAT': 1750,'RABBIT': 1850,'RED_FOX': 1900,'GRAY_FOX': 1950,'BROWN_FOX': 2000,'PANDA': 2050,'FROG': 2100,'OWL': 2150,'CHICKEN': 2200,'FEATHERLESS_CHICKEN': 2250,'GOAT': 2400,'TIGER': 2500,'KOALA': 2550,'KANGAROO': 2600,'HORSE': 2650,'BRAIN': 2950,'UNICORN': 2700,'GREEN_MONSTER': 2800,'PURPLE_MONSTER': 2850,'PINK_MONSTER': 2900,'ZOMBIE': 3000,'SKELETON': 3050,'GLOBE': 2750,}
        cosmetic_map = {'PANCAKES': 3950, 'CHRISTMAS_HAT': 5372, 'MONOCLE': 1250, 'SCARF': 2750, 'WINTER_HAT': 5371, 'EAR_MUFFS': 5370, 'SNOW_GOGGLES': 4100, 'COLORED_SUNGLASSES': 4050, 'SANTA_HAT': 5368, 'BEARD': 5367, 'TREE_HAT': 5366, 'PRESENT_HAT': 5365, 'KAHOOT_HAT': 1550, 'GLOWER_HAT': 3100, 'CROWN': 3150, 'VIKING_HAT': 3200, 'GRADUATION_CAP': 3250, 'COWBOY_HAT': 3300, 'WITCH_HAT': 3350, 'HEADPHONES': 3400, 'HEARTS': 3450, 'HEART_GLASSES': 3500, 'GOGGLES': 3550, 'HARD_HAT': 5300, 'EXPLORER_HAT': 5309, 'EYEPATCH': 3600, 'POWDERED_WIG': 1300, 'ALBERT_EINSTIEN': 1350, 'HAIR': 1400, 'SUNGLASSES': 3650, 'TOP_HAT': 3700, 'KID_HAT': 3750, 'PARTY_HAT': 3800, 'FAKE_DISGUISE': 3850, 'PACIFIER': 3900, 'ICE_CREAM_CONE': 4000, 'FOOTBALL_HELMET': 4150, 'ASTRONAUT_HELMET': 4200}
        avatarid=avatar_map.get(avatar.upper())
        cosmeticid=cosmetic_map.get(cosmetic.upper())
        return {"avatar":{"type":avatarid,"item":cosmeticid}}
    
    def auth_brute(self):
            authcodes=list(itertools.permutations([0,1,2,3],4))
            self.auth_reset.wait()
            for sequence in authcodes:
                if self.auth_correct.is_set():
                    break
                packet = [{
                    "id":self.ClientData["messageId"],
                    "channel":self.WebChannels["SERVICE_CONTROLLER"],
                    "data":
                    {"id":50,
                     "type":"message",
                     "gameid":self.ClientData["gamepin"],
                     "host":"kahoot.it",
                     "content":JSON.dumps({"sequence":''.join(map(str, sequence))})},
                     "clientId":str(self.ClientData["clientId"]),
                     "ext":{}}]
                self.send(packet)
                time.sleep(.1)

    # used to join an active kahoot game
    def join(self, name:str="",profile:str="",quizuuid=None):
        self.connection_init.wait()  # Wait for the WebSocket connection to be established
        time.sleep(1)

        self.quizuuid=quizuuid if quizuuid is not None else self.quizuuid
        name = self.ClientData["name"] if name == "" else name
        self.ClientData["name"] = name

        login_data=self.data_factory({"device":{"userAgent":f"{self.UserAgent}","screen":{"width":1920,"height":1080}}},"login")
        login_packet=self.packet_factory("SERVICE_CONTROLLER",login_data)
        login_follup_data=self.data_factory(profile,"message",16)
        login_followup_packet=self.packet_factory("SERVICE_CONTROLLER",login_follup_data)
        self.send(login_packet)
        self.send(login_followup_packet)

        self.join_sent=True

        time.sleep(5)
        
        if self.game_info.get("twoFactorAuth") is True:
            if self.auth_bypass:
                self.auth_brute()
            else:
                return "Awaitng Auth password"
        else:
            self.auth_correct.set()
            self.logged_in.set()

    
    # used to disconnect from a kahoot game
    def disconnect(self):
        self.disconnected=True
        self.send([{"id":self.ClientData["messageId"],"channel":self.WebChannels["META_DISCONNECT"],"clientId":str(self.ClientData["clientId"]),"ext":{"timesync":{"tc":self.time(),"l":0,"o":0}}}])
        if callable(self.ListeningData["functions"].get("disconnected")):
            self.ListeningData["functions"]["disconnected"]({"data":{"gameid":self.gamepin,'host':'kahoot.it',"id":10,'type':'message'},"reason":"player left"})
        self.logged_in.clear()
    
    # used to change profiles in a kahoot game
    def change_profile(self,profile):
        self.logged_in.wait()
        data=self.data_factory(profile,"message",46)
        packet=self.packet_factory("SERVICE_CONTROLLER",data)
        del packet[0]["connectionType"]
        del packet[0]["data"]["name"]
        self.send(packet)

    #used to submit an answer in a kahoot game
    def submit_answer(self,answer,delay:int=0):
        lag=round(random.random() * 60 + 5) + (delay*100)
        answer=0 if answer=="red" else answer
        answer=1 if answer=="blue" else answer
        answer=2 if answer=="yellow" else answer
        answer=3 if answer=="green" else answer
        time.sleep(delay+.25)
        packet=self.question_packet_factory(answer,lag)
        self.send(packet)
        self.questionindex+=1

    def random_answer(self,delay:int=0):
        answer=None
        content_data=JSON.loads(self.question_data.get("data").get("content"))
        question_type=content_data.get("type")
        if question_type=="drop_pin":
            # x:0 is far left
            # y:0 is far up
            answer={"x":(random.randint(0,100000000))/1000000,"y":(random.randint(0,100000000))/1000000}
        elif question_type=="jumble":
            answer=list(random.choice(list(itertools.permutations([0,1,2,3],4))))
        elif question_type=="multiple_select_poll" or question_type=="multiple_select_quiz":
            amount=random.randint(1,int(content_data.get("numberOfChoices")))
            numbers=[0,1,2,3]
            answer=[]
            while amount>0:
                num=random.choice(numbers)
                answer.append(num)
                numbers.remove(num)
                amount-=1
        elif question_type=="feedback" or question_type=="brainstorming" or question_type=="word_cloud" or question_type=="open_ended":
            answer=self.random_text
        elif question_type=="slider":
            step=int(content_data.get("step"))
            min=int(content_data.get("minRange"))
            max=int(content_data.get("maxRange"))
            number=random.randint(min,max)
            number=round(number / step) * step
            answer=number+min
        else:
            if content_data.get("layout")=="TRUE_FALSE":
                answer=random.randint(0,1)
            elif question_type=="quiz":
                answer=random.randint(0,3)
            elif question_type=="survey":
                answer=random.randint(0,int(content_data.get("numberOfChoices"))-1)
        self.submit_answer(answer,delay)
    
    def crash_lobby(self):
        time.sleep(random.randint(15,25)/100)
        packet=[{
            "id":self.ClientData["messageId"],
            "channel": self.WebChannels["SERVICE_CONTROLLER"],
            "data":{
                "id":45,
                "type":"message",
                "gameid":self.ClientData["gamepin"],
                "host":"kahoot.it",
                "content":JSON.dumps(None)
                },
            "clientId":str(self.ClientData["clientId"]),
            "ext":{}
        }]
        self.send(packet)
        return "Sent (only works when a question is present)"

    def find_game(self,gamepin):
        return Token(gamepin,self.UserAgent,check=True) 

    # added crash_lobby
    # fixed change_profile
    # added auth bypass (auth_correct event listener and auth_wrong event listener)
