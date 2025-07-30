from fake_useragent import UserAgent


def get_headers():
    ua = UserAgent()
    return {
        'accept': '*/*',
        'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
        'connection': 'keep-alive',
        'user-agent': ua.random,
    }