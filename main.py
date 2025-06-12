import asyncio
import json
from datetime import datetime, timezone
from websockets import connect
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Данные токена
SPT_ISSUER = "rswD8h8uzKPEUh26QKeWnxP2dR2HLkhCPm"
SPT_CURRENCY = "SPT"

# Google Sheets
CREDENTIALS_FILE = "credentials.json"
SPREADSHEET_NAME = "SPT Transactions"

# Настройка доступа к таблице
def setup_google_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
    client = gspread.authorize(creds)
    sheet = client.open(SPREADSHEET_NAME).sheet1
    return sheet

# Конвертация drops в XRP
def drops_to_xrp(drops):
    return int(drops) / 1_000_000

# Основная логика
async def listen_transactions():
    uri = "wss://s1.ripple.com/"
    sheet = setup_google_sheet()

    print("🔍 Слушаю XRPL для всех успешных транзакций...\n")
    async with connect(uri) as websocket:
        # Подписка на все транзакции
        subscribe_msg = {
            "id": 1,
            "command": "subscribe",
            "streams": ["transactions"]
        }
        await websocket.send(json.dumps(subscribe_msg))

        while True:
            try:
                response = await websocket.recv()
                data = json.loads(response)

                tx = data.get("transaction")
                meta = data.get("meta")
                if not tx or not meta:
                    continue

                if tx.get("TransactionResult", "") != "tesSUCCESS" and meta.get("TransactionResult", "") != "tesSUCCESS":
                    continue

                # Проверка наличия delivered_amount
                delivered = meta.get("delivered_amount")
                if isinstance(delivered, dict) and delivered.get("currency") == SPT_CURRENCY and delivered.get("issuer") == SPT_ISSUER:
                    spt_amount = float(delivered["value"])

                    # Определим хеш и отправителя
                    tx_hash = tx.get("hash", "N/A")
                    sender = tx.get("Account", "N/A")

                    # Время транзакции
                    timestamp = tx.get("date")
                    tx_time = datetime.fromtimestamp(timestamp + 946684800, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')

                    # Получение суммы в XRP из SendMax
                    sendmax = tx.get("SendMax")
                    if isinstance(sendmax, str):
                        xrp_spent = drops_to_xrp(sendmax)
                    else:
                        xrp_spent = 0

                    price_per_token = xrp_spent / spt_amount if spt_amount else 0

                    row = [tx_time, sender, spt_amount, round(xrp_spent, 6), round(price_per_token, 6), tx_hash]
                    sheet.append_row(row)

                    print(f"✅ Сделка записана: {row}")

            except Exception as e:
                print(f"❌ Ошибка: {e}")

# Запуск
if __name__ == "__main__":
    asyncio.run(listen_transactions())
