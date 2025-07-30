import requests

class AiaHttpClient:
    def __init__(self) -> None:
        pass

    def get(self, url, headers = None, params = None):
        response = requests.get(url, headers=headers, params=params)
        return response
    
    def post(self, url, headers = None, params = None, data = None, json = None):
        response = requests.post(url, headers=headers, params=params, data=data, json=json)
        return response
    