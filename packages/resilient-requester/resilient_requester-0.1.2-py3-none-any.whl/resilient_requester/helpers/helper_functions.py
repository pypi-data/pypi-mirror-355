import logging

from fake_useragent import UserAgent


def get_headers():
    ua = UserAgent()
    return {
        'accept': '*/*',
        'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
        'connection': 'keep-alive',
        'user-agent': ua.random,
    }

def check_params(proxy, headers, timeout, retries):
    if proxy:
        if not isinstance(proxy, dict):
            raise TypeError("Proxy must be a dictionary")
    if headers:
        if not isinstance(headers, dict):
            raise TypeError("Headers must be a dictionary")
    if timeout:
        if not isinstance(timeout, int):
            raise TypeError("Timeout must be an integer")

    if not timeout or timeout < 5:
        logging.info("Timeout must be at least 5 seconds. Setting to 5 seconds.")
        timeout = 5

    if not retries or retries < 1:
        logging.info("Retries must be at least 1. Setting to 1.")
        retries = 1

    if not headers:
        logging.info("No headers provided. Setting to default.")
        headers = get_headers()

    if not proxy:
        logging.info("No proxy provided. Adding a proxy is advised.")

    return proxy, headers, timeout, retries
