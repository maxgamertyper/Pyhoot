# Pyhoot

A package that allows users to create Kahoot! clients and use the Kahoot! API to their will.
Check out https://github.com/maxgamertyper/Pyhoot for more information or help.

[![Downloads](https://static.pepy.tech/badge/pyhoot)](https://pepy.tech/project/pyhoot)  [![Downloads a week](https://static.pepy.tech/badge/pyhoot/week)](https://pepy.tech/project/pyhoot)

This is a library made by MaxGamerTyper1 to interface with the Kahoot API.

New Release in 1996?

## Installation

https://pypi.org/project/Pyhoot/

pip install Pyhoot

## Stats

https://www.pepy.tech/projects/pyhoot

## current V1.3 Plans:
* V1.3.3 will fix the auth bypass

## Future Updates

### v1.4 (No Progress):
* V1.4.1 will rename the functions so that V1.3.3 doesnt have weird function names compared to V1.3.2
* add team mode support

### v1.5 (Little Progress):
* add ability to host a game or create a game

### v1.5+ (ideas noted):
* add course support
* add an answer getter (would not work with random answers and questions)
* add other connection type support
* add other game mode type support
* add an ability to host a game
* add an ability to create a game


## Documentation

#### everything in here is from client.py


Player() -> the base bot class, is used to join the kahoot games

BaseClient() -> this is not really useful unless you are trying to customize something

### BaseClient Class functions:
* **pong()** -> used to return the websockets Heartbeat ACK connection, enabled by default

* **time()** -> used in some websocket messages, returns time.time() * 1000

* **kill()** -> kills the websocket thread (i dont think this works)

* **close()** -> closes the websocket thread (i dont think this works)

* **EventListenerDecorator** -> sets a function to be an event listener

```python
# event listener example
@bot.event_listener(Ltype="handshake_1") 
def hand1(data):
print(f"handshake1 {data}")
```

* **find_game(pin:str)** -> checks to see if the game is running returns True if it is else False

has some other function that are used in the running of stuff

### Player Class:

* **Auth_Brute_Force:bool** this is used to determine if it should brute force the 2 factor authentication, broken at the moment, base value is False

* **random_text:str** this is used to determine what the text should be if random_answer() is called on a text question, base text is "Hello, I am a bot and can not answer this question"

* **closeafterdisconnect:bool** this is used to determine if the websocket should close after the player is disconnected, Base value is False (this does not work yet)

### Player Class Functions():

* **start(gamepin:str)** -> requires the gamepin, starts the websocket connection

##### Joining functions

* **join(*name:str,quizuuid:str,profile:str)** -> requires a username to join with, actually joins the gamepin specified in start(), optional args: profile, can be generated in profile_generator() and Quizuuid, this does nothing yet

* **join_crash(name:str)** -> requires a name to join with, joins the hosts game specified in start() but crashes the game

* **forceauth()** -> if enabled, this will be automatically activatedd in the join() function, does not work right now

##### Profile Functions

* **profile_generator(avatar:str,cosmetic:str)** ->

requires an avatar and comsmetic item (will update the list on release)
Warning: some event avatar and cosmetics might be in there but they wont work
returns the string that switches the avatar, should be sent into update_profile()

```python
# Official Kahoot names
avatars = [
'POLAR_BEAR', 'PENGUIN', 'SNOWMAN', 'WOODCHUCK', 'MOOSE', 'DOG', 'CAT', 'MOUSE', 'RABBIT', 'FOX', 'WOLF', 'RACCOON', 'PANDA', 'FROG', 'OWL', 'CHICKEN', 'TURKEY', 'CAMEL', 'TIGER', 'KOALA', 'KANGAROO', 'HORSE', 'UNICORN', 'DRAGON', 'MONSTER', 'FAUN', 'BRAIN', 'ZOMBIE', 'SKELETON', 'PLANET_EARTH'
]
# Kahoot doesnt have official names for these so i just made them up
cosmetics = [
'PROPELLER_HAT', 'PARTY_HAT', 'DISGUISE', 'PACIFIER', 'PANCAKES', 'ICE_CREAM', 'FOOTBALL_HELMET', 'ASTRONAUT_HELMET', 'WINTER_HUNTING_HAT', 'REINDEER_HAT', 'ORANGE_HAT', 'SNOWFLAKE_HAT', 'EAR_MUFFS', '2024_GLASSES', 'DRAGON_MASK', 'REFLECTIVE_GOGGLES', 'COLORFUL_SUNGLASSES', 'SCARF', 'KAHOOT_HAT', 'FLOWER_HAT', 'CROWN', 'VIKING_HELMET', 'GRADUATION_CAP', 'COWBOY_HAT', 'WITCH_HAT', 'HEADPHONES', 'HEARTS', 'HEART_SUNGLASSES', 'GOGGLES', 'HARD_HAT', 'SAFARI_HAT', 'EYEPATCH', 'MONOCOLE', 'POWDERED_WIG', 'EINSTEIN_WIG', 'HAIR', 'SUNGLASSES', 'TOP_HAT'
]
```

* **update_profile(profile:str)** -> 

requires the profile, a string, generated from profile_generator()
updates the players profile

* **profile_crash()** -> crashes the game by changing the profile of the player

##### Answer Functions

* **submit_answer(*answer,delay:int=0)** -> submits an asnwer

requires the answer and has an optional delay
answer of 0 is red, 1 is blue, 2 is yellow, 3 is green, auto corrects to the numbers if you type in the color

* **answer_crash()** -> 

crashes the game through answering a question

* **random_answer(delay:int=0)** ->

can have a custom delay to look less like a bot if wanted
just sends a random answer (put in the question_started listener function)

#### **Brainstorm Frunctions**

* **FinishBrainstorming()** ->

Tells Kahoot that you are finished with brainstorming questions (as multiple answers can be submitted)

* **BrainstormVote(vote:bool,OptionID:int)** ->

Sends the vote for the OptionID provided, OptionIDs are recieved in the brainstorm_voting listener function or at bot.BrainstormCandidates
a Vote of False does nothing but go to the next option in the webpage
you need to vote for all options for the game to register your answer as completed, including False

* **RandomBrainstormVote(delay:int=.5)** ->

Votes Randomly for brainstorm candidates
has a delay argument that is optional to include, default is .5

##### Other Functions

* **disconnect()** -> has the player leave the game

* **Any Function Avaliable in the BaseClient Class**

### **Listener Functions**:

* **Heartbeat** -> will return the heartbeat count once a heartbeat is sent, automatically returns the hearbeat call

* **handshake1** -> returns True once the handshake responds

* **handshake2** -> returns True once the second handshake responds

* **profile_updated** -> returns True if the profile updated else it returns False

* **disconnected** -> returns in the format {"Reason":Reason}

```python
#Set reasons are:
{"Reason":"Host Kicked Player"}
{"Reason":"Host Left the Game"}
{"Reason":"Player Left"}

#Unknown disconnect:
{"Reason":data,"Report":"This is an unknown disconnect, please report this and what happened"}
please make an issue and send me the data and what happened in the game
```

* **question_started** -> returns the data for the start of a question:

```python
{
"QuestionType": # the question type
"QuestionNumber": # the question number,
"QuizQuestionCount": # amount of questions,
"QuestionTime": #how long in miliseconds you have to answer the question,
"NumberOfChoices": # the number of answer options,
"SliderData": None if questiontype is not "slider" else 
{
"Unit": #the slider measurment unit,
"Minimum": # the minimum slider range,
"Maximum": # the maximum slider range,
"Step": # the step of the slider minimum -> step -> maximum
},
"BrainstormData": None if questiontype is not "brainstorming" else {
"NumberOfAnswers": #number of brainstorming answers allowed,
"MaximumAnswerLength": #maximum length of brainstorm
},
"DropPinData": None if questiontype is not "drop_pin" else {
"VideoData": #Video Data,
"ImageURL": # the ImageURL of the DropPin,
"ImageData": # basic data of the Image,
"Media": # tbh i have no idea, the amount of media im guessing
}
}
```


* **question_ended** -> returns the data for the end of the question:

```python
{"Correct": True or False,
"CorrectAnswer": #will be one of [0,1,2,3] or a list of them, 
"LeaderboardRank": #your leaderboard rank, int), 
"LeaderboardScore": #your score, 
"PointsData":{
"PointsWithBonuses": #how many points you got from the question,
"QuestionPoints": #how many points without bonuses you got from the question
},
"AnswerStreak": # Your answer streak level, 
"EndedQuestion": #Which question number just ended, 
"NemesisData": #None if first place or only player else {
"NemesisName": #nemsis' name,
"NemesisScore": #nemesis' score,
}
}
```

* **quiz_started** -> returns Quiz question count and a little bit of data on the questions

```python
{"QuestionCount":QuizQuestionCout,int}
QuestionData={"type":QuestionType,"PointType": PointType}
# PointType can be None, Standard, or Double, its the multiplier of the points
# QuestionType can be quiz, jumble, true or false, etc.
# each question will get a QuestionData marking with the key Question{number}
# the first question will contain another key called media
```

* **quiz_ended** -> returns the Quiz ended data:

```python
{"Rank": #players ending rank,
"MedalType": #Player's Medal info None if under Rank 3,
"QuizName": #the name of the quiz,
"QuizId": #the uuid of the quiz, the one in the url on the quiz's home page,
"IsNonPointQuiz": #True if the points dont count else false,
"OrganizationId": #the orginization id of the host,
"PrimaryUsage": #the primary usage of the kahoot,
"QuizCoverData":{
"QuizCoverAltText": # the alt text of the quiz image cover,
"QuizCoverType": # the type of image (jpg,png,etc),
"QuizCoverOrigin": #where the quiz cover came from,
"QuizCoverSize": # a tuple of the (width,height) of the image
},
"PlayerStatistics": {
"IncorrectAnswers": # how many answers were wrong,
"CorrectAnswers": # how many answers were correct,
"TotalScore": # total player score
}
}
```

* **unknown_message** -> just sends the actual websocket message, I would not use this but i added it if you want to

* **joined** -> returns True on success but can return an error

```python
#set error:
{"Error":"Duplicate name"}
```
* **auth_reset** ->
returns True when the auth is reset

* **auth_correct** ->
returns True when the auth is correct

* **auth_incorrect** ->
returns False when the auth is incorrect

* **brainstorm_voting** ->
returns the voting candidates in a list, this is automatically stored in the bot at bot.BrainstormCandidates

```python
[
    {'id':int,
    'answers':[
        {"text":str}, # this can be repeated multiple times in one "answers" key if there is a grouped item
        ]
    } # there will be multiple of these types of data as you need at least 2 to start a vote
]
# the name of the dictionary keys is correct and the value is just the type of object it will be
```

## Found Bugs

### severe bugs
* being able to crash lobbies

### decent bugs
* having infinite name length (have 4 bots with 80 char names and it fills the screen)
* bypasses name generator (namerator)

### minor bugs
* being able to create false lobbies (the lobby code is valid but nobody can join (stays open for like an hour im guessing))
* being able to change profiles mid-game

## Change Log:

### V1.0:
First Release!
The bot can connect to classic game mode and can answer quiz-type questions, join using a web socket, and understand some events within the game!

### V1.1:
Added support for all question types in Client.random_answer() and Client.submit_answer()

### V1.2:
Fixed the Client.change_profile() function so it actually works
Added a way to crash the Kahoot lobby with Client.crash_lobby()
Added a way to bypass the 2-step-join Kahoot feature

### v1.2.1:
Updated Github files so that it would auto-release to PyPi after realizing V1.2 didn't work

### v1.2.2:
Remove annoying print statements left in V1.2.1, Oops!

### V1.3.0:
Improved the code so that it was more readable and easier to understand, improved the listener outputs of [ auth_reset, auth_correct, auth_incorrect, disconnected] as they were the easiest:

auth_reset -> returns True when the auth is reset
auth_correct -> returns True when the auth is correct
auth_incorrect -> returns False when the auth is incorrect
disconnected -> returns in {"Reason": Reason} format with the reasons being: "Host Kicked Player", "Player Left", "Host Left the Game", if the disconnection reason is unknown please send it to me, it will be in the format: {"Reason": data, "Report": "This is an unknown disconnect, please report this and what happened"} with data being the WebSocket log

Thanks!
V1.3.1 should be out fairly soon, sorry for the wait kind of lost courage!

### V1.3.1:
I updated the readme.md file to include everything in the info directory
removed the info directory

Actually added documentation finally

Updated the rest of the listener functions to have relevant information (check the documentation for the updates)

V1.3.2 will add the ability to vote for brainstorming questions, hopefully, wont take too long

### V1.3.2:
Added the ability to vote for brainstorming

added functions:

RandomBrainstormVote(delay:int=.5)
BrainstormVote(vote:bool,OptionID:int)
FinishBrainstorming()

added the "brainstorm_voting" listener function for when brainstorm voting start

added the "QuestionType" to the question_started listener function (i can't believe i forgot this)

Updated the profile_generator to include the new profiles and cosmetics, made a thing to automate this process

updated documentation and readme to current release

V1.3.3 should fix the authentication brute force.

V1.4.1 will just be renaming functions as I like the format more and dont want 1.3.3 to be an outlier compared to 1.3.*. 
Ex: profile_generator -> GenerateProfile, random_answer -> RandomAnswer
