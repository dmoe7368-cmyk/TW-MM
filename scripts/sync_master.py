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
GW_RANGE = range(23, 30) # ၂၃ မှ ၂၉ ထိ

def sync_master_divisions():
    print(f"🚀 Master Setup (sync_master.py) စတင်ပါပြီ...")
    
    try:
        # ၁။ ထိပ်ဆုံး ၄၀ ကိုယူသည်
        league_res = requests.get(f"{FPL_API}leagues-classic/{LEAGUE_ID}/standings/").json()
        top_40_players = league_res['standings']['results'][:40]
    except Exception as e:
        print(f"❌ Error: {e}"); return

    for i, player in enumerate(top_40_players):
        entry_id = str(player['entry'])
        doc_ref = db.collection("tw_mm_tournament").document(entry_id)
        
        # ၂။ Division ခွဲဝေခြင်း (၁-၂၀: A, ၂၁-၄၀: B)
        division = "Division A" if i < 20 else "Division B"

        # ၃။ GW 23 မှ ၂၉ အထိ Field များ ကြိုတင်နေရာချခြင်း
        weekly_data = {}
        for gw in GW_RANGE:
            weekly_data[f"gw_{gw}_pts"] = 0
            weekly_data[f"gw_{gw}_hit"] = 0
            weekly_data[f"gw_{gw}_chip"] = None

        master_data = {
            "entry_id": entry_id,
            "name": player['player_name'],
            "team": player['entry_name'],
            "division": division,
            "total_net": 0,
            **weekly_data
        }

        # Firebase မှာ existing record ရှိရင် Division နဲ့ Info ကို update လုပ်ပြီး field တွေကို နေရာချမယ်
        doc_ref.set(master_data, merge=True)
        print(f"✅ [{i+1}/40] {player['entry_name']} -> {division}")
        time.sleep(0.1)

    print(f"---")
    print(f"⭐ Robot A: Master Setup ပြီးပါပြီ။")

if __name__ == "__main__":
    sync_master_divisions()
