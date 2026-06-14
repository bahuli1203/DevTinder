// Main Javascript for Dev Tinder

document.addEventListener('DOMContentLoaded', () => {
    // Initialize AOS
    if (typeof AOS !== 'undefined') {
        AOS.init({
            duration: 800,
            once: true
        });
    }

    // --- THEME TOGGLE LOGIC ---
    const themeToggle = document.getElementById('theme-toggle');
    const htmlTag = document.documentElement;

    function setTheme(theme) {
        htmlTag.setAttribute('data-theme', theme);
        localStorage.setItem('devtinder-theme', theme);
        
        const icon = themeToggle?.querySelector('i');
        if (icon) {
            icon.className = theme === 'light' ? 'fa-solid fa-moon' : 'fa-solid fa-sun';
        }
        
        if (typeof updateChartTheme === 'function') {
            updateChartTheme(theme);
        }
    }

    const savedTheme = localStorage.getItem('devtinder-theme') || 'dark';
    setTheme(savedTheme);

    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            const currentTheme = htmlTag.getAttribute('data-theme');
            setTheme(currentTheme === 'light' ? 'dark' : 'light');
        });
    }

    // --- NOTIFICATION POLLING ---
    const notifBell = document.getElementById('notif-bell');
    const notifBadge = document.getElementById('notif-count');
    const notifList = document.getElementById('notif-list');

    function pollNotifications() {
        if (!notifBell) return;
        fetch('/api/notifications')
            .then(res => res.json())
            .then(data => {
                const unread = data.unread_count;
                if (unread > 0) {
                    notifBadge.textContent = unread;
                    notifBadge.classList.remove('d-none');
                } else {
                    notifBadge.classList.add('d-none');
                }

                if (data.notifications && data.notifications.length > 0) {
                    notifList.innerHTML = '';
                    data.notifications.forEach(n => {
                        const item = document.createElement('a');
                        item.href = n.link || '#';
                        item.className = `dropdown-item bell-item ${n.is_read ? '' : 'fw-bold'}`;
                        item.innerHTML = `
                            <div class="d-flex align-items-center">
                                <div class="flex-grow-1">
                                    <div class="small text-white-50">${n.created_at}</div>
                                    <div class="text-white">${n.title}</div>
                                    <div class="small text-muted">${n.message}</div>
                                </div>
                            </div>
                        `;
                        item.addEventListener('click', (e) => {
                            fetch(`/api/notifications/read/${n.id}`, { method: 'POST' });
                        });
                        notifList.appendChild(item);
                    });
                } else {
                    notifList.innerHTML = '<div class="dropdown-item text-center text-muted py-3">No notifications</div>';
                }
            })
            .catch(err => console.log('Notification error:', err));
    }

    if (notifBell) {
        pollNotifications();
        setInterval(pollNotifications, 8000);
    }

    // --- MATCHES TINDER SWIPE DECK ---
    const swipeContainer = document.getElementById('swipe-container');
    const swipeActions = document.getElementById('swipe-actions');
    let cards = [];
    let currentCardIndex = 0;

    function initSwipeDeck() {
        if (!swipeContainer) return;

        fetch('/api/matches/potential')
            .then(res => res.json())
            .then(potentialMatches => {
                if (potentialMatches.length === 0) {
                    swipeContainer.innerHTML = `
                        <div class="glass-panel text-center p-5 d-flex flex-column align-items-center justify-content-center h-100">
                            <i class="fa-solid fa-face-sad-tear text-primary mb-4" style="font-size: 3.5rem;"></i>
                            <h3 class="text-white fw-bold mb-3">No More Developers!</h3>
                            <p class="text-muted mb-4">You have reviewed everyone nearby. Try editing your profile skills or check back later!</p>
                            <a href="/profile" class="btn btn-glow-primary px-4 py-2">Edit My Skills</a>
                        </div>
                    `;
                    if (swipeActions) swipeActions.classList.add('d-none');
                    return;
                }

                swipeContainer.innerHTML = '';
                potentialMatches.forEach((match, index) => {
                    const card = document.createElement('div');
                    card.className = 'swipe-card glass-panel';
                    card.style.zIndex = potentialMatches.length - index;
                    card.dataset.userId = match.id;
                    
                    const skillsBadges = match.skills.map(s => `<span class="badge-skill">${s}</span>`).join('');

                    card.innerHTML = `
                        <div class="match-score-badge">${match.match_score}% Match</div>
                        <div class="card-img-container">
                            <img src="${match.image}" alt="${match.full_name}">
                            <div class="card-gradient-overlay"></div>
                        </div>
                        <div class="card-content">
                            <div>
                                <h4 class="text-white fw-bold mb-1">${match.full_name}</h4>
                                <div class="text-primary small fw-semibold mb-2">
                                    <i class="fa-solid fa-graduation-cap me-1"></i> ${match.college} (${match.degree})
                                </div>
                                <p class="text-muted small mb-3 text-truncate-3">${match.bio}</p>
                            </div>
                            <div>
                                <div class="d-flex flex-wrap mb-3" style="max-height: 80px; overflow: hidden;">
                                    ${skillsBadges}
                                </div>
                                <div class="text-white-50 small">
                                    <i class="fa-solid fa-briefcase me-1"></i> Experience: <span class="text-accent fw-bold">${match.experience}</span>
                                </div>
                            </div>
                        </div>
                    `;
                    swipeContainer.appendChild(card);
                    setupDragHandlers(card);
                });

                cards = document.querySelectorAll('.swipe-card');
                currentCardIndex = 0;
            });
    }

    function setupDragHandlers(card) {
        let startX = 0;
        let startY = 0;
        let isDragging = false;

        const onStart = (e) => {
            isDragging = true;
            startX = e.type.includes('touch') ? e.touches[0].clientX : e.clientX;
            startY = e.type.includes('touch') ? e.touches[0].clientY : e.clientY;
            card.style.transition = 'none';
        };

        const onMove = (e) => {
            if (!isDragging) return;
            const currentX = e.type.includes('touch') ? e.touches[0].clientX : e.clientX;
            const currentY = e.type.includes('touch') ? e.touches[0].clientY : e.clientY;
            
            const deltaX = currentX - startX;
            const deltaY = currentY - startY;
            const rotate = deltaX * 0.08;

            card.style.transform = `translate(${deltaX}px, ${deltaY}px) rotate(${rotate}deg)`;
        };

        const onEnd = (e) => {
            if (!isDragging) return;
            isDragging = false;
            card.style.transition = 'transform 0.5s ease, opacity 0.5s ease';

            const currentX = e.type.includes('touch') ? e.changedTouches[0].clientX : e.clientX;
            const deltaX = currentX - startX;

            if (deltaX > 120) {
                swipeCardAction(card, 'connect');
            } else if (deltaX < -120) {
                swipeCardAction(card, 'pass');
            } else {
                card.style.transform = 'translate(0px, 0px) rotate(0deg)';
            }
        };

        card.addEventListener('mousedown', onStart);
        card.addEventListener('touchstart', onStart, { passive: true });

        document.addEventListener('mousemove', onMove);
        document.addEventListener('touchmove', onMove, { passive: true });

        document.addEventListener('mouseup', onEnd);
        document.addEventListener('touchend', onEnd);
    }

    function swipeCardAction(card, action) {
        const userId = card.dataset.userId;

        if (action === 'connect') {
            card.classList.add('swiped-right');
        } else if (action === 'pass') {
            card.classList.add('swiped-left');
        } else if (action === 'superlike') {
            card.classList.add('swiped-up');
        }

        setTimeout(() => {
            card.remove();
        }, 500);

        fetch('/api/matches/swipe', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userId, action: action })
        })
        .then(res => res.json())
        .then(data => {
            if (data.is_match) {
                // Show a Match celebration Modal
                showMatchCelebration(userId);
            }
            // Poll potential matches count to see if we run out
            currentCardIndex++;
            if (currentCardIndex >= cards.length) {
                initSwipeDeck();
            }
        });
    }

    function showMatchCelebration(userId) {
        const modal = document.createElement('div');
        modal.style.position = 'fixed';
        modal.style.top = '0';
        modal.style.left = '0';
        modal.style.width = '100vw';
        modal.style.height = '100vh';
        modal.style.background = 'rgba(15, 23, 42, 0.95)';
        modal.style.zIndex = '9999';
        modal.className = 'd-flex flex-column align-items-center justify-content-center text-center';
        
        modal.innerHTML = `
            <div class="glass-panel p-5 animate-float" style="max-width: 500px;">
                <h1 class="text-white fw-bold mb-4" style="background: linear-gradient(135deg, #d946ef, #8b5cf6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 3rem;">IT'S A MATCH! 🚀</h1>
                <p class="text-muted mb-4">You and the developer connected! Start chatting to form a winning team.</p>
                <div class="d-flex justify-content-center gap-3">
                    <a href="/chat" class="btn btn-glow-primary px-4 py-2">Go to Chat</a>
                    <button class="btn btn-outline-light px-4 py-2" id="close-celebration">Keep Swiping</button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);

        document.getElementById('close-celebration').addEventListener('click', () => {
            modal.remove();
        });
    }

    // Bind swipe buttons
    const passBtn = document.getElementById('swipe-pass');
    const connectBtn = document.getElementById('swipe-connect');
    const superBtn = document.getElementById('swipe-super');

    if (passBtn) {
        passBtn.addEventListener('click', () => {
            const activeCard = document.querySelector('.swipe-card:last-child');
            if (activeCard) swipeCardAction(activeCard, 'pass');
        });
    }
    if (connectBtn) {
        connectBtn.addEventListener('click', () => {
            const activeCard = document.querySelector('.swipe-card:last-child');
            if (activeCard) swipeCardAction(activeCard, 'connect');
        });
    }
    if (superBtn) {
        superBtn.addEventListener('click', () => {
            const activeCard = document.querySelector('.swipe-card:last-child');
            if (activeCard) swipeCardAction(activeCard, 'superlike');
        });
    }

    initSwipeDeck();

    // --- REALTIME CHAT LONG POLLING ---
    const chatForm = document.getElementById('chat-send-form');
    const chatInput = document.getElementById('chat-input');
    const chatMessages = document.getElementById('chat-messages');
    let lastMessageId = 0;

    function scrollChatToBottom() {
        if (chatMessages) {
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    }

    function pollChatMessages() {
        if (!chatMessages) return;
        const receiverId = chatMessages.dataset.receiverId;
        const teamId = chatMessages.dataset.teamId;

        let url = `/api/chat/messages?last_id=${lastMessageId}`;
        if (teamId) {
            url += `&team_id=${teamId}`;
        } else if (receiverId) {
            url += `&receiver_id=${receiverId}`;
        } else {
            return;
        }

        fetch(url)
            .then(res => res.json())
            .then(msgs => {
                if (msgs.length > 0) {
                    msgs.forEach(m => {
                        if (m.id > lastMessageId) {
                            lastMessageId = m.id;
                        }
                        
                        const isOutgoing = m.sender_id === parseInt(chatMessages.dataset.currentUserId);
                        const bubble = document.createElement('div');
                        bubble.className = `message-bubble ${isOutgoing ? 'outgoing' : 'incoming'}`;
                        
                        let senderLabel = '';
                        if (teamId && !isOutgoing) {
                            senderLabel = `<div class="fw-bold small text-accent mb-1">${m.sender_name}</div>`;
                        }

                        bubble.innerHTML = `
                            ${senderLabel}
                            <div>${m.content}</div>
                            <div class="text-end small text-white-50 mt-1" style="font-size: 0.75rem;">${m.created_at}</div>
                        `;
                        chatMessages.appendChild(bubble);
                    });
                    scrollChatToBottom();
                }
            });
    }

    if (chatForm) {
        scrollChatToBottom();
        setInterval(pollChatMessages, 3000);

        chatForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const text = chatInput.value.trim();
            if (!text) return;

            const receiverId = chatMessages.dataset.receiverId;
            const teamId = chatMessages.dataset.teamId;

            fetch('/api/chat/send', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    content: text,
                    receiver_id: receiverId || null,
                    team_id: teamId || null
                })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    chatInput.value = '';
                    pollChatMessages(); // update immediately
                }
            });
        });

        // Emoji Trigger panel
        const emojiToggle = document.getElementById('emoji-toggle');
        const emojiPanel = document.getElementById('emoji-panel');
        if (emojiToggle && emojiPanel) {
            emojiToggle.addEventListener('click', () => {
                emojiPanel.style.display = emojiPanel.style.display === 'grid' ? 'none' : 'grid';
            });
            document.querySelectorAll('.emoji-btn').forEach(btn => {
                btn.addEventListener('click', () => {
                    chatInput.value += btn.textContent;
                    emojiPanel.style.display = 'none';
                    chatInput.focus();
                });
            });
        }
    }

    // --- CHART.JS RADAR TEAM STRENGTH ---
    let radarChartInstance = null;
    
    window.updateChartTheme = function(theme) {
        if (!radarChartInstance) return;
        const isLight = theme === 'light';
        const gridColor = isLight ? 'rgba(0, 0, 0, 0.1)' : 'rgba(255, 255, 255, 0.1)';
        const textColor = isLight ? '#64748b' : '#94a3b8';
        
        radarChartInstance.options.scales.r.angleLines.color = gridColor;
        radarChartInstance.options.scales.r.grid.color = gridColor;
        radarChartInstance.options.scales.r.pointLabels.color = textColor;
        radarChartInstance.options.scales.r.ticks.color = textColor;
        radarChartInstance.update();
    };

    const radarCtx = document.getElementById('teamRadarChart');
    if (radarCtx) {
        const stats = JSON.parse(radarCtx.dataset.metrics);
        const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
        const isLight = currentTheme === 'light';
        const gridColor = isLight ? 'rgba(0, 0, 0, 0.1)' : 'rgba(255, 255, 255, 0.1)';
        const textColor = isLight ? '#64748b' : '#94a3b8';

        radarChartInstance = new Chart(radarCtx, {
            type: 'radar',
            data: {
                labels: ['Frontend', 'Backend', 'UI UX Design', 'AI / ML', 'Cybersecurity'],
                datasets: [{
                    label: 'Team Competency Strength',
                    data: [stats.frontend, stats.backend, stats.design, stats.ai, stats.security],
                    backgroundColor: 'rgba(139, 92, 246, 0.2)',
                    borderColor: 'rgba(139, 92, 246, 1)',
                    borderWidth: 2,
                    pointBackgroundColor: 'rgba(217, 70, 239, 1)',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: 'rgba(139, 92, 246, 1)'
                }]
            },
            options: {
                scales: {
                    r: {
                        angleLines: { color: gridColor },
                        grid: { color: gridColor },
                        pointLabels: {
                            color: textColor,
                            font: { family: 'Inter', size: 12 }
                        },
                        ticks: {
                            backdropColor: 'transparent',
                            color: textColor,
                            beginAtZero: true,
                            max: 100
                        }
                    }
                },
                plugins: { legend: { display: false } }
            }
        });
    }

    // --- GITHUB PROFILE ANALYZER ---
    const gitForm = document.getElementById('github-fetch-form');
    const gitUsername = document.getElementById('github-username-field');
    const gitResult = document.getElementById('github-analyzer-result');

    if (gitForm) {
        gitForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const username = gitUsername.value.trim();
            if (!username) return;

            gitResult.innerHTML = `
                <div class="text-center py-4">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Analyzing Profile...</span>
                    </div>
                    <div class="small text-muted mt-2">Pulling repository languages and stars...</div>
                </div>
            `;

            const formData = new FormData();
            formData.append('github_username', username);

            fetch('/profile/github', {
                method: 'POST',
                body: formData
            })
            .then(res => res.json())
            .then(data => {
                if (data.error) {
                    gitResult.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
                    return;
                }

                const repoList = data.repos.map(r => `
                    <div class="d-flex justify-content-between align-items-center py-2 border-bottom border-secondary" style="border-color: rgba(255,255,255,0.05) !important;">
                        <div>
                            <a href="${r.url}" target="_blank" class="text-white text-decoration-none fw-semibold">${r.name}</a>
                            <div class="small text-muted">${r.language || 'Documentation'}</div>
                        </div>
                        <span class="badge bg-secondary"><i class="fa-solid fa-star text-warning"></i> ${r.stars}</span>
                    </div>
                `).join('');

                const langTags = Object.keys(data.languages).map(lang => `
                    <span class="badge bg-primary m-1">${lang} (${data.languages[lang]} repos)</span>
                `).join('');

                gitResult.innerHTML = `
                    <div class="d-flex align-items-center gap-3 mb-4">
                        <img src="${data.avatar}" class="rounded-circle" style="width: 60px; height: 60px;">
                        <div>
                            <h5 class="text-white fw-bold mb-0">@${data.username}</h5>
                            <span class="text-accent small"><i class="fa-solid fa-fire text-secondary"></i> ${data.contributions} contributions</span>
                        </div>
                    </div>
                    <h6 class="text-white-50 mb-2">Dominant Tech Stack:</h6>
                    <div class="mb-4">${langTags}</div>
                    <h6 class="text-white-50 mb-2">Top Repositories:</h6>
                    <div>${repoList}</div>
                `;
            })
            .catch(err => {
                gitResult.innerHTML = `<div class="alert alert-danger">An error occurred while fetching GitHub profile.</div>`;
            });
        });
    }
});

// ===== Landing Page: Animated Counters =====
document.addEventListener('DOMContentLoaded', function () {
    const counters = document.querySelectorAll('.counter');
    if (counters.length) {
        counters.forEach(counter => {
            const target = parseFloat(counter.getAttribute('data-target'));
            const decimals = parseInt(counter.getAttribute('data-decimals') || '0');
            const suffix = counter.getAttribute('data-suffix') || '';
            const duration = 1500;
            const start = performance.now();

            function update(now) {
                const progress = Math.min((now - start) / duration, 1);
                const value = target * progress;
                counter.textContent = (decimals > 0 ? value.toFixed(decimals) : Math.floor(value).toLocaleString()) + suffix;
                if (progress < 1) requestAnimationFrame(update);
                else counter.textContent = (decimals > 0 ? target.toFixed(decimals) : target.toLocaleString()) + suffix;
            }
            requestAnimationFrame(update);
        });
    }

    // ===== Landing Page: Typewriter Terminal =====
    const terminalOutput = document.getElementById('terminal-output');
    if (terminalOutput) {
        const lines = [
            { text: '$ python app.py --generate-matching', cls: '' },
            { text: '> Skill similarity: 82%', cls: 'text-muted' },
            { text: '> Complementary score: 95% (Perfect Balance!)', cls: 'text-muted' },
            { text: '>> MATCH DETECTED. Notification dispatched.', cls: '' }
        ];
        let lineIndex = 0, charIndex = 0;

        function typeChar() {
            if (lineIndex >= lines.length) {
                setTimeout(() => {
                    terminalOutput.innerHTML = '';
                    lineIndex = 0; charIndex = 0;
                    typeChar();
                }, 3000);
                return;
            }
            const current = lines[lineIndex];
            if (charIndex === 0) {
                const div = document.createElement('div');
                if (current.cls) div.className = current.cls;
                div.id = 'typing-line';
                terminalOutput.appendChild(div);
            }
            const lineDiv = document.getElementById('typing-line');
            charIndex++;
            lineDiv.textContent = current.text.slice(0, charIndex);

            if (charIndex >= current.text.length) {
                lineDiv.removeAttribute('id');
                lineIndex++; charIndex = 0;
                setTimeout(typeChar, 400);
            } else {
                setTimeout(typeChar, 18);
            }
        }
        typeChar();
    }

    // ===== Landing Page: Live Activity Feed =====
    const feed = document.getElementById('activity-feed');
    if (feed) {
        const events = [
            '<strong>Aisha K.</strong> matched with <strong>Rohan P.</strong> — 91% compatibility',
            '<strong>Team NeuralNinjas</strong> just reached full strength (4/4 members)',
            '<strong>Priya & Kabir</strong> — Backend + AI specialist matched!',
            '<strong>Vikram S.</strong> joined as a UI/UX designer',
            '<strong>Team CodeCrafters</strong> hit a 96% team health score',
            '<strong>Maria G.</strong> connected her GitHub — 4.8k stars verified',
            '<strong>AI Project Lab</strong> generated a new pitch for Team Voltage',
            '<strong>Dev & Sara</strong> matched — Frontend + ML specialist'
        ];

        function pushEvent() {
            const item = document.createElement('div');
            item.className = 'activity-item';
            item.innerHTML = events[Math.floor(Math.random() * events.length)];
            feed.insertBefore(item, feed.firstChild);
            while (feed.children.length > 3) {
                feed.removeChild(feed.lastChild);
            }
        }
        pushEvent();
        setInterval(pushEvent, 2800);
    }
});

// ===== Avatar Picker: live preview + selection highlight =====
document.addEventListener('DOMContentLoaded', function () {
    const avatarOptions = document.querySelectorAll('.avatar-option');
    const avatarPreview = document.getElementById('avatar-preview');

    avatarOptions.forEach(option => {
        option.addEventListener('click', () => {
            avatarOptions.forEach(o => o.classList.remove('selected'));
            option.classList.add('selected');
            const radio = option.querySelector('.avatar-radio');
            radio.checked = true;
            if (avatarPreview) {
                const img = option.querySelector('img');
                avatarPreview.src = img.src;
            }
        });
    });
});
