# Navidrome On Console Player

NOCP (Navidrome On Console Player) is a console audio player designed to be powerful and easy to use inpired bien MOCP (Music On Console Player).

[Navidrome](https://www.navidrome.org/) is an open source web-based music collection server and streamer. It gives you freedom to listen to your music collection from any browser or mobile device. It's like your personal Spotify!

![custom-field](nocpglobal.png "Nocp")


## install

install by [pypi](https://pypi.org/project/nocp/)

> pip install nocp



## usage

> nocp --help

> nocp --server-url http://myserver-navidrome/rest --username myusername --password mypassword --lang en_US

after just

> nocp

You can access to three views

- listing song (shorcut **m**)
- listing radio (shorcut **r**)
- listing playlist (shorcut **l**)

You can access to

- help (shorcut **h**)
- volume (shorcut **v**)

You can listen to a song by selecting it and pressing "Enter"

![custom-field](nocpaction.png "help")

List of available languages

- English
- French
- German
- Spanish
- Italian
- Portuguese


## addshorcut

on ubuntu, create file ~/.local/share/applications/nocp.desktop

```
[Desktop Entry]
Type=Application
Name=Nocp
Exec=gnome-terminal -- bash -c 'nocp; exit;'
Icon=utilities-terminal
Terminal=false
```

and

> chmod +x ~/.local/share/applications/nocp.desktop


## todo

- random listen