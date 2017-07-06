import requests


def get_schedule(url):
    r = requests.get(url)
    try:
        return r.json()['items']
    except Exception:
        return None
