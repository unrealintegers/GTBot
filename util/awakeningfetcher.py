import requests
from bs4 import BeautifulSoup
import pandas as pd
import csv


def fetch_hero(hero):
    stones = [
        'low-grade-attack-stone',
        'mid-grade-attack-stone',
        'high-grade-attack-stone',
        'low-grade-def-stone',
        'mid-grade-def-stone',
        'high-grade-def-stone',
        'low-grade-hp-stone',
        'mid-grade-hp-stone',
        'high-grade-hp-stone',
        'low-grade-dream-stone',
        'mid-grade-dream-stone',
        'high-grade-dream-stone',
        'legendary-awakening-stone'
    ]

    def parse_stones(stone):
        return list(map(lambda x: int(x.contents[0]) if len(x) > 0 else None,
                        awa.find('div', class_=stone).parent.find_all('span')))

    req = requests.get(f'https://heavenhold.com/heroes/{hero}/').text
    soup = BeautifulSoup(req, 'lxml')

    awa = soup.find('table', class_="hero-abilities-table awakening-table")
    if not awa:
        print(hero)
        return False
    counts = pd.DataFrame(map(parse_stones, stones),
                          index=map(lambda x: x.replace('-', ' '), stones),
                          columns=["MLB", '5☆', '4☆', '3☆', '2☆', '1☆'])

    with open(f"../stats/{hero}.csv", "w") as f:
        counts.to_csv(f)


if __name__ == "__main__":
    with open("../stats/heroes.txt") as f:
        reader = csv.reader(f)
        heroes = map(lambda x: x[1].lower().replace(' ', '-'), reader)
        for hero in heroes:
            fetch_hero(hero)
