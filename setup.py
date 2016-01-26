#!/usr/bin/env python

from setuptools import setup

setup(
    name='Google-Music-Playlist-Sync',
    version='1.0.0',
    author='Shane Tully',
    author_email='shane@shanetully.com',
    scripts=['google-music-playlist-sync.py'],
    url='https://github.com/shanet/Google-Music-Playlist-Sync',
    license='LGPL3',
    description='A quick and dirty Python script to sync local XSPF or M3U playlists to Google Music',
    install_requires=[
        'gmusicapi >= 7.0.0',
        'mutagen   >= 1.20'
    ],
)
