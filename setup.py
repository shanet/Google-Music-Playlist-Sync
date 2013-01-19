from setuptools import setup

setup(
    name='Google-Music-Playlist-Sync',
    version='0.1.0',
    author='Shane Tully',
    author_email='shane@shanetully.com',
    scripts=['google-music-playlist-sync.py'],
    url='https://github.com/shanet/Google-Music-Playlist-Sync',
    license='COPYING',
    description='A quick and dirty Python script to sync local XSPF playlists to Google Music',
    install_requires=[
        'gmusicapi >= 2013.01.05'
    ],
)
