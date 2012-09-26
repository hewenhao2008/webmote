=====================
WHICH LICENSE HERE???
=====================

![Remote](https://raw.github.com/dmritard96/webmote/master/server/webmote_django/static/remote.png)
![Record](https://raw.github.com/dmritard96/webmote/master/server/webmote_django/static/record.png)


This project aims to allow any type of device to be controlled by a common web interface (IR, X10, etc.).

The original project is located at https://github.com/azylman/webmote and was written by Daniel Myers, Alex Wilson, and Alex Zylman. This rewrite serves to improve extensibility by using a plugin architechture with a minimal core and plugins for features or protocols.


Goals:
------
*Extensible - plugins for new protocols and functionality
*Mobile web interface - works on any browser on any platform
*Simple enough for my parents (old) to setup
*(eventually) Serve media connected to the server, upload to, download to, etc (this is more of a long term goal...)


Core Description:
-----------------
A set of superclasses (and associated methods) for the plugins to expand on.


Plugin Description:
-------------------
A set of subclasses, files and routines that expand the functionality of webmote.
The format is as follows:

A top level directory containing at least:
    templates (directory)
        html files containing pages specific to the plugin
    static    (directory)
        images, javascript, etc.
    models.py
    urls.py
    views.py
    __init__.py
    info.json
        authors
        version
        name
        url


Tasks:
------
Raspberry pi testing
Start on X10 plugin
Secondary:
    Remote/Local Media player
        In browser file browser
        Mobile playback
        Local playback
 

Setup:
------
```bash
#install virtualenv, pip
sudo apt-get install python-virtualenv, python-pip
cd webmote
./install
```


Run (development server):
-------------------------
```bash
./run
```
