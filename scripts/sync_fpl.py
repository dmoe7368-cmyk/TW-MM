import requests
import firebase_admin
from firebase_admin import credentials, firestore
import os, json, time

def initialize_firebase():
    if not firebase_admin._apps:
        sa_info = os.environ.get('FIREBASE_SERVICE_ACCOUNT')
        if sa_info:
            cred = credentials.Certificate(json.loads(sa_info))
        else:
            cred = credentials.Certificate('serviceAccountKey.json')
        firebase_admin.initialize_app(cred)
    return firestore.client()

db = initialize_firebase()
FPL_API = "https://fantasy.premierleague.com/api/"

# 🎯 တစ်ပတ်ချင်းစီ ဖြည့်ဖို့အတွက် ဒီနေရာမှာပဲ ပြောင်းပေးပါ
TARGET_GW = 26 

def get_gw_detailed_stats(entry_id, gw_num):
    url = f"{FPL_API}entry/{entry_id}/event/{gw_num}/picks/"
    for attempt in range(3):
        try:
            res = requests.get(url, timeout=15)
            if res.status_code == 200:
                d = res.json()
                pts = d['entry_history']['points']
                cost = d['entry_history']['event_transfers_cost']
                chip = d.get('active_chip')
                
                # TC သို့မဟုတ် BB သုံးထားမှ သိမ်းမည်
                valid_chips = ['3xc', 'bboost']
                chip_to_save = chip if chip in valid_chips else None
                
                return {
                    "net_pts": pts - cost,
                    "hit": cost,
                    "chip": chip_to_save
                }
            elif res.status_code == 429:
                time.sleep(10)
        except:
            time.sleep(2)
    return None

def sync_fpl_scores():
    print(f"⚽ GW {TARGET_GW} Update စတင်နေပါပြီ...")
    
    managers = db.collection("tw_mm_tournament").stream()
    manager_list = list(managers)

    for i, doc in enumerate(manager_list):
        entry_id = doc.id
        existing_data = doc.to_dict()
        
        data = get_gw_detailed_stats(entry_id, TARGET_GW)
        
        if data:
            # ✅ ယခုအပတ်အမှတ်ကို Firebase မှာ အရင် Update လုပ်မယ်
            update_payload = {
                f"gw_{TARGET_GW}_pts": data['net_pts'],
                f"gw_{TARGET_GW}_hit": data['hit'],
                f"gw_{TARGET_GW}_chip": data['chip']
            }
            
            # ✅ Total Net ကို ပြန်ပေါင်းမယ် (၂၃ ကနေ လက်ရှိ TARGET_GW အထိ)
            # ဒီနေရာမှာ အမှတ်အသစ်ကိုပါ ထည့်ပေါင်းရမှာမို့ target_gw + 1 လို့ သုံးထားပါတယ်
            new_total_net = 0
            temp_data = existing_data.copy()
            temp_data.update(update_payload) # လက်ရှိဆွဲထားတဲ့အမှတ်ကိုပါ ထည့်ပေါင်းရန်
            
            for gw in range(23, 30): # ၂၃ မှ ၂၉ အထိ ရှိသမျှအမှတ်ကုန်ပေါင်းမယ်
                new_total_net += temp_data.get(f"gw_{gw}_pts", 0)

            update_payload["total_net"] = new_total_net
            
            db.collection("tw_mm_tournament").document(entry_id).update(update_payload)
            print(f"✅ [{i+1}] {existing_data.get('name')} -> {data['net_pts']} pts (Total: {new_total_net})")
        
        if (i + 1) % 10 == 0:
            time.sleep(5)
        else:
            time.sleep(0.7)

if __name__ == "__main__":
    sync_fpl_scores()
