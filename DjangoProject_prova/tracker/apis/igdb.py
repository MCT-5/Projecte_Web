import requests

CLIENT_ID = "TU_CLIENT_ID"
CLIENT_SECRET = "TU_SECRET"

def get_token():
    url = "https://id.twitch.tv/oauth2/token"
    params = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials"
    }

    response = requests.post(url, params=params)
    return response.json()["access_token"]


def search_game(name):
    token = get_token()

    url = "https://api.igdb.com/v4/games"

    headers = {
        "Client-ID": CLIENT_ID,
        "Authorization": f"Bearer {token}"
    }

    data = f'search "{name}"; fields name, summary, rating, cover.url;'

    response = requests.post(url, headers=headers, data=data)

    return response.json()
