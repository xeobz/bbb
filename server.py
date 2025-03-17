import requests
import json
import uuid
import base64
from flask import Flask, request

# Настройки API Bitrix24
BITRIX_URL = "https://inwork.bitrix24.ru/rest/8/fjtuc0gmxac1ife0"
BITRIX_TEMPLATE_FILE_ID = "1704"  # ID файла-шаблона в Bitrix24
BITRIX_REPORT_FOLDER_ID = "666"  # ID папки "Отчеты"
BITRIX_SMART_PROCESS_ID = 1042  # ID смарт-процесса
BITRIX_ITEM_UPDATE_URL = f"{BITRIX_URL}/crm.item.update"
BITRIX_DISK_DOWNLOAD_URL = f"{BITRIX_URL}/disk.file.get"
BITRIX_DISK_UPLOAD_URL = f"{BITRIX_URL}/disk.folder.uploadfile"
BITRIX_FILE_FIELD = "ufCrm8_1741619470239"  # Поле для ссылки на файл

app = Flask(__name__)

def download_template():
    """ Скачивает шаблон из Bitrix24 """
    download_response = requests.post(BITRIX_DISK_DOWNLOAD_URL, json={"id": BITRIX_TEMPLATE_FILE_ID})
    download_data = download_response.json()
    if "result" not in download_data or "DOWNLOAD_URL" not in download_data["result"]:
        print(f"❌ Ошибка загрузки шаблона: {download_data}")
        return None
    
    file_url = download_data["result"]["DOWNLOAD_URL"]
    file_response = requests.get(file_url)
    if file_response.status_code == 200:
        return file_response.content
    else:
        print(f"❌ Ошибка скачивания файла: {file_response.status_code}")
        return None

import io

def upload_template_and_update(item_id):
    """ Загружает файл-шаблон в папку 'Отчеты' и обновляет сделку ссылкой """
    file_content = download_template()
    if not file_content:
        return
    
    unique_id = uuid.uuid4().hex[:8]  # Генерация уникального ID
    new_file_name = f"Сценарий продаж_{unique_id}.xlsx"

    # 1. Запрашиваем URL для загрузки файла
    upload_url_response = requests.post(BITRIX_DISK_UPLOAD_URL, json={"id": BITRIX_REPORT_FOLDER_ID})
    upload_url_data = upload_url_response.json()

    if "result" not in upload_url_data or "uploadUrl" not in upload_url_data["result"]:
        print(f"❌ Ошибка получения uploadUrl: {upload_url_data}")
        return

    upload_url = upload_url_data["result"]["uploadUrl"]

    # 2. Загружаем файл через полученный uploadUrl
    files = {"file": (new_file_name, io.BytesIO(file_content))}
    upload_file_response = requests.post(upload_url, files=files)
    upload_file_data = upload_file_response.json()

    if "result" not in upload_file_data or not upload_file_data["result"].get("ID"):
        print(f"❌ Ошибка загрузки файла: {upload_file_data}")
        return

    new_file_id = upload_file_data["result"]["ID"]
    new_file_url = upload_file_data["result"].get("DETAIL_URL", "")
    print(f"✅ Файл {new_file_name} загружен, ID: {new_file_id}, URL: {new_file_url}")

    # Обновляем сделку ссылкой на файл
    update_response = requests.post(BITRIX_ITEM_UPDATE_URL, json={
        "entityTypeId": BITRIX_SMART_PROCESS_ID,
        "id": item_id,
        "fields": {BITRIX_FILE_FIELD: new_file_url}
    })
    
    if update_response.json().get("result"):
        print(f"✅ Сделка {item_id} обновлена ссылкой на файл.")
    else:
        print(f"❌ Ошибка обновления сделки {item_id}: {update_response.json()}")

@app.route("/", methods=["GET", "POST"])
def handle_request():
    item_id = request.args.get("item_id") or (request.get_json() or {}).get("item_id")
    if not item_id:
        return "❌ Ошибка: не передан item_id", 400
    
    print(f"🔄 Запрос на обработку сделки {item_id}")
    upload_template_and_update(item_id)
    
    return f"✅ Шаблон загружен и добавлен в сделку {item_id}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
