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
    displaySystemMessage('⏳ 正在选择角色...');
    
    fetchAPI('/api/select_character', 'POST', { character_name: characterName })
        .then(data => {
            console.log('角色选择响应:', data);
            
            if (data.status === 'error') {
                // 重新启用按钮
                document.querySelectorAll('.btn-select-character').forEach(btn => {
                    btn.disabled = false;
                });
                displayError('无法选择角色: ' + (data.message || data.error));
                return;
            }
            
            appState.selectedCharacter = characterName;
            appState.playerCharacter = characterName;
            console.log('角色已选择，当前状态:', appState);
            
            // 隐藏角色选择面板，显示游戏界面
            document.getElementById('character-selection-panel').style.display = 'none';
            document.getElementById('game-interface-panel').style.display = 'grid';
            console.log('UI已更新');
            
            // 开始游戏，显示初始场景
            startGame();
        })
        .catch(error => {
            console.error('选择角色时出错:', error);
            // 重新启用按钮
            document.querySelectorAll('.btn-select-character').forEach(btn => {
                btn.disabled = false;
            });
            displayError('无法选择角色: ' + error);
        });
}

// 重置到角色选择
function resetToCharacterSelection() {
    document.getElementById('character-selection-panel').style.display = 'block';
    document.getElementById('game-interface-panel').style.display = 'none';
    appState.gameActive = false;
    appState.selectedCharacter = null;
    document.getElementById('narrative-display').innerHTML = '<p class="placeholder">点击"开始游戏"开始冒险...</p>';
    document.getElementById('options-panel').style.display = 'none';
}

// 设置事件监听器
function setupEventListeners() {
    // 回车键发送
    document.getElementById('user-input').addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendInput();
        }
    });
}

// 开始游戏
function startGame() {
    if (!appState.selectedCharacter) {
        displaySystemMessage('请先选择一个角色');
        return;
    }
    
    console.log('开始新游戏...');
    fetchAPI('/api/start_game', 'POST', {})
        .then(data => {
            appState.gameActive = true;
            appState.interactionCount = 0;
            appState.history = [];
            
            // 显示初始场景
            if (data.scene) {
                const sceneHtml = `
                    <div class="scene-display">
                        <h2 class="scene-title">${data.scene.title || '新的冒险开始'}</h2>
                        <p class="scene-description">${data.scene.scene_description || ''}</p>
                        <p class="scene-atmosphere"><em>氛围: ${data.scene.atmosphere || ''}</em></p>
                        <p class="scene-time"><em>时间: ${data.scene.time_of_day || ''}</em></p>
                        <p class="scene-prompt"><strong>${data.scene.prompt || '现在，你准备做什么？'}</strong></p>
                    </div>
                `;
                displayNarrative(sceneHtml, true);
            } else {
                displayNarrative(data.message || '游戏已开始');
            }
            
            updateGameStatus();
            
            // 启用输入相关控件
            document.getElementById('user-input').disabled = false;
            document.getElementById('submit-btn').disabled = false;
            document.getElementById('save-btn').disabled = false;
            document.getElementById('end-btn').disabled = false;
            
            console.log('游戏已开始');
        })
        .catch(error => {
            displayError('无法开始游戏: ' + error);
        });
}

// 发送用户输入
function sendInput() {
    if (!appState.gameActive) {
        displayError('请先选择一个角色');
        return;
    }

    const input = document.getElementById('user-input').value.trim();
    if (!input) {
        displayError('请输入你的行动');
        return;
    }

    // 禁用输入
    document.getElementById('user-input').disabled = true;
    document.getElementById('submit-btn').disabled = true;

    const startTime = performance.now();

    fetchAPI('/api/process_input', 'POST', { input: input })
        .then(data => {
            const responseTime = (performance.now() - startTime) / 1000;
            
            // 更新调试信息
            updateDebugInfo({
                'Intent': data.intent,
                'Confidence': data.intent_confidence.toFixed(3),
                'Response Time': responseTime.toFixed(3) + 's',
                'Consistency': data.consistency_check ? '✓' : '✗'
            });

            if (data.status === 'success') {
                // 显示叙述
                displayNarrative(data.narrative);
                
                // 显示选项
                if (data.next_options && data.next_options.length > 0) {
                    displayOptions(data.next_options);
                }
                
                // 更新统计信息
                appState.interactionCount++;
                updateStats(data.response_time);
                
                // 添加到历史
                appState.history.push({
                    input: input,
                    output: data.narrative,
                    intent: data.intent,
                    timestamp: new Date().toLocaleTimeString()
                });
                
                // 清空输入
                document.getElementById('user-input').value = '';
                
            } else if (data.status === 'clarification_requested') {
                displaySystemInfo('系统需要澄清: ' + data.message);
            } else if (data.status === 'consistency_violation') {
                displayWarning('一致性检查失败: ' + data.message);
            }
        })
        .catch(error => {
            displayError('处理输入失败: ' + error);
        })
        .finally(() => {
            // 重新启用输入
            if (appState.gameActive) {
                document.getElementById('user-input').disabled = false;
                document.getElementById('submit-btn').disabled = false;
                document.getElementById('user-input').focus();
            }
        });
}

// 保存游戏
function saveGame() {
    const saveName = prompt('请输入保存名称:', 'save_' + new Date().getTime());
    if (!saveName) return;

    fetchAPI('/api/save_game', 'POST', { save_name: saveName })
        .then(data => {
            displaySuccess('游戏已保存: ' + saveName);
            console.log('游戏保存地址:', data.file);
        })
        .catch(error => {
            displayError('保存游戏失败: ' + error);
        });
}

// 结束会话
function endSession() {
    if (confirm('确定要结束会话吗？')) {
        fetchAPI('/api/end_session', 'POST', {})
            .then(data => {
                displaySuccess('会话已结束');
                console.log('会话摘要:', data.summary);
                appState.gameActive = false;
                
                // 禁用游戏控件
                document.getElementById('user-input').disabled = true;
                document.getElementById('submit-btn').disabled = true;
                document.getElementById('save-btn').disabled = true;
                document.getElementById('end-btn').disabled = true;
            })
            .catch(error => {
                displayError('结束会话失败: ' + error);
            });
    }
}

// 显示叙述
function displayNarrative(text, isHTML = false) {
    const narrativeDiv = document.getElementById('narrative-display');
    if (isHTML) {
        narrativeDiv.innerHTML = text;
    } else {
        const paragraph = document.createElement('p');
        paragraph.textContent = text;
        narrativeDiv.appendChild(paragraph);
    }
    narrativeDiv.scrollTop = narrativeDiv.scrollHeight;
}

// 显示选项
function displayOptions(options) {
    const optionsPanel = document.getElementById('options-panel');
    const optionsContainer = document.getElementById('options-container');
    
    optionsContainer.innerHTML = '';
    options.forEach(option => {
        const button = document.createElement('button');
        button.className = 'option-btn';
        button.textContent = option;
        button.onclick = function() {
            document.getElementById('user-input').value = option;
            sendInput();
        };
        optionsContainer.appendChild(button);
    });
    
    optionsPanel.style.display = 'block';
}

// 更新游戏状态
function updateGameStatus() {
    fetchAPI('/api/game_status', 'GET')
        .then(data => {
            document.getElementById('current-location').textContent = data.current_location || '未知';
            document.getElementById('player-character').textContent = data.player_character || '未知';
            appState.currentLocation = data.current_location;
            appState.playerCharacter = data.player_character;
        })
        .catch(error => {
            console.error('获取游戏状态失败:', error);
        });
}

// 更新统计信息
function updateStats(responseTime) {
    document.getElementById('count-value').textContent = appState.interactionCount;
    document.getElementById('time-value').textContent = responseTime.toFixed(3) + 's';
}

// 切换历史面板
function toggleHistory() {
    const historyPanel = document.getElementById('history-panel');
    const historyContent = document.getElementById('history-content');
    
    if (historyPanel.style.display === 'none') {
        historyPanel.style.display = 'block';
        
        historyContent.innerHTML = '';
        appState.history.forEach((item, index) => {
            const historyItem = document.createElement('div');
            historyItem.className = 'history-item';
            historyItem.innerHTML = `
                <div class="user"><strong>第 ${index + 1} 轮</strong> [${item.intent}]</div>
                <div style="color: #ddd;">用户: ${escapeHtml(item.input)}</div>
                <div class="response">系统: ${escapeHtml(item.output.substring(0, 80))}...</div>
                <div style="color: #666; font-size: 0.8rem; margin-top: 0.5rem;">${item.timestamp}</div>
            `;
            historyContent.appendChild(historyItem);
        });
    } else {
        historyPanel.style.display = 'none';
    }
}

// 切换调试面板
function toggleDebug() {
    const debugPanel = document.getElementById('debug-panel');
    if (debugPanel.style.display === 'none') {
        debugPanel.style.display = 'block';
    } else {
        debugPanel.style.display = 'none';
    }
}

// 更新调试信息
function updateDebugInfo(info) {
    const debugContent = document.getElementById('debug-content');
    const debugItem = document.createElement('div');
    debugItem.className = 'debug-item';
    
    let html = '';
    for (const [key, value] of Object.entries(info)) {
        html += `<div><span class="key">${key}:</span> <span class="value">${value}</span></div>`;
    }
    
    debugItem.innerHTML = html;
    debugContent.insertBefore(debugItem, debugContent.firstChild);
    
    // 只保留最近10条
    while (debugContent.children.length > 10) {
        debugContent.removeChild(debugContent.lastChild);
    }
}

// 显示错误消息
function displayError(message) {
    const systemInfo = document.getElementById('system-info');
    const systemMessage = document.getElementById('system-message');
    systemMessage.innerHTML = '❌ ' + message;
    systemMessage.style.color = '#ff6b6b';
    systemInfo.style.display = 'block';
    setTimeout(() => {
        systemInfo.style.display = 'none';
    }, 5000);
}

// 显示成功消息
function displaySuccess(message) {
    const systemInfo = document.getElementById('system-info');
    const systemMessage = document.getElementById('system-message');
    systemMessage.innerHTML = '✓ ' + message;
    systemMessage.style.color = '#4caf50';
    systemInfo.style.display = 'block';
    setTimeout(() => {
        systemInfo.style.display = 'none';
    }, 4000);
}

// 显示警告消息
function displayWarning(message) {
    const systemInfo = document.getElementById('system-info');
    const systemMessage = document.getElementById('system-message');
    systemMessage.innerHTML = '⚠️ ' + message;
    systemMessage.style.color = '#ff9800';
    systemInfo.style.display = 'block';
    setTimeout(() => {
        systemInfo.style.display = 'none';
    }, 4000);
}

// 显示系统消息
function displaySystemInfo(message) {
    const systemInfo = document.getElementById('system-info');
    const systemMessage = document.getElementById('system-message');
    systemMessage.innerHTML = 'ℹ️ ' + message;
    systemMessage.style.color = '#2196f3';
    systemInfo.style.display = 'block';
}

// 显示系统消息（通用）
function displaySystemMessage(message) {
    displaySystemInfo(message);
}

// API调用函数
function fetchAPI(url, method, data) {
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json'
        }
    };

    if (method === 'POST') {
        options.body = JSON.stringify(data);
    }

    return fetch(url, options)
        .then(response => {
            // 接受 2xx 响应码（200, 201, 202, 204 等）
            if (response.status >= 200 && response.status < 300) {
                return response.json().catch(() => ({}));
            }
            
            // 对于错误响应，尝试解析 JSON，否则返回通用错误
            if (response.status >= 400) {
                return response.json().then(data => {
                    throw new Error(data.error || data.message || `HTTP ${response.status}: ${response.statusText}`);
                }).catch(e => {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                });
            }
            
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        });
}

// HTML转义函数
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 页面卸载时保存
window.addEventListener('beforeunload', function(e) {
    if (appState.gameActive && appState.interactionCount > 0) {
        e.preventDefault();
        e.returnValue = '';
    }
});
