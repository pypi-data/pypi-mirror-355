import requests
from tqdm import tqdm
import random

DEFAULT_SETTINGS = {
    'MIN_WORKING_PROXIES': 10,  # Было 'MIN_WORKING_PROXIES'
    'PROXY_LIMIT': 100,
    'TIMEOUT': 5,
    'MAX_ATTEMPTS': 3,
    'TEST_URLS': [
        "http://httpbin.org/ip",
        "http://icanhazip.com",
        "http://api.ipify.org"
    ]
}

class ProxyFetcher:
    """
    Main class for fetching and validating proxies.
    
    Args:
        **kwargs: Configuration overrides (see DEFAULT_SETTINGS)
        
    Example:
        >>> fetcher = ProxyFetcher(MIN_WORKING_PROXIES=5)
        >>> if fetcher.fetch_proxies():
        ...     print(fetcher.working_proxies)
    """
        
    def __init__(self, **kwargs):
        self.settings = DEFAULT_SETTINGS.copy()
        self.settings.update(kwargs)
        
        # Инициализируем все параметры как атрибуты
        self.min_working = self.settings['MIN_WORKING_PROXIES']  # Исправлено название
        self.proxy_limit = self.settings['PROXY_LIMIT']
        self.timeout = self.settings['TIMEOUT']
        self.max_attempts = self.settings['MAX_ATTEMPTS']
        self.test_urls = self.settings['TEST_URLS']
        
        self.working_proxies = []
    
    
    def get_proxies(self):
        """Получает прокси с нескольких источников"""
        sources = [
            f"https://proxylist.geonode.com/api/proxy-list?limit={self.proxy_limit}&page=1",
            "https://api.proxyscrape.com/v2/?request=displayproxies",
            "http://free-proxy.cz/en/proxylist/country/all/https/ping/all"
        ]
        
        proxies = []
        for url in sources:
            try:
                response = requests.get(url, timeout=15)
                if "geonode" in url:
                    proxies.extend([f"{p['ip']}:{p['port']}" for p in response.json().get("data", [])])
                else:
                    proxies.extend(response.text.strip().split('\r\n'))
            except:
                continue
        
        return list(set(proxies))
    
    def check_proxy(self, proxy_str):
        """Проверяет прокси на работоспособность"""
        test_url = random.choice(self.test_urls)
        try:
            response = requests.get(
                test_url,
                proxies={"http": f"http://{proxy_str}", "https": f"http://{proxy_str}"},
                timeout=self.timeout
            )
            return response.status_code == 200
        except:
            return False
    
    def fetch_proxies(self):
        """Основная функция получения прокси"""
        attempts = 0
        
        while len(self.working_proxies) < self.min_working and attempts < self.max_attempts:
            attempts += 1
            print(f"\nПопытка {attempts}/{self.max_attempts}. Получаем прокси...")
            
            proxies = self.get_proxies()
            if not proxies:
                print("Не удалось получить прокси. Повторяем...")
                continue
                
            print(f"Получено {len(proxies)} прокси. Начинаем проверку...")
            
            for proxy in tqdm(proxies, desc="Проверка прокси"):
                if self.check_proxy(proxy):
                    self.working_proxies.append(proxy)
                    if len(self.working_proxies) >= self.min_working:
                        break
            
            print(f"Найдено рабочих: {len(self.working_proxies)}/{self.min_working}")
        
        if self.working_proxies:
            with open('working_proxies.txt', 'w') as f:
                f.write('\n'.join(self.working_proxies))
            print(f"\nУспех! Сохранено {len(self.working_proxies)} рабочих прокси.")
            return True
        else:
            print("\nНе удалось найти рабочие прокси.")
            return False

def get_proxies(**kwargs):
    """
    Quick access function to get working proxies.
    
    Args:
        **kwargs: Configuration options:
            - MIN_WORKING_PROXIES (int): Default 10
            - PROXY_LIMIT (int): Default 100
            - TIMEOUT (int): Default 5
            - MAX_ATTEMPTS (int): Default 3
            - TEST_URLS (list): Default IP check services
    
    Returns:
        list: List of working proxies in 'ip:port' format
        
    Example:
        >>> proxies = get_proxies(TIMEOUT=10)
        >>> print(f"Found {len(proxies)} proxies")
    """
    
    fetcher = ProxyFetcher(**kwargs)
    success = fetcher.fetch_proxies()
    return fetcher.working_proxies if success else []