#!/usr/bin/env python

# Shane Tully
# 
# GitHub repo: https://github.com/shanet/Google-Music-Playlist-Sync
#
# This program is open source software. It is free to distribute, modify, and use
# with the exception of it being made closed source and sold for commercial purposes
# without the consent of the author.
#
# Makes use of the Unofficial Google Music API by Simon Weber
# https://github.com/simon-weber/Unofficial-Google-Music-API

import sys
from os import path
import re
import difflib
from getpass import getpass
from xml.etree.ElementTree import parse
from gmusicapi.api import Api


def init():
    api = Api() 
    
    logged_in = False
    attempts = 0

    while not logged_in and attempts < 3:
        email = raw_input("Google username or email: ")

        # Try to read the password from a file
        # If file doesn't exist, ask for password
        # This is useful for 2-step authentication only
        # Don't store your regular password in plain text
        try:
            pw_file = open("pass.txt")
            password = pw_file.readline()
            print "Reading password from pass.txt."
        except IOError:
            password = getpass()

        print "\nLogging in..."
        logged_in = api.login(email, password)
        if not logged_in:
            print "Log in failed."
        attempts += 1

    return api


def parse_xml(l_pl_path):
    # Parse the playlist XML file
    l_pl = parse(l_pl_path).getroot()

    # Get the list of tracks in the playlists
    l_tracks_elems = l_pl.find("{http://xspf.org/ns/0/}trackList")
    if l_tracks_elems is None:
        print "Error: Malformed or empty playlist."
        exit(1)

    # Convert the XML elements to a dict
    l_tracks = []
    for l_track in l_tracks_elems:
        track = {}
        for field in l_track:
            if field.tag == "{http://xspf.org/ns/0/}title":
                track['title'] = field.text.strip()
            elif field.tag == "{http://xspf.org/ns/0/}creator":
                track['artist'] = field.text.strip()
            elif field.tag == "{http://xspf.org/ns/0/}album":
                track['album'] = field.text.strip()
            elif field.tag == "{http://xspf.org/ns/0/}location":
                track['path'] = field.text.strip()
        l_tracks.append(track)

    return l_tracks


def print_usage(prog):
    print "Usage: " + prog + " [options] [path to playlist]\n"
    print "\tThe only valid options at this time are \"-h\" or \"--help\" to display this message."
    print "\tIf a playlist is not specified, a path to one will be asked for."


def clean_string(string):
    # Strip whitespaces and use lowercase
    string = string.strip()
    string = string.lower()

    # Remove (feat. [some artist])
    patterns = ['^(.*?)\(feat\..*?\).*?$',  '^(.*?)feat\..*?$']
    for pattern in patterns:
        reg = re.search(pattern,  string)
        if reg:
            string = reg.group(1)

    return string


def find_track(l_track,  trackList):
    seqMatchArtist = difflib.SequenceMatcher(None, "foobar", clean_string(l_track["artist"]))
    seqMatchTitle = difflib.SequenceMatcher(None, "foobar", clean_string(l_track["title"]))

    for remoteTrack in trackList:
        seqMatchArtist.set_seq1(clean_string(remoteTrack["artist"]))
        seqMatchTitle.set_seq1(clean_string(remoteTrack["title"]))

        scoreArtist = seqMatchArtist.quick_ratio()
        scoreTitle = seqMatchTitle.quick_ratio()
        
        totalScore = (scoreArtist + scoreTitle) / 2
        if totalScore >= 0.85:
            return remoteTrack

    return False


def main():
    # Show help if requested
    if len(sys.argv) == 2 and (sys.argv[1] == "--help" or sys.argv[1] == "-h"):
        print_usage(sys.argv[0])
        exit(0)

    # Show some pretty ASCII art
    print "  ____                   _        __  __           _        ____  _             _ _     _     ____                   "
    print " / ___| ___   ___   __ _| | ___  |  \/  |_   _ ___(_) ___  |  _ \| | __ _ _   _| (_)___| |_  / ___| _   _ _ __   ___ "
    print "| |  _ / _ \ / _ \ / _` | |/ _ \ | |\/| | | | / __| |/ __| | |_) | |/ _` | | | | | / __| __| \___ \| | | | '_ \ / __|"
    print "| |_| | (_) | (_) | (_| | |  __/ | |  | | |_| \__ \ | (__  |  __/| | (_| | |_| | | \__ \ |_   ___) | |_| | | | | (__ "
    print " \____|\___/ \___/ \__, |_|\___| |_|  |_|\__,_|___/_|\___| |_|   |_|\__,_|\__, |_|_|___/\__| |____/ \__, |_| |_|\___|"
    print "                   |___/                                                  |___/                     |___/            "

    print "\nThis script will sync a local XSPF format playlist, to a playlist on Google Music. Use the Google Music uploader to\nfirst upload the songs in the playlist.\n"

    # Log in to Google Music
    api = init()

    if not api.is_authenticated():
        print "Sorry, those credentials weren't accepted."
        exit(1)

    print "Successfully logged in.\n"

    # Check if the playlist file was given as a command line arg
    if len(sys.argv) == 2:
        print "Using \"" + sys.argv[1] + "\" as playlist to sync."
        l_pl_path = sys.argv[1]
    elif len(sys.argv) > 2:
        print "Too many command line arguments given."
        api.logout
        exit(1)
    else:
        # Prompt for the playlist file to use
        l_pl_path = raw_input("Path to playlist file: ")

    # Get the filename. This will be used as the playlist name.
    l_pl_name, l_pl_type = path.splitext(path.basename(l_pl_path))

    # Check that the file extension is xspf
    if l_pl_type != ".xspf":
        print "Error: Playlist must be XSPF format."
        api.logout()
        exit(1);

    # Parse the playlist
    l_tracks = parse_xml(l_pl_path)

    # Check that the playlist has tracks in it
    if len(l_tracks) == 0:
        print "Error: Playlist is empty."
        api.logout
        exit(1)

    # Get all available playlists from Google Music
    r_pls = api.get_all_playlist_ids(False, True)

    # Try to find the playlist if it already exists
    r_pl_id = None
    r_pl_items = r_pls['user'].items()
    for i in range(len(r_pl_items)):
        if r_pl_items[i][0] == l_pl_name:
            # Check if there are multiple playlists with that name
            if type(r_pl_items[i][1]) is list:
                # TODO: Handle multiple playlists with the same name
                print "Found multiple playlists with that name. Defaulting to the first one."
                r_pl_id = r_pl_items[i][1][0]
            else:
                r_pl_id = r_pl_items[i][1]
            print "Found playlist with ID: " + r_pl_id
            break

    # If the playlist wasn't found, create it
    if r_pl_id is None:
        print "Playlist not found on Google Music. Creating it."
        r_pl_id = api.create_playlist(l_pl_name)

    # Get the songs on the playlist
    r_tracks = api.get_playlist_songs(r_pl_id)

    # Get all songs in the library
    r_library = api.get_all_songs()

    # Check if each track in the local playlist is on the Google Music playlist
    tracks_to_add_names = []
    tracks_to_add_ids = []
    for l_track in l_tracks:
        added = False
        # Check if the track is already present in the playlist
        if find_track(l_track,  r_tracks) != False:
            added = True

        # Add the track to the playlist
        if not added:
            # Find the song ID
            l_track_id = None
            matchedTrack = find_track(l_track,  r_library)
            if matchedTrack:
                l_track_id = matchedTrack['id']
                tracks_to_add_names.append(matchedTrack['artist'] + " - " + matchedTrack['title'])
                tracks_to_add_ids.append(matchedTrack['id'])

            # Check if the song wasn't found in the library
            if l_track_id == None:
                print "Error: Track \"" + l_track['title'] + "\" in local playlist, but not found in Google Music library. Skipping this track."
                continue

    # Check that there are tracks to add
    if len(tracks_to_add_ids) == 0:
        print "\nPlaylist is already up-to-date."
        api.logout
        exit(0)

    # Print the songs about to be added
    print "Tracks to be added:"
    for track in tracks_to_add_names:
        print "\t" + track
    print  "\nThe above tracks will be added to the playlist \"" + l_pl_name + "\""
    if raw_input("Is this okay? (y,n) ") == "y":
        # Finally, add the new track to the playlist
        for track_id in tracks_to_add_ids:
            api.add_songs_to_playlist(r_pl_id, track_id)
        print "\nTracks added to playlist!"
    else:
        print "Sorry!\n"

    # Be a good citizen and log out
    api.logout()
    print "\nBye!"
    exit(0)


if __name__ == '__main__':
    main()
