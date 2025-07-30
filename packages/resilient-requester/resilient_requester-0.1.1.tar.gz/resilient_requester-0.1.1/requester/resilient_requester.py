import logging
import time
import random

import requests

from requester.helpers.helper_functions import get_headers


class Requester:
    def __init__(self):
        self.headers = get_headers()

    def request_page(self, url, proxy=None, headers=None, timeout=0, retries=0):

        if not timeout or timeout < 5:
            logging.info("Timeout must be at least 5 seconds. Setting to 5 seconds.")
            timeout = 5

        if not retries or retries < 1:
            logging.info("Retries must be at least 2. Setting to 1.")
            retries = 1

        if not headers:
            logging.info("No headers provided. Setting to default.")
            headers = self.headers

        if not proxy:
            logging.info("No proxy provided. Adding a proxy is advised.")

        attempts = 0

        while attempts <= retries:

            try:
                logging.info(f"Requesting page: {url}")
                response = requests.get(url=url, proxies=proxy, headers=headers, timeout=timeout)
                response.raise_for_status()
                return response
            except Exception as e:
                logging.error(f"Request failed: {e}")
                if attempts < retries:
                    attempts += 1
                    waiting_time = random.randint(1, 5)
                    logging.info(f"Retrying in {waiting_time} seconds...")
                    time.sleep(waiting_time)
                else:
                    logging.error(f"Maximum number of retries {retries} reached. Exiting...")
                    return None
        return None
