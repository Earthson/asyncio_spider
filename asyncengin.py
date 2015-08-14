import sys
import asyncio
import aiohttp
import http
import urllib.parse
from webtools import get_charset
from traceback import format_exc

import random

loop = asyncio.get_event_loop()

aiohttp_errors = (aiohttp.errors.TimeoutError, aiohttp.errors.ClientConnectionError)

@asyncio.coroutine
def httptasker(reqs, retry=3):
    for req, callback in reqs:
        if req is None:
            tl = random.random()*0.01
            yield from asyncio.sleep(tl)
            continue
        def get_response():
            response = None
            for i in range(retry):
                try:
                    try:
                        response = yield from asyncio.wait_for(aiohttp.request(**req), 5.0)
                        response.body = yield from response.read()
                        response.ourl = req['url']
                    finally:
                        if response is not None:
                            response.close()
                    return response
                except aiohttp_errors as e:
                    print('@FetchError: %s, %s, retry: %d' % (type(e), req['url'], i), file=sys.stderr)
                except http.cookies.CookieError as e:
                    print('@CookieError: %s, retry: %d' % (req['url'], i), file=sys.stderr)
                    #print('@error_trace_back', format_exc(), file=sys.stderr)
                except Exception as e:
                    print('@ErrorFetching: %s\nURL: %s' % (e, req['url']), file=sys.stderr)
                    print('@error_trace_back', format_exc(), file=sys.stderr)
            return None
        response = yield from get_response()
        try:
            if response is None:
                print('@Failed: %s' % req['url'], file=sys.stderr)
                continue
            c = get_charset(response)
            response.body = response.body.decode(c, 'ignore')
            response.charset = c
            yield from callback(response)
        except Exception as e:
            print('@ErrorProcess: %s\nURL: %s' % (e, req['url']), file=sys.stderr)
            print('@error_trace_back', format_exc(), file=sys.stderr)


def asyncdo(task_queue, n=3):
    tasks = [asyncio.async(httptasker(task_queue, 8)) for i in range(n)]
    for t in tasks:
        loop.run_until_complete(t)
    #loop.close()

