import asyncio
import websockets
import json
from datetime import datetime, timezone

SPT_ISSUER = "rswD8h8uzKPEUh26QKeWnxP2dR2HLkhCPm"
SPT_CURRENCY = "SPT"

def drops_to_xrp(drops):
    return int(drops) / 1_000_000

async def listen_spt_trades():
    url = "wss://xrplcluster.com"

    async with websockets.connect(url) as ws:
        await ws.send(json.dumps({
            "id": 1,
            "command": "subscribe",
            "streams": ["transactions"]
        }))

        print("🔍 Слушаю XRPL для SPT-транзакций...\n")

        while True:
            response = await ws.recv()
            data = json.loads(response)

            tx = data.get("transaction")
            meta = data.get("meta")

            if not tx or not meta or meta.get("TransactionResult") != "tesSUCCESS":
                continue

            delivered = meta.get("delivered_amount")
            if not isinstance(delivered, dict):
                continue

            if delivered.get("currency") == SPT_CURRENCY and delivered.get("issuer") == SPT_ISSUER:
                spt_amount = float(delivered.get("value"))
                sender = tx.get("Account")
                tx_hash = tx.get("hash")
                timestamp = tx.get("date")

                # ✅ Правильный способ получения времени
                tx_time = datetime.fromtimestamp(timestamp + 946684800, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')

                xrp_spent = None
                if isinstance(tx.get("Amount"), str):
                    xrp_spent = drops_to_xrp(tx.get("Amount"))

                if not xrp_spent:
                    affected_nodes = meta.get("AffectedNodes", [])
                    for node in affected_nodes:
                        if "ModifiedNode" in node:
                            mod = node["ModifiedNode"]
                            if mod.get("LedgerEntryType") == "AccountRoot":
                                prev = mod.get("PreviousFields", {}).get("Balance")
                                final = mod.get("FinalFields", {}).get("Balance")
                                if prev and final:
                                    spent = int(prev) - int(final)
                                    if spent > 0:
                                        xrp_spent = drops_to_xrp(spent)
                                        break

                price = xrp_spent / spt_amount if xrp_spent else None

                print("✅ Обнаружена покупка SPT:")
                print(f"• Время: {tx_time}")
                print(f"• Отправитель: {sender}")
                print(f"• Кол-во получено: {spt_amount} SPT")
                print(f"• Потрачено: {xrp_spent:.6f} XRP" if xrp_spent else "• XRP не определено")
                print(f"• Цена за SPT: {price:.8f} XRP" if price else "• Цена не определена")
                print(f"• TxHash: {tx_hash}\n")

            await asyncio.sleep(0.05)

if __name__ == "__main__":
    asyncio.run(listen_spt_trades())
