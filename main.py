import requests
from bs4 import BeautifulSoup
import os
import shutil
import csv
from time import sleep
from random import randrange
# Для начала работы нужно установить 3 модуля
# beautifulsoup4 для превращения html страницы к объекту beautifulsoup и дальнейшей работы с ней
# (взятие тегов, элементов и тд)
# requests для получения html страниц сайта
# lxml подойдет лучше всего для парса html страницы, используется как второй позиционный аргумент
# передаваемый классу Beautifulsoup


def create_first_page_obj_each_folder():
    """Создать первую страницу для каждой папки

    Функция получает html-код первой страницы объектов для каждой категории товаров(headers) и записывает в файл
    """
    for key, value in all_content.items():
        print(key)
        for href in value:
            if ((href['href'].count('/') == 3 and key in ['Смартфоны', 'Планшеты', 'Ноутбуки']
                 and 'naushniki' not in href['href'])
                    or (key in ['Гаджеты', 'Аудио'] and ('gadzhety' in href['href']
                                                         or href['href'][
                                                            href['href'].rindex('/') + 1:] == 'naushniki'))):

                if href.find("img")["alt"] == 'Оргтехника':
                    continue
                get_and_write(file=f'headers/{key}/list_objects_{href.find("img")["alt"]}.html',
                              href=f'{url}/{href["href"]}')
                print(f'{url}/{href["href"]}')
        print()
        sleep(randrange(2, 5))


def safe_print(*args, **kwargs):
    """Безопасный принт с возвращением результата

       Принт подавляет исключения, если они возникли и возвращает значения аргументов, если они есть,
       иначе '-'
        """
    try:
        print(*args, **kwargs)
        rez = args[0]
    except Exception:
        print('-')
        rez = '-'
    return rez


def get_and_write(file, href):
    """Получить html страницу и записать ее в файл

    Функция получает html-код страницы и записывает все содержимое в файл.
    Это делается для того, чтобы не перегружать сайт get-запросами
    """
    with open(file, 'w') as html_file:
        req = requests.get(href, headers=headers_for_req)
        src = req.text
        html_file.write(src)


def take_hrefs_of_objects(headers, html):
    """Получить все ссылки со страницы

    Функция открывает html файл, делает его объектом BeautifulSoup и находит там все ссылки,
    записывая их по соответствующему ключу, которому принадлежит html-страница
    """
    for folder in headers:
        with open(f'headers/{folder}/{html}.html') as file:
            src = file.read()
            soup = BeautifulSoup(src, 'lxml')
            content = soup.find('ul', class_='catalog_nodes').find_all('a')
            all_content[folder].extend(content)


def create_html_each_folder():
    """Создать html файл для каждой категории из headers

        Функция создает папку на каждую категорию из headers.
        Получает html-код начальной страницы каждой категории(headers) и загружает его в файл
    """
    for item in all_categories:
        try:
            os.mkdir(f'headers/{item.text}')
        except FileExistsError:
            pass
        get_and_write(file=f'headers/{item.text}/index.html', href=f'{url}/{item["href"]}')
        sleep(randrange(2, 5))
        print(f'{item.text}: {url}/{item["href"]}')


def load_all_pages(folder, html, src, namefile, count=1):
    """Загрузить все страницы объектов для каждой категории

        Функция рекурсивно обходит все страницы объектов, которые принадлежат соответствующим категориям(headers)
        и записывает их в файл
    """
    with open(f'headers/{folder}/{html}', 'w') as file:
        file.write(src)
        soup = BeautifulSoup(src, 'lxml')
        try:
            print(soup.find('ul', class_='pager').find_all('li')[-1])
        except AttributeError as e:  # Значит это страница единственная
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
    """
        Создать первую страницу для папки аудио

        Функция получает html-код первой страницы объектов для папки аудио и записывает в файл.
        Так как структура страницы, где находятся объекты аудио немного отличается,
         нам приходится погружаться еще глубже, чтобы достать первую страницу объектов аудио
        """
    for href in all_content['Аудио']:
        if '-naushniki-' in href["href"][href["href"].rindex('/'):]:
            get_and_write(file=f'headers/Аудио/list_objects_{href.find("img")["alt"]}.html',
                          href=f'{url}/{href["href"]}')

            print(f'{url}/{href["href"]}')


def load_all_pages_in_folders():
    """Загрузить все страницы для каждой категории

        Функция проходит по всем начальным страницам каждой категории и рекурсивно загружает оставшиеся соответствующие

    """
    for folder in headers:
        walks = os.walk(f'headers/{folder}')
        for files in walks:
            for file in files[-1]:
                if file == '.DS_Store':
                    continue
                with open(f'headers/{folder}/{file}') as rfile:
                    src = rfile.read()
                    name_file = rfile.name[rfile.name.rindex('/') + 1:rfile.name.rindex('.')]
                    os.remove(f'headers/{folder}/{file}')
                    load_all_pages(folder, f'{name_file}_page1.html', src, name_file)
                    print(f'{name_file.upper()}: LOADED')


def write_in_csv():
    """Получить данные и записать в csv файл

    Функция заходит на страницу каждого объекта, берет необходимые данные и записывает их в соответствующий csv файл
    """

    for folder in headers:
        count1 = 0
        walks = os.walk(f'headers/{folder}')
        for files in walks:
            with open(f'data/{folder}.csv', 'w') as file_csv:
                writer = csv.DictWriter(file_csv, fieldnames=fieldnames, delimiter=';',
                                        quoting=csv.QUOTE_NONNUMERIC)
                writer.writeheader()
                for file in files[-1]:
                    print(file)
                    if file == '.DS_Store':
                        continue
                    with open(f'headers/{folder}/{file}') as rfile:
                        src = rfile.read()
                    soup = BeautifulSoup(src, 'lxml').find('ul', class_='catalog_items').find_all('li')
                    for li in soup:
                        if not (any(name in li.text for name in names_obj[folder]) and "РУБ." in li.text
                                and li.text != '.DS_Store'):
                            continue
                        data = {}
                        href_of_page = f'{url}/{li.find("div", class_="catalog_item hoverable catalog_item_ops_bottom catalog_item_simplified").find("a", class_="catalog_item_link")["href"]}'
                        req = requests.get(href_of_page, headers=headers_for_req)
                        src = req.text
                        soup = BeautifulSoup(src, 'lxml')
                        print(href_of_page)
                        data['Категория'] = safe_print(f"{folder}")
                        data['Название'] = safe_print(f"{soup.find('h1').text}")
                        if data['Название'] in ['Ноутбуки MSI', 'Все варианты Lenovo IdeaCentre 5 24IOB6',
                                                'Моноблоки Lenovo', 'Мониторы Iiyama', 'Мониторы AOC']:
                            continue
                        try:
                            href = soup.find('div', class_='catalog_brand_more').find('a')
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
                        href = soup.find('ul', class_='catalog_variant_addon_other').find('a')
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
                        for category in ['Память', 'RAM', 'Частота и количество ядер процессора', 'ОС']:
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
    soup = BeautifulSoup(src, 'lxml')
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

    # os.remove('index.html')
    # shutil.rmtree('headers')  # Удалить папку с html страницами сайта


try:
    os.mkdir('headers')  # Создание корневого каталога, где будут храниться все html файлы
except FileExistsError:
    pass

url = 'https://xn----8sb1bezcm.xn--p1ai/'  # url главной страницы сайта

headers_for_req = {
    'accept': '*/*',  # Это необходимо, чтобы сайт не подумал, что мы бот и дал нам свои html страницы
    'User-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)' 
                  ' AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'
}

headers = (
    'Смартфоны',
    'Планшеты',
    'Ноутбуки',  # Соответствующие категории == будущие таблицы данных
    'Гаджеты',
    'Аудио'
)

names_obj = {
    'Смартфоны': ['Смартфон'],
    'Планшеты': ['Планшет'],
    'Ноутбуки': ['Ноутбук', 'Монитор', 'Моноблок'],  # Подкатегории каждой категории
    'Гаджеты': ['Смарт-браслеты', 'Смарт-часы'],
    'Аудио': ['Наушники', 'наушники', 'Гарнитура'],
}

fieldnames = ['Категория', 'Название', 'Все товары от бренда', 'Фото', 'Преимущество', 'ОС',  # Поля в csv файлах
              'Частота и количество ядер процессора', 'RAM', 'Память', 'Остальные характеристики',
              'Все характеристики', 'Описание', 'Код товара', 'Цена', 'Баллы за покупку', 'Ссылка на товар']

all_content = {folder: [] for folder in headers}

if __name__ == '__main__':
    main()