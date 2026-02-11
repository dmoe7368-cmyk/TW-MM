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
LEAGUE_ID = "400231" 
FPL_API = "https://fantasy.premierleague.com/api/"
TARGET_GW = 25 

def get_gw_stats(entry_id, gw_num):
    url = f"{FPL_API}entry/{entry_id}/event/{gw_num}/picks/"
    for attempt in range(3):
        try:
            res = requests.get(url, timeout=15)
            if res.status_code == 200:
                d = res.json()
                pts = d['entry_history']['points']
                cost = d['entry_history']['event_transfers_cost']
                chip = d.get('active_chip')
                
                # ✅ Triple Captain နှင့် Bench Boost Marking Logic
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

def sync_tournament_full():
    print(f"🚀 GW {TARGET_GW} Sync စတင်ပါပြီ (Chips & Batches အကုန်ပါဝင်သည်)...")
    
    try:
        league_res = requests.get(f"{FPL_API}leagues-classic/{LEAGUE_ID}/standings/").json()
        top_players = league_res['standings']['results'][:48]
    except Exception as e:
        print(f"❌ Error: {e}"); return

    for i, player in enumerate(top_players):
        entry_id = str(player['entry'])
        doc_ref = db.collection("tw_mm_tournament").document(entry_id)
        
        # ရှိပြီးသား Data ဖတ်ခြင်း (Division Protect လုပ်ရန်)
        current_doc = doc_ref.get()
        existing_data = current_doc.to_dict() if current_doc.exists else {}
        division = existing_data.get("division", "Division A")

        data = get_gw_stats(entry_id, TARGET_GW)
        
        if data:
            # Total Net ပြန်ပေါင်းခြင်း
            history_total = 0
            for gw in range(23, TARGET_GW):
                history_total += existing_data.get(f"gw_{gw}_pts", 0)
            
            new_total = history_total + data['net_pts']

            # Firebase Update Payload
            manager_entry = {
                "entry_id": entry_id,
                "name": player['player_name'],
                "team": player['entry_name'],
                "total_net": new_total,
                "division": division,
                f"gw_{TARGET_GW}_pts": data['net_pts'],
                f"gw_{TARGET_GW}_hit": data['hit'],
                f"gw_{TARGET_GW}_chip": data['chip'] # ✅ Chip marking သိမ်းဆည်းခြင်း
            }
            
            doc_ref.set(manager_entry, merge=True)
            print(f"✅ [{i+1}/48] {player['entry_name']} - Chip: {data['chip']}")
        else:
            print(f"⚠️ [{i+1}/48] {player['entry_name']} - No Data.")

        # --- 🎯 Batch Control (၁၀ သင်းလျှင် ၅ စက္ကန့်နား) ---
        if (i + 1) % 10 == 0:
            print(f"⏳ ၁၀ သင်းပြည့်၍ ၅ စက္ကန့် ခေတ္တနားနေပါသည်။...")
            time.sleep(5)
        else:
            time.sleep(0.6)

    print(f"✅ GW {TARGET_GW} Sync ပြီးပါပြီ။")

if __name__ == "__main__":
    sync_tournament_full()
