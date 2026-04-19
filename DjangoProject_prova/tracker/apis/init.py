from .apis.igdb import search_game
from .apis.SteamSpy import get_steamspy
from .apis.ggdeals import get_price

def search(request):

    query = request.GET.get("q")

    game = search_game(query)[0]

    steam_id = game.get("id")

    steamspy = get_steamspy(steam_id)

    price = get_price(steam_id)

    context = {
        "game": game,
        "steamspy": steamspy,
        "price": price
    }

    return render(request, "results.html", context)
