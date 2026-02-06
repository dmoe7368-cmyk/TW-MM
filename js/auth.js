/**
 * ၁။ Initialization & Toast Function
 */
const provider = new firebase.auth.GoogleAuthProvider();
const authRoot = document.getElementById('auth-root');

// App နဲ့ လိုက်ဖက်မည့် Custom Toast Alert
window.showToast = (message, type = "info") => {
    const container = document.getElementById('toast-container');
    if (!container) return; // container မရှိရင် ဘာမှမလုပ်ဘူး

    const toast = document.createElement('div');
    toast.className = `toast-alert ${type}`;
    
    let icon = "🔔";
    if(type === "success") icon = "✅";
    if(type === "error") icon = "❌";

    toast.innerHTML = `
        <div style="display:flex; align-items:center; gap:10px;">
            <span>${icon}</span>
            <span style="font-size: 0.9rem; font-weight: 600;">${message}</span>
        </div>
    `;

    container.appendChild(toast);

    // ၃ စက္ကန့်ကြာရင် ပြန်ဖျက်မယ်
    setTimeout(() => {
        toast.style.animation = "fadeOut 0.4s ease forwards";
        setTimeout(() => toast.remove(), 400);
    }, 3000);
};

/**
 * ၂။ Auth State Observer
 */
firebase.auth().onAuthStateChanged(async (user) => {
    if (user) {
        try {
            const userDoc = await db.collection("users").doc(user.uid).get();
            let managerName = user.displayName ? user.displayName.split(' ')[0] : "Manager";
            
            if (userDoc.exists) {
                const userData = userDoc.data();
                managerName = userData.manager_name;
                updateProfileModal(userData);
            }

            authRoot.innerHTML = `
                <div onclick="window.openProfile()" style="display: flex; align-items: center; gap: 8px; cursor: pointer; background: #1a1a1a; padding: 5px 12px; border-radius: 20px; border: 1px solid #333;">
                    <div style="font-size: 1rem;">⚽</div>
                    <span style="color: #D4AF37; font-size: 0.85rem; font-weight: 800;">${managerName}</span>
                </div>
            `;
        } catch (error) {
            console.error("Profile load error:", error);
        }
    } else {
        authRoot.innerHTML = `
            <button onclick="window.renderAuthUI()" 
                style="background: transparent; border: 1px solid #D4AF37; color: #D4AF37; padding: 6px 15px; border-radius: 20px; font-weight: 800; font-size: 0.75rem; cursor: pointer;">
                LOGIN
            </button>
        `;
    }
    // Community Tab ကို Refresh လုပ်ပေးရန်
    if (window.currentTab === 'community' && typeof renderCommunity === 'function') renderCommunity();
});

/**
 * ၃။ UI Rendering Functions
 */
window.renderAuthUI = function() {
    const mainRoot = document.getElementById('main-root');
    mainRoot.innerHTML = `
        <div class="auth-form-container" style="max-width: 400px; margin: 40px auto; padding: 20px; animation: fadeIn 0.3s ease;">
            <div style="display: flex; background: #111; padding: 5px; border-radius: 50px; margin-bottom: 25px; border: 1px solid #222;">
                <button id="tab-login" onclick="window.toggleAuthTab('login')" style="flex: 1; padding: 10px; border-radius: 40px; border: none; background: #D4AF37; color: #000; font-weight: 800; cursor: pointer;">LOGIN</button>
                <button id="tab-signup" onclick="window.toggleAuthTab('signup')" style="flex: 1; padding: 10px; border-radius: 40px; border: none; background: transparent; color: #666; font-weight: 800; cursor: pointer;">SIGN UP</button>
            </div>

            <div id="form-login">
                <input type="email" id="email" class="auth-input" placeholder="Gmail Address">
                <input type="password" id="pass" class="auth-input" placeholder="Password">
                <button onclick="window.handleLogin()" class="primary-btn" style="background: #00ff88; margin-top: 10px;">LOG IN</button>
                <div style="margin: 20px 0; color: #444; font-size: 0.8rem; text-align: center;">OR</div>
                <button onclick="window.loginWithGoogle()" class="primary-btn" style="background: #fff; color: #000; display: flex; align-items: center; justify-content: center; gap: 10px;">
                    GOOGLE LOGIN
                </button>
            </div>

            <div id="form-signup" style="display: none;">
                <input type="text" id="reg-manager" class="auth-input" placeholder="Manager Name">
                <input type="text" id="reg-team" class="auth-input" placeholder="FPL Team Name">
                <input type="text" id="reg-fb" class="auth-input" placeholder="Facebook Link">
                <input type="email" id="reg-email" class="auth-input" placeholder="Email Address">
                <input type="password" id="reg-pass" class="auth-input" placeholder="Password (Min 6 chars)">
                <button onclick="window.handleSignUp()" class="primary-btn" style="margin-top: 10px;">CREATE ACCOUNT</button>
            </div>
        </div>
    `;
};

window.toggleAuthTab = (type) => {
    const isLogin = type === 'login';
    const formLogin = document.getElementById('form-login');
    const formSignup = document.getElementById('form-signup');
    const tabLogin = document.getElementById('tab-login');
    const tabSignup = document.getElementById('tab-signup');

    formLogin.style.display = isLogin ? 'block' : 'none';
    formSignup.style.display = isLogin ? 'none' : 'block';
    
    tabLogin.style.background = isLogin ? '#D4AF37' : 'transparent';
    tabLogin.style.color = isLogin ? '#000' : '#666';
    tabSignup.style.background = isLogin ? 'transparent' : '#D4AF37';
    tabSignup.style.color = isLogin ? '#666' : '#000';
};

/**
 * ၄။ Logic Functions (Sign Up / Login / Logout)
 */
window.handleSignUp = async () => {
    const manager = document.getElementById('reg-manager').value;
    const team = document.getElementById('reg-team').value;
    const fb = document.getElementById('reg-fb').value;
    const email = document.getElementById('reg-email').value;
    const pass = document.getElementById('reg-pass').value;

    if (!manager || !email || pass.length < 6) {
        return window.showToast("အချက်အလက်များ ပြည့်စုံအောင် ဖြည့်ပါ", "error");
    }

    try {
        const res = await firebase.auth().createUserWithEmailAndPassword(email, pass);
        await db.collection("users").doc(res.user.uid).set({
            uid: res.user.uid,
            manager_name: manager,
            team_name: team,
            facebook_name: fb,
            email: email,
            role: 'member',
            joined_at: firebase.firestore.FieldValue.serverTimestamp()
        });
        window.showToast("Account Created! 😍", "success");
        setTimeout(() => location.reload(), 1500); 
    } catch (e) { window.showToast(e.message, "error"); }
};

window.handleLogin = () => {
    const email = document.getElementById('email').value;
    const pass = document.getElementById('pass').value;
    if(!email || !pass) return window.showToast("အီးမေးလ်နှင့် Password ရိုက်ပါ", "error");

    firebase.auth().signInWithEmailAndPassword(email, pass)
        .then(() => { 
            window.showToast("Welcome Back! ⚽", "success");
            setTimeout(() => location.reload(), 1000); 
        })
        .catch(e => window.showToast("Email သို့မဟုတ် Password မှားနေသည်", "error"));
};

window.loginWithGoogle = () => {
    firebase.auth().signInWithPopup(provider)
        .then(() => {
            window.showToast("Google Login Success!", "success");
            setTimeout(() => location.reload(), 1000);
        })
        .catch(e => console.error(e));
};

window.handleLogout = () => {
    if(confirm("Logout ထွက်မှာ သေချာပါသလား?")) {
        firebase.auth().signOut().then(() => {
            window.closeProfile();
            location.reload();
        });
    }
};

/**
 * ၅။ Modal & Profile Management
 */
function updateProfileModal(data) {
    if(document.getElementById('prof-manager')) document.getElementById('prof-manager').innerText = data.manager_name;
    if(document.getElementById('prof-team')) document.getElementById('prof-team').innerText = data.team_name;
    if(document.getElementById('prof-fb')) document.getElementById('prof-fb').innerText = data.facebook_name || "-";
    const logoutBtn = document.getElementById('logout-section');
    if(logoutBtn) logoutBtn.style.display = 'block';
}

window.openProfile = () => {
    const modal = document.getElementById('profile-modal');
    if(modal) modal.style.display = 'flex';
};

window.closeProfile = () => {
    const modal = document.getElementById('profile-modal');
    if(modal) modal.style.display = 'none';
};
