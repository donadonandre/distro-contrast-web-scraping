import json

import psycopg2
import requests
# import os
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def get_distro(conn, cur, distro_link):
    url = 'https://distrowatch.com/table.php?distribution='+distro_link

    # response = requests.get(url)
    # soup = BeautifulSoup(response.text, 'html.parser')
    # # html = soup.find('body')
    # # print(html)

    driver = webdriver.Chrome()  # Você pode usar o driver do navegador de sua escolha
    driver.get(url)

    wait = WebDriverWait(driver, 10)
    wait.until(EC.presence_of_element_located((By.TAG_NAME, 'body')))

    html = driver.page_source

    driver.quit()

    based_on = get_element('<li><b>Based on', '</li>', html)
    based_on_formatted = '|'.join(a_tag.text for a_tag in extract_a_element(based_on))

    if based_on_formatted is None or not based_on_formatted:
        based_on_formatted = 'Independent'

    origin = get_element('<li><b>Origin', '</li>', html)

    image_and_distro = get_element('<td class="TablesTitle">', '</h1>', html)

    feature = get_element('<th class="TablesInvert">Feature</th>', '</tr>', html)
    features = extract_versions(feature)
    print(features)

    data = {
        "Distro": extract_distro_name(image_and_distro),
        "Origin": extract_a_element(origin)[0].text,
        "Image": extract_image(image_and_distro),
        "BasedOn": based_on_formatted,
        "Versions": '|'.join(td_tag.text for td_tag in features)
    }

    # json_data = json.dumps(data, indent=2)
    # print(json_data)

    distro_id = select_from(cur, 'bases', data['Distro'])
    if distro_id == 0:
        distro_id = save_to_database_bases(cur, data)

    # save_image(extract_image(image_and_distro))

    for td_tag in features:
        if "stable" in td_tag.text or "snapshot" in td_tag.text:
            continue
        else:
            version = td_tag.text
            distro_complete = data['Distro'] + ' ' + version
            save_to_database_distro(conn, cur, distro_complete, version, distro_id)


def get_element(start_element, end_element, html):
    start_li = html.find(start_element)
    end_li = start_li + html[start_li:].find(end_element) + 5

    if start_li != -1:
        return html[start_li:end_li]
    else:
        return ''


def extract_a_element(text):
    soup: BeautifulSoup = BeautifulSoup(text, 'html.parser')
    return soup.find_all('a')


def extract_image(text):
    soup: BeautifulSoup = BeautifulSoup(text, 'html.parser')
    return 'https://distrowatch.com/' + soup.find('img').get('src')


def extract_versions(text):
    soup: BeautifulSoup = BeautifulSoup(text, 'html.parser')
    td_tags = soup.find_all('td')
    for td_tag in td_tags:
        br_tag = td_tag.find('br')
        if br_tag:
            br_tag.replace_with(' ')

    return td_tags


def extract_distro_name(text):
    soup: BeautifulSoup = BeautifulSoup(text, 'html.parser')
    return soup.find('h1').text


# def save_image(image_link):
#     pasta_destino = 'images'
#
#     # Certifique-se de que a pasta existe, se não, crie-a
#     if not os.path.exists(pasta_destino):
#         os.makedirs(pasta_destino)
#
#     # Obtém o nome do arquivo da URL
#     nome_arquivo = os.path.join(pasta_destino, os.path.basename(image_link))
#
#     # Verifica se o arquivo já existe
#     if os.path.exists(nome_arquivo):
#         print(f'A imagem {nome_arquivo} já existe.')
#     else:
#         # Faz o download da imagem
#         response = requests.get(image_link)
#
#         # Verifica se o download foi bem-sucedido (status code 200)
#         if response.status_code == 200:
#             # Salva a imagem no arquivo local
#             with open(nome_arquivo, 'wb') as f:
#                 f.write(response.content)
#             print(f'Imagem salva em: {nome_arquivo}')
#         else:
#             print(f'Falha ao baixar a imagem. Status code: {response.status_code}')


def save_to_database_distro(connection, cursor, name, version, base_id):
    insert_query = 'INSERT INTO distro (name, version, base_id) VALUES (%s,%s,%s)'
    cursor.execute(insert_query, (name, version, base_id))

    connection.commit()


def select_from(cursor, table_name, param):
    select_query = 'SELECT id FROM {} WHERE name = %s'.format(table_name)
    cursor.execute(select_query, (param,))

    existing_record = cursor.fetchone()

    if existing_record:
        return existing_record[0]
    else:
        return 0


def save_to_database_bases(cursor, json_data):
    insert_query = 'INSERT INTO bases (name, origin, image_link, based_on, versions) VALUES (%s,%s,%s,%s,%s) RETURNING id'
    cursor.execute(insert_query,
                   (json_data['Distro'], json_data['Origin'], json_data['Image'], json_data["BasedOn"],
                    json_data['Versions']))

    result = cursor.fetchone()

    if result is not None:
        return result[0]
    else:
        return 0


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    dbname = 'distro_contrast'
    user = 'postgres'
    password = 'postgres'
    host = 'localhost'
    port = '5432'

    conn = psycopg2.connect(dbname=dbname, user=user, password=password, host=host, port=port)
    cur = conn.cursor()

    with open('table.html', 'r', encoding='utf-8') as file:
        html_content = file.read()
        soup = BeautifulSoup(html_content, 'html.parser')
        table = soup.find('table')
        if table:
            td_tags_with_class = table.find_all('td', class_='phr2')
            for tds in td_tags_with_class:
                a_tag = tds.find('a')
                if a_tag and 'href' in a_tag.attrs:
                    href_value = a_tag['href']
                    get_distro(conn, cur, href_value)

    # get_distro(conn, cur)

    cur.close()
    conn.close()
