/**
 * Tab Navigation Logic
 * နှိပ်မရတဲ့ပြဿနာကို ဖြေရှင်းရန် window object ထဲသို့ တိုက်ရိုက်ထည့်သွင်းခြင်း
 */
window.showTab = function(tabId) {
    console.log("Switching to tab:", tabId);

    // ၁။ UI ပိုင်း ပြောင်းလဲခြင်း (Active Class)
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => item.classList.remove('active'));

    const targetItem = document.getElementById(`btn-${tabId}`);
    if (targetItem) {
        targetItem.classList.add('active');
    }

    // ၂။ Content Area ကို ရှာဖွေခြင်း
    const mainRoot = document.getElementById('main-root');
    if (!mainRoot) return;

    // ၃။ Tab တစ်ခုချင်းစီအလိုက် Function များကို ခေါ်ယူခြင်း
    switch(tabId) {
        case 'community':
            if (typeof window.renderCommunity === "function") {
                window.renderCommunity();
            } else {
                mainRoot.innerHTML = `<div class="loading">🏠 Community Loading...</div>`;
            }
            break;

        case 'leagues':
            if (typeof window.renderLeagues === "function") {
                window.renderLeagues();
            } else {
                mainRoot.innerHTML = `<div class="loading">🏆 Standings Loading...</div>`;
            }
            break;

        case 'scout':
            // scout.js ထဲက function နာမည်ကို စစ်ဆေးခေါ်ယူခြင်း
            if (typeof window.renderScoutHub === "function") {
                window.renderScoutHub();
            } else if (typeof window.renderScout === "function") {
                window.renderScout();
            } else {
                mainRoot.innerHTML = `<div class="loading">🔭 Scout Hub Loading...</div>`;
            }
            break;

        case 'live':
            if (typeof window.renderLiveHub === "function") {
                window.renderLiveHub();
            } else {
                mainRoot.innerHTML = `<div class="loading">⚡ Live Hub Loading...</div>`;
            }
            break;
    }

    // Tab ပြောင်းတိုင်း အပေါ်ဆုံးသို့ ပြန်တက်ရန်
    window.scrollTo({ top: 0, behavior: 'smooth' });
};

/**
 * App ကို စတင်ခြင်း (Auth State)
 */
firebase.auth().onAuthStateChanged((user) => {
    console.log("Auth state changed, starting app...");
    if (user) {
        window.showTab('live');
    } else {
        window.showTab('community');
    }
});

window.onload = () => {
    console.log("All scripts loaded. Application ready.");
};
