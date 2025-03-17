import requests
import json
import uuid
from flask import Flask, request

# Настройки API Bitrix24
BITRIX_URL = "https://inwork.bitrix24.ru/rest/8/fjtuc0gmxac1ife0"
BITRIX_TEMPLATE_FOLDER_ID = "1702"  # ID папки с шаблонами
BITRIX_TEMPLATE_FILE_ID = "1704"  # ID файла-шаблона
BITRIX_REPORT_FOLDER_ID = "666"  # ID папки "Отчеты"
BITRIX_SMART_PROCESS_ID = 1042  # ID смарт-процесса
BITRIX_ITEM_UPDATE_URL = f"{BITRIX_URL}/crm.item.update"
BITRIX_DISK_COPY_URL = f"{BITRIX_URL}/disk.file.copy"
BITRIX_FILE_FIELD = "ufCrm8_1741619470239"  # Поле для ссылки на файл

app = Flask(__name__)

def copy_template_and_upload(item_id):
    """ Копирует файл-шаблон в папку 'Отчеты' и обновляет сделку ссылкой """
    unique_id = uuid.uuid4().hex[:8]  # Генерация уникального ID
    new_file_name = f"Сценарий продаж_{unique_id}.xlsx"

    # Копируем файл в новую папку
    copy_response = requests.post(BITRIX_DISK_COPY_URL, json={
        "id": BITRIX_TEMPLATE_FILE_ID,
        "targetFolderId": BITRIX_REPORT_FOLDER_ID,
        "newName": new_file_name
    })
    
    copy_data = copy_response.json()
    if "result" not in copy_data or not copy_data["result"].get("ID"):
        print(f"❌ Ошибка копирования шаблона: {copy_data}")
        return
    
    new_file_id = copy_data["result"]["ID"]
    new_file_url = copy_data["result"].get("DETAIL_URL", "")

    print(f"✅ Файл {new_file_name} скопирован, ID: {new_file_id}, URL: {new_file_url}")

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
    copy_template_and_upload(item_id)
    
    return f"✅ Шаблон скопирован и добавлен в сделку {item_id}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
