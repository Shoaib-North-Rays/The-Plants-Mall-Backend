import json
import requests
from django.core.serializers.json import DjangoJSONEncoder
import uuid

API_URL = "http://127.0.0.1:8000/crawl/api/tasks/"

def send_order(order, is_whatsapp, phone):
    try:
        headers = {"Content-Type": "application/json"}
        base_payload = {
            "uuid": "",  
            "service": "whatsapp",
            "os": "browser",
            "data_point": "PlantsMallOrderArival",
            "end_point": "AdminNotificationForPlantsMall",   
            "input": "Lahore Restaurants",
            "targets": "",   
            "condition": "",
            "profile": "",
            "device": "",
            "is_order": "true",
            "add_data": {
                "phone": "",
                "order_detail": order,
                "wait_time": 9
            },
            "repeat": False,
            "repeat_duration": "1m",
            "status": "pending",
            "report": True,
            "retries_count": 0,
            "paused": False,
            "ref_id": "ref_001",
            "alloted_bots": "bot_1"
        }

   
        phone_list = [phone]   
        if is_whatsapp:
            phone_list.append(order.get("owner_phone_numbe", ""))  

   
        for p in phone_list:
            payload = base_payload.copy()
            payload["uuid"] = str(uuid.uuid4())
            payload["targets"] = "user"   
            payload["add_data"]["phone"] = p

            response = requests.post(
                API_URL,
                headers=headers,
                data=json.dumps([payload], cls=DjangoJSONEncoder)
            )

            if response.status_code in [200, 201]:
                print(f"✅ Notification sent to {p} successfully:", response.json())
            else:
                print(f"⚠️ Notification to {p} failed! Status: {response.status_code}, Response: {response.text}")

    except Exception as e:
        print("❌ Error while sending order:", str(e))
