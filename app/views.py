from app import app, db
from flask import flash, render_template, redirect, url_for, request
import requests
from bs4 import BeautifulSoup
import re

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

def get_page_count(soup, loaded_collect_page):
    if soup.find('div', class_='paginator') != None:
        page_count = int(soup.find('div', class_='paginator').findChildren('a')[-2].text) - loaded_collect_page + 1
    else:
        page_count = 1
    return page_count

def get_movie_list(soup):
    items = soup.select('li.item')
    movies = []
    for item in items:
        movie_id = re.search('\d+', item.select('div.title > a')[0]['href']).group(0)
        titles = [a.strip() for a in item.select('div.title > a')[0].text.split('/')]
        date_added = re.search('\d\d\d\d-\d\d-\d\d', str(item.select('div.date')[0])).group(0)
        tags = [a for a in item.select('span.intro')[0].text.split(' / ')]
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

def save_collect_movies(movies, first_time_load):
    if first_time_load == True: #如果从未加载过
        db.collect.insert_many(movies) #直接保存到数据库
    else: #如果加载过
        for movie in movies: #判断是否已经保存
            if db.collect.find({'movie_id':movie['movie_id']}).count() == 0:
                db.collect.insert(movie)
    return True

def save_wish_movies(movies, first_time_load):
    if first_time_load == True: #如果从未加载过
        db.wish.insert_many(movies) #直接保存到数据库
    else: #如果加载过
        for movie in movies: #判断是否已经保存
            if db.wish.find({'movie_id':movie['movie_id']}).count() == 0:
                db.wish.insert(movie)
    return True

@app.route('/')
@app.route('/index')
def index():
    title = '首页'
    collect = db.collect.find().sort('date_added',-1)
    wish = db.wish.find().sort('date_added',-1)
    return render_template('index.html',
                            title=title,
                            collect=collect,
                            wish=wish)

@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        keywords = request.form['keywords']
        order = request.form['order']
        keyword_list = keywords.split(' ')
        print(keyword_list)
        title = '搜索： '+keywords
        collect = db.collect.find({'$and': [{'tags': x} for x in [{'$regex':keyword} for keyword in keywords]]}).sort(order, -1)
        wish = db.wish.find({'$and': [{'tags': x} for x in [{'$regex':keyword} for keyword in keywords]]}).sort(order, -1)
        return render_template('index.html',
                                title=title,
                                collect=collect,
                                wish=wish,
                                keywords=keywords)
    else:
        return redirect(url_for('index'))

@app.route('/load_collect')
def load_collect():
    douban_id = app.config['DOUBAN_ID']
    loaded_collect_count = db.collect.find().count()
    loaded_collect_page = int(loaded_collect_count/30) + 1
    first_time_load = True if loaded_collect_count == 0 else False
    url = 'http://movie.douban.com/people/'+douban_id+'/collect?sort=time&amp;start=0&amp;filter=all&amp;mode=list&amp;tags_sort=count'
    soup = get_soup(url, 'collect')
    page_count = get_page_count(soup, loaded_collect_page)
    page_1_movies = get_movie_list(soup)
    save_collect_movies(page_1_movies, first_time_load)
    if page_count > 1:
        for i in range(1, page_count):
            url = 'http://movie.douban.com/people/'+douban_id+'/collect?sort=time&amp;start='+str(i*30)+'&amp;filter=all&amp;mode=list&amp;tags_sort=count'
            soup = get_soup(url, 'collect')
            movies = get_movie_list(soup)
            save_collect_movies(movies, first_time_load)
            print('loading page %s' % str(i+1))
    return redirect('/')

@app.route('/load_wish')
def load_wish():
    douban_id = app.config['DOUBAN_ID']
    loaded_wish_count = db.wish.find().count()
    loaded_wish_page = int(loaded_wish_count/30) + 1
    first_time_load = True if loaded_wish_count == 0 else False
    url = 'http://movie.douban.com/people/'+douban_id+'/wish?sort=time&amp;start=0&amp;filter=all&amp;mode=list&amp;tags_sort=count'
    soup = get_soup(url, 'wish')
    page_count = get_page_count(soup, loaded_wish_page)
    page_1_movies = get_movie_list(soup)
    save_wish_movies(page_1_movies, first_time_load)
    if page_count > 1:
        for i in range(1, page_count):
            url = 'http://movie.douban.com/people/'+douban_id+'/wish?sort=time&amp;start='+str(i*30)+'&amp;filter=all&amp;mode=list&amp;tags_sort=count'
            soup = get_soup(url, 'wish')
            movies = get_movie_list(soup)
            save_wish_movies(movies, first_time_load)
            print('loading page %s' % str(i+1))
    return redirect('/')