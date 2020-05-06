#!/usr/bin/env python3
# Copyright 2019, Chris Oboe
# SPDX-License-Identifier: GPL-3.0

import argparse
import tidalapi
import mutagen
from enum import Enum
from pprint import pprint
from requests import get
from pathlib import Path
import sys
import shlex
import xml.etree.ElementTree as ET
import re
import subprocess
import random

class Type(Enum):
    track = 1
    album = 2
    artist = 3


def download(url, path):
    with open(path, "wb") as file:
        response = get(url)
        file.write(response.content)


class Cli(object):
    tidal = 0

    def __init__(self):
        parser = argparse.ArgumentParser(
            description=
            'Scrapes metadata from tidal and writes it to the tags or as nfo')
        parser.add_argument('username', help="The username")
        parser.add_argument('password', help="The password")
        parser.add_argument('command', choices=Type.__members__)

        args = parser.parse_args(sys.argv[1:4])
        if not hasattr(self, args.command):
            print("Unrecognized command")
            parser.print_help()
            exit(1)

        self.tidal = tidalapi.Session()
        self.tidal.login(args.username, args.password)
        getattr(self, args.command)()

    def track(self):
        parser = argparse.ArgumentParser(
            description="Tags a track with data from tidal")
        parser.add_argument(
            'trackid',
            metavar='trackid',
            type=int,
            help="The track id from tidal")
        parser.add_argument('file', metavar='file', help="The file to tag")
        args = parser.parse_args(sys.argv[4:])

        # get data
        track = self.tidal.get_track(args.trackid)
        album = self.tidal.get_album(track.album.id)

        # create artiststring with feat. etc. 
        artiststring = track.artists[0].name
        if len(track.artists) > 1:
            artiststring += " feat. "

        for artist in track.artists[1:]:
            artiststring += artist.name
            if (artist != track.artists[-1]):
                if (artist == track.artists[-2]):
                    artiststring += ' & '
                else:
                    artiststring += ', '

        # tag file
        tags = mutagen.File(args.file)
        tags.delete()

        if tags.__class__.__name__ == "MP4":
            tags['\xa9nam'] = track.name
            tags['\xa9ART'] = artiststring
            tags['\xa9alb'] = album.name
            tags['aART'] = album.artist.name
            if track.track_num:
                if album.num_tracks:
                    tags['trkn'] = [(track.track_num, album.num_tracks)]
                else:
                    tags['trkn'] = [(track.track_num, 0)]

            if track.disc_num:
                if album.num_discs:
                    tags['disk'] = [(track.disc_num, album.num_discs)]
                else:
                    tags['disk'] = [(track.disc_num, 1)]

            if album.release_date:
                tags['\xa9day'] = str(album.release_date.year)
 
        else:
            tags['title'] = track.name
            tags['artist'] = artiststring
            tags['album'] = album.name
            tags['albumartist'] = album.artist.name
            tags['tracknumber'] = str(track.track_num)
            tags['discnumber'] = str(track.disc_num)
            if album.num_tracks:
                tags['totaltracks'] = str(album.num_tracks)
            if album.num_discs:
                tags['totaldiscs'] = str(album.num_discs)
            if album.release_date:
                tags['year'] = str(album.release_date.year)
        
        tags.save()

    def album(self):
        parser = argparse.ArgumentParser(
            description="Writes a nfo with album infos")
        parser.add_argument(
            'albumid',
            metavar='albumid',
            type=int,
            help="The album id from tidal")
        parser.add_argument('nfo', metavar='nfo', help="The nfo to write")
        parser.add_argument(
            'cover', metavar='cover', help="The cover image to write")
        parser.add_argument('files', metavar='files', nargs='+', help="The files of the album")
        args = parser.parse_args(sys.argv[4:])

        album = self.tidal.get_album(args.albumid)

        # download album art
        download(album.image, args.cover)

        # create album nfo
        nfo_album = ET.Element('album')
        if album.name:
            nfo_title = ET.SubElement(nfo_album, 'title')
            nfo_title.text = album.name
        if album.release_date:
            nfo_year = ET.SubElement(nfo_album, 'year')
            nfo_year.text = str(album.release_date.year)

        with open(args.nfo, 'w') as nfo:
            nfo.write(ET.tostring(nfo_album, encoding='unicode'))

        # calculate replaygain values
        subprocess.run(['loudgain', '--pregain=-5', '--noclip', '--tagmode=l', *args.files])

    def artist(self):
        parser = argparse.ArgumentParser(
            description="Writes a nfo with artist infos")
        parser.add_argument(
            'artistid',
            metavar='artistid',
            type=int,
            help="The artist id from tidal")
        parser.add_argument('file', metavar='file', help="The nfo to write")
        parser.add_argument(
            'image', metavar='image', help="The artist image to write")
        args = parser.parse_args(sys.argv[4:])

        artist = self.tidal.get_artist(args.artistid)
        bio = self.tidal.get_artist_bio(args.artistid)
        download(artist.image, args.image)

        nfo_artist = ET.Element('artist')
        if artist.name:
            nfo_name = ET.SubElement(nfo_artist, 'name')
            nfo_name.text = artist.name
        if bio:
            # strip tidal specific stuff
            bio = re.sub("\[.*?\]", "", bio)
            nfo_biography = ET.SubElement(nfo_artist, 'biography')
            nfo_biography.text = bio

        with open(args.file, 'w') as file:
            file.write(ET.tostring(nfo_artist, encoding='unicode'))

if __name__ == '__main__':
    Cli()
