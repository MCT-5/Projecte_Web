import requests

def get_price(appid):
    url = f"https://gg.deals/api/v1/price/{appid}"

    response = requests.get(url)

    return response.json()
