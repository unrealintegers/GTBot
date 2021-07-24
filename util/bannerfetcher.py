import csv
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime as dt


def fetch_hero(name):
    print(f"Fetching {name}...")
    req = requests.get(f'https://heavenhold.com/heroes/{name}/').text
    soup = BeautifulSoup(req, 'lxml')
    ban = soup.find_all('td', class_="banner-date")
    dates = [re.search(r"(\d\d/){2}(\d){4}(?=( ?~))", str(w)) for w in ban]
    dates = [dt.strptime(w.group(0), r"%m/%d/%Y") for w in dates]

    return dates


if __name__ == "__main__":
    banners = {}
    with open("../stats/heroes.txt") as f:
        reader = csv.reader(f)
        heroes = map(lambda x: x[1].lower().replace(' ', '-'), reader)
        for hero in heroes:
            if b := fetch_hero(hero):
                banners[hero] = b

    banners = sorted(banners.items(), key=lambda x: max(x[1]))
    banners = map(lambda x: (x[0], map(lambda w: w.strftime(r"%d/%m/%Y"),
                                       x[1])), banners)

    print('\n'.join(map(lambda x: f"{x[0]}\t{', '.join(x[1])}", banners)))
