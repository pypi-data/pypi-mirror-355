import logging
import requests
from resilient_requester.helpers.helper_functions import check_params, handle_exception


def get_request(url, proxy=None, headers=None, timeout=0, retries=0):
    proxy, headers, timeout, retries = check_params(proxy, headers, timeout, retries)
    attempts = 0

    while attempts <= retries:
        try:
            logging.info(f"Sending a GET REQUEST: {url}")
            response = requests.get(url=url, proxies=proxy, headers=headers, timeout=timeout)
            response.raise_for_status()
            logging.info(f"Request successful: {response.status_code}.")
            return response
        except Exception as e:
            attempts = handle_exception(e, attempts, retries)
            if not attempts: return None
    return None
