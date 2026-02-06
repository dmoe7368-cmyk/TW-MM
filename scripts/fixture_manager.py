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
TARGET_GW = 25  # လက်ရှိ Update လုပ်မည့် Week ကို ဤနေရာတွင် ပြောင်းပါ

def get_gw_detailed_stats(entry_id, gw_num):
    """ FPL API မှ Points, Hits နှင့် Chips ဒေတာများကို ရယူခြင်း """
    if not entry_id: return {"pts": 0, "hit": 0, "chip": None}
    try:
        url = f"{FPL_API}entry/{entry_id}/event/{gw_num}/picks/"
        res = requests.get(url, timeout=10).json()
        
        pts = res['entry_history']['points']
        cost = res['entry_history']['event_transfers_cost']
        chip = res.get('active_chip')
        
        # TC နှင့် BB ကိုသာ Marking ပြရန် (အမှတ်နှုတ်ရန် ဆရာ့အတွက် မှတ်သားပေးခြင်း)
        valid_chips = ['3xc', 'bboost']
        chip_to_save = chip if chip in valid_chips else None
        
        return {
            "pts": pts - cost, # Net point (-4 နှုတ်ပြီးသား)
            "hit": cost,
            "chip": chip_to_save
        }
    except:
        return {"pts": 0, "hit": 0, "chip": None}

def sync_playoff_points():
    print(f"🚀 GW {TARGET_GW} Playoff Scores & Markings ကို Update လုပ်နေသည်...")
    
    # tw_fa_playoff collection ထဲက Document အားလုံးကို ယူမည်
    matches = db.collection("tw_fa_playoff").stream()
    
    for doc in matches:
        m = doc.to_dict()
        doc_id = doc.id
        
        # --- အရေးကြီးသောအပိုင်း: ပွဲပြီးမပြီး စစ်ဆေးခြင်း ---
        # status က 'complete' ဖြစ်နေရင် ဆရာ Manual ပြင်ထားတဲ့ အမှတ်တွေ မပျက်စေရန် ကျော်သွားပါမယ်
        if m.get('status') == 'complete':
            print(f"⏩ Match {doc_id} is COMPLETE. Skipping to protect manual edits.")
            continue
        
        h_id = m.get('home_id')
        a_id = m.get('away_id')
        
        # ID မရှိလျှင် ကျော်သွားမည်
        if not h_id or not a_id:
            continue

        print(f"🔄 Updating Match {doc_id}...")
        
        # ရမှတ်များကို API မှ ရယူခြင်း
        h_stats = get_gw_detailed_stats(h_id, TARGET_GW)
        a_stats = get_gw_detailed_stats(a_id, TARGET_GW)
        
        # Firebase သို့ Update လုပ်ခြင်း
        # မှတ်ချက် - status ကို live လို့ ပေးထားပါမယ်။ ဆရာက Manual ပြင်ပြီးမှ Firebase ထဲမှာ 'complete' လို့ ပြောင်းပေးရပါမယ်။
        db.collection("tw_fa_playoff").document(doc_id).update({
            "home_pts": h_stats['pts'],
            "home_hit": h_stats['hit'],
            "home_chip": h_stats['chip'],
            "away_pts": a_stats['pts'],
            "away_hit": a_stats['hit'],
            "away_chip": a_stats['chip'],
            "status": "live"
        })
        
        # API Rate limit မထိအောင် ခဏနားခြင်း
        time.sleep(0.3)

    print(f"---")
    print(f"✅ FA Cup Sync ပြီးပါပြီ။ 'complete' ပွဲများမှလွဲ၍ ကျန်ပွဲများ Update ဖြစ်သွားပါပြီ။")

if __name__ == "__main__":
    sync_playoff_points()
