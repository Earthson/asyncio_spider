import sys
import re
import cchardet as chardet
from urllib.parse import urlparse, urljoin
import asyncio
from random import random

def req_gen(url, baseurl='', method='GET', session=None):
    url = urljoin(url, baseurl)
    parsed_url = urlparse(url)
    headers = {
        "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language":"en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4",
        "Accept-Encoding": "gzip",
        "Host":parsed_url.hostname,
        "Referer":baseurl,
        "Cache-Control":"no-cache",
        #"Connection":"keep-alive",
        "User-Agent":'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/33.0.1750.152 Safari/537.36',
        }
    return {
            'method': method,
            'url': url,
            'headers':headers,
            }


charset_pat = re.compile(r'charset *= *"?([-a-zA-Z0-9]+)', re.IGNORECASE)

def charset_trans(charset):
    if charset.lower() in ('gbk', 'gb2312'):
        return 'gb18030'
    return charset.lower()


def charset_det(body):
    for i in range(3):
        c = chardet.detect(body)['encoding']
        if c is not None:
            return c.lower()
    return None


def get_charset(response, default='utf-8'):
    to_test = response.body.decode('utf-8', 'ignore')[:500]
    tmpset = set(charset_trans(e) for e in charset_pat.findall(to_test))
    if len(tmpset) == 1:
        return tmpset.pop()
    elif len(tmpset) > 1:
        c = charset_det(response.body)
        if c is not None:
            return c
    c = response.get_content_charset()
    if c is not None:
        return c
        print('@Warning: charset detect failed! set to %s by default\nURL: %s\nData: %s' % (default, response.ourl, to_test), file=sys.stderr)
    return default


from time import time

def host_rebalance(reqs, interval=1.0):
    host_map = dict()
    reqs_l = list()
    def try_yield(req, callback):
        host = urlparse(req['url']).hostname
        if host not in host_map:
            host_map[host] = time()
            yield req, callback
            return
        if time() - host_map[host] < 1.0:
            reqs_l.append((req, callback))
            yield None, None
            return
        host_map[host] = time()
        yield req, callback
    for req, callback in reqs:
        yield from try_yield(req, callback)
        while random() < len(reqs_l)/(len(reqs_l)+50):
            req, callback = reqs_l.pop(0)
            yield from try_yield(req, callback)
    while len(reqs_l) > 0:
        req, callback = reqs_l.pop(0)
        yield from try_yield(req, callback)
