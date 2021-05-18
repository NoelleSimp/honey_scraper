import requests
from bs4 import BeautifulSoup
import csv

def get_base_stats(soup):

    stat_map = {}
    stat_tables = soup.findAll('table', class_='add_stat_table')
    stat_table = stat_tables[1]
    rows = stat_table.find_all('tr')
    titles = [val.text for val in rows[0].find_all('td')[:-1]]
    for title in titles:
        stat_map[title] = []

    for row in rows[1:]:
        cols = row.find_all('td')[:-1]
        for index, col in enumerate(cols):
            stat_map[titles[index]].append(col.text)

    return stat_map

def get_talents(soup):
    talent_map = {}
    talents = []
    talent_tables = soup.findAll('table', class_='item_main_table')[1:]

    # Gets talent names first so we can associate alternate talents
    for talent_table in talent_tables:
        rows = talent_table.find_all('tr')
        if len(rows) > 3:
            break
        talents.append(rows[0].find('a').text)

    # Gets talent descriptions
    for index, talent_table in enumerate(talent_tables):
        rows = talent_table.find_all('tr')
        if index >= len(talents):
            break
        if index == 0:
            talent_map['Normal Attack'] = {'name': talents[index], 'desc': rows[1].text}
        elif index == 1:
            talent_map['Elemental Skill'] = {'name': talents[index], 'desc': rows[1].text}
        elif index == 2 and len(talents) == 3:
            talent_map['Alternate Sprint'] = {'name': talents[index], 'desc': rows[1].text}
        else:
            talent_map['Elemental Burst'] = {'name': talents[index], 'desc': rows[1].text}

    # Gets Talent Value INFO first, THEN get the values
    value_titles = []
    value_tables = soup.findAll('table', class_='add_stat_table')[2:2 + len(talents)]
    for index, value_table in enumerate(value_tables):
        value_map = {}
        rows = value_table.find_all('tr')
        # value_titles = [row.find('td').text for row in rows[1:]]

        for row in rows[1:]:
            value_map[row.find('td').text] = [col.text for col in row.find_all('td')[1:]]
        print(value_map)
        if index == 0:
            talent_map['Normal Attack']['values'] = value_map
        elif index == 1:
            talent_map['Elemental Skill']['values'] = value_map
        elif index == 2 and len(talents) == 3:
            talent_map['Alternate Sprint']['values'] = value_map
        else:
            talent_map['Elemental Burst']['values'] = value_map

    print(talent_map)
    return talent_map

def get_character_desc(soup):
    rows = soup.find_all('tr')

    data = {}
    index = 0
    for row in rows:
        cols = row.find_all('td')

        cols_text = [ele.text.strip() for ele in cols]
        if len(cols_text) > 1:
            data[cols_text[0]] = (cols_text[1])  # Get rid of empty values

        if cols_text[0] == 'Rarity':
            data['Rarity'] = len(cols[1])

        # Get element from PNG link.
        if cols_text[0] == 'Element':
            element = cols[1].find('img')['src'][len("/img/icons/element/"):]
            element = element[:len('_35.png') * -1]
            data['Element'] = element.capitalize()

        index += 1

    return data

def get_character(id: str):
    url = f'https://genshin.honeyhunterworld.com/db/char/{id}/'
    page = requests.get(url)
    # soup = BeautifulSoup(page.content, 'html.parser')
    soup = BeautifulSoup(page.content, 'html5lib')

    character = {'name': soup.find('div', class_='custom_title')}

    desc_soup = soup.find('table', {'class': "item_main_table"})

    desc = get_character_desc(desc_soup)
    character['desc'] = desc

    character['Talents'] = get_talents(soup)

    character['stats'] = get_base_stats(soup)

    print(character)
    return character

def write_to_csv(data):
    with open('scrape.csv', mode='w', newline='') as scraped_furniture:
        scrape_writer = csv.writer(scraped_furniture, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        scrape_writer.writerow(
            [data[0][0][0], data[0][1][0], data[0][2][0], data[0][3][0], data[0][4][0], data[0][5][0]])

        for line in data:
            # print(line)
            scrape_writer.writerow([line[0][-1], line[1][-1], line[2][-1], line[3][-1], line[4][-1], line[5][-1]])

def talents_to_md(talents):
    output = '## **Attacks**' + '\n\n' + '{% tabs %}\n'
    for index, talent in enumerate(talents):
        if index == 0:
            output += "{% tab title=\"" + talents[talent]['name'][len("Normal Attack: "):] + "\" %}\n"
            output += "**Normal Attacks**\n" + talents[talent]['desc'][
                                               len('Normal Attack '):talents[talent]['desc'].find(
                                                   " Charged Attack")] + "\n\n"
            output += '| String | Talent 6% | Frames | Motion Value |" + "\n| :--- | :--- | :--- | :--- |\n'
            for hit in talents[talent]['values']:
                if hit.find("Charged Attack") != -1:
                    break
                output += "| " + hit + " | " + talents[talent]['values'][hit][5] + " | -- | -- |\n"

            output += "\n**Charged Attacks**\n" + talents[talent]['desc'][
                                                talents[talent]['desc'].find(" Charged Attack") + len(
                                                    ' Charged Attack '):
                                                talents[talent]['desc'].find(" Plunging Attack")] + "\n\n"
            output += '| String | Talent 6% | Frames | Motion Value |" + "\n| :--- | :--- | :--- | :--- |\n'

            for hit in talents[talent]['values']:
                if hit.find("Charged Attack") == -1:
                    continue
                if hit.find("Stamina Cost") != -1:
                    break
                output += "| " + hit + " | " + talents[talent]['values'][hit][5] + " | -- | -- |\n"

            output += "\n**Plunge Attacks**\n" + talents[talent]['desc'][
                                                talents[talent]['desc'].find(" Plunging Attack") + len(
                                                    ' Plunging Attack '):] + "\n\n"

            output += '| String | Talent 6% |" + "\n| :--- | :--- |\n'
            for hit in talents[talent]['values']:
                if hit.find("Plunge") == -1:
                    continue
                output += "| " + hit + " | " + talents[talent]['values'][hit][5] + " |\n"
            output += "{% endtab %}\n\n"
        elif index == 1:
            output += "{% tab title=\"" + talents[talent]['name'] + "\" %}\n"
            output += f'{talents[talent]["desc"]}\n\n'
            output += '| Type | Talent 6% | Cooldown | U | Particles | Frames | Motion Value |' + '\n| :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n'
            for hit in talents[talent]['values']:
                output += "| " + hit + " | " + talents[talent]['values'][hit][5] + " | -- | -- | -- | --| -- |\n"
            output += "{% endtab %}\n\n"
        else:
            output += "{% tab title=\"" + talents[talent]['name'] + "\" %}\n"
            output += f'{talents[talent]["desc"]}\n\n'
            output += '| Effect | Talent 6% / Data |' + '\n| :--- | :--- |\n'
            for hit in talents[talent]['values']:
                output += "| " + hit + " | " + talents[talent]['values'][hit][5] + " |\n"
            output += "{% endtab %}\n"
    output += "{% endtabs %}\n\n"
    output += "## Full Talent Values\n\n{% tabs %}"

    for index, talent in enumerate(talents):
        if index == 0:
            output += "{% tab title=\"" + talents[talent]['name'][len("Normal Attack: "):] + "\" %}\n"
            output += "### Normal Attacks\n\n"
            output += "|  | Lv6 | Lv7 | Lv8 | Lv9 | Lv10 | Lv11 |" + "\n| :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n"
            for hit in talents[talent]['values']:
                if hit.find("Charged Attack") != -1:
                    break
                output += "| " + hit + " |"
                for val in talents[talent]['values'][hit][5:11]:
                    output += " " + val[:-1] + " |"
                output += "\n"

            output += "\n### Charged Attack\n\n"
            output += "|  | Lv6 | Lv7 | Lv8 | Lv9 | Lv10 | Lv11 |" + "\n| :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n"
            for hit in talents[talent]['values']:
                if hit.find("Charged Attack") == -1:
                    continue
                if hit.find("Stamina Cost") != -1:
                    break
                output += "| " + hit + " |"
                for val in talents[talent]['values'][hit][5:11]:
                    output += " " + val[:-1] + " |"
                output += "\n"

            output += "\n### Plunge \n\n"
            output += "|  | Lv6 | Lv7 | Lv8 | Lv9 | Lv10 | Lv11 |" + "\n| :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n"
            for hit in talents[talent]['values']:
                if hit.find("Plunge") == -1:
                    continue
                output += "| " + hit + " |"
                for val in talents[talent]['values'][hit][5:11]:
                    output += " " + val[:-1] + " |"
                output += "\n"
            output += "{% endtab %}\n\n"
        if index == 1:
            output += "{% tab title=\"" + talents[talent]['name'] + "\" %}\n"
            output += "|  | Lv6 | Lv7 | Lv8 | Lv9 | Lv10 | Lv11 | Lv12 | Lv13 |" + "\n| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n"
            for hit in talents[talent]['values']:
                output += "| " + hit + " |"
                for val in talents[talent]['values'][hit][5:13]:
                    output += " " + val + " |"
                output += "\n"
            output += "{% endtab %}\n\n"
        if index == 2:
            output += "{% tab title=\"" + talents[talent]['name'] + "\" %}\n"
            output += "|  | Lv6 | Lv7 | Lv8 | Lv9 | Lv10 | Lv11 | Lv12 | Lv13 |" + "\n| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n"
            for hit in talents[talent]['values']:
                output += "| " + hit + " |"
                for val in talents[talent]['values'][hit][5:13]:
                    output += " " + val + " |"
                output += "\n"
            output += "{% endtab %}\n"
    output += "{% endtabs %}"
    print(output)
    return output

def main():
    data = get_character('diluc')
    # talents_to_md(data['Talents'])
    # write_to_csv(data)

if __name__ == "__main__":
    main()
