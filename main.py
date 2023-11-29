import json
import os
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def get_distro():
    url = 'https://distrowatch.com/table.php?distribution=mint'

    driver = webdriver.Chrome()  # Você pode usar o driver do navegador de sua escolha
    driver.get(url)

    wait = WebDriverWait(driver, 10)
    wait.until(EC.presence_of_element_located((By.TAG_NAME, 'body')))

    html = driver.page_source

    driver.quit()

    based_on = get_element('<li><b>Based on', '</li>', html)

    origin = get_element('<li><b>Origin', '</li>', html)

    image_and_distro = get_element('<td class="TablesTitle">', '</h1>', html)

    data = {
        "Distro": extract_distro_name(image_and_distro),
        "Origin": extract_a_element(origin)[0].text,
        "Image": extract_image(image_and_distro),
        "BasedOn": '|'.join(a_tag.text for a_tag in extract_a_element(based_on))
    }

    json_data = json.dumps(data, indent=2)
    save_image(extract_image(image_and_distro))

    print(json_data)


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


def extract_distro_name(text):
    soup: BeautifulSoup = BeautifulSoup(text, 'html.parser')
    return soup.find('h1').text


def save_image(image_link):
    pasta_destino = 'images'

    # Certifique-se de que a pasta existe, se não, crie-a
    if not os.path.exists(pasta_destino):
        os.makedirs(pasta_destino)

    # Obtém o nome do arquivo da URL
    nome_arquivo = os.path.join(pasta_destino, os.path.basename(image_link))

    # Verifica se o arquivo já existe
    if os.path.exists(nome_arquivo):
        print(f'A imagem {nome_arquivo} já existe.')
    else:
        # Faz o download da imagem
        response = requests.get(image_link)

        # Verifica se o download foi bem-sucedido (status code 200)
        if response.status_code == 200:
            # Salva a imagem no arquivo local
            with open(nome_arquivo, 'wb') as f:
                f.write(response.content)
            print(f'Imagem salva em: {nome_arquivo}')
        else:
            print(f'Falha ao baixar a imagem. Status code: {response.status_code}')


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    get_distro()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
