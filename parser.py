# !/usr/bin/local
# -*- coding:utf-8 -*-
import urllib
from time import sleep as sl
from random import randint
from BeautifulSoup import BeautifulSoup
import os
import io
from pymongo import MongoClient
from sqlalchemy import create_engine, Table, Column, MetaData, String
from change_color import change_pic
import socket
socket.setdefaulttimeout(2)

def mongo_init():
    client = MongoClient('localhost', 27017)
    db = client.songs_database
    db.drop_collection("songs")
    return db

def sqlite_init():
    db = create_engine('sqlite:///songs_singers.db')
    db.echo = False  # Try changing this to True and see what happens
    metadata = MetaData(db)
    songs = Table('songs', metadata,
                Column('type', String),
                Column('page_num', String),
                Column('rus_name', String),
                Column('eng_name', String),
                Column('song_words', String),
                Column('txt_path', String),
                Column('url', String),
                Column('song_name', String))
    metadata.drop_all()
    songs.create()
    return songs

class AmDmParser(object):
    def __init__(self, datatable_sqlite, datatable_mongo):
        self.songs_db = datatable_sqlite
        self.mongo_songs = datatable_mongo
        self.cyr_art, self.lat_art = {}, {}
        self.cur_dir=''
        self.candidate_proxies = []
        self.urls_with_proxies = ["http://proxy-ip-list.com/download/proxy-list-port-3128.txt",
                                  "http://proxy-ip-list.com/download/free-usa-proxy-ip.txt",
                                  "http://proxy-ip-list.com/download/free-uk-proxy-list.txt",
                                  "http://proxy-ip-list.com/download/free-proxy-list.txt"]


    def insert_info_mongodb(self, type_art, page_num, rus_name, eng_name, song_words, txt_path, url, song_name):
        song = {"type": type_art,
                "page_num": page_num,
                "rus_name": rus_name,
                "eng_name": eng_name,
                "song_words": song_words,
                "txt_path": txt_path,
                "url": url,
                "song_name": song_name}
        song_id = self.mongo_songs.insert(song)
        print "ID песни", song_id

    def insert_info_sqlite(self, type_art, page_num, rus_name, eng_name, song_words, txt_path, url, song_name):
        song = {"type": type_art,
                "page_num": page_num,
                "rus_name": rus_name,
                "eng_name": eng_name,
                "song_words": song_words,
                "txt_path": txt_path,
                "url": url,
                "song_name": song_name}
        action = self.songs_db.insert()
        action.execute(song)
        print "PK песни", url

    def set_proxies_list(self):
        self.candidate_proxies=[]
        for url_with_proxies in self.urls_with_proxies:
            html = urllib.urlopen(url_with_proxies).read()
            new_html = html.split("\r")
            other_list = new_html[3:-1]
            self.candidate_proxies.extend([i.split(";")[0] for i in other_list])

    def _download_data(self, href, path, song):
        while(1):
            try:
                self.set_proxies_list()
                proxy = self.candidate_proxies[randint(0, len(self.candidate_proxies)-1)]
                proxy={"https": proxy}
                print "Trying HTTP proxy %s" % proxy
                html = urllib.urlopen(href, proxies=proxy).read()
                if "Too Many Requests" in html:
                    print "Too Many Requests"
                    continue
                with io.open(path + song + u".txt", "w", encoding="utf-8") as trg:
                    soup = BeautifulSoup(html)
                    song_name = soup.find("span", {"itemprop": "name"})
                    song_words = unicode(soup.find("pre", {"itemprop": "chordsBlock"}))
                    song_applicature = unicode(soup.find("div", {"id": "song_chords"}))
                    soup_for_chords = BeautifulSoup(song_applicature)
                    # list_chords = [(tag["src"], tag["alt"]) if ")" not in tag["src"].split("/")[-1] else ("","")
                    #                for tag in soup_for_chords.findAll("img")]
                    list_chords = [(tag["src"], tag["alt"]) for tag in soup_for_chords.findAll("img")]
                    # print "PATH", os.path.realpath(__file__).replace("parser.py","")+path
                    # os.chdir(os.path.realpath(__file__).replace("parser.py", "")+path)
                    directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), path)
                    print "LIST CHORDS", list_chords
                    for url, chord_name in list_chords:
                        proxy = self.candidate_proxies[randint(0, len(self.candidate_proxies)-1)]
                        proxy = {"https": proxy}
                        image = urllib.URLopener(proxies=proxy)
                        filename = os.path.join(directory, chord_name)
                        try:
                            image.retrieve(url, filename+".png")
                        except IOError:
                            list_chords.remove((url, chord_name))
                            continue
                        print filename
                        change_pic((filename+".png").encode("utf-8"))
                    for string in song_words:
                        trg.write(string)
                print "Got URL using proxy %s" % proxy
                self.insert_info_mongodb(self.cur_dir.split("/")[-2], self.i, self.singer, self.singer_eng, song_words, path+song, href, song_name.getString())
                self.insert_info_sqlite(self.cur_dir.split("/")[-2], self.i, self.singer, self.singer_eng, song_words, path+song, href, song_name.getString())
                break
            except:
                print "Trying next proxy in 5 seconds"
                sl(0.001)

    def _make_dir(self, href):
        dirs_list = href.split(u"/")[4:7]
        dirs_list.pop(-2)
        print dirs_list
        tmpPath = self.cur_dir+u"./"
        path = tmpPath+u"/".join(dirs_list)+"/"
        if not os.path.exists(path):
            os.makedirs(path)
            song_name = dirs_list[-1]
            print path
            self._download_data(href, path, song_name)


    def get_part_struct(self, elem):
        print elem['href']
        self._make_dir(elem['href'])
        return elem['href'], elem.string
    def get_full_struct(self, elem):
        return elem['href'], elem.string, \
            map(self.get_part_struct, self.find_songs(elem['href'])[:-1])

    def find_artists(self, url):
        while(1):
            try:
                self.set_proxies_list()
                proxy = self.candidate_proxies[randint(0, len(self.candidate_proxies)-1)]
                proxy = {"https": proxy}
                print "Trying HTTP proxy %s" % proxy
                html = urllib.urlopen(url, proxies=proxy).read()
                if "Too Many Requests" in html:
                        print "Too Many Requests"
                        continue
                print "Got URL using proxy %s" % proxy
                soup = BeautifulSoup(html)
                artists = map(self.get_full_struct, soup.findAll('a',{'class':'artist'}))
                return artists
            except:
                print "Trying next proxy in 5 seconds"
                sl(0.001)


    def find_songs(self, url):
        while(1):
            try:
                self.set_proxies_list()
                proxy = self.candidate_proxies[randint(0, len(self.candidate_proxies)-1)]
                print "Trying HTTP proxy %s" % proxy
                proxy = {"https": proxy}
                html = urllib.urlopen(url, proxies=proxy).read()
                if "Too Many Requests" in html:
                    print "Too Many Requests"
                    continue
                print "Got URL using proxy %s" % proxy
                soup = BeautifulSoup(html)
                songs = soup.findAll('a', {'class':'g-link'})
                self.singer = soup.find('title').string.split(u"подборы")[0]
                self.singer_eng = url.split("/")[-2]
                print self.singer_eng
                return songs
            except:
                print "Trying next proxy in 5 seconds"
                sl(0.001)
    def get_arts_info(self, a, b, art_dict):
        for self.i in xrange(a,b):
            cur_url = "http://www.amdm.ru/chords/%s"%self.i
            #art_dict.update({self.i:self.find_artists(cur_url)})
            art_info=self.find_artists(cur_url)
            # self.find_artists(cur_url)
        return art_info

    def get_one_art_info(self, cur_url = "http://www.amdm.ru/chords/0"):
        strange_art = self.find_artists(cur_url)
        return strange_art

if __name__ == '__main__':
    songs_mongo = mongo_init()
    songs = songs_mongo.songs
    songs_db = sqlite_init()
    parser = AmDmParser(songs_db, songs)
    
    # parser.songs = songs_db
    # parser.mongo_songs = songs
    # rus_singers = parser.get_arts_info(1, 29, parser.cyr_art)
    parser.cur_dir = "./cyr/"
    rus_singers = parser.get_arts_info(1, 29, parser.cyr_art)
    print rus_singers
    parser.cur_dir = "./lat/"
    eng_singers = parser.get_arts_info(29, 55, parser.lat_art)
    print eng_singers
    parser.cur_dir = "./any/"
    anyone_singers = parser.get_one_art_info()
    print anyone_singers