import requests


def requestGet(url):
    response = requests.get(url)
    return response.json()
