import csv
import os
import shutil
from random import randrange
from time import sleep

import requests
from bs4 import BeautifulSoup


def create_first_page_obj_each_folder():
    """Create the first page for each folder

        The function receives the html code of the first page of objects
        for each product category (headers) and writes it to a file
    """
    for key, value in all_content.items():
        print(key)
        for href in value:
            if ((href['href'].count('/') == 3 and key in [
                'Смартфоны',
                'Планшеты',
                'Ноутбуки'
                ]
                 and 'naushniki' not in href['href'])
                    or (key in ['Гаджеты', 'Аудио'] and (
                        'gadzhety' in href['href']
                        or href['href'][
                                        href['href'].rindex('/') + 1:] ==
                        'naushniki'))):

                if href.find("img")["alt"] == 'Оргтехника':
                    continue
                get_and_write(
                    file=f'headers/{key}/list_objects_'
                    f'{href.find("img")["alt"]}.html',
                    href=f'{url}/{href["href"]}')
                print(f'{url}/{href["href"]}')
        print()
        sleep(randrange(2, 5))


def safe_print(*args, **kwargs):
    """Safe print with result return

        Print suppresses exceptions if they occur and returns the argument
        values if any,
        otherwise '-'
    """
    try:
        print(*args, **kwargs)
        rez = args[0]
    except Exception:
        print('-')
        rez = '-'
    return rez


def get_and_write(file, href):
    """Get html page and write it to file

        The function receives the html code of the page and writes all
        the content to a file.
        This is done in order not to overload the site with get requests.
    """
    with open(file, 'w') as html_file:
        req = requests.get(href, headers=headers_for_req)
        src = req.text
        html_file.write(src)


def take_hrefs_of_objects(headers, html):
    """Get all links from a page

        The function opens the html file, makes it a BeautifulSoup object and
        finds all the links there,
        writing them by the corresponding key to which the html page belongs
    """
    for folder in headers:
        with open(f'headers/{folder}/{html}.html') as file:
            src = file.read()
            soup = BeautifulSoup(src, 'lxml')
            content = soup.find('ul', class_='catalog_nodes').find_all('a')
            all_content[folder].extend(content)


def create_html_each_folder():
    """Create html file for each category from headers

        The function creates a folder for each category from headers.
        Gets the html code of the home page of each category (headers) and
        loads it into a file
    """
    for item in all_categories:
        try:
            os.mkdir(f'headers/{item.text}')
        except FileExistsError:
            pass
        get_and_write(
            file=f'headers/{item.text}/index.html',
            href=f'{url}/{item["href"]}'
        )
        sleep(randrange(2, 5))
        print(f'{item.text}: {url}/{item["href"]}')


def load_all_pages(folder, html, src, namefile, count=1):
    """Download all object pages for each category

        The function recursively traverses all pages of objects
        that belong to the corresponding categories (headers)
        and writes them to a file
    """
    with open(f'headers/{folder}/{html}', 'w') as file:
        file.write(src)
        soup = BeautifulSoup(src, 'lxml')
        try:
            print(soup.find('ul', class_='pager').find_all('li')[-1])
        except AttributeError:  # It means that this page is single
            return
        soup = str(soup.find('ul', class_='pager').find_all('li')[-1])
        if 'следующая' in soup:
            href = soup[soup.index('href') + len('href') + 2:soup.rindex('">')]
            req = requests.get(f'{url}{href}')
            src = req.text
            return load_all_pages(folder, namefile=namefile,
                                  html=f'{namefile}_page{count + 1}.html',
                                  src=src, count=count + 1)
        else:
            return


def create_first_page_obj_audio():
    """Create first page for audio folder

        The function gets the html code of the first page of objects
        for the audio folder and writes it to a file.
        Since the structure of the page where the audio objects are located
        is slightly different,
        we have to dive even deeper to get the first page of audio objects
    """
    for href in all_content['Аудио']:
        if '-naushniki-' in href["href"][href["href"].rindex('/'):]:
            get_and_write(
                file=f'headers/Аудио/list_objects_'
                f'{href.find("img")["alt"]}.html',
                href=f'{url}/{href["href"]}')

            print(f'{url}/{href["href"]}')


def load_all_pages_in_folders():
    """Download all pages for each category

        The function iterates through all the start pages of each category and
        recursively loads the remaining matching ones.

    """
    for folder in headers:
        walks = os.walk(f'headers/{folder}')
        for files in walks:
            for file in files[-1]:
                if file == '.DS_Store':
                    continue
                with open(f'headers/{folder}/{file}') as rfile:
                    src = rfile.read()
                    name_file = (
                        rfile.name[rfile.name.rindex('/') + 1:
                                   rfile.name.rindex('.')]
                        )
                    os.remove(f'headers/{folder}/{file}')
                    load_all_pages(
                        folder,
                        f'{name_file}_page1.html',
                        src,
                        name_file
                        )
                    print(f'{name_file.upper()}: LOADED')


def write_in_csv():
    """Get data and write to csv file

        The function visits the page of each object, takes the necessary data
        and writes it to the corresponding csv file
    """

    for folder in headers:
        count1 = 0
        walks = os.walk(f'headers/{folder}')
        for files in walks:
            with open(f'data/{folder}.csv', 'w') as file_csv:
                writer = csv.DictWriter(
                    file_csv,
                    fieldnames=fieldnames,
                    delimiter=';',
                    quoting=csv.QUOTE_NONNUMERIC
                    )
                writer.writeheader()
                for file in files[-1]:
                    print(file)
                    if file == '.DS_Store':
                        continue
                    with open(f'headers/{folder}/{file}') as rfile:
                        src = rfile.read()
                    soup = BeautifulSoup(src, 'lxml').find(
                        'ul',
                        class_='catalog_items'
                        ).find_all('li')
                    for li in soup:
                        if not (
                            any(name in li.text for name in names_obj[folder])
                            and "РУБ." in li.text
                            and li.text != '.DS_Store'
                                ):
                            continue
                        data = {}
                        href_of_page = f'{url}/{li.find("div", class_="catalog_item hoverable catalog_item_ops_bottom catalog_item_simplified").find("a", class_="catalog_item_link")["href"]}'
                        req = requests.get(href_of_page, headers=headers_for_req)
                        src = req.text
                        soup = BeautifulSoup(src, 'lxml')
                        print(href_of_page)
                        data['Категория'] = safe_print(f"{folder}")
                        data['Название'] = safe_print(f"{soup.find('h1').text}")
                        if data['Название'] in [
                            'Ноутбуки MSI',
                            'Все варианты Lenovo IdeaCentre 5 24IOB6',
                            'Моноблоки Lenovo',
                            'Мониторы Iiyama',
                            'Мониторы AOC'
                        ]:
                            continue
                        try:
                            href = soup.find(
                                'div',
                                class_='catalog_brand_more'
                                ).find('a')
                            data['Все товары от бренда'] = safe_print(f"{url}/{href['href']}")
                        except AttributeError:
                            data['Все товары от бренда'] = '-'
                        try:
                            data['Фото'] = safe_print(
                                f"{url}{soup.find('div', class_='media_display').find('img')['src']}")
                        except (TypeError, AttributeError):
                            data['Фото'] = '-'
                        data['Преимущество'] = safe_print(
                            f"{soup.find('div', class_='catalog_variant_specs').text}")
                        href = soup.find(
                            'ul',
                            class_='catalog_variant_addon_other'
                            ).find('a')
                        try:
                            base_charac = \
                            f"{soup.find('div', class_='catalog_variant_addon_characteristics').text}".split(':')[
                                -1]
                            base_charac = base_charac.split('•')
                            base_rest = base_charac[:]
                        except AttributeError:
                            base_charac, base_rest = [], []

                        '''Details for each category'''
                        count = 0
                        for char in range(len(base_charac)):
                            if 'Android' in base_charac[char] or 'OS' in base_charac[char] or 'Windows' in \
                                    base_charac[char]:
                                data['ОС'] = safe_print(f"{base_charac[char]}")
                                base_rest.remove(base_charac[char])
                            elif 'яд' in base_charac[char]:
                                if 'ГГц' in base_charac[char]:
                                    data['Частота и количество ядер процессора'] = safe_print(
                                        f"{', ('.join(base_charac[char].split('('))}")
                                else:
                                    data['Частота и количество ядер процессора'] = safe_print(
                                        f"- , {base_charac[char]}")
                                base_rest.remove(base_charac[char])
                                count += 1
                            elif 'RAM' in base_charac[char] and 'Гб' in base_charac[char]:
                                data['RAM'] = safe_print(
                                    f"{base_charac[char].strip()[base_charac[char].strip().rindex('M') + 2:]}")
                                base_rest.remove(base_charac[char])
                                count += 1
                            elif (((('SSD' in base_charac[char] and 'Гб' in base_charac[char])
                                    or 'SSD' in base_charac[char] and 'Мб' in base_charac[
                                        char]) and folder == 'Ноутбуки')
                                  or (folder == 'Смартфоны' and 'RAM' not in base_charac[char] and 'Гб' in
                                      base_charac[char])):
                                data['Память'] = safe_print(f"{base_charac[char]}")
                                base_rest.remove(base_charac[char])
                                count += 1
                            if count == 4:
                                break
                        for category in [
                            'Память',
                            'RAM',
                            'Частота и количество ядер процессора',
                            'ОС'
                        ]:
                            if category not in data:
                                data[category] = '-'
                        data['Остальные характеристики'] = safe_print(f"{'•'.join(base_rest)}")
                        data[f'Все характеристики'] = safe_print(f"{url}{href['href']}")
                        data['Описание'] = safe_print(
                            f"{soup.find('div', class_='catalog_variant_description').text}")
                        data['Код товара'] = safe_print(
                            f"{soup.find('div', class_='catalog_variant2_statehead_code gray').find('b').text}")
                        data['Цена'] = safe_print(
                            f"{soup.find('ul', class_='catalog_variant_state_left').find('strong').text}")
                        data['Баллы за покупку'] = safe_print(
                            f"{soup.find('li', class_='catalog_variant2_profit_item catalog_variant2_profit_item_bonus').find('span').text}")
                        data['Ссылка на товар'] = safe_print(href_of_page)
                        writer.writerow(data)
                        count1 += 1
                        print('COUNT' + str(count1))
                        print()
                        print()


def main():
    global all_categories
    get_and_write(file='index.html', href=url)
    with open('index.html') as file:
        src = file.read()
    soup = BeautifulSoup(src, 'html.parser')
    all_categories = soup.find('ul', class_='header_groups').find_all('a', class_='popup_handle header_group')
    all_categories = list(filter(lambda x: 'Apple' not in str(x) and 'Аксессуары' not in str(x), all_categories))
    create_html_each_folder()
    take_hrefs_of_objects(headers=headers, html='index')
    create_first_page_obj_each_folder()
    take_hrefs_of_objects(headers=('Аудио',), html='list_objects_Наушники')
    os.remove('headers/Аудио/list_objects_Наушники.html')
    create_first_page_obj_audio()
    for folder in headers:
        try:
            os.remove(f'headers/{folder}/index.html')
        except FileNotFoundError:
            pass
    load_all_pages_in_folders()
    try:
        os.mkdir('data')
    except FileExistsError:
        pass
    write_in_csv()

    # Delete folder with html pages of the site
    os.remove('index.html')
    shutil.rmtree('headers')


# Creating a root directory where all html files will be stored
try:
    os.mkdir('headers')
except FileExistsError:
    pass

# home page url
url = 'https://xn----8sb1bezcm.xn--p1ai/'

# This is necessary so that the site does not think that
# we are a bot and give us their html pages
headers_for_req = {
    'accept': '*/*',
    'User-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'
                  ' AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/102.0.0.0 Safari/537.36'
}

# Relevant categories == future datasheets
headers = (
    'Смартфоны',
    'Планшеты',
    'Ноутбуки',
    'Гаджеты',
    'Аудио'
)

# Subcategories of each category
names_obj = {
    'Смартфоны': [
        'Смартфон'
        ],
    'Планшеты': [
        'Планшет'
        ],
    'Ноутбуки': [
        'Ноутбук',
        'Монитор',
        'Моноблок'
        ],
    'Гаджеты': [
        'Смарт-браслеты',
        'Смарт-часы'
        ],
    'Аудио': [
        'Наушники',
        'наушники',
        'Гарнитура'
        ],
}

# Fields in csv files
fieldnames = [
    'Категория',
    'Название',
    'Все товары от бренда',        
    'Фото',
    'Преимущество',
    'ОС',
    'Частота и количество ядер процессора',
    'RAM',
    'Память',
    'Остальные характеристики',
    'Все характеристики',
    'Описание',
    'Код товара',
    'Цена',
    'Баллы за покупку',
    'Ссылка на товар'
    ]

all_content = {folder: [] for folder in headers}


if __name__ == '__main__':
    main()
