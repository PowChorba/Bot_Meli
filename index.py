import pandas as pd
import requests
from bs4 import BeautifulSoup
from csv import writer
from demo import get_url

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
        # Veo a que categoria pertenece para agregar a la URL
        try:
            category = soup.find('li', class_='andes-breadcrumb__item shops__breadcrumb-item').text
            print('entro aca')
        except:
            print('entro aca dos')
            category = soup.find(attrs={'itemprop': 'itemListElement'}).text
            # for i in category:
            #     print(i.text)
        print(category)    
        # category = category.lower()
        # category = category.replace(' ', '-')
        # category = category.replace(',', '')
        # category = category.replace('-y-', '-')
        # Multiplico la cantidad de paginas por la cantidad de articulos por pagina
        total_pages = total_pages.replace('de ', '')
        total_pages = int(total_pages) * 50
        counter = 1
        # Loopeo por cada pagina, hasta llegar a la ultima
        while counter <= total_pages:
            if counter == 1:
                html = requests.get(f'https://listado.mercadolibre.com.ar/{category}/{product}_NoIndex_True').text
            else:
                html = requests.get(f'https://listado.mercadolibre.com.ar/{category}/{product}_Desde_{counter}_NoIndex_True').text    
            soup = BeautifulSoup(html, 'html.parser')
            titles = soup.find_all('h2', class_='ui-search-item__title shops__item-title')
            price = soup.find_all('span', class_='andes-money-amount__fraction')
            link = soup.find_all('a', class_='ui-search-item__group__element shops__items-group-details ui-search-link')
            for index,title in enumerate(titles):
                # print('Title:', title.text, 'Price: $', price[index].text)
                title = title.text
                title = title.replace('"', '')
                article_link = link[index].get('href')
                article_price = price[index].text
                article_price = article_price.replace('.','')
                with open(f'{product}.csv', 'a', encoding='UTF-8', newline='') as f:
                    write = writer(f)
                    write.writerow([title,article_price, article_link])
                    # write.writerow([title,f'{price[index].text}'])
            counter += 50
        filter_articles(product)    

def filter_articles(product):
    data = pd.read_csv(f'{product}.csv')
    for index,title in enumerate(data['title']):
        if product.capitalize() in title or product in title:
            continue
        else:
            # print(title, index, 'Data')
            data = data.drop(index=index)
            data.to_csv(f'{product}.csv', index=False) 

def get_min(product):
    data = pd.read_csv(f'{product}.csv')
    min_price = 0
    price_index = 0
    for index,price in enumerate(data['price']):
        if min_price == 0:
            min_price = int(price)
        elif int(price) < min_price:
            min_price = int(price)
            title = data['title'][index]
            price_index = index
    print('Price:', min_price, 'Index: ', price_index, 'Title: ',title)        

def get_max(product):
    data = pd.read_csv(f'{product}.csv')
    max_price = 0
    price_index = 0
    for index,price in enumerate(data['price']):
        if max_price == 0:
            max_price = int(price)
        elif int(price) > max_price:
            max_price = int(price)
            title = data['title'][index]
            price_index = index + 2
    print('Price:', max_price, 'Index: ', price_index, 'Title: ',title)              

def get_average(product):
    data = pd.read_csv(f'{product}.csv')
    total_price = 0
    counter_items = 0
    for price in data['price']:
        total_price += int(price)
        counter_items += 1
    average_price =  total_price / counter_items  
    print('Price:', total_price, 'Average: ', average_price, 'Total items: ',counter_items)
            
read_articles()    
# get_average('remo')    