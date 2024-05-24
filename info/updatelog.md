
# V1.0:
First Release!
Bot can connect to classic game mode and can answer quiz type question, joins using websocket, and can undestand some events within the game!

# V1.1:
Added support for all question types in Client.random_answer() and Client.submit_answer()

# V1.2:
Fixed the Client.change_profile() function so it actually works
Added a way to crash the kahoot lobby with Client.crash_looby()
Added a way to bypass the 2-step-join Kahoot feature

# v1.2.1:
Updated Github files so that it would auto-release to PyPi after realizing V1.2 didn't work

# v1.2.2:
Remove annoying print statements left in V1.2.1, Oops!

# V1.3.0:
Improved the code so that it was more readable and easier to understand, improved the listener outputs of [ auth_reset, auth_correct, auth_incorrect, disconnected] as they were the easiest:

auth_reset -> returns True when the auth is reset
auth_correct -> returns True when the auth is correct
auth_incorrect -> returns False when the auth is incorrect
disconnected -> returns in {"Reason": Reason} format with the reasons being: "Host Kicked Player", "Player Left", "Host Left the Game", if the disconnection reason is unknown please send it to me, it will be in the format: {"Reason": data,"Report": "This is an unknown disconnect, please report this and what happened"} with data being the WebSocket log

Thanks!
V1.3.1 should be out fairly soon, sorry for the wait kinda lost courage!
