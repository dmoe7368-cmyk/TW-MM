import firebase_admin
from firebase_admin import credentials, firestore
import os, json

def initialize_firebase():
    if not firebase_admin._apps:
        # Environment Variable စစ်မယ်၊ မရှိရင် local file သုံးမယ်
        sa_info = os.environ.get('FIREBASE_SERVICE_ACCOUNT')
        if sa_info:
            cred = credentials.Certificate(json.loads(sa_info))
        else:
            cred = credentials.Certificate('serviceAccountKey.json')
        firebase_admin.initialize_app(cred)
    return firestore.client()

db = initialize_firebase()

def setup_tw_fa_playoffs():
    print("🚀 Initializing TW FA Cup Play-off Structure (15 Matches)...")
    
    # ဆောက်ရမည့် အဆင့်များနှင့် ပွဲအရေအတွက် သတ်မှတ်ချက်
    stages = [
        {"prefix": "R16", "label": "Round of 16", "count": 8},
        {"prefix": "QF",  "label": "Quarter-Finals", "count": 4},
        {"prefix": "SF",  "label": "Semi-Finals", "count": 2},
        {"prefix": "Final", "label": "Grand Final", "count": 1}
    ]
    
    batch = db.batch()
    total_created = 0

    for stage in stages:
        prefix = stage["prefix"]
        count = stage["count"]
        
        for i in range(1, count + 1):
            # Document ID (e.g., R16_01)
            doc_id = f"{prefix}_{i:02d}"
            
            fa_ref = db.collection("tw_fa_playoff").document(doc_id)
            
            # Field အသစ်များဖြစ်သော home_id နှင့် away_id ကို ထည့်သွင်းထားသည်
            match_data = {
                "match_id": doc_id,
                "home_id": "",              # အသင်း ID ထည့်ရန် (Manual)
                "home_name": "TBD",         # အသင်းနာမည်ထည့်ရန် (Manual)
                "away_id": "",              # အသင်း ID ထည့်ရန် (Manual)
                "away_name": "TBD",         # အသင်းနာမည်ထည့်ရန် (Manual)
                "home_pts": 0,
                "away_pts": 0,
                "status": "upcoming",
                "winner": "",
                "round_label": stage["label"]
            }
            
            batch.set(fa_ref, match_data)
            total_created += 1
            print(f"📦 Prepared: {doc_id} ({stage['label']})")

    # Firebase ထဲသို့ Batch Commit လုပ်မယ်
    batch.commit()
    print(f"---")
    print(f"✅ Setup Success!")
    print(f"🏆 {total_created} Play-off fixtures created in 'tw_fa_playoff' collection.")
    print(f"💡 အခု Firebase Console မှာ home_id, away_id တို့ကိုပါ Manual ဖြည့်နိုင်ပါပြီ။")

if __name__ == "__main__":
    setup_tw_fa_playoffs()
