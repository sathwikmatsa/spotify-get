#!/usr/bin/python

from __future__ import unicode_literals
from config import *
import os, sys
import string
import spotipy
import util
import requests
import youtube_dl
import lyricsgenius
import eyed3

def download_album_art(url):
    response = requests.get(url, stream=True)
    if response.ok:
        return response.content

def get_song_lyrics(track):
    if '-' in track['name']:
        return ""
    try:
        genius = lyricsgenius.Genius(GENIUS_CLIENT_ACCESS_TOKEN)
        song = genius.search_song(track['name'], track['album_artist'])
    except:
        return ""
    return song.lyrics

def add_metadata_to_song(song):
    #song = {'name': track_name,
    #        'album': album_name,
    #        'artists': artist_names,
    #        'album_artist': album_artist,
    #        'album_art': album_art_url
    #        'path': os.path.join(directory+'/', filename + '.mp3')
    #        }

    mp3 = eyed3.load(song['path'])
    mp3.tag.title = song['name']
    mp3.tag.album = song['album']
    mp3.tag.album_artist = song['album_artist']
    mp3.tag.artist = ", ".join(song['artists'])

    image_data = download_album_art(song['album_art'])
    mp3.tag.images.set(3, image_data, "image/jpeg")

    lyrics = get_song_lyrics(song)
    mp3.tag.lyrics.set(lyrics)

    mp3.tag.save()

    print("Added metadata to ", song['name'])
    return

def download_audio(searchItem, ofn, d):
    # searchItem : youtube query string
    # ofn : output filename
    # d : directory

    # create a dir if it doesn't exist
    if not os.path.exists(d):
        os.makedirs(d)

    ydl_opts = {
        'format': 'bestaudio',
        'outtmpl': d + '/' + ofn + '.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '320',
        }],
        'noplaylist': True,
        'quiet': False,  # debug
        'no_warnings': True,
    }

    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download(['ytsearch1:'+ searchItem])
    except KeyError as e:
        sys.exit()
    except:
        # retry
        download_audio(searchItem, ofn, d)


#def remove_np_chars(s):
#
#    # remove trailing whitespaces
#    s = s.strip()
#    # remove non printable characters
#    s = "".join(filter(lambda x: x in string.printable and x not in '-', s))
#    # remove consecutive whitespaces by split and join
#    s = " ".join(s.split())
#
#    return s



# get user_library_read access
library_read_token = util.obtain_user_token(
            username=USERNAME,
            client_id=SPOTIFY_CLIENT_ID,
            client_secret=SPOTIFY_CLIENT_SECRET,
            redirect_uri=SPOTIFY_REDIRECT_URI,
            scope='user-library-read',
            cache_file='.cache-library'
        )

user_library_read = spotipy.Spotify(auth=library_read_token)

# get user_follow_read access
#follow_read_token = util.obtain_user_token(
#            username=USERNAME,
#            client_id=SPOTIFY_CLIENT_ID,
#            client_secret=SPOTIFY_CLIENT_SECRET,
#            redirect_uri=SPOTIFY_REDIRECT_URI,
#            scope='user-follow-read',
#            cache_file='.cache-follow'
#        )
#
#user_follow_read = spotipy.Spotify(auth=follow_read_token)
#
#fav_artists = user_follow_read.current_user_followed_artists(limit=50)

# change directory to music
os.chdir(os.path.join(os.path.expanduser('~'), 'Music' ))


# retreive saved tracks
max_retrieved = 0
new_downloads = 0
while True:
    results = user_library_read.current_user_saved_tracks(limit=50)
    max_retrieved += 50

    # extract track info
    for item in results['items']:

        track = item['track']
        artists = track['artists']

        track_name = track['name']
        album_name = track['album']['name']
        artist_names = [artist['name'] for artist in artists]
        album_artist = artist_names[0]
        album_art_url = track['album']['images'][0]['url']

        filename = track_name
        directory = album_artist

        song = {'name': track_name,
                'album': album_name,
                'artists': artist_names,
                'album_artist': album_artist,
                'album_art': album_art_url,
                'path': os.path.join(directory+'/', filename + '.mp3')
                }

        query = track_name + ' ' + " ".join(artist_names) + ' official audio'

        # ignore if song already downloaded
        if not os.path.exists(song['path']):
            print("Downloading: ", directory + '/' + filename + '.mp3')
            download_audio(query, filename, directory)
            add_metadata_to_song(song)
            new_downloads += 1

    if max_retrieved >= results['total']:
        break

print("Total no. of new songs downloaded: ", new_downloads)

