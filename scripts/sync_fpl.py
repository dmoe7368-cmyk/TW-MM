import requests
import firebase_admin
from firebase_admin import credentials, firestore
import os, json, time

def initialize_firebase():
    if not firebase_admin._apps:
        sa_info = os.environ.get('FIREBASE_SERVICE_ACCOUNT')
        cred = credentials.Certificate(json.loads(sa_info)) if sa_info else credentials.Certificate('serviceAccountKey.json')
        firebase_admin.initialize_app(cred)
    return firestore.client()

db = initialize_firebase()
LEAGUE_ID = "400231" 
FPL_API = "https://fantasy.premierleague.com/api/"
GW_RANGE = range(23, 30)

def get_gw_stats(entry_id, gw_num):
    try:
        url = f"{FPL_API}entry/{entry_id}/event/{gw_num}/picks/"
        res = requests.get(url, timeout=10).json()
        
        pts = res['entry_history']['points']
        cost = res['entry_history']['event_transfers_cost']
        chip = res.get('active_chip')
        
        # Free Hit ကို မယူဘဲ TC နဲ့ BB ကိုပဲ စစ်ထုတ်မည်
        valid_chips = ['3xc', 'bboost']
        chip_to_save = chip if chip in valid_chips else None
        
        return {
            "net_pts": pts - cost,
            "hit": cost,
            "chip": chip_to_save
        }
    except:
        return {"net_pts": 0, "hit": 0, "chip": None}

def sync_top_48_managers():
    print(f"🚀 Syncing GW 23-29 Data (Chips & Hits included)...")
    try:
        league_res = requests.get(f"{FPL_API}leagues-classic/{LEAGUE_ID}/standings/").json()
        top_players = league_res['standings']['results'][:48]
    except Exception as e:
        print(f"❌ Error: {e}"); return

    for i, player in enumerate(top_players):
        entry_id = str(player['entry'])
        doc_ref = db.collection("tw_mm_tournament").document(entry_id)
        
        # Division ရှိပြီးသားဆိုရင် Protect လုပ်မယ်
        current_doc = doc_ref.get()
        existing_division = current_doc.to_dict().get("division", "Division A") if current_doc.exists else "Division A"

        weekly_data = {}
        total_sum = 0
        
        for gw in GW_RANGE:
            data = get_gw_stats(entry_id, gw)
            weekly_data[f"gw_{gw}_pts"] = data['net_pts']
            weekly_data[f"gw_{gw}_hit"] = data['hit']
            weekly_data[f"gw_{gw}_chip"] = data['chip']
            total_sum += data['net_pts']
            time.sleep(0.05)

        manager_entry = {
            "entry_id": entry_id,
            "name": player['player_name'],
            "team": player['entry_name'],
            "total_net": total_sum,
            "division": existing_division,
            **weekly_data
        }
        doc_ref.set(manager_entry, merge=True)
        print(f"✅ Updated {player['entry_name']} - {existing_division}")

if __name__ == "__main__":
    sync_top_48_managers()
