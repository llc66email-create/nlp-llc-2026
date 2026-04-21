// Story Weaver Web界面 - 主要JavaScript

// 应用状态
const appState = {
    gameActive: false,
    interactionCount: 0,
    history: [],
    currentLocation: '',
    playerCharacter: '',
    selectedCharacter: null,
    systemInitialized: false,
    initializationCheckInterval: null,
    activeModal: null,
    modalResolver: null
};

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    console.log('Story Weaver Web界面已加载');
    initializeGoldenSnitchCursor();
    setupEventListeners();
    checkSystemInitialization();
    loadCharacters();
});

function initializeGoldenSnitchCursor() {
    const cursor = document.getElementById('golden-snitch-cursor');

    if (!cursor) {
        return;
    }

    const supportsFinePointer = window.matchMedia('(hover: hover) and (pointer: fine)').matches;

    if (!supportsFinePointer) {
        return;
    }

    const state = {
        targetX: window.innerWidth / 2,
        targetY: window.innerHeight / 2,
        currentX: window.innerWidth / 2,
        currentY: window.innerHeight / 2,
        rafId: null,
        visible: false
    };

    function tick() {
        state.currentX += (state.targetX - state.currentX) * 0.22;
        state.currentY += (state.targetY - state.currentY) * 0.22;
        cursor.style.left = `${state.currentX + 12}px`;
        cursor.style.top = `${state.currentY + 10}px`;
        state.rafId = window.requestAnimationFrame(tick);
    }

    function updateCursorMode(target) {
        const editableTarget = target && target.closest('input, textarea, [contenteditable="true"], select');
        const hoverTarget = target && target.closest('button, a, .character-card, .option-button, .close-btn, .btn-secondary, .btn-danger, #submit-btn');

        cursor.classList.toggle('is-hidden', Boolean(editableTarget));
        cursor.classList.toggle('is-hovering', Boolean(hoverTarget) && !editableTarget);
    }

    document.addEventListener('mousemove', (event) => {
        state.targetX = event.clientX;
        state.targetY = event.clientY;

        if (!state.visible) {
            state.visible = true;
            cursor.classList.add('is-visible');
        }

        updateCursorMode(event.target);
    });

    document.addEventListener('mouseover', (event) => {
        updateCursorMode(event.target);
    });

    document.addEventListener('mousedown', (event) => {
        const pressTarget = event.target && event.target.closest('button, a, .character-card, .option-button, .close-btn, .btn-secondary, .btn-danger, #submit-btn');
        cursor.classList.toggle('is-pressing', Boolean(pressTarget));
    });

    document.addEventListener('mouseup', () => {
        cursor.classList.remove('is-pressing');
    });

    document.addEventListener('dragend', () => {
        cursor.classList.remove('is-pressing');
    });

    document.addEventListener('mouseleave', () => {
        cursor.classList.remove('is-visible');
        cursor.classList.remove('is-pressing');
    });

    window.addEventListener('blur', () => {
        cursor.classList.remove('is-visible');
        cursor.classList.remove('is-pressing');
    });

    window.addEventListener('focus', () => {
        if (state.visible) {
            cursor.classList.add('is-visible');
        }
    });

    if (!state.rafId) {
        state.rafId = window.requestAnimationFrame(tick);
    }
}

// 检查系统初始化状态
function checkSystemInitialization() {
    fetchAPI('/api/init_status', 'GET', null)
        .then(data => {
            if (data.status === 'complete') {
                appState.systemInitialized = true;
                console.log('✓ 系统初始化完成');
                if (appState.initializationCheckInterval) {
                    clearInterval(appState.initializationCheckInterval);
                    appState.initializationCheckInterval = null;
                }
            } else {
                console.log('⏳ 系统初始化中...');
                appState.systemInitialized = false;
                // 每 2 秒检查一次初始化状态
                if (!appState.initializationCheckInterval) {
                    appState.initializationCheckInterval = setInterval(checkSystemInitialization, 2000);
                }
            }
        })
        .catch(error => {
            console.error('检查初始化状态失败: ' + error);
        });
}

// 加载可用角色
function loadCharacters() {
    const grid = document.getElementById('characters-grid');
    if (!grid) return;
    
    // 显示加载指示
    grid.innerHTML = '<div class="loading-message">⏳ 加载角色中...</div>';
    
    fetchAPI('/api/get_characters', 'GET', null)
        .then(data => {
            if (data.characters) {
                displayCharacterSelection(data.characters);
                
                if (!data.initialized) {
                    console.log('⚠️ 使用预定义角色（系统还在初始化中）');
                    displaySystemMessage('💫 系统正在后台初始化，请稍候...');
                    // 初始化完成后重新加载角色
                    setTimeout(loadCharacters, 3000);
                }
            }
        })
        .catch(error => {
            console.error('无法加载角色: ' + error);
            grid.innerHTML = '<div class="error-message">❌ 无法加载角色列表</div>';
            displayError('无法加载角色列表');
        });
}

// 显示角色选择界面
function displayCharacterSelection(characters) {
    const grid = document.getElementById('characters-grid');
    grid.innerHTML = '';
    
    for (const [name, info] of Object.entries(characters)) {
        const card = document.createElement('div');
        card.className = 'character-card';
        card.innerHTML = `
            <div class="character-card-header">${info.title}</div>
            <div class="character-card-body">
                <p class="character-description">${info.description}</p>
                <div class="character-info">
                    <p><strong>起始位置:</strong> ${info.starting_location}</p>
                    <p><strong>能力:</strong> ${info.abilities.join(', ')}</p>
                </div>
            </div>
            <button class="btn-select-character" onclick="selectCharacter('${name}')">选择此角色</button>
        `;
        grid.appendChild(card);
    }
}

// 选择角色
function selectCharacter(characterName) {
    console.log('选择角色: ' + characterName);
    
    if (!appState.systemInitialized) {
        displayError('⏳ 系统还在初始化中，请稍候...');
        // 等待 2 秒后重试
        setTimeout(() => selectCharacter(characterName), 2000);
        return;
    }
    
    console.log('发送请求到 /api/select_character，参数:', { character_name: characterName });
    
    // 禁用所有选择按钮，显示加载状态
    document.querySelectorAll('.btn-select-character').forEach(btn => {
        btn.disabled = true;
    });
    
    fetchAPI('/api/select_character', 'POST', { character_name: characterName })
        .then(data => {
            // 检查是否成功
            if (data.status !== 'character_selected' || !data.character_info) {
                throw new Error(data.message || '选择角色失败');
            }
            
            const charInfo = data.character_info;
            
            appState.selectedCharacter = characterName;
            appState.playerCharacter = characterName;
            appState.currentLocation = charInfo.starting_location;
            appState.gameActive = true;
            appState.interactionCount = 0;
            
            // 隐藏角色选择，显示游戏界面
            document.getElementById('character-selection-panel').style.display = 'none';
            document.getElementById('game-interface-panel').style.display = 'block';
            
            // 更新显示信息
            document.getElementById('current-location').textContent = charInfo.starting_location;
            document.getElementById('player-character').textContent = characterName;
            document.getElementById('count-value').textContent = '0';
            
            // 启用输入和按钮
            document.getElementById('user-input').disabled = false;
            document.getElementById('submit-btn').disabled = false;
            document.getElementById('change-character-btn').disabled = false;
            document.getElementById('save-btn').disabled = false;
            document.getElementById('end-btn').disabled = false;
            
            // 显示初始故事
            displayNarrative(charInfo.description || '你开始在霍格沃茨的冒险...');
            console.log('✓ 成功选择角色');
        })
        .catch(error => {
            console.error('选择角色失败: ' + error);
            displayError('❌ 选择角色失败: ' + error);
            // 重新启用按钮
            document.querySelectorAll('.btn-select-character').forEach(btn => {
                btn.disabled = false;
            });
        });
}

// 发送用户输入
function sendInput() {
    if (!appState.gameActive) {
        displayError('游戏未启动');
        return;
    }
    
    const input = document.getElementById('user-input').value.trim();
    if (!input) return;
    
    console.log('用户输入: ' + input);
    
    // 添加到历史
    appState.history.push({ type: 'user', content: input });
    
    // 显示用户消息
    displayNarrative(input, 'user-input');
    
    // 清空输入框
    document.getElementById('user-input').value = '';
    
    // 禁用输入
    document.getElementById('user-input').disabled = true;
    document.getElementById('submit-btn').disabled = true;
    
    // 显示处理中
    const responseTime = document.getElementById('time-value');
    responseTime.textContent = '处理中...';
    
    const startTime = Date.now();
    
    streamProcessInput(input, startTime, responseTime)
        .catch(async (streamError) => {
            console.warn('流式接口失败，回退普通接口:', streamError);
            // 回退旧接口，保持兼容
            return fetchAPI('/api/process_input', 'POST', { input: input })
                .then(data => {
                    applyFinalResponse(data, startTime, responseTime);
                });
        })
        .catch(error => {
            console.error('获取响应失败: ' + error);
            displayError('❌ 获取响应失败: ' + error);
            responseTime.textContent = '-';
            document.getElementById('user-input').disabled = false;
            document.getElementById('submit-btn').disabled = false;
            document.getElementById('user-input').focus();
        });
}

async function streamProcessInput(input, startTime, responseTime) {
    const resp = await fetch('/api/process_input_stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ input: input })
    });

    if (!resp.ok || !resp.body) {
        throw new Error(`流式接口不可用: ${resp.status}`);
    }

    const reader = resp.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const chunks = buffer.split('\n\n');
        buffer = chunks.pop() || '';

        for (const chunk of chunks) {
            const evt = parseSSEChunk(chunk);
            if (!evt) continue;

            if (evt.event === 'quick' && evt.data && evt.data.text) {
                displayNarrative('⚡ ' + evt.data.text, 'assistant-quick');
                appState.history.push({ type: 'assistant_quick', content: evt.data.text });
            }

            if (evt.event === 'final' && evt.data) {
                applyFinalResponse(evt.data, startTime, responseTime);
            }

            if (evt.event === 'error') {
                throw new Error(evt.data?.message || '流式处理失败');
            }
        }
    }
}

function parseSSEChunk(chunk) {
    const lines = chunk.split('\n');
    let event = 'message';
    let data = '';

    for (const line of lines) {
        if (line.startsWith('event:')) {
            event = line.slice(6).trim();
        } else if (line.startsWith('data:')) {
            data += line.slice(5).trim();
        }
    }

    if (!data) return null;
    try {
        return { event, data: JSON.parse(data) };
    } catch (_) {
        return { event, data: { text: data } };
    }
}

function applyFinalResponse(data, startTime, responseTime) {
    const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
    responseTime.textContent = elapsed + 's';

    if (data.status === 'error' || !data.narrative) {
        throw new Error(data.message || '获取响应失败');
    }

    appState.currentLocation = data.current_location || appState.currentLocation;
    appState.interactionCount++;

    document.getElementById('current-location').textContent = appState.currentLocation;
    document.getElementById('count-value').textContent = appState.interactionCount;

    displayNarrative(data.narrative, 'assistant-final');
    appState.history.push({ type: 'assistant', content: data.narrative });

    if (data.task_completions && data.task_completions.length > 0) {
        data.task_completions.forEach(msg => {
            displayNarrative(msg, 'task-complete');
        });
    }

    if (data.next_task_hint) {
        displayNarrative(data.next_task_hint, 'task-hint');
    }

    if (data.story_progress) {
        updateProgressPanel(data.story_progress);
    }

    if (data.constraint_warning) {
        console.warn('[约束引擎]', data.constraint_warning);
    }

    if (data.next_options && data.next_options.length > 0) {
        displayOptions(data.next_options);
    }

    document.getElementById('user-input').disabled = false;
    document.getElementById('submit-btn').disabled = false;
    document.getElementById('user-input').focus();
    console.log('✓ 成功获得响应');
}

// 显示叙事内容
function displayNarrative(content, type = 'narrative') {
    const narrativeDisplay = document.getElementById('narrative-display');
    
    const p = document.createElement('p');
    p.className = `narrative-text ${type}`;
    p.textContent = content;
    
    // 清空占位符
    const placeholder = narrativeDisplay.querySelector('.placeholder');
    if (placeholder) {
        placeholder.remove();
    }
    
    narrativeDisplay.appendChild(p);
    
    // 滚动到最后
    narrativeDisplay.scrollTop = narrativeDisplay.scrollHeight;
}

// 显示选项
function displayOptions(options) {
    const optionsPanel = document.getElementById('options-panel');
    const optionsContainer = document.getElementById('options-container');
    
    optionsContainer.innerHTML = '';
    
    for (const option of options) {
        const btn = document.createElement('button');
        btn.className = 'option-button';
        btn.textContent = option;
        btn.onclick = () => {
            document.getElementById('user-input').value = option;
            sendInput();
        };
        optionsContainer.appendChild(btn);
    }
    
    optionsPanel.style.display = 'block';
}

// 显示系统消息
function displaySystemMessage(message) {
    const systemInfo = document.getElementById('system-info');
    const systemMessage = document.getElementById('system-message');
    
    systemMessage.textContent = message;
    systemInfo.style.display = 'block';
    
    // 5秒后隐藏
    setTimeout(() => {
        systemInfo.style.display = 'none';
    }, 5000);
}

// 显示错误
function displayError(message) {
    displaySystemMessage('❌ 错误: ' + message);
}

function escapeHtml(value) {
    return String(value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

function openMagicModal({ title, kicker = '霍格沃茨档案室', bodyHTML = '', actions = [], modalType = 'default' }) {
    const modal = document.getElementById('magic-modal');
    const titleElement = document.getElementById('magic-modal-title');
    const kickerElement = document.getElementById('magic-modal-kicker');
    const bodyElement = document.getElementById('magic-modal-body');
    const actionsElement = document.getElementById('magic-modal-actions');

    if (!modal || !titleElement || !kickerElement || !bodyElement || !actionsElement) {
        return;
    }

    titleElement.textContent = title;
    kickerElement.textContent = kicker;
    bodyElement.innerHTML = bodyHTML;
    actionsElement.innerHTML = '';

    actions.forEach((action) => {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = `magic-action-btn ${action.variant || 'secondary'}`;
        button.textContent = action.label;
        button.addEventListener('click', () => {
            if (typeof action.onClick === 'function') {
                action.onClick();
            }
        });
        actionsElement.appendChild(button);
    });

    modal.classList.add('is-open');
    modal.setAttribute('aria-hidden', 'false');
    document.body.classList.add('modal-open');
    appState.activeModal = modalType;
}

function closeMagicModal(result = null) {
    const modal = document.getElementById('magic-modal');

    if (!modal) {
        return;
    }

    modal.classList.remove('is-open');
    modal.setAttribute('aria-hidden', 'true');
    document.body.classList.remove('modal-open');
    appState.activeModal = null;

    if (typeof appState.modalResolver === 'function') {
        const resolver = appState.modalResolver;
        appState.modalResolver = null;
        resolver(result);
    }
}

function showConfirmModal({ title, message, confirmLabel, cancelLabel = '返回', confirmVariant = 'primary', kicker = '魔法抉择' }) {
    return new Promise((resolve) => {
        appState.modalResolver = resolve;

        openMagicModal({
            title,
            kicker,
            modalType: 'confirm',
            bodyHTML: `<p>${escapeHtml(message)}</p>`,
            actions: [
                {
                    label: cancelLabel,
                    variant: 'secondary',
                    onClick: () => closeMagicModal(false)
                },
                {
                    label: confirmLabel,
                    variant: confirmVariant,
                    onClick: () => closeMagicModal(true)
                }
            ]
        });
    });
}

function showNoticeModal({ title, message, kicker = '魔法回执', summary = [] }) {
    const summaryHtml = summary.length
        ? `<div class="modal-summary-grid">${summary.map((item) => `
            <div class="modal-summary-card">
                <span>${escapeHtml(item.label)}</span>
                <strong>${escapeHtml(item.value)}</strong>
            </div>
        `).join('')}</div>`
        : '';

    openMagicModal({
        title,
        kicker,
        modalType: 'notice',
        bodyHTML: `<p>${escapeHtml(message)}</p>${summaryHtml}`,
        actions: [
            {
                label: '继续冒险',
                variant: 'primary',
                onClick: () => closeMagicModal()
            }
        ]
    });
}

function renderHistoryModal() {
    const historyHtml = appState.history.length
        ? `<div class="history-log-list">${appState.history.map((item) => `
            <div class="history-item ${escapeHtml(item.type)}">
                <strong>${item.type === 'user' ? '你的行动' : item.type === 'assistant_quick' ? '飞贼低语' : '故事回响'}</strong>
                <p>${escapeHtml(item.content)}</p>
            </div>
        `).join('')}</div>`
        : '<div class="history-empty">羽毛笔还没有记录下新的冒险。</div>';

    openMagicModal({
        title: '交互历史',
        kicker: '霍格沃茨档案室',
        modalType: 'history',
        bodyHTML: historyHtml,
        actions: [
            {
                label: '合上卷轴',
                variant: 'primary',
                onClick: () => closeMagicModal()
            }
        ]
    });
}

function performResetToCharacterSelection() {
    appState.gameActive = false;
    appState.interactionCount = 0;
    appState.history = [];
    appState.currentLocation = '';
    appState.selectedCharacter = null;
    appState.playerCharacter = '';

    document.getElementById('game-interface-panel').style.display = 'none';
    document.getElementById('character-selection-panel').style.display = 'block';
    document.getElementById('narrative-display').innerHTML = '<p class="placeholder">点击"开始游戏"开始冒险...</p>';
    document.getElementById('options-panel').style.display = 'none';

    const progressPanel = document.getElementById('progress-panel');
    if (progressPanel) {
        progressPanel.remove();
    }

    loadCharacters();
}

// 重置到角色选择
async function resetToCharacterSelection() {
    const confirmed = await showConfirmModal({
        title: '更换角色',
        kicker: '分院与抉择',
        message: '更换角色后，当前旅程记录会被清空。要重新踏上另一位巫师的冒险吗？',
        confirmLabel: '更换角色',
        cancelLabel: '继续当前旅程'
    });

    if (!confirmed) {
        return;
    }

    performResetToCharacterSelection();
}

// 保存游戏
function saveGame() {
    console.log('保存游戏...');
    
    const gameData = {
        character: appState.selectedCharacter,
        location: appState.currentLocation,
        interactionCount: appState.interactionCount,
        history: appState.history,
        timestamp: new Date().toISOString()
    };
    
    // 保存到本地存储
    localStorage.setItem('story-weaver-save', JSON.stringify(gameData));
    
    // 发送到后端
    fetchAPI('/api/save_game', 'POST', gameData)
        .then(() => {
            console.log('✓ 游戏保存到服务器');
            showNoticeModal({
                title: '游戏已存档',
                kicker: '记忆冥想盆',
                message: '你的冒险已经被封存进魔法档案，随时都可以继续这段旅程。',
                summary: [
                    { label: '角色', value: appState.selectedCharacter || '未选择' },
                    { label: '当前位置', value: appState.currentLocation || '未知' },
                    { label: '记录轮数', value: String(appState.interactionCount) },
                    { label: '保存时间', value: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }) }
                ]
            });
        })
        .catch(error => {
            console.error('保存到服务器失败: ' + error);
            displayError('保存到服务器失败');
        });
}

// 查看历史
function toggleHistory() {
    if (appState.activeModal === 'history') {
        closeMagicModal();
        return;
    }

    renderHistoryModal();
}

// 结束会话
async function endSession() {
    const confirmed = await showConfirmModal({
        title: '结束会话',
        kicker: '城堡宵禁',
        message: '这会结束当前对话并返回角色选择界面。要把这段冒险先收进羊皮卷吗？',
        confirmLabel: '结束会话',
        cancelLabel: '继续冒险',
        confirmVariant: 'danger'
    });

    if (!confirmed) {
        return;
    }
    
    fetchAPI('/api/end_session', 'POST', {
        character_name: appState.selectedCharacter,
        interaction_count: appState.interactionCount
    })
        .then(() => {
            console.log('✓ 会话已结束');
            showNoticeModal({
                title: '会话已结束',
                kicker: '羊皮卷归档',
                message: '今晚的冒险已经合卷。下次回到霍格沃茨时，你仍可以重新展开新的故事。',
                summary: [
                    { label: '角色', value: appState.selectedCharacter || '未选择' },
                    { label: '完成轮数', value: String(appState.interactionCount) }
                ]
            });
            performResetToCharacterSelection();
        })
        .catch(error => {
            console.error('结束会话失败: ' + error);
            displayError('结束会话失败');
        });
}

// 更新故事推进进度面板
function updateProgressPanel(progress) {
    let panel = document.getElementById('progress-panel');
    if (!panel) {
        // 动态创建进度面板（插入游戏界面侧边）
        panel = document.createElement('div');
        panel.id = 'progress-panel';
        panel.style.cssText = 'position:fixed;top:80px;right:16px;width:220px;background:rgba(20,20,40,0.92);border:1px solid #5c3a8a;border-radius:8px;padding:12px 14px;color:#e8d5b7;font-size:13px;z-index:999;box-shadow:0 4px 16px rgba(0,0,0,0.5);';
        panel.innerHTML = '<div style="font-weight:bold;color:#c9a227;margin-bottom:6px;">📜 故事进度</div><div id="progress-content"></div>';
        document.body.appendChild(panel);
    }
    const content = document.getElementById('progress-content');
    const recommended = progress.recommended_task || null;
    const recommendedHtml = recommended
        ? `<div style="margin-top:8px;color:#a0d0a0;">▶ 当前推荐主线：</div>
           <div style="margin-top:4px;color:#f5e7c4;font-weight:600;">${recommended.title}</div>
           <div style="margin-top:3px;line-height:1.4;opacity:0.9;">${recommended.description}</div>`
        : '<div style="margin-top:8px;color:#a0d0a0;">▶ 当前推荐主线：已全部完成</div>';

    const sideHints = (progress.next_tasks && progress.next_tasks.length > 1)
        ? `<div style="margin-top:8px;color:#9ab9ff;">可选支线：</div><ul style="margin:4px 0 0 12px;padding:0;">${progress.next_tasks.slice(1).map(t => `<li>${t}</li>`).join('')}</ul>`
        : '';

    content.innerHTML = `
        <div>📍 ${progress.current_chapter || '未知章节'}</div>
        <div style="margin-top:4px;">章节主线：${progress.chapter_main_progress || '-'}</div>
        <div style="margin-top:4px;">主线：${progress.main_progress}</div>
        <div>支线：${progress.side_progress}</div>
        ${recommendedHtml}
        ${sideHints}
    `;
}

// 调试信息
function toggleDebug() {
    const debugPanel = document.getElementById('debug-panel');
    if (debugPanel.style.display === 'none' || !debugPanel.style.display) {
        debugPanel.style.display = 'block';
        updateDebugInfo();
    } else {
        debugPanel.style.display = 'none';
    }
}

function updateDebugInfo() {
    const debugContent = document.getElementById('debug-content');
    debugContent.innerHTML = `
        <p>游戏激活: ${appState.gameActive}</p>
        <p>系统初始化: ${appState.systemInitialized}</p>
        <p>当前角色: ${appState.selectedCharacter || '未选择'}</p>
        <p>当前位置: ${appState.currentLocation || '未知'}</p>
        <p>交互次数: ${appState.interactionCount}</p>
        <p>历史记录: ${appState.history.length} 条</p>
    `;
}

// 设置事件监听器
function setupEventListeners() {
    const modal = document.getElementById('magic-modal');
    const modalCloseButton = document.getElementById('magic-modal-close');

    // 回车发送
    const userInput = document.getElementById('user-input');
    if (userInput) {
        userInput.addEventListener('keypress', function(event) {
            if (event.key === 'Enter') {
                sendInput();
            }
        });
    }
    
    // 快捷键
    document.addEventListener('keydown', function(event) {
        if (event.ctrlKey && event.key === 'h') {
            event.preventDefault();
            toggleHistory();
        }
        if (event.ctrlKey && event.key === 'd') {
            event.preventDefault();
            toggleDebug();
        }
        if (event.key === 'Escape' && appState.activeModal) {
            event.preventDefault();
            closeMagicModal(false);
        }
    });

    if (modal) {
        modal.addEventListener('click', function(event) {
            if (event.target.dataset.modalClose === 'true') {
                closeMagicModal(false);
            }
        });
    }

    if (modalCloseButton) {
        modalCloseButton.addEventListener('click', function() {
            closeMagicModal(false);
        });
    }
}

// API 调用函数
function fetchAPI(endpoint, method = 'GET', data = null) {
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json'
        }
    };
    
    if (data) {
        options.body = JSON.stringify(data);
    }
    
    return fetch(endpoint, options)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        });
}
