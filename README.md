# Google-Music-Playlist Sync

#### shane tully
#### shane@shanetully.com

This is a simple Python script that uses the Unofficial-Google-Music-API to sync local XSPF or M3U format playlists to Google Music. For M3U playlists, the song info is determined by the song metadata so only MP3, FLAC, M4A, and MP4 formats are supported.

## Prerequisties

This script makes use of the Unofficial-Google-Music-API to interface with Google Music. To use it, you'll need to get to gmusicapi module from https://github.com/simon-weber/Unofficial-Google-Music-API. After cloning, run `python setup.py build` and then `sudo python setup.py install`.

Note that the gmusicapi changes often breaking this script. If this happens feel free to open an issue or submit a pull request fixing compatibility.

## Usage

Once the GoogleMusicAPI is installed, just run the playlist sync script like any other Python script. It will guide you through logging in and syncing songs.

If you use two-step authentication with your Google account, you can store your application specific key in a file called "pass.txt" in the same directory as the script. You should ONLY store an application specific key here. Storing your real password in plain text is a horrible idea. Granted, so is storing an app-specific key, so type it in each time if you want.

<pre>
usage: google-music-playlist-sync.py [-h] [-u [USER]] [-r [ROOT_DIR]] [-n]
                                     [-d] [-y]
                                     playlists [playlists ...]

positional arguments:
  playlists             The filenames of playlists.

optional arguments:
  -h, --help            show this help message and exit
  -u [USER], --user [USER]
                        The Google username/email to log in with.
  -r [ROOT_DIR], --root-dir [ROOT_DIR]
                        The root directory of a music directory. Useful for
                        M3U playlists.
  -n, --no-remove       Only add to playlists; don't remove anything.
  -d, --dry-run         Only show what would be sync'd; don't actually sync
                        anything.
  -y, --yes             Say yes to all prompts.
</pre>

## Credentials File

Users of two factor authentication can store an application specific password in a file so it does not need to be entered each time the script is run. To do this, place a file called `creds.json` in the same directory as the script with the following contents:

<pre>
{
  "username": "your username",
  "password": "your application specific password"
}
</pre>

**WARNING:** Do not store your regular password here as plain text!

Combining the credentials file with the `--yes` option allows for unattended synchronizations

## License

Copyright (C) 2013 Shane Tully

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
