#!/usr/bin/env python2

# Shane Tully (shane@shanetully.com)
# shanetully.com

# GitHub repo: https://github.com/shanet/Google-Music-Playlist-Sync
# Makes use of the Unofficial Google Music API by Simon Weber
# https://github.com/simon-weber/Unofficial-Google-Music-API

# Copyright (C) 2013 Shane Tully

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.

# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import argparse
import difflib
import re
import sys

from os                    import path
from getpass               import getpass
from gmusicapi             import Mobileclient
from mutagen.easyid3       import EasyID3
from mutagen.easymp4       import EasyMP4
from mutagen.flac          import FLAC
from mutagen.id3           import ID3NoHeaderError
from xml.etree.ElementTree import parse

no_remove = False
dry_run = False
yes = False

def main():
    [user, root_dir, playlists] = parse_cmdline_args()

    # Show some pretty ASCII art
    print "  ____                   _        __  __           _        ____  _             _ _     _     ____                   "
    print " / ___| ___   ___   __ _| | ___  |  \/  |_   _ ___(_) ___  |  _ \| | __ _ _   _| (_)___| |_  / ___| _   _ _ __   ___ "
    print "| |  _ / _ \ / _ \ / _` | |/ _ \ | |\/| | | | / __| |/ __| | |_) | |/ _` | | | | | / __| __| \___ \| | | | '_ \ / __|"
    print "| |_| | (_) | (_) | (_| | |  __/ | |  | | |_| \__ \ | (__  |  __/| | (_| | |_| | | \__ \ |_   ___) | |_| | | | | (__ "
    print " \____|\___/ \___/ \__, |_|\___| |_|  |_|\__,_|___/_|\___| |_|   |_|\__,_|\__, |_|_|___/\__| |____/ \__, |_| |_|\___|"
    print "                   |___/                                                  |___/                     |___/            "

    print '\nThis script will sync a local XSPF or M3U format playlist, to a playlist on Google Music. Use the Google Music uploader to\nfirst upload the songs in the playlist.\n'

    # Log in to Google Music
    api = login_to_google_music(user)

    # Get all songs in the library
    print 'Retrieving all songs in library. This may take a minute...'
    remote_library = api.get_all_songs()

    for playlist in playlists:
        print 'Syncing playlist: %s' % (playlist)
        process_playlist(api, playlist, remote_library, root_dir)

    # Be a good citizen and log out
    api.logout()
    print 'Bye!'
    exit(0)


def parse_cmdline_args():
    argvParser = argparse.ArgumentParser()
    argvParser.add_argument('-u', '--user', dest='user', nargs='?', help='The Google username/email to log in with.')
    argvParser.add_argument('-r', '--root-dir', dest='root_dir', nargs='?', default='./', help='The root directory of a music directory. Useful for M3U playlists.')
    argvParser.add_argument('-n', '--no-remove', dest='no_remove', action='store_true', help='Only add to playlists; don\'t remove anything.')
    argvParser.add_argument('-d', '--dry-run', dest='dry_run', action='store_true', help='Only show what would be sync\'d; don\'t actually sync anything.')
    argvParser.add_argument('-y', '--yes', dest='yes', action='store_true', help='Say yes to all prompts.')
    argvParser.add_argument('playlists', nargs='+', help='The filenames of playlists.')

    args = argvParser.parse_args()

    # If the root directory doesn't have a directory separator at the end, add it
    if not args.root_dir.endswith('/'):
        args.root_dir += '/'

    if args.no_remove:
        global no_remove
        no_remove = args.no_remove

    if args.dry_run:
        global dry_run
        dry_run = args.dry_run

    if args.yes:
        global yes
        yes = args.yes

    return [args.user, args.root_dir, args.playlists]


def login_to_google_music(user):
    api = Mobileclient()
    attempts = 0

    while attempts < 3:
        if user == None:
            user = raw_input('Google username or email: ')

        # Try to read the password from a file
        # If file doesn't exist, ask for password
        # This is useful for 2-step authentication only
        # Don't store your regular password in plain text!
        try:
            pw_file = open('pass.txt')
            password = pw_file.readline()
            print 'Reading password from pass.txt.'
        except IOError:
            password = getpass()

        print '\nLogging in...'
        if api.login(user, password):
            return api
        else:
            print 'Login failed.'
            # Set the username to none so it is prompted to be re-entered on the next loop iteration
            user = None
            attempts += 1

    print '%d failed login attempts. Giving up.' % (attempts)
    exit(0)


def process_playlist(api, local_playlist_path, remote_library, root_dir):
    # Get the filename. This will be used as the playlist name.
    local_playlist_name, local_playlist_type = path.splitext(path.basename(local_playlist_path))

    # Check that the file extension and parse the playlist
    if local_playlist_type == '.xspf':
        (name, local_tracks) = parse_xml(local_playlist_path)
        # If the xml contained a playlist name, use that instead of the filename
        if name:
            local_playlist_name = name
    elif local_playlist_type == '.m3u':
        local_tracks = parse_m3u(local_playlist_path, root_dir)

    else:
        print 'Error: Playlist \'%s\' must be XSPF or M3U format.' % (local_playlist_name)
        return

    # Check that the playlist has tracks in it
    if len(local_tracks) == 0:
        print 'Error: Playlist \'%s\' is empty.' % (local_playlist_name)
        if local_playlist_type == '.m3u':
            print 'Friendly reminder: m3u playlists use relative paths. Use the \'--root-dir\' option for syncing m3u playlists in a different directory than this script.'
        return

    # Sync the playlist
    if sync_playlist(api, remote_library, local_tracks , local_playlist_name):
        print 'Playlist \'%s\' sync\'d.' % (local_playlist_name)
    else:
        print 'Syncing playlist \'%s\' failed.' % (local_playlist_name)
        return


def parse_xml(local_playlist_path):
    # Parse the playlist XML file
    xml_root = parse(local_playlist_path).getroot()

    # Get the playlist title
    playlist_name = None
    title_element = xml_root.find('{http://xspf.org/ns/0/}title')
    if not title_element is None:
        playlist_name = title_element.text.strip()

    # Get the list of tracks in the playlists
    tracks_elements = xml_root.find('{http://xspf.org/ns/0/}trackList')
    if tracks_elements is None:
        print 'Error: Malformed or empty playlist.'
        exit(1)

    # Convert the XML elements to a dict
    tracks = []
    for track in tracks_elements:
        new_track = {}
        for field in track:
            if field.tag == '{http://xspf.org/ns/0/}title':
                new_track['title'] = field.text.strip()
            elif field.tag == '{http://xspf.org/ns/0/}creator':
                new_track['artist'] = field.text.strip()
            elif field.tag == '{http://xspf.org/ns/0/}album':
                new_track['album'] = field.text.strip()
            elif field.tag == '{http://xspf.org/ns/0/}location':
                new_track['path'] = field.text.strip()
        tracks.append(new_track)

    return (playlist_name, tracks)


def parse_m3u(local_playlist_path, root_dir):
    playlist = open(local_playlist_path, 'r')

    # Convert the tracks in the playlist into a dict
    tracks = []
    for line in playlist:
        # Remove the newline from the end of the string
        line = line.rstrip()

        format = get_song_format(line)

        try:
            if format == 'mp3':
                song = EasyID3(root_dir + line)
            elif format == 'mp4' or format == 'm4a':
                song = EasyMP4(root_dir + line)
            elif format == 'flac':
                song = FLAC(root_dir + line)
            else:
                print '\'%s\' is not a supported format. Supported formats are MP3, MP4, M4A, or FLAC.' % (line)
                continue
        except ID3NoHeaderError:
            print '\'%s\' does not contain an ID3 tag.' % (filename)
            continue
        # IO errors are most likely file not found errors or the wrong format file
        except IOError as ioe:
            print '\'' + line + '\': ' + ioe.strerror
            continue

        # Only take the first metadata info for each category
        try:
            track = {}
            track['title']  = song['title'][0]
            track['artist'] = song['artist'][0]
            track['album']  = song['album'][0]
            track['path']   = root_dir + line
            tracks.append(track)
        except KeyError:
            print 'The following track has missing metadata: %s. Skipping.' % str(track)

    return tracks


def get_song_format(filename):
    # Use the filename extension as the format
    return path.splitext(path.basename(filename))[1].lower()[1:]


def sync_playlist(api, remote_library, local_tracks, local_playlist_name):
    global dry_run

    remote_playlist = get_playlist(api, local_playlist_name)

    # If the playlist wasn't found, create it
    if remote_playlist is None:
        print 'Playlist not found on Google Music. Creating it.'
        if dry_run:
            print 'Dry-run option given, but cannot continue without creating new playlist.'
            return False
        api.create_playlist(local_playlist_name)
        remote_playlist = get_playlist(api, local_playlist_name)

    # Tracks on playlists have IDs unique to that playlist. We need the ID for the overall track.
    remote_tracks = get_track_ids_from_playlist_ids(remote_playlist['tracks'], remote_library)

    # Get the tracks to be added/removed from the remote playlist
    (tracks_to_add_ids, tracks_to_add_names) = get_tracks_to_add(api, local_tracks, remote_tracks, remote_library)
    (tracks_to_remove_ids, tracks_to_remove_names) = get_tracks_to_remove(api, local_tracks, remote_tracks)

    # Check that there are tracks to add/remove
    if len(tracks_to_add_ids) == 0 and len(tracks_to_remove_ids) == 0:
        print '\nPlaylist is already up-to-date.'
        return True

    # Finally, add/remove the tracks to/from the playlist
    if confirm_pending_modifications(local_playlist_name, tracks_to_add_names, tracks_to_remove_names):
        if not dry_run:
            api.add_songs_to_playlist(remote_playlist['id'], tracks_to_add_ids)
            api.remove_entries_from_playlist(tracks_to_remove_ids)
        else:
            print 'Dry-run enabled. Not doing anything.'
    else:
        print 'Sorry!'
        return False

    return True


def get_playlist(api, local_playlist_name):
    remote_playlists = api.get_all_user_playlist_contents()

    remote_playlist = None
    for playlist in remote_playlists:
        if playlist['name'] == local_playlist_name:
            return playlist

    return None


def get_track_ids_from_playlist_ids(playlist_tracks, remote_library):
    tracks = []

    # Find the track in the library each playlist track cooresponds to
    for track in remote_library:
        for playlist_track in playlist_tracks:
            if track['id'] == playlist_track['trackId']:
                # Keep the unique playlist track ID for track removal from the playlist
                track['playlistId'] = playlist_track['id']
                tracks.append(track)

    return tracks


def get_tracks_to_add(api, local_tracks, remote_tracks, remote_library):
    track_names = []
    track_ids = []

    for local_track in local_tracks:
        # Check if the local track is already present in the remote playlist
        result = find_track(local_track, remote_tracks)

        if result is None:
            track_id = find_track_id(local_track, remote_library)

            # Check if the song wasn't found in the library
            if track_id == None:
                print 'Warning: Track \'%s - %s\' in local playlist, but not found in Google Music library. Skipping this track.' % (local_track['artist'], local_track['title'])
            else:
                track_names.append('%s - %s' % (local_track['artist'], local_track['title']))
                track_ids.append(track_id)

    return (track_ids, track_names)


def get_tracks_to_remove(api, local_tracks, remote_tracks):
    global no_remove
    if no_remove:
        return ([], [])

    track_names = []
    track_ids = []
        
    for remote_track in remote_tracks:
        # Check if the remote track is present in the local playlist
        result = find_track(remote_track, local_tracks)

        if result is None:
            track_names.append('%s - %s' % (remote_track['artist'], remote_track['title']))
            track_ids.append(remote_track['playlistId'])

    return (track_ids, track_names)


def find_track(local_track, remote_library):
    artist_match = difflib.SequenceMatcher(None, 'foobar', clean_string(local_track['artist']))
    title_match = difflib.SequenceMatcher(None, 'foobar', clean_string(local_track['title']))
    best_match = 0

    for remote_track in remote_library:
        artist_match.set_seq1(clean_string(remote_track['artist']))
        title_match.set_seq1(clean_string(remote_track['title']))

        artist_score = artist_match.quick_ratio()
        title_score = title_match.quick_ratio()
        
        total_score = (artist_score + title_score) / 2

        if total_score == 1:
            return remote_track
        elif total_score >= best_match:
            best_match = total_score
            best_match_track = remote_track

    if best_match >= 0.85:
        return best_match_track
    else:
        return None


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


def find_track_id(track, remote_library):
    remote_track = find_track(track, remote_library)
    return (remote_track['id'] if remote_track else None)


def confirm_pending_modifications(playlist_name, tracks_to_add, tracks_to_remove):
    print  '\nPlaylist \'%s\' will be modified.' % (playlist_name)

    # Print the songs about to be added/removed
    if len(tracks_to_add) > 0:
        print 'Tracks to be added:'
        for track in tracks_to_add:
            print '\t' + track
        
    if len(tracks_to_remove) > 0:
        print 'Tracks to be removed:'
        for track in tracks_to_remove:
            print '\t' + track

    global yes
    return (yes or raw_input('Is this okay? (y,n) ') == 'y')


if __name__ == '__main__':
    main()
