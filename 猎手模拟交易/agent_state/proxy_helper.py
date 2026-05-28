#!/usr/bin/env python3
"""代理轮换帮助模块 - 从本地proxy_pool获取代理并自动轮换重试
用法: from proxy_helper import ProxyFetch
fetcher = ProxyFetch()
resp = fetcher.get('https://sz.lianjia.com/ershoufang/')
"""
import requests, json, time, random

POOL_API = 'http://127.0.0.1:5010'

class ProxyFetch:
    def __init__(self, max_retries=5, timeout=10):
        self.max_retries = max_retries
        self.timeout = timeout
        self.ua_list = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0.0.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Chrome/126.0.0.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 Safari/17.5',
        ]
    
    def _get_proxy(self):
        try:
            r = requests.get(f'{POOL_API}/get', timeout=3)
            data = r.json()
            return data.get('proxy')
        except:
            return None
    
    def _random_ua(self):
        return random.choice(self.ua_list)
    
    def get(self, url, **kwargs):
        headers = kwargs.pop('headers', {})
        headers.setdefault('User-Agent', self._random_ua())
        
        # 先试直连
        try:
            resp = requests.get(url, headers=headers, timeout=self.timeout, **kwargs)
            if resp.status_code == 200:
                return resp
        except:
            pass
        
        # 直连失败，用代理轮换
        for i in range(self.max_retries):
            proxy = self._get_proxy()
            if not proxy:
                time.sleep(1)
                continue
            try:
                resp = requests.get(url, headers=headers, 
                                  proxies={'http':f'http://{proxy}','https':f'http://{proxy}'},
                                  timeout=self.timeout, **kwargs)
                if resp.status_code == 200:
                    return resp
                elif resp.status_code in [403, 420, 429]:
                    # 被WAF/反爬拦截，删掉这个代理
                    try:
                        requests.get(f'{POOL_API}/delete?proxy={proxy}', timeout=2)
                    except:
                        pass
            except:
                pass
            time.sleep(0.5)
        
        return None  # 全部失败

if __name__ == '__main__':
    f = ProxyFetch()
    print('Testing lianjia...')
    r = f.get('https://sz.lianjia.com/')
    print(f'Lianjia: {"OK " + str(len(r.text)) if r else "FAILED"} bytes')
    
    print('Testing szftedu...')
    r = f.get('https://www.szftedu.cn/')
    print(f'Szftedu: {"OK " + str(len(r.text)) if r else "FAILED"} bytes')
