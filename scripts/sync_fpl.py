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

# 🎯 Target Week ကို ဤနေရာတွင် အပတ်စဉ် ပြောင်းပေးပါ
TARGET_GW = 23 

def get_gw_detailed_stats(entry_id, gw_num):
    """ API မှ ရမှတ်၊ Hit နှင့် Chip Marking များကို တိကျစွာ ဆွဲယူခြင်း """
    url = f"{FPL_API}entry/{entry_id}/event/{gw_num}/picks/"
    for attempt in range(3):
        try:
            res = requests.get(url, timeout=15)
            if res.status_code == 200:
                d = res.json()
                # Points နှင့် Transfer Hits (Cost) ယူခြင်း
                pts = d['entry_history']['points']
                cost = d['entry_history']['event_transfers_cost']
                chip = d.get('active_chip')
                
                # Triple Captain နှင့် Bench Boost Marking သီးသန့်စစ်ထုတ်ခြင်း
                valid_chips = ['3xc', 'bboost']
                chip_to_save = chip if chip in valid_chips else None
                
                return {
                    "net_pts": pts - cost, # Transfer Hit နှုတ်ပြီးသား Net Point
                    "hit": cost,
                    "chip": chip_to_save
                }
            elif res.status_code == 429:
                print("⏳ API Busy... Waiting 10s")
                time.sleep(10)
        except:
            time.sleep(2)
    return None

def sync_fpl_scores():
    print(f"⚽ sync_fpl.py: GW {TARGET_GW} ရမှတ်များကို စတင် Update လုပ်နေပါသည်...")
    
    # Firebase မှ လက်ရှိ Master Data (အသင်း ၄၀) ကို ဆွဲထုတ်မည်
    managers = db.collection("tw_mm_tournament").stream()
    manager_list = list(managers)
    total_managers = len(manager_list)

    if total_managers == 0:
        print("⚠️ Firebase မှာ Manager စာရင်းမတွေ့ပါ။ sync_master.py ကို အရင် Run ပေးပါ။")
        return

    for i, doc in enumerate(manager_list):
        entry_id = doc.id
        existing_data = doc.to_dict()
        
        # API မှ အချက်အလက်ယူခြင်း
        data = get_gw_detailed_stats(entry_id, TARGET_GW)
        
        if data:
            # ၁။ Total Net ပြန်ပေါင်းရန် (GW 23 မှ လက်ရှိအပတ်အထိ)
            history_total = 0
            for gw in range(23, TARGET_GW):
                history_total += existing_data.get(f"gw_{gw}_pts", 0)
            
            new_total = history_total + data['net_pts']

            # ၂။ Firebase Update (update function သုံး၍ Master Info ကို Protect လုပ်မည်)
            update_payload = {
                f"gw_{TARGET_GW}_pts": data['net_pts'],
                f"gw_{TARGET_GW}_hit": data['hit'],
                f"gw_{TARGET_GW}_chip": data['chip'],
                "total_net": new_total
            }
            
            db.collection("tw_mm_tournament").document(entry_id).update(update_payload)
            print(f"✅ [{i+1}/{total_managers}] {existing_data.get('name')} -> {data['net_pts']} pts (Chip: {data['chip']})")
        else:
            print(f"⚠️ [{i+1}/{total_managers}] {existing_data.get('name')} -> API Error (Skipped)")

        # --- 🎯 ၁၀ သင်းလျှင် ၅ စက္ကန့်နားမည့် Batch System ---
        if (i + 1) % 10 == 0:
            print(f"⏳ API Block မဖြစ်စေရန် ၅ စက္ကန့် ခေတ္တနားနေပါသည်။...")
            time.sleep(5)
        else:
            time.sleep(0.7)

    print(f"---")
    print(f"✅ sync_fpl.py: GW {TARGET_GW} Sync လုပ်ငန်းစဉ် အောင်မြင်စွာ ပြီးဆုံးပါပြီ။")

if __name__ == "__main__":
    sync_fpl_scores()
