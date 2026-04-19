import requests

def get_steamspy(appid):
    url = f"https://steamspy.com/api.php?request=appdetails&appid={appid}"
    
    response = requests.get(url)
    
    return response.json()
