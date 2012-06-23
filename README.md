# Google-Music-Playlist Sync
#### Shane Tully (shane@shanetully.com)
#### shanetully.com

This is a simple Python script that uses the Unofficial-Google-Music-API to sync local XSPF format playlists to Google Music.

## Prerequisties

This scripts makes use of the Unofficial-Google-Music-API to interface with Google Music. To use it, you'll need to get to gmusicapi module from https://github.com/simon-weber/Unofficial-Google-Music-API

## Usage

Just run it like any other Python script. It will guide you through logging in and syncing songs.

If you use two-step authentication with your Google account, you can store your application specific key in a file called "pass.txt" in the same directory as the script. You should ONLY store an application specific key here. Storing your real password in plain text is a horrible idea. Granted, so is storing an app-specific key, so type it in each time if you want.

    Usage: ./google-music-playlist-sync.py [options] [path to playlist]
        The only valid options at this time are "-h" or "--help" to display this message.
        If a playlist is not specified, a path to one will be asked for.

## Support
This program is a little side project and carries no warranty or support
from its author. However, bugs and feature requests may be submitted to the GitHub repo
linked to above.


## Legal
This program is open source software. It is free to distribute, modify, and use
with the exception of it being made closed source and sold for commercial purposes
without the consent of the author. However, the author simply requests that if you 
do something cool with it, you let him check it out by emailing shane@shanetully.com 
or just let him know you find it useful.