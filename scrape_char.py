import json

import requests
from bs4 import BeautifulSoup

def get_passives_cons(soup, len_talents):
    map = {}
    passive_tables = soup.findAll('table', class_='item_main_table')[1 + len_talents:1 + len_talents + 2]
    map['passives'] = {}
    map['cons'] = {}
    index = 0
    for passive_table in passive_tables:
        rows = passive_table.find_all('tr')
        dic = map['passives'] if index == 0 else map['cons']
        for i in range(0, len(rows), 2):
            name = rows[i].find_all('td')[1].text
            desc = rows[i + 1].find('div').text.replace("#", "")
            dic[name] = desc
        index += 1
    return map

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
            talent_map['Normal Attack'] = {'name': talents[index], 'desc': rows[1].text.replace("#", "")}
        elif index == 1:
            talent_map['Elemental Skill'] = {'name': talents[index], 'desc': rows[1].text.replace("#", "")}
        elif index == 2 and len(talents) == 4:
            talent_map['Alternate Sprint'] = {'name': talents[index], 'desc': rows[1].text.replace("#", "")}
        else:
            talent_map['Elemental Burst'] = {'name': talents[index], 'desc': rows[1].text.replace("#", "")}

    # Gets Talent Value INFO first, THEN get the values
    value_titles = []
    value_tables = soup.findAll('table', class_='add_stat_table')[2:2 + len(talents)]
    for index, value_table in enumerate(value_tables):
        value_map = {}
        rows = value_table.find_all('tr')
        # value_titles = [row.find('td').text for row in rows[1:]]

        for row in rows[1:]:
            value_map[row.find('td').text] = [col.text for col in row.find_all('td')[1:]]
        # print(value_map)
        if index == 0:
            talent_map['Normal Attack']['values'] = value_map
        elif index == 1:
            talent_map['Elemental Skill']['values'] = value_map
        elif index == 2 and len(talents) == 4:
            talent_map['Alternate Sprint']['values'] = value_map
        else:
            talent_map['Elemental Burst']['values'] = value_map

    # print(talent_map)
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
            element = cols[1].find('img')['data-src'][len("/img/icons/element/"):]
            element = element[:len('_35.png') * -1]
            data['Element'] = element.capitalize()

        index += 1

    return data

def get_character(id: str):
    url = f'https://genshin.honeyhunterworld.com/db/char/{id}/?lang=EN'
    page = requests.get(url)
    # soup = BeautifulSoup(page.content, 'html.parser')
    soup = BeautifulSoup(page.content, 'html5lib')

    character = {'id': id, 'name': soup.find('div', class_='custom_title').text}

    desc_soup = soup.find('table', {'class': "item_main_table"})

    desc = get_character_desc(desc_soup)
    character['desc'] = desc

    character['talents'] = get_talents(soup)

    character['stats'] = get_base_stats(soup)

    character.update(get_passives_cons(soup, len(character['talents'])))

    # print(json.dumps(character, indent=4))
    return character

def char_data_to_md(character):
    output = "---\n" + "description: >-\n" + f"  {character['desc']['In-game Description']}" + "\n---\n"
    output += f"\n# {character['name']}\n"
    output += f"\n## ![](../../.gitbook/assets/element_{character['desc']['Element'].lower()}.png) {character['name']}\n"
    output += f"\n![](../../.gitbook/assets/character_{character['id']}_wish.png)\n"
    # print(output)
    return output

def base_stats_to_md(base_stats):
    asc_stat = list(base_stats)[4]
    output = '## **Base Stats**' + '\n\n'
    output += f"| Lv | Base HP | Base ATK | Base DEF | {asc_stat} |" + "\n| :--- | :--- | :--- | :--- | :--- |\n"
    for i in range(7, len(base_stats['Lv'])):
        output += f"| {base_stats['Lv'][i]} | {base_stats['Base HP'][i]} | {base_stats['Base ATK'][i]} | {base_stats['Base DEF'][i]} | {base_stats[asc_stat][i]} |\n"
    # print(output)
    return output

def talent_desc_to_md(talents):
    output = '## **Attacks**' + '\n\n' + '{% tabs %}\n'
    for index, talent in enumerate(talents):
        if index == 0:
            output += "{% tab title=\"" + talents[talent]['name'][len("Normal Attack: "):] + "\" %}\n"
            output += "**Normal Attacks**  \n" + talents[talent]['desc'][
                                                 len('Normal Attack '):talents[talent]['desc'].find(
                                                     " Charged Attack")] + "\n\n"
            output += '| String | Talent 6% | Frames | Motion Value |\n| :--- | :--- | :--- | :--- |\n'
            for hit in talents[talent]['values']:
                if hit.find("Charged Attack") != -1 or hit.find("Aimed Shot") != -1:
                    break
                output += "| " + hit + " | " + talents[talent]['values'][hit][5].strip() + " | -- | -- |\n"

            output += "\n**Charged Attacks**  \n" + talents[talent]['desc'][
                                                    talents[talent]['desc'].find(" Charged Attack") + len(
                                                        ' Charged Attack '):
                                                    talents[talent]['desc'].find(" Plunging Attack")] + "\n\n"
            output += '| String | Talent 6% | Frames | Motion Value |\n| :--- | :--- | :--- | :--- |\n'

            for hit in talents[talent]['values']:
                if hit.find("Charged Attack") == -1 and hit.find("Aimed Shot") == -1:
                    continue
                if hit.find("Stamina Cost") != -1:
                    output += f"\n* Stamina Cost: {talents[talent]['values']['Charged Attack Stamina Cost'][0].replace(' /s','')}\n"
                    break
                output += "| " + hit + " | " + talents[talent]['values'][hit][5].strip() + " | -- | -- |\n"

            output += "\n**Plunge Attacks**  \n" + talents[talent]['desc'][
                                                   talents[talent]['desc'].find(" Plunging Attack") + len(
                                                       ' Plunging Attack '):] + "\n\n"

            output += "| String | Talent 6% |" + "\n| :--- | :--- |\n"
            for hit in talents[talent]['values']:
                if hit.find("Plunge") == -1:
                    continue
                if hit.find("Low/High") > -1:
                    low = talents[talent]['values'][hit][5].strip().split()[0]
                    high = talents[talent]['values'][hit][5].strip().split()[-1]
                    output += f"| Low Plunge DMG | {low} |\n| High Plunge DMG | {high} |\n"
                    continue
                output += "| " + hit + " | " + talents[talent]['values'][hit][5].strip() + " |\n"
            output += "{% endtab %}\n\n"
        elif index == 1:
            output += "{% tab title=\"" + talents[talent]['name'] + "\" %}\n"
            output += f'{talents[talent]["desc"]}\n\n'
            output += '| Type | Talent 6% | Cooldown | U | Particles | Frames | Motion Value |\n' + \
                      '| :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n'
            for hit in talents[talent]['values']:
                output += "| " + hit + " | " + talents[talent]['values'][hit][5].strip() + " | -- | -- | -- | --| -- |\n"
            output += "{% endtab %}\n\n"
        elif index == 2 and len(talents) > 3:
            output += "{% tab title=\"" + talents[talent]['name'] + "\" %}\n"
            output += f'{talents[talent]["desc"]}\n\n'
            output += '| Effect | Values |\n' + \
                      '| :--- | :--- |\n'
            for hit in talents[talent]['values']:
                output += "| " + hit + " | " + talents[talent]['values'][hit][0].strip() + " |\n"
            output += "{% endtab %}\n\n"
        else:
            output += "{% tab title=\"" + talents[talent]['name'] + "\" %}\n"
            output += f'{talents[talent]["desc"]}\n\n'
            output += '| Effect | Talent 6% / Data |' + '\n| :--- | :--- |\n'
            for hit in talents[talent]['values']:
                output += "| " + hit + " | " + talents[talent]['values'][hit][5].strip() + " |\n"
            output += "{% endtab %}\n"
    output += "{% endtabs %}\n\n"
    # print(output)
    return output

def talents_to_md(talents):
    output = "## Full Talent Values\n\n{% tabs %}"

    for index, talent in enumerate(talents):
        if index == 0:
            output += "{% tab title=\"" + talents[talent]['name'][len("Normal Attack: "):] + "\" %}\n"
            output += "### Normal Attacks\n\n"
            output += "|  | Lv6 | Lv7 | Lv8 | Lv9 | Lv10 | Lv11 |" + "\n| :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n"
            for hit in talents[talent]['values']:
                if hit.find("Charged Attack") != -1 or hit.find("Aimed Shot") != -1:
                    break
                output += "| " + hit + " |"
                for val in talents[talent]['values'][hit][5:11]:
                    output += " " + val.replace("%", "").strip() + " |"
                output += "\n"

            output += "\n### Charged Attack\n\n"
            output += "|  | Lv6 | Lv7 | Lv8 | Lv9 | Lv10 | Lv11 |" + "\n| :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n"
            for hit in talents[talent]['values']:
                if hit.find("Charged Attack") == -1 and hit.find("Aimed Shot") == -1:
                    continue
                if hit.find("Stamina Cost") != -1:
                    output += f"\n**Stamina Cost:** {talents[talent]['values']['Charged Attack Stamina Cost'][0].replace(' /s','')}\n"
                    break
                output += "| " + hit + " |"
                for val in talents[talent]['values'][hit][5:11]:
                    output += " " + val.replace("%", "").strip() + " |"
                output += "\n"

            output += "\n### Plunge \n\n"
            output += "|  | Lv6 | Lv7 | Lv8 | Lv9 | Lv10 | Lv11 |" + "\n| :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n"
            for hit in talents[talent]['values']:
                if hit.find("Plunge") == -1:
                    continue
                if hit.find("Low/High") > -1:
                    low = []
                    high = []
                    for val in talents[talent]['values'][hit][5:11]:
                        low.append(val.split()[0])
                        high.append(val.split()[-1])
                    output += "| Low Plunge DMG |"
                    for val in low:
                        output += " " + val.replace("%", "").strip() + " |"
                    output += "\n| High Plunge DMG |"
                    for val in high:
                        output += " " + val.replace("%", "").strip() + " |"
                    output += "\n"
                    continue

                output += "| " + hit + " |"
                for val in talents[talent]['values'][hit][5:11]:
                    output += " " + val.replace("%", "").strip() + " |"
                output += "\n"
            output += "{% endtab %}\n\n"
        if index == 1:
            output += "{% tab title=\"" + talents[talent]['name'] + "\" %}\n"
            output += "|  | Lv6 | Lv7 | Lv8 | Lv9 | Lv10 | Lv11 | Lv12 | Lv13 |" + "\n| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n"
            for hit in talents[talent]['values']:
                if hit == "Duration":
                    output += f"\n**Duration:** {talents[talent]['values'][hit][0]}\n"
                    continue
                if hit == "CD":
                    output += f"\n**Cooldown:** {talents[talent]['values'][hit][0]}\n"
                    continue
                output += "| " + hit + " |"
                for val in talents[talent]['values'][hit][5:13]:
                    output += " " + val.replace("%", "").strip() + " |"
                output += "\n"
            output += "{% endtab %}\n\n"
        if index == len(talents)-1:
            output += "{% tab title=\"" + talents[talent]['name'] + "\" %}\n"
            output += "|  | Lv6 | Lv7 | Lv8 | Lv9 | Lv10 | Lv11 | Lv12 | Lv13 |" + "\n| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n"
            for hit in talents[talent]['values']:
                if hit == "Duration":
                    output += f"\n**Duration:** {talents[talent]['values'][hit][0]}\n"
                    continue
                if hit == "CD":
                    output += f"\n**Cooldown:** {talents[talent]['values'][hit][0]}\n"
                    continue
                if hit == "Energy Cost":
                    output += f"\n**Energy Cost:** {talents[talent]['values'][hit][0]}\n"
                    continue
                output += "| " + hit + " |"
                for val in talents[talent]['values'][hit][5:13]:
                    output += " " + val.replace("%", "").strip() + " |"
                output += "\n"
            output += "{% endtab %}\n"
    output += "{% endtabs %}\n"
    # print(output)
    return output

def passives_to_md(passives):
    output = '## **Ascension Passives**' + '\n\n'
    output += '{% tabs %}'
    keys = list(passives)
    for i in range(0, 3):
        if i == 0:
            output += "\n{% tab title=\"Passive\" %}\n"
        if i == 1:
            output += "\n{% tab title=\"Ascension 1\" %}\n"
        if i == 2:
            output += "\n{% tab title=\"Ascension 4\" %}\n"
        output += f"### {keys[i]}\n\n{passives[keys[i]]}\n"
        output += "{% endtab %}\n"
    output += "{% endtabs %}\n"
    # print(output)
    return output

def cons_to_md(cons):
    output = '## **Constellations**' + '\n\n'
    output += '{% tabs %}'
    keys = list(cons)
    for i in range(0,len(keys)):
        output += "\n{% tab title=\"C" + str(i + 1) + "\" %}\n"
        output += f"### {keys[i]}\n\n{cons[keys[i]]}\n"
        output += "{% endtab %}\n"
    output += "{% endtabs %}\n"
    output.replace('\u2022', "*")
    # print(output)
    return output

def links_to_md(character):
    output = '## **External Links**' + '\n\n'
    output += f"* [**Genshin Impact Fandom**](https://genshin-impact.fandom.com/wiki/{character['name']})\n\n"
    output += '**Evidence Vault:**' + '\n\n'
    output += f"{{% page-ref page=\"../../evidence/characters/{character['desc']['Element'].lower()}/{character['id']}.md\" %}}\n"
    return output

def char_to_md(character):
    f = open(f"{character['id']}.md", "w", encoding='utf-8')
    f.write(char_data_to_md(character) + "\n")
    f.write(base_stats_to_md(character['stats']) + "\n")
    f.write(talent_desc_to_md(character['talents']) + "\n")
    f.write(passives_to_md(character['passives']) + "\n")
    f.write(cons_to_md(character["cons"]) + "\n")
    f.write(talents_to_md(character['talents']) + "\n")
    f.write(links_to_md(character))
    f.close()

def main():
    character = input("Enter the character's name: ")
    data = get_character(character)
    char_to_md(data)
    print(json.dumps(data, indent=4))
    print("File saved to " + data['id'] + ".md\n")
    f = open(f"{data['id']}.json", "w", encoding='utf-8')
    f.write(json.dumps(data, indent=4))
    f.close()
    # base_stats_to_md(data['stats'])
    # talents_to_md(data['talents'])
    # passives_to_md(data['passives'])
    # cons_to_md(data["cons"])

if __name__ == "__main__":
    main()
