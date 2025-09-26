import json
import requests
from django.core.serializers.json import DjangoJSONEncoder
import uuid
API_URL = "http://127.0.0.1:8000/crawl/api/tasks/"

def send_shop_whatsapp_message(shop,shop_id,address,phone,owner_name):
    try:
        headers = {"Content-Type": "application/json"}
        payload = [
            {
                "uuid": str(uuid.uuid4()),
                "service": "whatsapp",
                "os": "browser",
                "data_point": "add_contact",
                "end_point": "ContactCreation",
                "input": "Lahore Restaurants",
                "targets": "restaurants",
                "condition": "",
                "profile": "",
                "device": "",
                "add_data": {
                    "shop_id":shop_id,
                    "shop_name":shop,
                    "address":address,
                    "phone":phone,
                    "owner":owner_name,
                    
                     
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
        ]

        response = requests.post(
            API_URL, 
            headers=headers, 
            data=json.dumps(payload, cls=DjangoJSONEncoder)  
        )

        if response.status_code in [200, 201]:
            print("✅ Order sent successfully:", response.json())
        else:
            print(f"⚠️ Failed! Status: {response.status_code}, Response: {response.text}")
    except Exception as e:
        print("❌ Error while sending order:", str(e))
