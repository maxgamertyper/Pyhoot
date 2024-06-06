import requests
from bs4 import BeautifulSoup
import base64
from . import Exceptions
import json as JSON
import time

def Token(gamepin:str,UA,check=False):
    if gamepin=="":
        raise Exceptions.GamePinException(gamepin)
    
    def ChallengeTokenSolver(message,offset):
        def repl(char, position):
            return chr((((ord(char)*position)+ offset)% 77)+ 48)
        res=""
        for i in range(0,len(message)):
            res+=repl(message[i],i)
        return res
    
    def HeaderTokenSolver(base):
        try:
            base += "=" * ((4 - len(base) % 4) % 4)
            return base64.b64decode(base).decode("utf-8")
        except Exception as e:
            return e
        
    def TokenMerger(headerToken,challengeToken):
        token = ""
        for i in range(0,len(headerToken)):
            char = ord(headerToken[i])
            mod = ord(challengeToken[i % len(challengeToken)])
            decodedChar = char ^ mod
            token += chr(decodedChar)
        return token

    r = requests.get(f'https://kahoot.it/reserve/session/{gamepin}/?{time.time()}',headers={"User-Agent":UA})
    
    sourcecode = BeautifulSoup(r.text, 'html.parser').prettify()
    if str(sourcecode)=="Not found\n" and not check:
        raise Exceptions.GamePinException(gamepin)
    elif str(sourcecode)=="Not found\n" and check:
        return False
    elif str(sourcecode)!="Not found\n" and check:
        return True
    sourcecode=JSON.loads(sourcecode)

    challenge=sourcecode.pop("challenge")
    challenge=challenge.split('= ')

    offsetdecode=challenge[1].split(';')[0]
    offsetdecode=str(offsetdecode).replace('\t','').replace(' ','')
    offsetdecode=offsetdecode.replace('\u2003','')
    offsetvalue=eval(offsetdecode)
    
    challengetoken=challenge[0].split('\'')[1].split('\'')[0]
    

    headertoken=r.headers["x-kahoot-session-token"]

    FinalChallengeToken = ChallengeTokenSolver(challengetoken,offsetvalue)
    FinalHeadToken=HeaderTokenSolver(headertoken)
    
    return {"Token":TokenMerger(FinalHeadToken,FinalChallengeToken),"info":sourcecode}
