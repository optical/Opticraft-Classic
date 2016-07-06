# Opticraft-Classic

This is the new home for the original Opticraft Minecraft classic server, originally hosted over at sourceforge.

Opticraft-Classic is a project that was developed in my spare time during my first year of studies at university.
It fully implements the original classic server protocol and provides significantly more features than the vanilla server implementation.

## Features
Some of the main features provided by Opticraft include
* Plugin support (Written in Python 2)
* Customizable rank system
* Drawing commands
* Zone system
* Titles
* Chat colours
* Portals
* IRC Integration
* Significant performance improvement over Vanilla - Tested with hundreds of concurrent players on a cheap VM
* 127 Players per world
* Unlimited player cap, hardware allowing.

## Development
Opticraft will run on virtually any platform that supports Python 2. Once you've cloned the repository, you can simply run the server by executing `python run.py`.
The default configuration options should work for most setups, however they're worth tinkering with once you've got the server running.

### Plugins
There are several plugins which ship with opticraft, some of which provide core behaviour and are enabled by default. Plugins can be found within the Plugin directory.
The server determine which plugins to load via the configuration file setting.


## Contributing
Contributions are welcome! For small changes submit pull requests directly, however anything significant should start as an issue for discussion

## Disclaimer
The codebase has aged significantly, and in retrospect the code style chosen at the time might not've been the most standard.
Despite this the software is still in use today. Feel free to give it a look over.
