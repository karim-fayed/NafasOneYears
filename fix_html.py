import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f'Before fix: {len(lines)} lines')

# Lines are 1-indexed in view; list is 0-indexed
# The broken region is lines 1577-1638 (0-indexed: 1576-1637)
# We need to replace lines 1576-1637 with the correct code

# Keep lines 0..1575 (up to but not including the broken line 1577)
# Then insert the correct code
# Then keep lines 1639..end (skipping the duplicate extractYouTubeId at 1634-1638)

correct_block = '''                    showToast(`جاري تشغيل: ${track.title} 🎶`);
                }
            } else if (track.type === 'mp3') {
                const audioPlayer = document.getElementById('bgMusic');
                audioPlayer.src = track.src;
                audioPlayer.play();
                audioIsPlaying = true;
                isYouTubeAudio = false;
                showToast(`جاري تشغيل: ${track.title} 🎶`);
            }
            updatePlaylistUI();
        }

        function playNextTrack() {
            if (playlistQueue.length > 0) playTrackAtIndex(currentPlaylistIndex + 1);
        }

        function playPrevTrack() {
            if (playlistQueue.length > 0) playTrackAtIndex(currentPlaylistIndex - 1);
        }

        function removeTrackFromPlaylist(index) {
            playlistQueue.splice(index, 1);
            if (currentPlaylistIndex >= playlistQueue.length) {
                currentPlaylistIndex = Math.max(0, playlistQueue.length - 1);
            }
            saveLocalPlaylist();
            updatePlaylistUI();
        }

        function updatePlaylistUI() {
            const listContainer = document.getElementById('playlistItemsList');
            if (!listContainer) return;

            if (playlistQueue.length === 0) {
                listContainer.innerHTML = `<div style="color: rgba(255,255,255,0.5); font-size:0.85rem; text-align:center; padding:5px;">القائمة فارغة — أضف روابط يوتيوب واضغط "حفظ للجميع" لتعمل لدى كل العائلة.</div>`;
                return;
            }

            listContainer.innerHTML = playlistQueue.map((track, i) => `
                <div style="display:flex; justify-content:space-between; align-items:center; background: ${i === currentPlaylistIndex ? 'rgba(212,175,55,0.25)' : 'rgba(255,255,255,0.06)'}; padding: 6px 12px; border-radius: 8px; border: 1px solid ${i === currentPlaylistIndex ? 'var(--gold-primary)' : 'transparent'}; font-size:0.9rem; margin-bottom:4px;">
                    <span style="color:${i === currentPlaylistIndex ? 'var(--gold-light)' : '#FFF'}; cursor:pointer;" onclick="playTrackAtIndex(${i})">
                        ${i === currentPlaylistIndex ? '▶️ ' : ''}${i + 1}. ${escapeHtml(track.title)}
                    </span>
                    <button onclick="removeTrackFromPlaylist(${i})" style="background:none; border:none; color:#FF5555; cursor:pointer;"><i class="fa-solid fa-trash-can"></i></button>
                </div>
            `).join('');
        }

        function extractYouTubeId(url) {
            if (!url) return '';
            url = url.trim();
            const regExp = /^.*(?:youtu\\.be\\/|v\\/|u\\/\\w\\/|embed\\/|shorts\\/|watch\\?v=|&v=)([^#&?]*).*/;
            const match = url.match(regExp);
            if (match && match[1] && match[1].length === 11) return match[1];
            if (/^[a-zA-Z0-9_-]{11}$/.test(url)) return url;
            return '';
        }
'''

# Also fix localStorage key in duplicate block around lines 1366-1375
# Check if there's a duplicate try/catch block
# Lines 1362-1370 have the correct block, but 1370-1375 may have duplicate

# Build the fixed file:
# Keep lines 0..1575 (index 0 to 1575, i.e., first 1576 lines)
# Add the correct_block
# Keep lines 1639..end (skip the broken 1577-1638 which are indices 1576-1637)

fixed_lines = lines[:1576]  # lines 1..1576
fixed_lines.append(correct_block)
fixed_lines.extend(lines[1638:])  # from line 1639 onwards

# Also fix the duplicate localStorage try-catch block
# Around lines 1363-1374 there's:
# line 1363: try {
# line 1364:     const savedLocal = localStorage.getItem('nafas_playlist_v3');
# ...
# line 1370:     } catch (e) { }
# line 1371:     if (savedLocal) {   <--- DUPLICATE
# line 1372:         playlistQueue = JSON.parse(savedLocal);
# line 1373:     }
# line 1374: } catch (e) { }

content = ''.join(fixed_lines)
print(f'After fix: {len(content.split(chr(10)))} lines')

# Check for the duplicate try-catch pattern and remove it
# Pattern: close of first try-catch followed by orphaned if block
import re
# Remove the broken duplicate fragment
content = content.replace(
    '        } catch (e) { }\n            if (savedLocal) {\n                playlistQueue = JSON.parse(savedLocal);\n                updatePlaylistUI();\n            }\n        } catch (e) { }',
    '        } catch (e) { }'
)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done! File fixed successfully.')
print(f'Final lines: {len(content.split(chr(10)))}')

# Verify no broken markers remain
broken_markers = ['sho        function', 'tYouTubeId', '} + 1);']
for marker in broken_markers:
    if marker in content:
        print(f'WARNING: Still found broken marker: {repr(marker)}')
    else:
        print(f'OK: No broken marker: {repr(marker)}')
