/**
 * ၁။ Chip နှင့် Transfer Hit များကို Marking ပြပေးမည့် Function
 */
function renderPointCell(pts, hit, chip) {
    let extraTags = '';
    
    // Transfer Hit ရှိလျှင် (ဥပမာ -4)
    if (hit && hit > 0) {
        extraTags += `<div style="color: #ff4d4d; font-size: 0.6rem; font-weight: 700; margin-top: 2px;">-${hit}</div>`;
    }
    
    // Chip အသုံးပြုထားလျှင် (TC သို့မဟုတ် BB)
    if (chip === '3xc') {
        extraTags += `<div style="background: #e1ff00; color: #000; font-size: 0.5rem; padding: 1px 4px; border-radius: 3px; font-weight: 900; margin-top: 3px; display: inline-block;">TC</div>`;
    } else if (chip === 'bboost') {
        extraTags += `<div style="background: #00ffcc; color: #000; font-size: 0.5rem; padding: 1px 4px; border-radius: 3px; font-weight: 900; margin-top: 3px; display: inline-block;">BB</div>`;
    }

    return `
        <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 40px;">
            <span style="color: #E0E0E0; font-weight: 600; font-size: 0.85rem;">${pts || 0}</span>
            ${extraTags}
        </div>
    `;
}

/**
 * ၂။ Tournament Standings Render လုပ်ခြင်း
 */
window.renderLeagues = function() {
    const mainRoot = document.getElementById('main-root');
    if (!mainRoot) return;

    mainRoot.innerHTML = `
        <div style="padding: 12px; max-width: 600px; margin: 0 auto; font-family: 'Inter', sans-serif; background: #000; min-height: 100vh; color: white;">
            <div style="text-align: center; margin-bottom: 20px;">
                <h2 style="color: #D4AF37; font-size: 1.2rem; letter-spacing: 2px; text-transform: uppercase; font-weight: 900;">League Standings</h2>
            </div>

            <div style="display: flex; background: #111; padding: 4px; border-radius: 50px; margin-bottom: 20px; border: 1px solid #222;">
                <button id="btn-divA" onclick="window.filterDivision('Division A')" 
                    style="flex: 1; padding: 12px; border: none; border-radius: 40px; font-weight: 800; cursor: pointer; transition: 0.3s; background: #D4AF37; color: #000; font-size: 0.7rem;">
                    DIVISION A (Gold)
                </button>
                <button id="btn-divB" onclick="window.filterDivision('Division B')" 
                    style="flex: 1; padding: 12px; border: none; border-radius: 40px; font-weight: 800; cursor: pointer; transition: 0.3s; background: transparent; color: #666; font-size: 0.7rem;">
                    DIVISION B (Silver)
                </button>
            </div>
            
            <div id="league-content" style="overflow-x: auto; background: #0a0a0a; border-radius: 12px; border: 1px solid #1a1a1a;">
                <div style="text-align:center; color:#555; padding:50px;">🎮 Loading Standings...</div>
            </div>
        </div>
    `;
    setTimeout(() => { window.filterDivision('Division A'); }, 100);
};

/**
 * ၃။ Division အလိုက် ဒေတာဆွဲထုတ်ခြင်း
 */
window.filterDivision = function(divName) {
    const content = document.getElementById('league-content');
    const btnA = document.getElementById('btn-divA');
    const btnB = document.getElementById('btn-divB');
    if (!content) return;

    const isDivA = divName === 'Division A';
    const themeColor = isDivA ? '#D4AF37' : '#C0C0C0';

    btnA.style.background = isDivA ? '#D4AF37' : 'transparent';
    btnA.style.color = isDivA ? '#000' : '#666';
    btnB.style.background = !isDivA ? '#C0C0C0' : 'transparent';
    btnB.style.color = !isDivA ? '#000' : '#666';

    db.collection("tw_mm_tournament")
      .where("division", "==", divName)
      .onSnapshot((snapshot) => {
        if (!snapshot || snapshot.empty) {
            content.innerHTML = `<div style="text-align:center; padding:50px; color:#444;">NO DATA FOUND</div>`;
            return;
        }

        let players = [];
        snapshot.forEach(doc => players.push(doc.data()));
        players.sort((a, b) => (b.total_net || 0) - (a.total_net || 0));

        let html = `
            <table style="width: 100%; border-collapse: collapse; font-size: 0.75rem; min-width: 700px;">
                <thead>
                    <tr style="background: #111; color: ${themeColor}; border-bottom: 2px solid #222;">
                        <th style="padding: 15px 10px; text-align: left; position: sticky; left: 0; background: #111; z-index: 3; border-right: 1px solid #222;">TEAM / MANAGER</th>
                        <th style="padding: 10px; text-align: center;">W23</th>
                        <th style="padding: 10px; text-align: center;">W24</th>
                        <th style="padding: 10px; text-align: center;">W25</th>
                        <th style="padding: 10px; text-align: center;">W26</th>
                        <th style="padding: 10px; text-align: center;">W27</th>
                        <th style="padding: 10px; text-align: center;">W28</th>
                        <th style="padding: 10px; text-align: center;">W29</th>
                        <th style="padding: 10px; text-align: center; background: ${themeColor}; color: #000; font-weight: 900;">TOTAL</th>
                    </tr>
                </thead>
                <tbody>
        `;

        players.forEach((p, index) => {
            const pos = index + 1;
            const isTop3 = pos <= 3;
            const nameColor = isTop3 ? themeColor : '#fff';
            const managerSubColor = isTop3 ? 'rgba(255,255,255,0.7)' : '#666';

            html += `
                <tr style="border-bottom: 1px solid #111;">
                    <td style="padding: 12px 10px; text-align: left; position: sticky; left: 0; background: #0a0a0a; z-index: 2; border-right: 1px solid #1a1a1a; min-width: 135px;">
                        <div style="font-weight: 800; color: ${nameColor};">${pos}. ${p.team || 'Unknown'}</div>
                        <div style="font-size: 0.65rem; color: ${managerSubColor}; text-transform: uppercase; margin-top: 4px; display: block;">
                            ${p.name || 'Manager'}
                        </div>
                    </td>
                    
                    <td style="padding: 8px;">${renderPointCell(p.gw_23_pts, p.gw_23_hit, p.gw_23_chip)}</td>
                    <td style="padding: 8px;">${renderPointCell(p.gw_24_pts, p.gw_24_hit, p.gw_24_chip)}</td>
                    <td style="padding: 8px;">${renderPointCell(p.gw_25_pts, p.gw_25_hit, p.gw_25_chip)}</td>
                    <td style="padding: 8px;">${renderPointCell(p.gw_26_pts, p.gw_26_hit, p.gw_26_chip)}</td>
                    <td style="padding: 8px;">${renderPointCell(p.gw_27_pts, p.gw_27_hit, p.gw_27_chip)}</td>
                    <td style="padding: 8px;">${renderPointCell(p.gw_28_pts, p.gw_28_hit, p.gw_28_chip)}</td>
                    <td style="padding: 8px;">${renderPointCell(p.gw_29_pts, p.gw_29_hit, p.gw_29_chip)}</td>

                    <td style="padding: 10px; text-align: center; font-weight: 900; color: #00ff88; background: rgba(0, 255, 136, 0.05); font-size: 0.9rem; border-left: 1px solid #1a1a1a;">
                        ${p.total_net || 0}
                    </td>
                </tr>
            `;
        });

        html += `</tbody></table>`;
        content.innerHTML = html;
          
      });
};
