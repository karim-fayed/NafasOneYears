"""
Final fix: Replace the broken Firebase+GitHub system with a clean GitHub API solution.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('index.html', 'r', encoding='utf-8') as f:
    content = f.read()

print(f"Original: {len(content)} chars")

# Find the exact start and end using \n (not \r\n)
START_MARKER = "        /* =========================================================\n           PLAYLIST ENGINE v3.0"
END_MARKER = "            return '';\n        }\n\n        /* Local File Picker"

si = content.find(START_MARKER)
ei = content.find(END_MARKER)
print(f"Start at: {si}, End at: {ei}")

if si < 0 or ei < 0:
    print("FATAL: Markers not found")
    sys.exit(1)

# The replacement ends BEFORE "/* Local File Picker" - keep that
end_of_replaced = ei + len(END_MARKER) - len("        /* Local File Picker")

NEW_ENGINE = '''        /* =========================================================
           NAFAS DATA ENGINE v4.0 — GitHub Repo as Cloud Database
           READ: public GitHub raw URL (no auth, works for everyone)
           WRITE: GitHub Contents API with Token (admin saves data)
           ========================================================= */
        const REPO_OWNER        = 'karim-fayed';
        const REPO_NAME         = 'NafasOneYears';
        const REPO_BRANCH       = 'main';
        const PLAYLIST_PATH     = 'playlist.json';
        const WISHES_PATH       = 'wishes.json';

        // GitHub token stored locally (never sent to 3rd parties)
        let _ghToken = '';
        try { _ghToken = localStorage.getItem('nafas_gh_token') || ''; } catch(e) {}

        function _storeToken(t) {
            _ghToken = t.trim();
            try { if (_ghToken) localStorage.setItem('nafas_gh_token', _ghToken); } catch(e) {}
        }

        // ---- READ file from GitHub repo (public, no auth) ----
        async function _readRepoFile(path) {
            const url = `https://raw.githubusercontent.com/${REPO_OWNER}/${REPO_NAME}/${REPO_BRANCH}/${path}?t=${Date.now()}`;
            const res = await fetch(url);
            if (!res.ok) throw new Error('HTTP ' + res.status);
            return await res.json();
        }

        // ---- WRITE file to GitHub repo via Contents API ----
        async function _writeRepoFile(path, data, commitMsg, token) {
            const json = JSON.stringify(data, null, 2);
            const encoded = btoa(unescape(encodeURIComponent(json)));
            let sha = '';
            try {
                const r = await fetch(`https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/contents/${path}`, {
                    headers: { 'Authorization': `Bearer ${token}`, 'Accept': 'application/vnd.github+json' }
                });
                if (r.ok) { const d = await r.json(); sha = d.sha || ''; }
            } catch(e) {}
            const body = { message: commitMsg, content: encoded, branch: REPO_BRANCH };
            if (sha) body.sha = sha;
            const res = await fetch(`https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/contents/${path}`, {
                method: 'PUT',
                headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json', 'Accept': 'application/vnd.github+json' },
                body: JSON.stringify(body)
            });
            if (!res.ok) {
                const errText = await res.text();
                throw new Error(`GitHub API: ${res.status} - ${errText}`);
            }
            return true;
        }

        // ======== PLAYLIST ========
        // Load instantly from localStorage
        try {
            const cached = localStorage.getItem('nafas_playlist_v4');
            if (cached) { playlistQueue = JSON.parse(cached); }
        } catch(e) {}

        // Then fetch fresh from GitHub Pages
        async function fetchPlaylistJson() {
            try {
                const data = await _readRepoFile(PLAYLIST_PATH);
                if (data && Array.isArray(data.tracks)) {
                    playlistQueue = data.tracks;
                    localStorage.setItem('nafas_playlist_v4', JSON.stringify(playlistQueue));
                    updatePlaylistUI();
                }
            } catch(e) {
                console.log('Playlist: using local cache');
            }
        }
        fetchPlaylistJson();

        function saveLocalPlaylist() {
            try { localStorage.setItem('nafas_playlist_v4', JSON.stringify(playlistQueue)); } catch(e) {}
        }

        // ======== WISHES ========
        async function fetchWishesFromRepo() {
            try {
                const data = await _readRepoFile(WISHES_PATH);
                if (!data || !Array.isArray(data.wishes)) return;
                const grid = document.getElementById('wishesGrid');
                if (!grid) return;
                grid.innerHTML = '';
                data.wishes.forEach(w => renderWishCard(w.author, w.text, w.rel || 'تهنئة عائلية', w.timestamp, false));
            } catch(e) { /* keep sample cards */ }
        }

        // Save a new wish to GitHub repo (called from saveWish)
        async function appendWishToRepo(wishData) {
            // Works with OR without token:
            // If admin token available: save to repo (permanent for all)
            // If no token: save to localStorage only
            const t = _ghToken;
            if (!t) {
                // Save locally only
                let localWishes = [];
                try { localWishes = JSON.parse(localStorage.getItem('nafas_local_wishes') || '[]'); } catch(e) {}
                localWishes.unshift(wishData);
                localStorage.setItem('nafas_local_wishes', JSON.stringify(localWishes));
                return 'local';
            }
            // Read current wishes
            let wishes = [];
            try {
                const data = await _readRepoFile(WISHES_PATH);
                if (data && Array.isArray(data.wishes)) wishes = data.wishes;
            } catch(e) {}
            wishes.unshift(wishData);
            await _writeRepoFile(WISHES_PATH, { wishes }, 'إضافة تهنئة جديدة 💌', t);
            return 'cloud';
        }

        // ======== GITHUB TOKEN MODAL ========
        function showGitHubTokenModal(purpose, onConfirm) {
            const existing = document.getElementById('ghTokenModal');
            if (existing) existing.remove();
            const modal = document.createElement('div');
            modal.id = 'ghTokenModal';
            modal.style.cssText = 'position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.92);z-index:99999;display:flex;align-items:center;justify-content:center;padding:16px;';
            modal.innerHTML = `
                <div style="background:linear-gradient(135deg,#1a0a2e,#2d1b4e);border:1px solid #D4AF37;border-radius:20px;padding:26px;max-width:500px;width:100%;text-align:center;font-family:Cairo,sans-serif;">
                    <div style="font-size:1.6rem;margin-bottom:10px;">🔐 ${purpose}</div>
                    <p style="color:rgba(255,255,255,0.8);font-size:0.83rem;margin-bottom:14px;">أدخل <strong style="color:#FFD700;">GitHub Token</strong> وسيُحفظ تلقائياً على جهازك.</p>
                    <div style="background:rgba(0,0,0,0.4);border-radius:12px;padding:12px;margin-bottom:14px;text-align:right;">
                        <p style="color:#D4AF37;font-size:0.8rem;margin-bottom:7px;">📋 كيفية الحصول على Token:</p>
                        <ol style="color:rgba(255,255,255,0.75);font-size:0.76rem;padding-right:18px;line-height:1.9;margin:0;">
                            <li>افتح: <a href="https://github.com/settings/tokens/new?scopes=public_repo&description=NafasApp" target="_blank" style="color:#FFD700;">github.com/settings/tokens/new</a></li>
                            <li>في <b>Note</b>: اكتب "NafasApp"، اختر <b>public_repo</b> ثم <b>Generate Token</b></li>
                            <li>انسخ الـ Token والصقه هنا ↓</li>
                        </ol>
                    </div>
                    <input id="ghTokenFieldInput" type="text" placeholder="ghp_xxxxxxxxxxxxxxxxxxxx" style="width:100%;padding:11px 14px;border-radius:30px;border:1.5px solid #D4AF37;background:rgba(0,0,0,0.5);color:#FFF;font-size:0.85rem;margin-bottom:12px;box-sizing:border-box;direction:ltr;letter-spacing:1px;">
                    <div style="display:flex;gap:8px;justify-content:center;flex-wrap:wrap;margin-bottom:10px;">
                        <button id="ghConfirmBtn" style="background:linear-gradient(135deg,#D4AF37,#996515);color:#000;font-weight:700;padding:10px 22px;border-radius:30px;border:none;cursor:pointer;font-size:0.9rem;">✅ تأكيد</button>
                        <button onclick="document.getElementById('ghTokenModal').remove()" style="background:rgba(255,255,255,0.07);color:#FFF;padding:10px 18px;border-radius:30px;border:1px solid rgba(255,255,255,0.2);cursor:pointer;">إلغاء</button>
                    </div>
                    <div id="ghTokenStatus" style="font-size:0.8rem;min-height:18px;"></div>
                </div>
            `;
            document.body.appendChild(modal);
            if (_ghToken) document.getElementById('ghTokenFieldInput').value = _ghToken;

            document.getElementById('ghConfirmBtn').onclick = async function() {
                const t = document.getElementById('ghTokenFieldInput').value.trim();
                if (!t) { document.getElementById('ghTokenStatus').innerHTML = '<span style="color:#FF5555;">⚠️ الرجاء إدخال الـ Token</span>'; return; }
                _storeToken(t);
                document.getElementById('ghTokenStatus').innerHTML = '<span style="color:#FFD700;">⏳ جاري الحفظ...</span>';
                try {
                    await onConfirm(t);
                    document.getElementById('ghTokenStatus').innerHTML = '<span style="color:#55FF88;">✅ تم بنجاح! سيظهر للجميع خلال دقيقة.</span>';
                    setTimeout(() => { const m = document.getElementById('ghTokenModal'); if(m) m.remove(); }, 2500);
                } catch(err) {
                    document.getElementById('ghTokenStatus').innerHTML = `<span style="color:#FF5555;">❌ فشل: ${err.message.substring(0,120)}</span>`;
                }
            };
        }

        function showSaveToGitHubModal() {
            showGitHubTokenModal('حفظ قائمة الأغاني للجميع', async (token) => {
                const ok = await _writeRepoFile(PLAYLIST_PATH, { tracks: playlistQueue }, 'تحديث قائمة أغاني نَفَس 🎵', token);
                if (!ok) throw new Error('فشل الحفظ في GitHub');
                showToast('تم حفظ قائمة الأغاني للجميع! 🎉');
            });
        }

        function addYouTubeToPlaylist() {
            const input = document.getElementById('ytUrlInput');
            if (!input || !input.value.trim()) { showToast('الرجاء لصق رابط الأغنية ⚠️'); return; }
            const videoId = extractYouTubeId(input.value.trim());
            if (!videoId) { showToast('رابط يوتيوب غير صحيح ❌'); return; }
            const trackTitle = `أغنية ${playlistQueue.length + 1} 🎵`;
            const track = { type: 'yt', id: videoId, title: trackTitle };
            playlistQueue.push(track);
            saveLocalPlaylist();
            input.value = '';
            updatePlaylistUI();
            showToast('تمت الإضافة 🎶 — اضغط "حفظ للجميع" لتثبيتها');
            if (playlistQueue.length === 1 && !audioIsPlaying) playTrackAtIndex(0);
        }

        function playYouTubeFromInput() {
            const input = document.getElementById('ytUrlInput');
            if (!input || !input.value.trim()) { showToast('الرجاء لصق رابط الأغنية ⚠️'); return; }
            const videoId = extractYouTubeId(input.value.trim());
            if (!videoId) { showToast('رابط يوتيوب غير صحيح ❌'); return; }
            const trackTitle = `أغنية ${playlistQueue.length + 1} 🎵`;
            const track = { type: 'yt', id: videoId, title: trackTitle };
            playlistQueue.push(track);
            saveLocalPlaylist();
            currentPlaylistIndex = playlistQueue.length - 1;
            input.value = '';
            updatePlaylistUI();
            playTrackAtIndex(currentPlaylistIndex);
        }

        function playTrackAtIndex(index) {
            if (playlistQueue.length === 0) return;
            currentPlaylistIndex = (index + playlistQueue.length) % playlistQueue.length;
            const track = playlistQueue[currentPlaylistIndex];
            if (track.type === 'yt') {
                if (ytPlayer && ytPlayer.loadVideoById) {
                    ytPlayer.loadVideoById(track.id);
                    ytPlayer.playVideo();
                    isYouTubeAudio = true; audioIsPlaying = true;
                    const statusEl = document.getElementById('audioStatusText');
                    if (statusEl) statusEl.innerText = track.title;
                    const btn = document.querySelector('#mainAudioBtn i');
                    if (btn) btn.className = 'fa-brands fa-youtube';
                    showToast('▶️ ' + track.title);
                }
            } else if (track.type === 'mp3') {
                const ap = document.getElementById('bgMusic');
                if (ap) { ap.src = track.src; ap.play(); }
                audioIsPlaying = true; isYouTubeAudio = false;
                showToast('▶️ ' + track.title);
            }
            updatePlaylistUI();
        }

        function playNextTrack() { if (playlistQueue.length > 0) playTrackAtIndex(currentPlaylistIndex + 1); }
        function playPrevTrack() { if (playlistQueue.length > 0) playTrackAtIndex(currentPlaylistIndex - 1); }

        function removeTrackFromPlaylist(index) {
            playlistQueue.splice(index, 1);
            if (currentPlaylistIndex >= playlistQueue.length) currentPlaylistIndex = Math.max(0, playlistQueue.length - 1);
            saveLocalPlaylist();
            updatePlaylistUI();
        }

        function updatePlaylistUI() {
            const el = document.getElementById('playlistItemsList');
            if (!el) return;
            if (playlistQueue.length === 0) {
                el.innerHTML = '<div style="color:rgba(255,255,255,0.4);font-size:0.83rem;text-align:center;padding:8px;">القائمة فارغة — أضف روابط يوتيوب واضغط "حفظ للجميع"</div>';
                return;
            }
            el.innerHTML = playlistQueue.map((t, i) => `
                <div style="display:flex;justify-content:space-between;align-items:center;background:${i===currentPlaylistIndex?'rgba(212,175,55,0.2)':'rgba(255,255,255,0.05)'};padding:7px 12px;border-radius:9px;border:1px solid ${i===currentPlaylistIndex?'#D4AF37':'transparent'};margin-bottom:4px;">
                    <span style="color:${i===currentPlaylistIndex?'#F9F295':'#EEE'};cursor:pointer;font-size:0.87rem;" onclick="playTrackAtIndex(${i})">${i===currentPlaylistIndex?'▶️ ':''}${i+1}. ${escapeHtml(t.title)}</span>
                    <button onclick="removeTrackFromPlaylist(${i})" style="background:none;border:none;color:#FF5555;cursor:pointer;padding:2px 6px;">🗑</button>
                </div>
            `).join('');
        }

        function extractYouTubeId(url) {
            if (!url) return '';
            url = url.trim();
            const m = url.match(/^.*(?:youtu\.be\/|v\/|u\/\w\/|embed\/|shorts\/|watch\?v=|&v=)([^#&?]{11})/);
            if (m && m[1]) return m[1];
            if (/^[a-zA-Z0-9_-]{11}$/.test(url)) return url;
            return '';
        }

        /* Local File Picker'''

new_content = content[:si] + NEW_ENGINE + content[end_of_replaced:]
print(f"New size: {len(new_content)} chars, {new_content.count(chr(10))} lines")

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(new_content)
print("Saved OK!")
