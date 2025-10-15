import requests
import json
import re
from tqdm import tqdm

GROUP_NAME = 'PD-136'  

def sanitize_filename(filename):
    return re.sub(r'[<>:"/\\|?*]', '_', filename)

def get_cat_image(text):
    url = f'https://cataas.com/cat/says/{text}?json=true'
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    img_url = 'https://cataas.com' + data['url']
    img_response = requests.get(img_url)
    img_response.raise_for_status()
    return img_response.content

def create_folder_on_yandex(token, folder_name):
    url = 'https://cloud-api.yandex.net/v1/disk/resources'
    headers = {'Authorization': f'OAuth {token}'}
    params = {'path': folder_name}
    response = requests.put(url, headers=headers, params=params)
    if response.status_code == 201:
        print(f'Папка "{folder_name}" успешно создана.')
    elif response.status_code == 409:
        print(f'Папка "{folder_name}" уже существует.')
    else:
        response.raise_for_status()

def upload_file_to_yandex(token, folder_name, file_name, file_data):
    headers = {'Authorization': f'OAuth {token}'}
    upload_url = 'https://cloud-api.yandex.net/v1/disk/resources/upload'
    params = {'path': f'{folder_name}/{file_name}', 'overwrite': 'true'}

  
    response = requests.get(upload_url, headers=headers, params=params)
    response.raise_for_status()
    upload_link = response.json()['href']

    
    total_size = len(file_data)

    
    with tqdm(total=total_size, unit='B', unit_scale=True, desc='Загрузка') as pbar:
        def progress_callback(monitor):
            pbar.update(monitor.bytes_read - pbar.n)

        
        put_response = requests.put(
            upload_link,
            data=file_data,
            headers={'Content-Type': 'application/octet-stream'}
        )
        
        pbar.update(total_size - pbar.n)
        put_response.raise_for_status()

   
    info_url = 'https://cloud-api.yandex.net/v1/disk/resources'
    info_params = {'path': f'{folder_name}/{file_name}'}
    info_response = requests.get(info_url, headers=headers, params=info_params)
    info_response.raise_for_status()
    file_info = info_response.json()

    return file_info['size']

def main():
    text = input("Введите текст для картинки кота: ").strip()
    token = input("Введите OAuth-токен Яндекс.Диска (не публикуйте в открытых местах!): ").strip()

    create_folder_on_yandex(token, GROUP_NAME)

    try:
        print("Получаем картинку…")
        cat_image = get_cat_image(text)
    except requests.RequestException as e:
        print(f"Ошибка при загрузке картинки: {e}")
        return

    
    sanitized_text = sanitize_filename(text)
    file_name = f'{sanitized_text}.jpg'

    try:
        print("Загружаем картинку на Яндекс.Диск…")
        size_bytes = upload_file_to_yandex(token, GROUP_NAME, file_name, cat_image)
    except requests.RequestException as e:
        print(f"Ошибка при загрузке на Яндекс.Диск: {e}")
        return

    
    info = [{
        "filename": file_name,
        "size_bytes": size_bytes
    }]

    with open('files_info.json', 'w', encoding='utf-8') as f:
        json.dump(info, f, ensure_ascii=False, indent=4)

    print(f'Картинка "{file_name}" успешно загружена в папку "{GROUP_NAME}" на Яндекс.Диске.')
    print('Информация о файле сохранена в "files_info.json".')

if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()
