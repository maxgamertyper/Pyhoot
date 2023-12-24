import websocket
import time
import json as JSON
import threading
from fake_useragent import UserAgent as UA
from Pyhoot.Token import Token
import Pyhoot.Exceptions as Exceptions
import inspect
import random

class Client():
    def __init__(self, gamepin=None, name="bot",quizuuid=None):
        self.data = {}
        self.sent = {}
        self.log=[]
        self.latest_listener_call=None
        self.previous_send={}
        self.message_count = 1
        self.WebSocket = None
        self.WebChannels={ "META_HANDSHAKE": "/meta/handshake", "META_CONNECT": "/meta/connect", "META_DISCONNECT": "/meta/disconnect", "SERVICE_CONTROLLER": "/service/controller", "SERVICE_PLAYER": "/service/player" }
        self.clientId = None
        self.gamepin = gamepin
        self.pong_count = 1
        self.UserAgent = UA().random
        self.name = name
        self.token = None
        self.game_info = None
        self.connection_init = threading.Event()
        self.logged_in=threading.Event()
        self.quizuuid=quizuuid
        self.questionindex=1
        self.listening_functions={}
        self.listening_types=["pinged","handshake_1","handshake_2","avatar_updated", "disconnected", "question_started", "question_ended", "question_awaited", "quiz_started", "quiz_ended", "unknown_message","joined"]
        self.question_data=None
        self.disconnected=False
        self.quiz_data={}

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

    def start(self,gamepin=None):
        self.gamepin=gamepin if gamepin is not None else self.gamepin
        if self.gamepin==None:
            self.exception_handler(Exceptions.GamePinException,"")
        if self.token==None:
            a=Token(self.gamepin,self.UserAgent)
            self.token=a["Token"]
            self.game_info=a["info"]
        try:
            ws = websocket.WebSocketApp(f'wss://kahoot.it/cometd/{self.gamepin}/{self.token}/', on_message=self.on_message, on_open=self.on_open)
            wst=threading.Thread(target=ws.run_forever)
            wst.start()
        except Exception as e:
            self.exception_handler(Exceptions.WebSocketInitException,e)
    
    def kill(self):
        if self.WebSocket:
            self.WebSocket.close()
            thread_id = threading.get_ident()
            for thread in threading.enumerate():
                if thread.ident == thread_id:
                    thread.terminate()

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
            secondhandshake = [{"id": "2", "channel": self.WebChannels["META_CONNECT"], "connectionType": "websocket", "advice": {"timeout": 0}, "clientId": self.clientId, "ext": {"ack": 0, "timesync": {"tc": self.time(), "l": 0, "o": 0}}}]
            self.send(secondhandshake)
            self.connection_init.set()
        except Exception as e:
            self.exception_handler(Exceptions.KahootInitException,e)
    
    #the decorator for functions that calls them on use
    def event_listener(self, type):
        def custom_decorator(func):
            if not callable(func):
                raise Exceptions.ListenerFunctionNotCallableException(type)
            parameters = inspect.signature(func).parameters
            has_parameters = any(p.kind == p.POSITIONAL_OR_KEYWORD for p in parameters.values())
            if not has_parameters:
                raise Exceptions.ListenerFunctionParamatersException(type)
            if type in self.listening_types:
                self.listening_functions[type] = func
            else:
                self.exception_handler(Exceptions.UnknownListenerException,type)
        return custom_decorator
    
    #used for reciving messages
    def MessageReceiver(self, msg):
        self.previous_send=self.data
        self.data = JSON.loads(msg)[0]
        self.log.append(JSON.loads(msg))
        self.MessageHandler()

    #used for handling information on messages
    def MessageHandler(self):
        func=None
        prev_func=None
        data=self.data.get("data",{})
        
        error = data.get("error") if data.get("error") is not None else self.data.get("error")

        if error is not None:
            reason = str(data.get("description"))
            if reason == "Duplicate name":
                self.exception_handler(Exceptions.NameTakenException,self.name)
            elif error=="402::session_unknown":
                self.exception_handler(Exceptions.UnknownSessionException,self.clientId,self.sent.get("clientId"))
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
                prev_func=self.listening_functions.get("question_started")
            func=self.listening_functions.get("pinged")
        elif ack=="True":
            self.clientId = self.data.get("clientId")
            self.second_handshake()
            func=self.listening_functions.get("handshake1")

        id=data.get("id")
        event_map={14:"handshake2",46:"avatar_updated",10:"disconnected",2:"question_awaited",8:"question_ended",9:"quiz_started",13:"quiz_ended"}
        info=self.data
        del info["ext"]
        del info["channel"]

        if id in event_map:
            if id==10:
                if info.get("data",{}).get("content")=='{"kickCode":1}':
                    del info["data"]["content"]
                    info["reason"]="kicked"
            if id ==2:
                self.questionindex=int(JSON.loads(self.data.get("data").get("content")).get("gameBlockIndex"))
                self.question_data=self.data
            func=self.listening_functions.get(event_map[id])
            self.latest_listener_call=event_map[id]
        elif data.get("reason")=="disconnect":
            func=self.listening_functions.get("disconnected")
            info["reason"]='host left'
            del info["data"]["reason"]
            self.disconnected=True
        elif str(data.get("type"))=="loginResponse":
            self.latest_listener_call="joined"
            func=self.listening_functions.get("joined")
        else:
            func=self.listening_functions.get("unknown message")
            self.latest_listener_call="unknown message"
        
        if callable(func):
            func(info)
        if callable(prev_func):
            prev_func(self.previous_send)
            self.latest_listener_call="question_answered"
    
    #used for sending messages
    def send(self, msg):
        try:
            self.sent=msg[0]
            msg = JSON.dumps(msg)
            self.log.append(msg)
            self.WebSocket.send(msg)
            self.message_count += 1
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

    # used to generate the information on a profile
    def profile_generator(self,avatar:str,cosmetic:str):
        avatar_map={'WHITE_BEAR': 2350,'PENGUIN': 2300,'REINDEER': 5373,'CHRISTMAS_TREE': 5374,'COOKIE': 5375,'BROWN_RAT': 1800,'GROUNDHOG': 1600,'GRAY_RAT': 4000,'MOOSE': 1500,'PUG': 1700,'DOG': 1700, 'CAT': 1750,'RABBIT': 1850,'RED_FOX': 1900,'GRAY_FOX': 1950,'BROWN_FOX': 2000,'PANDA': 2050,'FROG': 2100,'OWL': 2150,'CHICKEN': 2200,'FEATHERLESS_CHICKEN': 2250,'GOAT': 2400,'TIGER': 2500,'KOALA': 2550,'KANGAROO': 2600,'HORSE': 2650,'BRAIN': 2950,'UNICORN': 2700,'GREEN_MONSTER': 2800,'PURPLE_MONSTER': 2850,'PINK_MONSTER': 2900,'ZOMBIE': 3000,'SKELETON': 3050,'GLOBE': 2750,}
        cosmetic_map = {'PANCAKES': 3950, 'CHRISTMAS_HAT': 5372, 'MONOCLE': 1250, 'SCARF': 2750, 'WINTER_HAT': 5371, 'EAR_MUFFS': 5370, 'SNOW_GOGGLES': 4100, 'COLORED_SUNGLASSES': 4050, 'SANTA_HAT': 5368, 'BEARD': 5367, 'TREE_HAT': 5366, 'PRESENT_HAT': 5365, 'KAHOOT_HAT': 1550, 'GLOWER_HAT': 3100, 'CROWN': 3150, 'VIKING_HAT': 3200, 'GRADUATION_CAP': 3250, 'COWBOY_HAT': 3300, 'WITCH_HAT': 3350, 'HEADPHONES': 3400, 'HEARTS': 3450, 'HEART_GLASSES': 3500, 'GOGGLES': 3550, 'HARD_HAT': 5300, 'EXPLORER_HAT': 5309, 'EYEPATCH': 3600, 'POWDERED_WIG': 1300, 'ALBERT_EINSTIEN': 1350, 'HAIR': 1400, 'SUNGLASSES': 3650, 'TOP_HAT': 3700, 'KID_HAT': 3750, 'PARTY_HAT': 3800, 'FAKE_DISGUISE': 3850, 'PACIFIER': 3900, 'ICE_CREAM_CONE': 4000, 'FOOTBALL_HELMET': 4150, 'ASTRONAUT_HELMET': 4200}
        avatarid=avatar_map.get(avatar.upper())
        cosmeticid=cosmetic_map.get(cosmetic.upper())
        return {"avatar":{"type":avatarid,"item":cosmeticid}}

    # kills the websocket if open
    def close(self):
        if self.WebSocket:
            self.WebSocket.close()
        return "Killed"

    # used to join an active kahoot game
    def join(self, name="",profile="",quizuuid=None):
        self.connection_init.wait()  # Wait for the WebSocket connection to be established
        time.sleep(1)

        self.quizuuid=quizuuid if quizuuid is not None else self.quizuuid
        name = self.name if name == "" else name
        self.name = name
        profile = JSON.dumps({"avatar":{"type":2050,"item":3350}}) if profile is None else profile

        login_data=self.data_factory({"device":{"userAgent":f"{self.UserAgent}","screen":{"width":1920,"height":1080}}},"login")
        login_packet=self.packet_factory("SERVICE_CONTROLLER",login_data)
        login_follup_data=self.data_factory(profile,"message",16)
        login_followup_packet=self.packet_factory("SERVICE_CONTROLLER",login_follup_data)
        self.send(login_packet)
        self.send(login_followup_packet)

        time.sleep(1)
        self.logged_in.set()
        return "Joined"
    
    # used to disconnect from a kahoot game
    def disconnect(self):
        self.disconnected=True
        self.send([{"id":str(self.message_count),"channel":self.WebChannels["META_DISCONNECT"],"clientId":str(self.clientId),"ext":{"timesync":{"tc":self.time(),"l":0,"o":0}}}])
        self.listening_functions["disconnected"]({"data":{"gameid":self.gamepin,'host':'kahoot.it',"id":10,'type':'message'},"reason":"player left"})
        self.logged_in.clear()
    
    # used to change profiles in a kahoot game
    def change_profile(self,profile):
        self.logged_in.wait()
        data=self.data_factory(str(profile),"message",46)
        packet=self.packet_factory("SERVICE_CONTROLLER",data)
        self.send(packet)

    #used to submit an answer in a kahoot game
    def submit_answer(self,answer,delay:int=0):
        lag=round(random.random() * 60 + 5)
        answer=0 if answer=="red" else answer
        answer=1 if answer=="blue" else answer
        answer=2 if answer=="yellow" else answer
        answer=3 if answer=="green" else answer
        time.sleep(delay+.25)
        data=self.data_factory(JSON.dumps({"choice": answer, "questionIndex": self.questionindex, "meta": {"lag": lag}, "type": "quiz"}),"message",45)
        packet=self.packet_factory("SERVICE_CONTROLLER",data)
        self.send(packet)
        self.questionindex+=1

    def packet_factory(self,channel,data="",ext={}):
        packet=[{
            "channel":self.WebChannels[channel],
            "clientId":str(self.clientId),
            "data":data,
            "id":str(self.message_count),
            "ext":ext,
            "connectionType": "websocket"
            }]
        if data=="":
            packet[0].pop("data")
        return packet
    
    def data_factory(self, content, type1: str, id_int: int = -1):
        data = {
            "gameid": str(self.gamepin),
            "host": "kahoot.it",
            "type": str(type1),
            "id": id_int,
            "content": JSON.dumps(content),
            "name": str(self.name)
        }
        if id_int==-1:
            data.pop("id")
        return data

    def random_answer(self,delay:int=0):
        self.submit_answer(random.randint(0,3),delay)
