# !/usr/bin/local
# -*- coding:utf-8 -*-
import urllib.request
from random import randint
from bs4 import BeautifulSoup
import os
import io
from pymongo import MongoClient
from sqlalchemy import create_engine, Table, Column, MetaData, String
from change_color import change_pic
import socket
from gevent import spawn, monkey, joinall
import inspect
socket.setdefaulttimeout(2)
monkey.patch_all()


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
        print("ID песни", song_id)

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
        print("PK песни", url)

    def set_proxies_list(self):
        self.candidate_proxies=[]
        for url_with_proxies in self.urls_with_proxies:
            html = urllib.request.urlopen(self.get_request_obj(url_with_proxies)).read()
            new_html = html.split(b"\r")
            other_list = new_html[3:-1]
            self.candidate_proxies.extend([i.split(b";")[0] for i in other_list])

    def get_request_obj(self, url):
        return urllib.request.Request(
            url,
            data=None,
            headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'
            }
        )

    def _download_data(self, href, path, song):
        while(1):
            try:
                self.set_proxies_list()
                proxy = self.candidate_proxies[randint(0, len(self.candidate_proxies)-1)]
                proxy={"https": proxy}
                print("Trying HTTP proxy %s" % proxy)
                self.set_opener(proxy)
                html = urllib.request.urlopen(self.get_request_obj("http:"+href)).read()
                if b"Too Many Requests" in html:
                    print("Too Many Requests")
                    continue
                soup = BeautifulSoup(html, "lxml")
                song_name = soup.find("span", {"itemprop": "name"})
                song_words = str(soup.find("pre", {"itemprop": "chordsBlock"}))
                song_applicature = str(soup.find("div", {"id": "song_chords"}))
                if song_name is None:
                    continue
                with io.open(path + song + u".txt", "w", encoding="utf-8") as trg:
                    soup_for_chords = BeautifulSoup(song_applicature, "lxml")
                    list_chords = [(tag["src"], tag["alt"]) for tag in soup_for_chords.findAll("img")]
                    directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), path)
                    print("LIST CHORDS", list_chords)
                    for url, chord_name in list_chords:
                        proxy = self.candidate_proxies[randint(0, len(self.candidate_proxies)-1)]
                        proxy = {"https": proxy}
                        image = urllib.request.URLopener(proxies=proxy)
                        filename = os.path.join(directory, chord_name)
                        try:
                            image.retrieve("http:"+url, filename+".png")
                        except IOError:
                            list_chords.remove((url, chord_name))
                            continue
                        print(filename)
                        change_pic(filename+".png")
                    for string in song_words:
                        trg.write(string)
                print("Got URL using proxy %s" % proxy)
                self.insert_info_mongodb(self.cur_dir.split("/")[-2], self.i, self.singer, self.singer_eng, song_words, path+song, href, song_name.string)
                self.insert_info_sqlite(self.cur_dir.split("/")[-2], self.i, self.singer, self.singer_eng, song_words, path+song, href, song_name.string)
                break
            except Exception as e:
                print("Exception", e)
                print("Trying next proxy", inspect.stack()[0][3])

    def _make_dir(self, href):
        dirs_list = href.split(u"/")[4:7]
        try:
            dirs_list.pop(-2)
        except IndexError:
            print("Pop index is out of range")
        print(dirs_list)
        tmpPath = self.cur_dir+u"./"
        path = tmpPath+u"/".join(dirs_list)+"/"
        if not os.path.exists(path):
            os.makedirs(path)
            song_name = dirs_list[-1]
            print(path)
            self._download_data(href, path, song_name)

    def get_part_struct(self, elem):
        print(elem['href'])
        self._make_dir(elem['href'])
        return elem['href'], elem.string

    def get_full_struct(self, elem):
        return elem['href'], elem.string, \
            list(map(self.get_part_struct, self.find_songs(elem['href'][2:])[:-1]))

    def set_opener(self, proxy):
        proxy = {'http': '127.0.0.1:8118'}
        proxy_support = urllib.request.ProxyHandler(proxy)
        opener = urllib.request.build_opener(proxy_support)
        urllib.request.install_opener(opener)

    def find_artists(self, url):
        while(1):
            try:
                self.set_proxies_list()
                proxy = self.candidate_proxies[randint(0, len(self.candidate_proxies)-1)]
                proxy = {"https": proxy}
                print("Trying HTTP proxy %s" % proxy)
                self.set_opener(proxy)
                html = urllib.request.urlopen(self.get_request_obj(url)).read()
                if b"Too Many Requests" in html:
                    print("Too Many Requests")
                    continue
                print("Got URL using proxy %s" % proxy)
                soup = BeautifulSoup(html, "lxml")
                artists = map(self.get_full_struct, soup.findAll('a',{'class':'artist'}))
                return list(artists)
            except Exception as e:
                print("Exception", e)
                print("Trying next proxy", inspect.stack()[0][3])

    def find_songs(self, url):
        while(1):
            try:
                self.set_proxies_list()
                proxy = self.candidate_proxies[randint(0, len(self.candidate_proxies)-1)]
                print("Trying HTTP proxy %s" % proxy)
                proxy = {"https": proxy}
                self.set_opener(proxy)
                html = urllib.request.urlopen(self.get_request_obj("http://"+url)).read()
                if b"Too Many Requests" in html:
                    print("Too Many Requests")
                    continue
                print("Got URL using proxy %s" % proxy)
                soup = BeautifulSoup(html, "lxml")
                songs = soup.findAll('a', {'class':'g-link'})
                self.singer = soup.find('title').string.split(u"подборы")[0]
                self.singer_eng = url.split("/")[-2]
                print(self.singer_eng)
                return songs
            except Exception as e:
                print("Exception", e)
                print("Trying next proxy", inspect.stack()[0][3])

    def get_arts_info(self, a, b, art_dict):
        jobs = [spawn(self.find_artists, "http://www.amdm.ru/chords/%s"%self.i) for self.i in range(a, b)]
        joinall(jobs)

    def get_one_art_info(self, cur_url = "http://www.amdm.ru/chords/0"):
        strange_art = self.find_artists(cur_url)
        return strange_art

if __name__ == '__main__':
    songs_mongo = mongo_init()
    songs = songs_mongo.songs
    songs_db = sqlite_init()
    parser = AmDmParser(songs_db, songs)
    parser.cur_dir = "./cyr/"
    rus_singers = parser.get_arts_info(1, 29, parser.cyr_art)
    print(rus_singers)
    parser.cur_dir = "./lat/"
    eng_singers = parser.get_arts_info(29, 55, parser.lat_art)
    print(eng_singers)
    parser.cur_dir = "./any/"
    anyone_singers = parser.get_one_art_info()
    print(anyone_singers)