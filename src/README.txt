Thanks for choosing opticraft!

== INSTALLING ==

*Windows*:
If you have downloaded the binary version of opticraft you may skip the installation step and go to configuration

If you have downloaded the source, you will need to download and install python 2.6.
Python 2.6 download: http://www.python.org/download/releases/2.6/

Once you have installed python 2.6, proceed to the configuration step

*Unix / Mac OS X*:
Most distributions come with python 2.6 preinstalled. However, if your variant
does not have it, you will need to manually install it.

General instructions can be found at http://www.python.org/download/releases/2.6/
See your vendor for more specific information on how to install python 2.6.


== Configuration ==

Windows users: Open up opticraft.ini in a plain text editor, such as notepad (Notepad should be the default editor for .ini files)
Unix/Mac OS X: Open it with your favourite editor, such as vi or nano.

The configuration file is relatively straight forward. Edit the settings as you go along.
This will allow you to change the Name and Motd of the server, as well as the player cap and port it runs on.
Other more advanced settings can also be changed, such as disabling Block Logs, and enabling the IRC bot.

Finally, you will want to open up ranks.ini and give yourself the owner permission flag. This will set you as
an owner and give you access to all ingame commands.

== Running ==

Windows: If you have the binary package, simply run Opticraft.exe
	 If you have the source, run "run.py" by either double clicking it, or from a command prompt.
Unix/Mac OS X: navigate to the directory you extracted opticraft to, and execute run.py in the console
	     : with the command: python run.py

The server will then register itself with www.minecraft.net, and give you your specific URL so users can connect to it.

== Commands ==

This section contains a brief description of some of the important commands available.
To see a full list of commands, use /commands ingame, and /help <command> to get help on specific commands

/kick <username>: Kicks a user from the server
/ban <username>: Bans a user from the server
/ipban <username/ip>: Ipbans a user and their ipaddress from the server. Accepts either a currently connect username, or an ip address
/join <world>: Changes to another world
/worlds: Lists all available worlds
/createworld <name> <x> <y> <z>: Creates a new world
/zcreate: Starts the zone creation process.
/modifyrank <username> <rank>: Sets a users rank to a rank. Valid ranks include: Guest, Builder, operator or Admin
/worldsetrank <World> <Rank>: Sets the worlds minimum rank to build on it. 
                                   : Eg /worldsetrank Guest Builder. Will allows on builders and above to edit the world Guest

