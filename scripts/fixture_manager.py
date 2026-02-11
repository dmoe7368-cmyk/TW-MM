import requests
import firebase_admin
from firebase_admin import credentials, firestore
import os, json, time

def initialize_firebase():
    if not firebase_admin._apps:
        # GitHub Secrets (FIREBASE_SERVICE_ACCOUNT) သို့မဟုတ် Local File စစ်ဆေးခြင်း
        sa_info = os.environ.get('FIREBASE_SERVICE_ACCOUNT')
        if sa_info:
            cred = credentials.Certificate(json.loads(sa_info))
        else:
            cred = credentials.Certificate('serviceAccountKey.json')
        firebase_admin.initialize_app(cred)
    return firestore.client()

db = initialize_firebase()
FPL_API = "https://fantasy.premierleague.com/api/"
TARGET_GW = 26  # လက်ရှိ Update လုပ်မည့် Week ကို ဤနေရာတွင် ပြောင်းပါ

def get_gw_detailed_stats(entry_id, gw_num):
    """ Points, Hits, Chips, Captains နှင့် GK Points များ အားလုံးကို ရယူခြင်း """
    if not entry_id: 
        return {"pts": 0, "hit": 0, "chip": None, "cap": 0, "vcap": 0, "gk_pts": 0}
    
    try:
        # ၁။ User ရဲ့ Picks (Captain/GK) ကို ကြည့်ရန်
        url = f"{FPL_API}entry/{entry_id}/event/{gw_num}/picks/"
        res = requests.get(url, timeout=10).json()
        
        # ၂။ Live Points (GK အမှတ်စစ်စစ် သိရန်)
        live_url = f"{FPL_API}event/{gw_num}/live/"
        live_res = requests.get(live_url, timeout=10).json()
        # ကစားသမား ID အလိုက် အမှတ်များကို Map လုပ်ထားခြင်း
        live_pts_map = {item['id']: item['stats']['total_points'] for item in live_res['elements']}

        picks = res['picks']
        # Captain, Vice-Captain နှင့် Goalkeeper (Position 1) တို့၏ Player ID ကိုရှာခြင်း
        cap_id = next(p['element'] for p in picks if p['is_captain'])
        vcap_id = next(p['element'] for p in picks if p['is_vice_captain'])
        gk_id = next(p['element'] for p in picks if p['position'] == 1)

        pts = res['entry_history']['points']
        cost = res['entry_history']['event_transfers_cost']
        chip = res.get('active_chip')
        
        # TC နှင့် BB ကိုသာ Marking ပြရန်
        valid_chips = ['3xc', 'bboost']
        chip_to_save = chip if chip in valid_chips else None
        
        return {
            "pts": pts - cost,      # Transfer hit နှုတ်ပြီးသား အမှတ်
            "hit": cost,
            "chip": chip_to_save,
            "cap": cap_id,          # Captain Player ID
            "vcap": vcap_id,        # Vice-Captain Player ID
            "gk_pts": live_pts_map.get(gk_id, 0) # GK တစ်ယောက်တည်း၏ ရမှတ်
        }
    except Exception as e:
        print(f"Error fetching data for {entry_id}: {e}")
        return {"pts": 0, "hit": 0, "chip": None, "cap": 0, "vcap": 0, "gk_pts": 0}

def sync_playoff_points():
    print(f"🚀 GW {TARGET_GW} Playoff Scores, Chips & Captain Stats Update လုပ်နေသည်...")
    
    # tw_fa_playoff collection ထဲက Document အားလုံးကို ဖတ်မည်
    matches = db.collection("tw_fa_playoff").stream()
    
    for doc in matches:
        m = doc.to_dict()
        doc_id = doc.id
        
        # --- ပွဲပြီးမပြီး စစ်ဆေးခြင်း (Manual Edit များ မပျက်စေရန်) ---
        if m.get('status') == 'complete':
            print(f"⏩ Match {doc_id} is COMPLETE. Skipping...")
            continue
        
        h_id = m.get('home_id')
        a_id = m.get('away_id')
        
        if not h_id or not a_id:
            continue

        print(f"🔄 Syncing Match {doc_id}...")
        
        # အချက်အလက်များ API မှ ဆွဲယူခြင်း
        h_s = get_gw_detailed_stats(h_id, TARGET_GW)
        a_s = get_gw_detailed_stats(a_id, TARGET_GW)
        
        # Firebase သို့ Field အားလုံး Update လုပ်ခြင်း
        db.collection("tw_fa_playoff").document(doc_id).update({
            # Home Data
            "home_pts": h_s['pts'],
            "home_hit": h_s['hit'],
            "home_chip": h_s['chip'],
            "home_cap": h_s['cap'],
            "home_vcap": h_s['vcap'],
            "home_gk_pts": h_s['gk_pts'],
            
            # Away Data
            "away_pts": a_s['pts'],
            "away_hit": a_s['hit'],
            "away_chip": a_s['chip'],
            "away_cap": a_s['cap'],
            "away_vcap": a_s['vcap'],
            "away_gk_pts": a_s['gk_pts'],
            
            "status": "live"
        })
        
        # API Rate limit အတွက် ခေတ္တနားခြင်း
        time.sleep(0.5)

    print(f"---")
    print(f"✅ FA Cup Sync ပြီးပါပြီ။ Captain ID များနှင့် GK ရမှတ်များပါ ထည့်သွင်းပြီးပါပြီ။")

if __name__ == "__main__":
    sync_playoff_points()
