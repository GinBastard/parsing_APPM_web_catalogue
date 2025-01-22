from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
options = Options()
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
import requests

import pandas as pd
pd.set_option('display.expand_frame_repr', False)   # показывать все строки и столбцы без переносов
pd.set_option('display.max_colwidth', 20)


types = {'Лианы': 'https://www.ruspitomniki.ru/catalog/liany/',
         'Лиственные деревья': 'https://www.ruspitomniki.ru/catalog/listvennye-derevya/',
         'Лиственные кустарники': 'https://www.ruspitomniki.ru/catalog/listvennye-kustarniki/',
         'Розы': 'https://www.ruspitomniki.ru/catalog/rozy/',
         'Травянистые многолетники': 'https://www.ruspitomniki.ru/catalog/mnogoletnie-cvety/',
         'Хвойные': 'https://www.ruspitomniki.ru/catalog/hvojnye/'}


def get_plants_categories(types):
    '''
    Из словаря типов растений получаем список категорий растений
    :param types:
    :return:
    '''
    driver = webdriver.Chrome(options=options)
    categories = []
    for type, url in types.items():   # перебираем словарь типов и ссылок
        driver.get(url)

        # находим секцию страницы с категориями
        section_element = driver.find_element(By.CSS_SELECTOR, "section.section.pt-0")

        # получаем массив элементов категорий растений
        cat_elements = section_element.find_elements(By.CSS_SELECTOR, "div.col-sm-6.col-lg-4")

        for element in cat_elements:  # перебираем массив элементов категорий растений
            category = []
            try:
                a_elements = element.find_elements(By.TAG_NAME, 'a')  # выбираем элементы с тэгом a
                # Находим русское название и ссылку на страницу растений категории
                count = 0
                for a in a_elements:  # перебираем элементы с тэгом a
                    count += 1
                    # вторая ссылка - это ссылка на страницу растений категории
                    if count == 2:
                        cat_name = a.text.strip()  # у второй ссылки получаем название категории
                        href = a.get_attribute("href")  # у второй ссылки получаем url (href) на страницу растений категории

                # Находим латинское название категории
                try:
                    div_element = element.find_element(By.TAG_NAME, 'div')
                    cat_name_lat = div_element.text.strip()  # Находим латинское название категории
                except NoSuchElementException:
                    cat_name_lat = None  # Если нет латинского названия категории, то присваиваем None

            except StaleElementReferenceException:
                pass
            category.append(type)
            category.append(cat_name)
            category.append(cat_name_lat)
            category.append(href)
            categories.append(category)

    # [тип, название категории, название латинское категории, ссылка на страницу категории,
    # список растений в категории с ссылками]

    driver.quit()  # закрываем движок

    # Передаем полученный список в функцию получения информации о растениях (название и ссылка)
    get_plants(categories)


def get_plants(categories):
    '''
    Функция получения ДФ с категориями растений и ссылками на страницы растений
    :param categories:
    :return:
    '''
    driver = webdriver.Chrome(options=options)   # открываем движок

    plant_categories = []

    for category in categories:
        driver.get(category[3])
        # находим секцию страницы с растениями
        section_element_plants = driver.find_element(By.CSS_SELECTOR, "section.section.section-content")
        # получаем массив элементов категорий растений
        plant_elements = section_element_plants.find_elements(By.CSS_SELECTOR, "div.col-sm-6.col-lg-4")

        # перебираем массив элементов карточки растения в каталоге
        for plant in plant_elements:
            plant_dict = {}

            p_elements = plant.find_elements(By.TAG_NAME, 'a')  # выбираем элементы с тэгом a

            # Обрабатываем ссылки - получаем картинку и название растения
            count = 0
            for x in p_elements:  # перебираем элементы с тэгом a
                count += 1
                # достаем ссылку на картинку, название картинки, загружаем картинку в каталог pics
                if count == 1:
                    pic_link = x.find_element(By.TAG_NAME, 'img').get_attribute("src")
                    pic_name = pic_link.split('/')[-1]

                    response = requests.get(pic_link)
                    if response.status_code == 200:
                        with open(f'pics/{pic_name}', 'wb') as file: file.write(response.content)
                        # print("Файл успешно загружен.")
                    else:
                        print(f"Не удалось загрузить файл. Статус код:", response.status_code)
                # получаем название растения из ссылки
                elif count == 2:
                    plant_name = x.text.strip()      # у второй ссылки получаем название растения и ссылку
                    plant_href = x.get_attribute("href")

            # Получаем латинское название растения (если есть)
            try:
                div_plant = plant.find_element(By.TAG_NAME, 'div')
                plant_name_lat = div_plant.text.strip()
            except NoSuchElementException:
                plant_name_lat = None

            # Заполняем словарь
            plant_dict['type'] = category[0]
            plant_dict['cat_name'] = category[1]
            plant_dict['cat_name_lat'] = category[2]
            plant_dict['plant_name'] = plant_name
            plant_dict['plant_name_lat'] = plant_name_lat
            plant_dict['pic_name'] = pic_name
            plant_dict['plant_href'] = plant_href
            plant_categories.append(plant_dict)

    driver.quit()  # закрываем движок

    # Создание DataFrame
    df = pd.DataFrame(plant_categories)


    # Сохранение DataFrame в CSV файл
    df.to_csv('plant_categories.csv', encoding='utf-8', index=False)

    # Чтение CSV файла и создание DataFrame
    df_from_csv = pd.read_csv('plant_categories.csv', encoding='utf-8')
    # # Вывод DataFrame
    print(df_from_csv)


get_plants_categories(types)