"""
Fix wishes engine: Replace broken Firebase with localStorage + GitHub repo solution.
Also fix: Load wishes from wishes.json in repo if it exists.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('index.html', 'r', encoding='utf-8') as f:
    content = f.read()

print(f"Size: {len(content)}")

# Find and replace the wishes engine
START = "        /* Cloud Wishes Database Engine (Free Live Realtime Backend) */"
END = "        function renderWishCard("

si = content.find(START)
ei = content.find(END)
print(f"Start: {si}, End: {ei}")

if si < 0 or ei < 0:
    print("ERROR: Could not find markers")
    sys.exit(1)

NEW_WISHES_ENGINE = """        /* =====================================================
           WISHES ENGINE v2.0 — localStorage + GitHub Repo
           ===================================================== */

        // Load wishes: first from localStorage, then from repo
        async function fetchWishesFromRepo() {
            // Load from localStorage first
            try {
                const localWishes = JSON.parse(localStorage.getItem('nafas_local_wishes') || '[]');
                if (localWishes.length > 0) {
                    const grid = document.getElementById('wishesGrid');
                    if (grid) {
                        grid.innerHTML = '';
                        localWishes.forEach(w => renderWishCard(w.author, w.text, w.rel || 'تهنئة', w.timestamp, false));
                    }
                }
            } catch(e) {}

            // Then fetch from GitHub repo (if wishes.json exists)
            try {
                const url = `https://raw.githubusercontent.com/${REPO_OWNER}/${REPO_NAME}/${REPO_BRANCH}/wishes.json?t=${Date.now()}`;
                const res = await fetch(url);
                if (!res.ok) return;
                const data = await res.json();
                if (!data || !Array.isArray(data.wishes) || data.wishes.length === 0) return;
                const grid = document.getElementById('wishesGrid');
                if (!grid) return;
                grid.innerHTML = '';
                data.wishes.forEach(w => renderWishCard(w.author, w.text, w.rel || 'تهنئة عائلية', w.timestamp, false));
                // Also save to localStorage for offline use
                localStorage.setItem('nafas_local_wishes', JSON.stringify(data.wishes));
            } catch(err) {
                // Keep what we already showed
            }
        }
        fetchWishesFromRepo();

        async function saveWish(e) {
            e.preventDefault();
            const authorInput = document.getElementById('wishAuthor');
            const textInput   = document.getElementById('wishText');
            const relInput    = document.getElementById('wishRel');
            const author = authorInput ? authorInput.value.trim() : '';
            const text   = textInput ? textInput.value.trim() : '';
            const rel    = (relInput ? relInput.value.trim() : '') || 'تهنئة عائلية';

            if (!author || !text) {
                showToast('الرجاء كتابة اسمك والتهنئة ⚠️');
                return;
            }

            const timestamp = Date.now();
            const wishData = { author, text, rel, timestamp };

            // Show it immediately
            renderWishCard(author, text, rel, timestamp, true);
            if (document.getElementById('wishForm')) document.getElementById('wishForm').reset();
            triggerConfetti();
            showToast('تم حفظ تهنئتك! 💌');

            // Save to localStorage
            try {
                const localWishes = JSON.parse(localStorage.getItem('nafas_local_wishes') || '[]');
                localWishes.unshift(wishData);
                localStorage.setItem('nafas_local_wishes', JSON.stringify(localWishes));
            } catch(e) {}

            // If admin token available: save permanently to GitHub repo
            if (_ghToken) {
                try {
                    let wishes = [];
                    try {
                        const url = `https://raw.githubusercontent.com/${REPO_OWNER}/${REPO_NAME}/${REPO_BRANCH}/wishes.json?t=${Date.now()}`;
                        const r = await fetch(url);
                        if (r.ok) { const d = await r.json(); if (Array.isArray(d.wishes)) wishes = d.wishes; }
                    } catch(e) {}
                    wishes.unshift(wishData);
                    await _writeRepoFile(WISHES_PATH, { wishes }, 'إضافة تهنئة 💌', _ghToken);
                    showToast('✅ تم حفظ تهنئتك للجميع!');
                } catch(err) {
                    console.log('Wish saved locally only:', err.message);
                }
            }
        }

        """

new_content = content[:si] + NEW_WISHES_ENGINE + content[ei:]
print(f"New size: {len(new_content)}, lines: {new_content.count(chr(10))}")

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(new_content)
print("Wishes engine fixed!")
