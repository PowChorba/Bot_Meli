import pandas as pd
import requests
from time import sleep
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from csv import writer
from datetime import datetime


def read_articles():
    # Leo los productos a buscar dentro del txt
    with open('products.txt', 'r') as f:
        data = f.read()
        data = data.split('\n')
        f.close
    # Lopeo por cada procuto 
    for product in data:
        with open(f'{product}.csv', 'w', encoding='UTF-8', newline='') as f:
            write = writer(f)
            write.writerow(['title','price', 'link'])
        html = requests.get(f'https://listado.mercadolibre.com.ar/{product}#D[A:{product}]').text
        soup = BeautifulSoup(html, 'html.parser')
        # Veo cuantas paginas tiene para ver cuantos articulos tiene que agarrar
        total_pages = soup.find('li', class_='andes-pagination__page-count').text
        # Multiplico la cantidad de paginas por la cantidad de articulos por pagina
        total_pages = total_pages.replace('de ', '')
        total_pages = int(total_pages) * 50
        counter = 1
        # Obtengo la url exacta con las categorias que tiene
        url = get_url(product)
        # Loopeo por cada pagina, hasta llegar a la ultima
        while counter <= total_pages:
            if counter == 1:
                html = requests.get(f'{url}/{product}_NoIndex_True').text
            else:
                html = requests.get(f'{url}/{product}_Desde_{counter}_NoIndex_True').text    
            soup = BeautifulSoup(html, 'html.parser')
            titles = soup.find_all('h2', class_='ui-search-item__title shops__item-title')
            price = soup.find_all('span', class_='andes-money-amount__fraction')
            link = soup.find_all('a', class_='ui-search-item__group__element shops__items-group-details ui-search-link')
            for index,title in enumerate(titles):
                title = title.text
                if 'ptfe' in title.lower() or 'all metal' in title.lower() or 'repuesto' in title.lower() or 'hotend' not in title.lower():
                    continue
                title = title.replace('"', '')
                article_link = link[index].get('href')
                article_price = price[index].text
                article_price = article_price.replace('.','')
                with open(f'{product}.csv', 'a', encoding='UTF-8', newline='') as f:
                    write = writer(f)
                    write.writerow([title,article_price, article_link])
            counter += 50
        duplicates(product)    
        check_product(product)    
            
            
def get_url(product):
    driver = webdriver.Chrome(ChromeDriverManager().install())
    driver.get(f'https://listado.mercadolibre.com.ar/{product}#D[A:{product}]')
    sleep(5)
    driver.find_element(By.XPATH, '/html/body/div[2]/div[1]/div/div[2]/button[1]').click()
    sleep(3)
    driver.find_element(By.XPATH, '//*[@id="root-app"]/div/div[2]/section/div[9]/nav/li[3]/a/span[1]').click()
    sleep(5)
    url = driver.current_url
    url = url.split('/')
    url = ' '.join(url[:-1])
    url = url.replace(' ', '/')
    return url

def check_link_selenium(link, driver):
        caracteristicas = []
        driver.maximize_window()
        driver.execute_script(f"window.open('{link}')")
        window_handles = driver.window_handles  
        driver.switch_to.window(window_handles[-1])
        sleep(5)
        try:
            driver.find_element(By.XPATH, '/html/body/div[2]/div[1]/div/div[2]/button[1]').click()
        except:
            pass  
        sleep(2)
        # try:
        #     tipo_entrada = driver.find_element(By.XPATH, '//*[@id="technical_specifications"]/div/div[2]/ul[1]/li[1]/p').text
        # except:
        #     print(link)    
        try:
            modelo = driver.find_element(By.XPATH, '//*[@id="technical_specifications"]/div/div[1]/table/tbody/tr[1]/td/span').text
            caracteristicas.append(modelo)
        except:
            modelo = 'No especifica'    
            caracteristicas.append(modelo)
        try:
            entrada = driver.find_element(By.XPATH, '//*[@id="technical_specifications"]/div/div[2]/ul[1]/li[1]/p').text
            caracteristicas.append(entrada)
        except:
            entrada = 'No especifica'
            caracteristicas.append(entrada)
        try:
            voltaje = driver.find_element(By.XPATH, '//*[@id="variations"]/div/div/p').text
            caracteristicas.append(voltaje)
        except:
            voltaje = 'No especifica'   
            caracteristicas.append(voltaje)
        try:
            descripcion = driver.find_element(By.XPATH, '//*[@id="description"]').text
            caracteristicas.append(descripcion)
        except:
            descripcion = 'No especifica' 
            caracteristicas.append(descripcion)    
        sleep(2)
        driver.close() 
        driver.switch_to.window(window_handles[0])
        return caracteristicas

def check_product(product):
    list_links = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    data = pd.read_csv(f'{product}.csv')
    # driver = login()
    driver = webdriver.Chrome(ChromeDriverManager().install())
    for link in data['link']:
        boolean_modelo = False
        boolean_voltaje = False
        boolean_entrada = False
        boolean_metal = True
        html = requests.get(link, headers=headers).text
        soup = BeautifulSoup(html, 'html.parser')
        try:
            modelo = soup.find('span', class_='andes-table__column--value').text
            entrada = soup.find('p', class_='ui-pdp-family--REGULAR ui-pdp-list__text').text
            voltaje = soup.find('p', class_='ui-pdp-variations__label ui-pdp-variations__label-only-text ui-pdp-color--BLACK').text
            descripcion = soup.find('div', class_='ui-pdp-container__row ui-pdp-container__row--description').text
            caracteristicas = [modelo,entrada, voltaje, descripcion]
        except:
            caracteristicas = check_link_selenium(link, driver)  
        if '12' in caracteristicas[2]:
            boolean_voltaje = True
        if 'v6' in caracteristicas[0].lower() or 'v6' in caracteristicas[3].lower() or 'repuesto' in caracteristicas[3].lower():
            boolean_modelo = True      
        if 'all metal' in caracteristicas[3].lower():
            boolean_metal = False   
        if boolean_modelo == True and boolean_voltaje == True and boolean_metal == True:
            print(boolean_modelo, boolean_metal, boolean_voltaje, 'Deberian ser los 3 verdaderos')      
        else:
            list_links.append(link)
    for i in list_links:
        data_link = pd.read_csv(f'{product}.csv')
        for index,links in enumerate(data_link['link']):
            if i == links:
                data = data_link.drop(index=index)
                data.to_csv(f'{product}.csv', index=False)
            else:
                pass                      
    print('Listo')

def login():
    driver = webdriver.Chrome()
    driver.get('https://www.mercadolibre.com.ar/')
    sleep(5)
    # Clickeo el boton de Ingreso
    driver.find_element(By.XPATH,'//*[@id="nav-header-menu"]/a[2]').click()
    sleep(5)
    # Escribo el email en el input
    driver.find_element(By.XPATH, '//*[@id="user_id"]').send_keys('rpa.robotize@gmail.com')
    sleep(2)
    # Clickeo el boton de continuar
    driver.find_element(By.XPATH, '//*[@id="login_user_form"]/div[2]/button/span').click()
    sleep(5)
    # Chequeo si salio el captcha y lo resuelvo
    try:
        # CAPTCHA
        driver.find_element(By.XPATH, '//*[@id="g-recaptcha"]/div/div/iframe').click()
        sleep(3)
        driver.find_element(By.XPATH, '//*[@id="login_user_form"]/div[2]/button/span').click()
        sleep(5)
    except:
        print('No hay captcha')
    # Escribo la password en el input
    driver.find_element(By.XPATH, '//*[@id="password"]').send_keys('laColina123@')
    sleep(5)
    # Clickeo el boto de login
    driver.find_element(By.XPATH,'//*[@id="action-complete"]/span').click()
    sleep(5)
    # Chequeo si salio el segundo captcha y lo resuelvo
    try:
        # CAPTCHA
        driver.find_element(By.XPATH, '//*[@id="g-recaptcha"]/div/div/iframe').click()
        sleep(5)
        driver.find_element(By.XPATH, '//*[@id="password"]').send_keys('laColina123@')
        sleep(5)
        driver.find_element(By.XPATH,'//*[@id="action-complete"]/span').click()
    except:
        print('No hay captcha en segunda parte')    
    return driver

def duplicates(product):
    variable_csv = f'{product}.csv'
    data = pd.read_csv(variable_csv) 
    # data = data.drop_duplicates()    
    duplicates_mask = data.duplicated(subset=['title'], keep='first')
    data = data[~duplicates_mask]
    data.to_csv(variable_csv, index=False) 
    
# login()  
# check_product('hotend')    
# duplicates('hotend')
read_articles()

def file_time():
    fecha = datetime.now()
    fecha = str(fecha).split(' ')
    hora = fecha[1]
    hora = hora.split('.')
    hora = hora[0][:5].replace(':', '_')
    fecha = fecha[0]
    fecha = fecha.replace('-', '_')
    fecha = fecha + ' ' + hora
    return fecha

# file_time()