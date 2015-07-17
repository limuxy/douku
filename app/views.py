# -*- coding: utf-8 -*-
from app import app, db
from flask import flash, render_template, redirect, url_for, request
from bs4 import BeautifulSoup
import requests, re, sys

#windows下搞定编码问题
reload(sys)
sys.setdefaultencoding('utf-8')

#读取网页，返回soup
def get_soup(url, referer):
    headers = {
        'Referer' : 'http://movie.douban.com/people/lorienlove/'+referer,
        'User-Agent' : 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36',
        'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Encoding' : 'gzip, deflate, sdch',
        'Accept-Language' : 'zh-CN,zh;q=0.8,en;q=0.6,zh-TW;q=0.4',
        'Cookie' : app.config['COOKIE']
        }
    page = requests.get(url, headers=headers)
    soup = BeautifulSoup(page.text)
    return soup

#获取看过的、想看的页数
def get_page_count(soup, loaded_collect_page):
    if soup.find('div', class_='paginator') != None:
        page_count = int(soup.find('div', class_='paginator').findChildren('a')[-2].text) - loaded_collect_page + 1
    else:
        page_count = 1
    return page_count

#获取看过的、想看的列表
def get_movie_list(soup):
    items = soup.select('li.item')
    movies = []
    for item in items:
        movie_id = re.search('\d+', item.select('div.title > a')[0]['href']).group(0)
        titles = [a.strip() for a in item.select('div.title > a')[0].text.split('/')]
        date_added = re.search('\d\d\d\d-\d\d-\d\d', str(item.select('div.date')[0])).group(0)
        tags = [a for a in item.select('span.intro')[0].text.split(' / ')]
        tags.extend(titles)
        tags = list(set(tags))
        date_online = [{'date':  re.search('\d\d\d\d-\d\d-\d\d', tag).group(0),
                        'location': '' if re.match('\d\d\d\d-\d\d-\d\d$', tag) else tag[10:].lstrip('(（').rstrip(')）')}
                        for tag in tags if re.match('\d\d\d\d-\d\d-\d\d',tag)]
        my_rating = None if item.select('div.date > span') == [] else re.search('\d', item.select('div.date > span')[0]['class'][0]).group(0)
        movies.append({'movie_id':movie_id,
                        'titles':titles, 
                        'date_added':date_added, 
                        'tags':tags, 
                        'date_online':date_online, 
                        'my_rating':my_rating})
    return movies

#保存电影信息
def save_movies(movies):
    for movie in movies: #判断是否已经保存
        if db.movies.find({'movie_id':movie['movie_id']}).count() == 0:
            db.movies.insert(movie)

#保存看过的、想看的列表
def save_my(lib, movies):
    for movie in movies:
        db.user.update({'user':app.config['DOUBAN_ID']},
                        {'$addToSet': {
                                lib :{'movie_id':movie['movie_id'], 
                                            'my_tags':[]
                                            }}},
                        upsert=True)

@app.route('/')
@app.route('/index')
def index():
    title = u'首页'
    return render_template('index.html', title=title)

@app.route('/collect')
def collect():
    title = u'我看过的'
    data = db.user.find_one({'user':app.config['DOUBAN_ID']})
    collect_list = data['collect'] if 'collect' in data else []
    if collect_list:
        collects = []
        for movie in collect_list:
            if movie != None:
                movie_detail = db.movies.find_one({"movie_id":movie['movie_id']})
                if movie_detail:
                    collects.append(movie_detail)
        movies = sorted(collects, key=lambda k:k['date_added'], reverse=True)
    else:
        movies = None
    return render_template('movies.html', title=title, movies=movies, collect_active=True)

@app.route('/wish')
def wish():
    title = u'我想看的'
    data = db.user.find_one({'user':app.config['DOUBAN_ID']})
    wish_list = data['wish'] if 'wish' in data else []
    wishes = []
    for movie in wish_list:
        if movie != None:
            movie_detail = db.movies.find_one({"movie_id":movie['movie_id']})
            if movie_detail:
                wishes.append(movie_detail)
    if len(wishes) > 0:
        movies = sorted(wishes, key=lambda k:k['date_added'], reverse=True)
    else:
        movies = None
    return render_template('movies.html', title=title, movies=movies, wish_active=True)

@app.route('/search', methods=['GET', 'POST'])
def search():
    keywords = request.values.get('keywords')
    order = request.values.get('order')
    if not order:
        order = 'date_added'
    cat = request.values.get('cat')
    if not cat:
        cat = 'all'
    keyword_list = keywords.split() if keywords else None
    title = u'搜索： '+keywords if keywords else u'搜索'
    data = db.movies.find({'$and': [{'tags': x} for x in [{'$regex':keyword} for keyword in keywords]]}).sort(order, -1) if keywords else None
    if data:
        movies = []
        if cat == 'collect':
            for movie in data:
                if db.user.find_one({'$and':[{'user':app.config['DOUBAN_ID']}, {'collect':{'$elemMatch': {'movie_id':movie['movie_id']}}}]})   != None:
                    movies.append(movie)
        elif cat == 'wish':
            for movie in data:
                if db.user.find_one({'$and':[{'user':app.config['DOUBAN_ID']}, {'wish':{'$elemMatch': {'movie_id':movie['movie_id']}}}]})   != None:
                    movies.append(movie)
        else:
            for movie in data:
                movies.append(movie)
    else:
        movies = None
    return render_template('search.html', title=title, search_active=True, keywords=keywords, movies=movies, cat=cat)

@app.route('/load_collect')
def load_collect():
    douban_id = app.config['DOUBAN_ID']
    data = db.user.find_one({'user':douban_id})
    loaded_collect_count = len(data['collect']) if 'collect' in data else 0
    loaded_collect_page = int(loaded_collect_count/30) + 1
    first_time_load = True if loaded_collect_count == 0 else False
    url = 'http://movie.douban.com/people/'+douban_id+'/collect?sort=time&amp;start=0&amp;filter=all&amp;mode=list&amp;tags_sort=count'
    soup = get_soup(url, 'collect')
    page_count = get_page_count(soup, loaded_collect_page)
    page_1_movies = get_movie_list(soup)
    save_movies(page_1_movies)
    save_my('collect', page_1_movies)
    if page_count > 1:
        for i in range(1, page_count):
            url = 'http://movie.douban.com/people/'+douban_id+'/collect?sort=time&amp;start='+str(i*30)+'&amp;filter=all&amp;mode=list&amp;tags_sort=count'
            soup = get_soup(url, 'collect')
            movies = get_movie_list(soup)
            save_movies(movies)
            save_my('collect', movies)
            print 'loading page %s' % str(i+1)
    return redirect('collect')

@app.route('/load_wish')
def load_wish():
    douban_id = app.config['DOUBAN_ID']
    db.user.update({'user':douban_id},{'$unset': {'wish':1}}, False, True)
    url = 'http://movie.douban.com/people/'+douban_id+'/wish?sort=time&amp;start=0&amp;filter=all&amp;mode=list&amp;tags_sort=count'
    soup = get_soup(url, 'wish')
    page_count = get_page_count(soup, 0)
    for i in range(0, page_count):
        url = 'http://movie.douban.com/people/'+douban_id+'/wish?sort=time&amp;start='+str(i*30)+'&amp;filter=all&amp;mode=list&amp;tags_sort=count'
        soup = get_soup(url, 'wish')
        movies = get_movie_list(soup)
        save_movies(movies)
        save_my('wish', movies)
        print 'loading page %s' % str(i+1)
    return redirect('wish')