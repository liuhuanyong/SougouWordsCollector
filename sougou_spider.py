# -*- coding: utf-8 -*-
import os,sys
import urllib
from urllib import quote, urlretrieve
from lxml import etree

class ProductSyper:
    def __init__(self):
        pass

    def get_html(self, url):
        return urllib.urlopen(url).read()

    def html_parser(self, html):
        return etree.HTML(html)

    def get_links(self, selector, page_index):
        data = {}
        page_title = selector.xpath('//title/text()')[0]
        if len(page_title.split('_')) == 2:
            dict_name = page_title.split('_')[0].encode('utf-8')
            download_link = 'https://pinyin.sogou.com/d/dict/download_cell.php?id='+str(page_index)+'&name='+quote(dict_name)+'&f=detail'
            data['title'] = page_title
            data['download_link'] = download_link
            data['dict_name'] = dict_name
            return data
        else:
            return {}

    def download_dict(self, data):
        download_link = data['download_link']
        dict_name = data['dict_name']
        urlretrieve(download_link, 'dict/%s.scel'%dict_name)

    def spider(self,url):
        page_index = url.split('/')[-1]
        html = self.get_html(url)
        data = self.get_links(self.html_parser(html), page_index)
        if data:
            try:
                self.download_dict(data)
            except:
                pass
            return data
        else:
            return {}

def main():
    product_spider = ProductSyper()
    for page_index in range(1, 40001):
        url = 'https://pinyin.sogou.com/dict/detail/index/%s'%page_index
        data = product_spider.spider(url)
        print url
        if data:
            print page_index, data['dict_name']


main()

