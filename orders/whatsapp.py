import json
import requests
API_URL = "http://192.168.2.7:81/crawl/api/tasks/"


def send_order(order):
    try:
        
      headers = {"Content-Type": "application/json"}
      payload = [
                {
                    "uuid": "123e4567-e89b-12d3-a456-426614174001",
                    "service": "whatsapp",
                    "os": "browser",
                    "data_point": "PlantsMallOrderArival",
                    "end_point": "AdminNotificationForPlantsMall",
                    "input": "Lahore Restaurants",
                    "targets": "restaurants",
                    "condition": "",
                    "profile": "",
                    "device": "",
                    "add_data": {
                        "phone": "03070033237",
                        "message": "New order received! Order #1234\nCustomer: Ali\nItem: Plant Pot\nPrice: Rs. 1200",
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
            ]

      response = requests.post(API_URL, headers=headers, data=json.dumps(payload))
                    
      if response.status_code == 200 or response.status_code == 201:
        print("✅ Order sent successfully:", response.json())
      else:
        print(f"⚠️ Failed! Status: {response.status_code}, Response: {response.text}")
    except Exception as e:
            print("❌ Error while sending order:", str(e))

                    