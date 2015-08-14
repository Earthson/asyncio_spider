import sys
from asyncengin import asyncdo
from webtools import req_gen, host_rebalance
import aiohttp
from urllib import parse
import asyncio_mongo

def print_response(response):
    mongo = yield from asyncio_mongo.Connection.create()
    yield from mongo.test.url_html.update({'_id': response.ourl}, {'_id':response.ourl, 'html':response.body}, upsert=True)


urls = ((req_gen(l.strip()), print_response) for l in sys.stdin if '.swf' not in l.lower())

reqs = host_rebalance(urls, interval=0.5)

asyncdo(reqs, n=50)
