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
    initializationCheckInterval: null
};

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    console.log('Story Weaver Web界面已加载');
    setupEventListeners();
    checkSystemInitialization();
    loadCharacters();
});

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
    
    // 发送到后端
    fetchAPI('/api/process_input', 'POST', {
        input: input
    })
        .then(data => {
            const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
            responseTime.textContent = elapsed + 's';
            
            // 检查是否成功
            if (data.status === 'error' || !data.narrative) {
                throw new Error(data.message || '获取响应失败');
            }
            
            // 更新游戏状态
            appState.currentLocation = data.current_location || appState.currentLocation;
            appState.interactionCount++;
            
            // 更新显示
            document.getElementById('current-location').textContent = appState.currentLocation;
            document.getElementById('count-value').textContent = appState.interactionCount;
            
            // 显示响应
            displayNarrative(data.narrative);
            
            // 添加到历史
            appState.history.push({ type: 'assistant', content: data.narrative });
            
            // 如果有选项，显示选项
            if (data.next_options && data.next_options.length > 0) {
                displayOptions(data.next_options);
            }
            
            // 重新启用输入
            document.getElementById('user-input').disabled = false;
            document.getElementById('submit-btn').disabled = false;
            document.getElementById('user-input').focus();
            
            console.log('✓ 成功获得响应');
        })
        .catch(error => {
            console.error('获取响应失败: ' + error);
            displayError('❌ 获取响应失败: ' + error);
            responseTime.textContent = '-';
            
            // 重新启用输入
            document.getElementById('user-input').disabled = false;
            document.getElementById('submit-btn').disabled = false;
            document.getElementById('user-input').focus();
        });
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

// 重置到角色选择
function resetToCharacterSelection() {
    if (!confirm('确定要更换角色吗？当前进度将丢失。')) {
        return;
    }
    
    appState.gameActive = false;
    appState.interactionCount = 0;
    appState.history = [];
    appState.currentLocation = '';
    appState.selectedCharacter = null;
    appState.playerCharacter = '';
    
    document.getElementById('game-interface-panel').style.display = 'none';
    document.getElementById('character-selection-panel').style.display = 'block';
    
    // 清空游戏状态
    document.getElementById('narrative-display').innerHTML = '<p class="placeholder">点击"开始游戏"开始冒险...</p>';
    document.getElementById('options-panel').style.display = 'none';
    
    loadCharacters();
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
    displaySystemMessage('✓ 游戏已保存');
    
    // 发送到后端
    fetchAPI('/api/save_game', 'POST', gameData)
        .then(data => {
            console.log('✓ 游戏保存到服务器');
        })
        .catch(error => {
            console.error('保存到服务器失败: ' + error);
        });
}

// 查看历史
function toggleHistory() {
    const historyPanel = document.getElementById('history-panel');
    const historyContent = document.getElementById('history-content');
    
    if (historyPanel.style.display === 'none' || !historyPanel.style.display) {
        // 显示历史
        historyContent.innerHTML = '';
        
        for (const item of appState.history) {
            const div = document.createElement('div');
            div.className = `history-item ${item.type}`;
            div.innerHTML = `<p><strong>${item.type === 'user' ? '你' : '故事'}:</strong> ${item.content}</p>`;
            historyContent.appendChild(div);
        }
        
        historyPanel.style.display = 'block';
    } else {
        // 隐藏历史
        historyPanel.style.display = 'none';
    }
}

// 结束会话
function endSession() {
    if (!confirm('确定要结束会话吗？')) {
        return;
    }
    
    fetchAPI('/api/end_session', 'POST', {
        character_name: appState.selectedCharacter,
        interaction_count: appState.interactionCount
    })
        .then(data => {
            console.log('✓ 会话已结束');
            displaySystemMessage('✓ 会话已结束。感谢游玩！');
            
            resetToCharacterSelection();
        })
        .catch(error => {
            console.error('结束会话失败: ' + error);
            displayError('结束会话失败');
        });
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
    });
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
