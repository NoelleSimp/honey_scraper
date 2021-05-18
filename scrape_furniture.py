import requests
from bs4 import BeautifulSoup
import csv

def get_furniture(id: str):
    """
    gets furniture given the id
    :param id: string holding furniture ID
    :return: returns furniture stats
    """
    url = f'https://genshin.honeyhunterworld.com/db/item/{id[0]}_{id[1:]}/?'
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')

    title = soup.find('div', class_='custom_title')

    data = [['Name', title.text.strip()]]

    table_soup = soup.find('table', {'class': "item_main_table"})
    # table_body = table_soup.find('tbody')

    rows = table_soup.find_all('tr')

    for row in rows:
        cols = row.find_all('td')

        cols_text = [ele.text.strip() for ele in cols]
        data.append([ele for ele in cols_text if ele])  # Get rid of empty values

        if cols_text[0] == 'Rarity':
            data[2].append(len(cols[1]))
    print(data[0][1])
    return data

def get_all_furniture():
    """
    Gets winrate of summoner on all champs in ranked

    :param summoner_name: summoner to get winrates from
    :return: dictionary mapping champion names to winrates
    """
    url = f'https://genshin.honeyhunterworld.com/db/item/furniture-list/?'
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')

    furniture_soup = soup.find_all('div', class_='itemcont')
    # print(furniture_soup)
    furniture_data = []
    index = 0
    for furniture in furniture_soup:
        # if index > 10:
        #     break
        furniture_data.append(get_furniture(furniture.get('data-id')))
        index += 1

    return furniture_data

def write_to_csv(data):
    with open('scrape.csv', mode='w', newline='') as scraped_furniture:
        scrape_writer = csv.writer(scraped_furniture, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        scrape_writer.writerow([data[0][0][0], data[0][1][0], data[0][2][0], data[0][3][0], data[0][4][0], data[0][5][0]])

        for line in data:
            # print(line)
            scrape_writer.writerow([line[0][-1], line[1][-1], line[2][-1], line[3][-1], line[4][-1], line[5][-1]])


def main():
    data = get_all_furniture()
    # data = [['Name', 'Jade-Eyed Cat'], ['Type', 'Furniture'], ['Rarity', 3], ['Comfort Points', '100'], ['Cost Points', '500'], ['In-game Description', "An agile and wise soul, endowed since birth with a well-maintained elegance and pride.A grimalkin with emerald-green eyes, they walk upon roof beams at night with great grace. Its furry footsteps are nearly inaudible and it often sneaks into shops and kitchens undetected.Luckily, since they needn't worry about food or drink here, they've become much more honest after arriving in the Realm Within."]]
    # print(data)
    write_to_csv(data)

if __name__ == "__main__":
    main()
