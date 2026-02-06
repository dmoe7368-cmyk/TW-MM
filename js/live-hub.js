/**
 * ၁။ Playoff အမှတ်နှင့် Marking ပြပေးမည့် Function
 */
function renderPlayoffScore(pts, hit, chip) {
    let tags = '';
    
    // Transfer Hit ပြရန် (Python က အမှတ်ထဲက နှုတ်ပေးထားပြီးဖြစ်သော်လည်း Marking အဖြစ်ပြခြင်း)
    if (hit > 0) {
        tags += `<span style="color: #ff4d4d; font-size: 0.55rem; font-weight: bold; margin-left: 4px;">(-${hit})</span>`;
    }
    
    // Chip Marking ပြရန် (TC သို့မဟုတ် BB)
    let chipTag = '';
    if (chip === '3xc') {
        chipTag = `<div style="background: #e1ff00; color: #000; font-size: 0.45rem; padding: 1px 4px; border-radius: 3px; font-weight: 900; margin-top: 2px; display: inline-block;">TC</div>`;
    } else if (chip === 'bboost') {
        chipTag = `<div style="background: #00ffcc; color: #000; font-size: 0.45rem; padding: 1px 4px; border-radius: 3px; font-weight: 900; margin-top: 2px; display: inline-block;">BB</div>`;
    }

    return `
        <div style="display: flex; flex-direction: column; align-items: flex-end;">
            <div style="display: flex; align-items: center;">
                <span style="font-weight: 900; color: #00ff88; font-family: 'Courier New', monospace; font-size: 1.1rem;">
                    ${pts ?? '-'}
                </span>
                ${tags}
            </div>
            ${chipTag}
        </div>
    `;
}

/**
 * ၂။ Live Hub (FA Cup Bracket) Render လုပ်ခြင်း
 */
window.renderLiveHub = function() {
    const mainRoot = document.getElementById('main-root');
    if (!mainRoot) return;

    mainRoot.innerHTML = `
        <div style="padding: 15px; max-width: 600px; margin: 0 auto; font-family: 'Inter', sans-serif; background: #000; min-height: 100vh; color: white;">
            
            <div style="text-align: center; margin-bottom: 30px; padding: 20px 0; border-bottom: 1px solid #222;">
                <h2 style="color: #D4AF37; text-transform: uppercase; font-size: 1.5rem; margin: 0; font-weight: 900; letter-spacing: 3px;">🏟️ TW FA CUP</h2>
                <div style="font-size: 0.6rem; color: #555; margin-top: 5px; letter-spacing: 2px;">KNOCKOUT STAGE BRACKET</div>
            </div>

            <div id="playoff-bracket-container" style="display: flex; flex-direction: column; gap: 40px;">
            </div>

            <div style="text-align: center; padding: 40px 0; color: #222; font-size: 0.5rem;">
                POWERED BY TW MM TOURNAMENT
            </div>
        </div>
    `;

    loadFACupBracket();
};

/**
 * ၃။ Firebase မှ Playoff ဒေတာများ ဆွဲတင်ခြင်း
 */
function loadFACupBracket() {
    const container = document.getElementById('playoff-bracket-container');
    if (!container) return;

    db.collection("tw_fa_playoff").onSnapshot((snapshot) => {
        let matches = [];
        snapshot.forEach(doc => matches.push(doc.data()));

        const stages = [
            { key: "R16", label: "ROUND OF 16", count: 8, color: "#888" },
            { key: "QF", label: "QUARTER-FINALS", count: 4, color: "#C0C0C0" },
            { key: "SF", label: "SEMI-FINALS", count: 2, color: "#D4AF37" },
            { key: "Final", label: "GRAND FINAL 🏆", count: 1, color: "#00ff88" }
        ];

        let html = '';

        stages.forEach(stage => {
            const stageMatches = matches.filter(m => m.match_id && m.match_id.includes(stage.key));

            html += `
                <div style="display: flex; flex-direction: column; gap: 15px;">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <div style="height: 2px; flex: 1; background: linear-gradient(to right, transparent, #222);"></div>
                        <span style="color: ${stage.color}; font-size: 0.75rem; font-weight: 900; letter-spacing: 1.5px;">${stage.label}</span>
                        <div style="height: 2px; flex: 1; background: linear-gradient(to left, transparent, #222);"></div>
                    </div>

                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 12px;">
            `;

            for (let i = 1; i <= stage.count; i++) {
                const currentMatchId = `${stage.key}_${i.toString().padStart(2, '0')}`;
                const m = stageMatches.find(match => match.match_id === currentMatchId) || {};
                const isLive = m.status === 'live';

                html += `
                    <div style="background: #0a0a0a; border: 1px solid ${isLive ? '#D4AF37' : '#1a1a1a'}; border-radius: 12px; padding: 14px; position: relative;">
                        ${isLive ? '<div style="position: absolute; top: -8px; left: 15px; background: #ff4d4d; color: white; font-size: 0.5rem; padding: 2px 8px; font-weight: 900; border-radius: 4px; z-index: 1;">LIVE</div>' : ''}
                        
                        <div style="display: flex; flex-direction: column; gap: 8px;">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <span style="font-size: 0.85rem; font-weight: 700; color: ${m.winner === m.home_name && m.home_name ? '#00ff88' : '#fff'};">
                                    ${m.home_name || 'TBD'}
                                </span>
                                ${renderPlayoffScore(m.home_pts, m.home_hit, m.home_chip)}
                            </div>

                            <div style="height: 1px; background: #151515; margin: 2px 0;"></div>

                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <span style="font-size: 0.85rem; font-weight: 700; color: ${m.winner === m.away_name && m.away_name ? '#00ff88' : '#fff'};">
                                    ${m.away_name || 'TBD'}
                                </span>
                                ${renderPlayoffScore(m.away_pts, m.away_hit, m.away_chip)}
                            </div>
                        </div>
                    </div>
                `;
            }
            html += `</div></div>`;
        });

        container.innerHTML 
            = html;
    });
}
