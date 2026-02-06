// --- 🛠️ Inject Professional Styles ---
const style = document.createElement('style');
style.innerHTML = `
    .comm-wrapper { max-width: 600px; margin: auto; padding: 20px; color: white; padding-bottom: 100px; }
    .post-card { background: #1a1a1a; border: 1px solid #333; padding: 15px; margin-bottom: 15px; border-radius: 12px; border-left: 4px solid #D4AF37; }
    .initial-box { 
        width: 40px; height: 40px; background: linear-gradient(45deg, #D4AF37, #aa8c2c); 
        color: black; border-radius: 50%; display: flex; align-items: center; 
        justify-content: center; font-weight: bold; cursor: pointer; font-size: 18px;
        text-transform: uppercase;
    }
    .post-btn { 
        background: #D4AF37; color: black; font-weight: bold; border: none; 
        padding: 12px; border-radius: 8px; cursor: pointer; width: 100%; margin-top: 10px;
    }
    .chat-modal {
        position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%);
        background: #111; border: 1px solid #D4AF37; padding: 20px; border-radius: 15px;
        z-index: 3000; width: 85%; max-width: 350px; box-shadow: 0 0 30px rgba(0,0,0,1);
    }
    .overlay { position: fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.8); z-index:2999; }
    
    .bottom-nav, footer, #bottom-menu { z-index: 5000 !important; }
`;
document.head.appendChild(style);

// --- 🛠️ Global Variable for Manager Name ---
let currentManagerName = "User";

// --- 🛠️ Core Functions ---

async function renderCommunity() {
    const main = document.getElementById('main-root');
    const user = auth.currentUser;

    // Firestore ထဲက manager_name ကို အရင်ရှာမယ်
    if (user) {
        try {
            const userDoc = await db.collection("users").doc(user.uid).get();
            if (userDoc.exists) {
                currentManagerName = userDoc.data().manager_name || userDoc.data().facebook_name || "User";
            }
        } catch (e) {
            console.error("Error fetching user name:", e);
        }
    }

    const initial = currentManagerName.charAt(0);

    main.innerHTML = `
        <div class="comm-wrapper">
            <h2 style="color: #D4AF37; text-align: center; margin-bottom: 20px;">🤝 Community Hub ✨</h2>
            ${user ? `
                <div style="background: #1a1a1a; padding: 15px; border-radius: 15px; border: 1px solid #333; margin-bottom: 25px;">
                    <div style="display: flex; gap: 10px; align-items: center; margin-bottom: 10px;">
                        <div class="initial-box">${initial}</div>
                        <strong>${currentManagerName} <br><small style="color:#4caf50; font-size:10px;">● Online</small></strong>
                    </div>
                    <textarea id="postInput" style="width:100%; background:#000; color:white; border:1px solid #444; padding:10px; border-radius:8px; height:80px; resize:none; box-sizing:border-box;" placeholder="ဘာပြောချင်လဲဗျာ..."></textarea>
                    <button onclick="savePost()" class="post-btn">🚀 POST တင်မယ်</button>
                </div>
            ` : `<div style="text-align:center; padding:20px; color:#888;">စာရေးဖို့ Login အရင်ဝင်ပေးပါဗျ။</div>`}
            
            <div id="posts-list"></div>
        </div>
        <div id="modal-holder"></div>
    `;
    loadPosts();
}

function savePost() {
    const text = document.getElementById('postInput').value;
    const user = auth.currentUser;
    if (!text.trim()) return alert("စာအရင်ရေးပါဦး!");

    // Firestore ကနေ ရထားတဲ့ currentManagerName ကိုပဲ သုံးမယ်
    db.collection("tw_posts").add({
        name: currentManagerName, 
        uid: user.uid, 
        message: text,
        timestamp: firebase.firestore.FieldValue.serverTimestamp()
    }).then(() => { 
        document.getElementById('postInput').value = ""; 
    });
}

function loadPosts() {
    db.collection("tw_posts").orderBy("timestamp", "desc").onSnapshot(snapshot => {
        const list = document.getElementById('posts-list');
        if (!list) return;

        list.innerHTML = snapshot.docs.map(doc => {
            const p = doc.data();
            const time = p.timestamp ? new Date(p.timestamp.seconds * 1000).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) : 'Just now';
            
            const displayName = p.name || "User";
            const initial = displayName.charAt(0);
            const targetId = p.uid || "no-id";

            return `
                <div class="post-card">
                    <div style="display:flex; align-items:center; gap:10px; margin-bottom:10px;">
                        <div class="initial-box" onclick="openChat('${targetId}', '${displayName}')">${initial}</div>
                        <div>
                            <strong style="color:#D4AF37; cursor:pointer;" onclick="openChat('${targetId}', '${displayName}')">${displayName}</strong>
                            <div style="color:#666; font-size:10px;">${time}</div>
                        </div>
                    </div>
                    <div style="font-size:15px; line-height:1.5; color:#eee; white-space: pre-wrap;">${p.message}</div>
                    <div style="margin-top:12px; display:flex; gap:20px; color:#666; font-size:13px; border-top:1px solid #222; padding-top:10px;">
                        <span style="cursor:pointer;" onclick="alert('Liked!')">❤️ Like</span>
                        <span style="cursor:pointer;" onclick="openChat('${targetId}', '${displayName}')">💬 Message Send</span>
                    </div>
                </div>
            `;
        }).join('');
    });
}

// --- 💬 Message System ---

function openChat(targetUid, targetName) {
    const user = auth.currentUser;
    if (!user) return alert("Login အရင်ဝင်ပါ!");
    if (targetUid === "no-id") return alert("User ID မရှိသေးလို့ စာပို့မရပါဘူး။");
    if (user.uid === targetUid) return alert("ဒါက သင့် Profile ပါ!");

    const finalTargetName = targetName || "User";

    const holder = document.getElementById('modal-holder');
    holder.innerHTML = `
        <div class="overlay" onclick="closeChat()"></div>
        <div class="chat-modal">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px;">
                <strong style="color:#D4AF37; font-size:18px;">${finalTargetName}</strong>
                <span onclick="closeChat()" style="cursor:pointer; color:#888; font-size:24px;">&times;</span>
            </div>
            <div id="chat-box" style="height:200px; overflow-y:auto; background:#000; padding:10px; border-radius:8px; display:flex; flex-direction:column; gap:8px;">
                <p style="color:#444; text-align:center; font-size:12px;">စာတိုလေး ပို့လိုက်ပါ... 💌</p>
            </div>
            <div style="display:flex; gap:5px; margin-top:10px;">
                <input type="text" id="mInput" style="flex:1; background:#222; color:white; border:1px solid #444; padding:10px; border-radius:5px; outline:none;" placeholder="စာရေးရန်...">
                <button onclick="sendMsg('${targetUid}')" style="background:#D4AF37; border:none; padding:0 15px; border-radius:5px; font-weight:bold; cursor:pointer;">ပို့</button>
            </div>
        </div>
    `;
    listenMsgs(targetUid);
}

function sendMsg(targetUid) {
    const input = document.getElementById('mInput');
    const text = input.value.trim();
    if (!text) return;

    db.collection("tw_messages").add({
        sender: auth.currentUser.uid,
        receiver: targetUid,
        text: text,
        timestamp: firebase.firestore.FieldValue.serverTimestamp()
    }).then(() => { input.value = ""; });
}

function listenMsgs(targetUid) {
    const myUid = auth.currentUser.uid;
    db.collection("tw_messages")
        .orderBy("timestamp", "asc")
        .onSnapshot(snap => {
            const chatBox = document.getElementById('chat-box');
            if (!chatBox) return;

            const html = snap.docs.filter(doc => {
                const d = doc.data();
                return (d.sender === myUid && d.receiver === targetUid) || 
                       (d.sender === targetUid && d.receiver === myUid);
            }).map(doc => {
                const m = doc.data();
                const isMe = m.sender === myUid;
                return `
                    <div style="align-self: ${isMe ? 'flex-end' : 'flex-start'}; background: ${isMe ? '#D4AF37' : '#333'}; color: ${isMe ? 'black' : 'white'}; padding: 6px 12px; border-radius: 12px; max-width: 80%; font-size: 14px;">
                        ${m.text}
                    </div>
                `;
            }).join('');
            chatBox.innerHTML = html || chatBox.innerHTML;
            chatBox.scrollTop = chatBox.scrollHeight;
        });
}

function closeChat() {
    document.getElementById('modal-holder').innerHTML = "";
}
