# Douku 豆库

###介绍 Instroduction
豆库是一个私人的电影库，基于豆瓣电影，可导入豆瓣电影中的想看、看过，并根据关键字（演员、导演、语言等）进行搜索，并在自己的360云盘中进行搜索。

Douku is a personal movie library, basing on Douban Movie. You can import movie lists from Douban and search by keywords(actors, directors, languages, etc). Searching in your own 360 cloud drive is also possible.

###安装 Installation
请先安装mongodb！ Please install mongodb which is used as database!
>git clone

>virtualenv venv

>activate virtualenv (different cmd depending on os)

>pip install -r requirements.txt

>python run.py

###配置 Config
修改config.py，填入自己的豆瓣ID，以及COOKIE（用chrome访问豆瓣，按F12选Network，刷新后点左侧链接查看右侧Headers里的Cookie，直接复制出来即可。

###使用 Usage
使用右侧工具栏：刷新看过的电影、刷新想看的电影。刷新数量很大时，shell会显示正在加载的页数。

使用搜索：关键词请以单个空格分割，搜索结果会显示符合所有关键词的结果。
