import requests
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
TARGET_GW = 27 

def get_gw_detailed_stats(entry_id, gw_num):
    if not entry_id: 
        return {"pts": 0, "hit": 0, "chip": None, "cap": 0, "vcap": 0, "gk_pts": 0}
    try:
        url = f"{FPL_API}entry/{entry_id}/event/{gw_num}/picks/"
        res = requests.get(url, timeout=10).json()
        
        live_url = f"{FPL_API}event/{gw_num}/live/"
        live_res = requests.get(live_url, timeout=10).json()
        live_pts_map = {item['id']: item['stats']['total_points'] for item in live_res['elements']}

        picks = res['picks']
        cap_id = next(p['element'] for p in picks if p['is_captain'])
        vcap_id = next(p['element'] for p in picks if p['is_vice_captain'])
        gk_id = next(p['element'] for p in picks if p['position'] == 1)

        pts = res['entry_history']['points']
        cost = res['entry_history']['event_transfers_cost']
        chip = res.get('active_chip')
        
        valid_chips = ['3xc', 'bboost']
        chip_to_save = chip if chip in valid_chips else None
        
        return {
            "pts": pts - cost,
            "hit": cost,
            "chip": chip_to_save,
            "cap": cap_id,
            "vcap": vcap_id,
            "gk_pts": live_pts_map.get(gk_id, 0)
        }
    except Exception as e:
        return {"pts": 0, "hit": 0, "chip": None, "cap": 0, "vcap": 0, "gk_pts": 0}

def sync_playoff_points():
    print(f"🚀 GW {TARGET_GW} Playoff Updating...")
    matches = db.collection("tw_fa_playoff").stream()
    
    for doc in matches:
        m = doc.to_dict()
        doc_id = doc.id
        
        # ၁။ Status ကို ပိုမိုတိကျစွာ စစ်ဆေးခြင်း
        current_status = m.get('status', '').lower()
        if current_status == 'complete':
            print(f"⏩ Match {doc_id} is already COMPLETE. Skipping...")
            continue
        
        h_id = m.get('home_id')
        a_id = m.get('away_id')
        if not h_id or not a_id: continue

        print(f"🔄 Updating Match {doc_id}...")
        h_s = get_gw_detailed_stats(h_id, TARGET_GW)
        a_s = get_gw_detailed_stats(a_id, TARGET_GW)
        
        # ၂။ Update Logic (status: live ကို ဖြုတ်ထားပါသည်)
        # အကယ်၍ status က 'upcoming' ဖြစ်နေရင် 'live' လို့ ပြောင်းပေးမယ်
        update_data = {
            "home_pts": h_s['pts'],
            "home_hit": h_s['hit'],
            "home_chip": h_s['chip'],
            "home_cap": h_s['cap'],
            "home_vcap": h_s['vcap'],
            "home_gk_pts": h_s['gk_pts'],
            "away_pts": a_s['pts'],
            "away_hit": a_s['hit'],
            "away_chip": a_s['chip'],
            "away_cap": a_s['cap'],
            "away_vcap": a_s['vcap'],
            "away_gk_pts": a_s['gk_pts']
        }
        
        if current_status == 'upcoming':
            update_data["status"] = "live"

        db.collection("tw_fa_playoff").document(doc_id).update(update_data)
        time.sleep(0.5)

    print(f"✅ Sync Finished.")

if __name__ == "__main__":
    sync_playoff_points()
