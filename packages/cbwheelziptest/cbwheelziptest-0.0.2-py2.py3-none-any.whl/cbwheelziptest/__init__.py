import requests

def do():
    # A GET request
    r = requests.get('https://httpbin.org/get')
    print(r.text)
