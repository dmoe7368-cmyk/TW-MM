import requests
import firebase_admin
from firebase_admin import credentials, firestore
import os, json, time

def initialize_firebase():
    if not firebase_admin._apps:
        # GitHub Secrets သို့မဟုတ် Local Key ဖိုင် စစ်ဆေးခြင်း
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

# 🎯 Target Week ကို ၂၅ လို့ သတ်မှတ်ပါတယ်
TARGET_GW = 25 

def get_gw_stats(entry_id, gw_num):
    """ FPL API မှ တစ်ပတ်စာ အမှတ်၊ Hit နှင့် Chip ကို ဆွဲယူခြင်း """
    try:
        url = f"{FPL_API}entry/{entry_id}/event/{gw_num}/picks/"
        res = requests.get(url, timeout=10).json()
        
        pts = res['entry_history']['points']
        cost = res['entry_history']['event_transfers_cost']
        chip = res.get('active_chip')
        
        # TC နှင့် BB ကိုသာ Marking ပြရန်
        valid_chips = ['3xc', 'bboost']
        chip_to_save = chip if chip in valid_chips else None
        
        return {
            "net_pts": pts - cost,
            "hit": cost,
            "chip": chip_to_save
        }
    except Exception as e:
        # ဒေတာမရရင် None ပြန်ပေးပြီး အဟောင်းကို မဖျက်အောင် လုပ်ပါမယ်
        return None

def sync_gw_25_only():
    print(f"🚀 Syncing GW {TARGET_GW} Data... Collection ဟောင်းကို Merge လုပ်ပါမည်။")
    
    try:
        # League Standing မှ ထိပ်ဆုံး ၄၈ ယောက်ကို ယူမည်
        league_res = requests.get(f"{FPL_API}leagues-classic/{LEAGUE_ID}/standings/").json()
        top_players = league_res['standings']['results'][:48]
    except Exception as e:
        print(f"❌ League API Error: {e}")
        return

    for i, player in enumerate(top_players):
        entry_id = str(player['entry'])
        doc_ref = db.collection("tw_mm_tournament").document(entry_id)
        
        # ၁။ လက်ရှိ Firebase ထဲမှာ ရှိပြီးသား ဒေတာကို အရင်ဖတ်မည်
        current_doc = doc_ref.get()
        existing_data = current_doc.to_dict() if current_doc.exists else {}
        
        # ၂။ API မှ GW 25 အမှတ်ကို ဆွဲယူမည်
        data = get_gw_stats(entry_id, TARGET_GW)
        
        if data:
            # ၃။ Total Net ကို ပြန်တွက်မည် (အရင် GW အဟောင်းများ + အခု GW 25)
            # အရင် GW 23, 24 အမှတ်တွေ Firebase ထဲမှာ ရှိနေရင် ယူသုံးမယ်၊ မရှိရင် 0 လို့ ယူဆမယ်
            history_total = 0
            for gw in range(23, TARGET_GW):
                history_total += existing_data.get(f"gw_{gw}_pts", 0)
            
            new_total = history_total + data['net_pts']

            # ၄။ Update လုပ်မည့် Field များ (Division နဲ့ Name တွေကို မပြောင်းလဲစေရန် Merge လုပ်မည်)
            manager_entry = {
                "entry_id": entry_id,
                "name": player['player_name'],
                "team": player['entry_name'],
                "total_net": new_total,
                f"gw_{TARGET_GW}_pts": data['net_pts'],
                f"gw_{TARGET_GW}_hit": data['hit'],
                f"gw_{TARGET_GW}_chip": data['chip']
            }

            # set(merge=True) ကြောင့် Division field နဲ့ တခြား GW အချက်အလက်တွေ မပျက်ပါဘူး
            doc_ref.set(manager_entry, merge=True)
            print(f"✅ [{i+1}/48] {player['entry_name']} - GW {TARGET_GW} Updated (Total: {new_total})")
        else:
            print(f"⚠️ [{i+1}/48] {player['entry_name']} - No API data. Skipping to protect records.")

        # Rate Limit မထိစေရန်
        time.sleep(0.3)

    print(f"---")
    print(f"✅ GW {TARGET_GW} Tournament Sync ပြီးပါပြီ။")

if __name__ == "__main__":
    sync_gw_25_only()
