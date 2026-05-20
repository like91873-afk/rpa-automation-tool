/**
 * RPA 流程设计器 - 前端应用
 */

// ==================== 状态管理 ====================
const AppState = {
    nodes: [],          // 流程节点列表
    connections: [],    // 连接列表
    variables: {},      // 全局变量
    flowId: null,       // 当前流程ID
    flowName: '新流程', // 流程名称
    selectedNodeId: null,
    nodeDefinitions: [], // 节点类型定义
    zoom: 1,
    isDragging: false,
    isConnecting: false,
    connectSource: null,
    dragOffset: { x: 0, y: 0 },
    nextNodeId: 1,
};

// ==================== API 客户端 ====================
const API = {
    baseUrl: '',

    async request(method, path, body = null) {
        const opts = {
            method,
            headers: { 'Content-Type': 'application/json' },
        };
        if (body) opts.body = JSON.stringify(body);
        const resp = await fetch(`${this.baseUrl}${path}`, opts);
        if (!resp.ok) {
            const err = await resp.json().catch(() => ({ detail: resp.statusText }));
            throw new Error(err.detail || `HTTP ${resp.status}`);
        }
        return resp.json();
    },

    getNodes() { return this.request('GET', '/api/nodes'); },
    getFlows() { return this.request('GET', '/api/flows'); },
    getFlow(id) { return this.request('GET', `/api/flows/${id}`); },
    saveFlow(flow) { return this.request('POST', '/api/flows', { flow, overwrite: true }); },
    executeFlow(id, variables = {}, debug = false) {
        return this.request('POST', `/api/flows/${id}/execute`, { flow_id: id, variables, debug });
    },
    getSampleFlow() { return this.request('GET', '/api/flows/sample'); },
};

// ==================== 工具函数 ====================
function generateId() {
    return `node-${AppState.nextNodeId++}`;
}

function generateConnId() {
    return `conn-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`;
}

function getNodeColor(category) {
    const colors = {
        'Python': '#3b82f6',
        '文件操作': '#10b981',
        '系统操作': '#f59e0b',
        '逻辑控制': '#8b5cf6',
        '网络操作': '#06b6d4',
        '数据处理': '#ec4899',
        '数据库': '#f97316',
        'Excel': '#22c55e',
        'Web': '#6366f1',
        '控制流': '#a855f7',
        '邮件操作': '#ef4444',
        '时间处理': '#14b8a6',
        'FTP操作': '#0ea5e9',
        'SFTP操作': '#0d9488',
    };
    return colors[category] || '#64748b';
}

function getNodeIcon(category) {
    const icons = {
        'Python': '🐍',
        '文件操作': '📁',
        '系统操作': '💻',
        '逻辑控制': '🔀',
        '网络操作': '🌐',
        '数据处理': '📊',
        '数据库': '🗄️',
        'Excel': '📗',
        'Web': '🌍',
        '控制流': '⏱️',
        '邮件操作': '📧',
        '时间处理': '⏰',
        'FTP操作': '📤',
        'SFTP操作': '🔒',
    };
    return icons[category] || '📦';
}

function setStatus(text) {
    document.getElementById('status-text').textContent = text;
}

function updateCounts() {
    document.getElementById('node-count').textContent = `节点: ${AppState.nodes.length}`;
    document.getElementById('connection-count').textContent = `连接: ${AppState.connections.length}`;
}

// ==================== 节点面板 ====================
async function loadNodeDefinitions() {
    try {
        const defs = await API.getNodes();
        AppState.nodeDefinitions = defs;
        renderNodePanel(defs);
        setStatus('节点定义加载完成');
    } catch (e) {
        setStatus(`加载节点定义失败: ${e.message}`);
    }
}

function renderNodePanel(definitions) {
    // 按分类分组
    const groups = {};
    for (const def of definitions) {
        const cat = def.category || '其他';
        if (!groups[cat]) groups[cat] = [];
        groups[cat].push(def);
    }

    const container = document.getElementById('node-categories');
    container.innerHTML = '';

    for (const [category, nodes] of Object.entries(groups)) {
        const catDiv = document.createElement('div');
        catDiv.className = 'node-category';
        catDiv.innerHTML = `
            <div class="category-header" data-category="${category}">
                <span class="arrow">▼</span>
                ${getNodeIcon(category)} ${category} (${nodes.length})
            </div>
            <div class="category-nodes" data-category="${category}">
                ${nodes.map(n => `
                    <div class="node-item" draggable="true" data-type="${n.type}" data-name="${n.name}" data-category="${category}">
                        <div>${n.name}</div>
                        <div class="node-type-label">${n.type}</div>
                    </div>
                `).join('')}
            </div>
        `;
        container.appendChild(catDiv);
    }

    // 分类折叠
    container.querySelectorAll('.category-header').forEach(header => {
        header.addEventListener('click', () => {
            header.classList.toggle('collapsed');
            const nodesDiv = header.nextElementSibling;
            nodesDiv.classList.toggle('collapsed');
        });
    });

    // 拖拽事件
    container.querySelectorAll('.node-item').forEach(item => {
        item.addEventListener('dragstart', (e) => {
            e.dataTransfer.setData('text/plain', JSON.stringify({
                type: item.dataset.type,
                name: item.dataset.name,
                category: item.dataset.category,
            }));
        });
    });

    // 搜索过滤
    document.getElementById('node-search').addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase();
        container.querySelectorAll('.node-item').forEach(item => {
            const name = item.dataset.name.toLowerCase();
            const type = item.dataset.type.toLowerCase();
            item.style.display = (name.includes(query) || type.includes(query)) ? '' : 'none';
        });
    });
}

// ==================== 画布与节点渲染 ====================
function renderCanvas() {
    renderNodes();
    renderConnections();
    updateCounts();
}

function renderNodes() {
    const container = document.getElementById('nodes-container');
    container.innerHTML = '';

    for (const node of AppState.nodes) {
        const def = AppState.nodeDefinitions.find(d => d.type === node.type);
        const category = def ? def.category : '其他';
        const el = document.createElement('div');
        el.className = `flow-node${node.id === AppState.selectedNodeId ? ' selected' : ''}${node.disabled ? ' disabled' : ''}`;
        el.id = `node-${node.id}`;
        el.dataset.id = node.id;
        el.dataset.category = category;
        el.style.left = `${node.position.x}px`;
        el.style.top = `${node.position.y}px`;

        const alias = node.alias || node.name || (def ? def.name : node.type);

        el.innerHTML = `
            <div class="node-port port-in" data-port="in" data-node-id="${node.id}"></div>
            <div class="node-header">
                <span class="node-icon">${getNodeIcon(category)}</span>
                <span>${alias}</span>
            </div>
            <div class="node-body">
                <span>${node.type}</span>
            </div>
            <div class="node-port port-out" data-port="out" data-node-id="${node.id}"></div>
        `;

        // 选中节点
        el.addEventListener('mousedown', (e) => {
            if (e.target.classList.contains('node-port')) return;
            selectNode(node.id);
            startDrag(e, node);
        });

        container.appendChild(el);
    }

    // 端口事件
    container.querySelectorAll('.node-port').forEach(port => {
        port.addEventListener('mousedown', (e) => {
            e.stopPropagation();
            const nodeId = port.dataset.nodeId;
            const portType = port.dataset.port;
            if (portType === 'out') {
                startConnection(nodeId, e);
            }
        });
        port.addEventListener('mouseup', (e) => {
            const nodeId = port.dataset.nodeId;
            const portType = port.dataset.port;
            if (portType === 'in' && AppState.isConnecting) {
                finishConnection(nodeId);
            }
        });
    });
}

function renderConnections() {
    const svg = document.getElementById('connections-svg');
    svg.innerHTML = '';

    for (const conn of AppState.connections) {
        const sourceNode = document.getElementById(`node-${conn.source_node_id}`);
        const targetNode = document.getElementById(`node-${conn.target_node_id}`);
        if (!sourceNode || !targetNode) continue;

        const sourceRect = sourceNode.getBoundingClientRect();
        const targetRect = targetNode.getBoundingClientRect();
        const canvasRect = document.getElementById('canvas-container').getBoundingClientRect();

        const x1 = sourceRect.right - canvasRect.left;
        const y1 = sourceRect.top + sourceRect.height / 2 - canvasRect.top;
        const x2 = targetRect.left - canvasRect.left;
        const y2 = targetRect.top + targetRect.height / 2 - canvasRect.top;

        const dx = Math.abs(x2 - x1) * 0.5;
        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.setAttribute('d', `M${x1},${y1} C${x1 + dx},${y1} ${x2 - dx},${y2} ${x2},${y2}`);
        path.setAttribute('stroke', '#4f46e5');
        path.setAttribute('stroke-width', '2');
        path.setAttribute('fill', 'none');
        path.setAttribute('data-conn-id', conn.id);
        path.addEventListener('dblclick', () => deleteConnection(conn.id));
        svg.appendChild(path);
    }
}

// ==================== 节点拖拽 ====================
function startDrag(e, node) {
    AppState.isDragging = true;
    const el = document.getElementById(`node-${node.id}`);
    AppState.dragOffset = {
        x: e.clientX - node.position.x,
        y: e.clientY - node.position.y,
    };

    function onMove(e) {
        if (!AppState.isDragging) return;
        const newX = Math.max(0, e.clientX - AppState.dragOffset.x);
        const newY = Math.max(0, e.clientY - AppState.dragOffset.y);
        node.position.x = newX;
        node.position.y = newY;
        el.style.left = `${newX}px`;
        el.style.top = `${newY}px`;
        renderConnections();
    }

    function onUp() {
        AppState.isDragging = false;
        document.removeEventListener('mousemove', onMove);
        document.removeEventListener('mouseup', onUp);
    }

    document.addEventListener('mousemove', onMove);
    document.addEventListener('mouseup', onUp);
}

// ==================== 连接管理 ====================
function startConnection(sourceNodeId, e) {
    AppState.isConnecting = true;
    AppState.connectSource = sourceNodeId;
    setStatus('拖拽到目标节点的输入端口以创建连接');

    function onMove(e) {
        // 临时线条已在SVG中，这里可以添加实时预览
    }

    function onUp(e) {
        AppState.isConnecting = false;
        AppState.connectSource = null;
        document.removeEventListener('mousemove', onMove);
        document.removeEventListener('mouseup', onUp);
        setStatus('就绪');
    }

    document.addEventListener('mousemove', onMove);
    document.addEventListener('mouseup', onUp);
}

function finishConnection(targetNodeId) {
    if (!AppState.connectSource || AppState.connectSource === targetNodeId) return;

    // 检查是否已存在
    const exists = AppState.connections.some(
        c => c.source_node_id === AppState.connectSource && c.target_node_id === targetNodeId
    );
    if (exists) {
        setStatus('连接已存在');
        return;
    }

    AppState.connections.push({
        id: generateConnId(),
        source_node_id: AppState.connectSource,
        target_node_id: targetNodeId,
    });

    AppState.isConnecting = false;
    AppState.connectSource = null;
    renderConnections();
    updateCounts();
    setStatus('连接已创建');
}

function deleteConnection(connId) {
    AppState.connections = AppState.connections.filter(c => c.id !== connId);
    renderConnections();
    updateCounts();
    setStatus('连接已删除');
}

// ==================== 节点选择与属性 ====================
function selectNode(nodeId) {
    AppState.selectedNodeId = nodeId;
    renderNodes();
    renderProperties(nodeId);
}

function deselectNode() {
    AppState.selectedNodeId = null;
    renderNodes();
    document.getElementById('properties-content').innerHTML = `
        <div class="empty-state"><p>选择一个节点查看和编辑属性</p></div>
    `;
}

function renderProperties(nodeId) {
    const node = AppState.nodes.find(n => n.id === nodeId);
    if (!node) return;

    const def = AppState.nodeDefinitions.find(d => d.type === node.type);
    const panel = document.getElementById('properties-content');

    let html = `
        <div class="prop-section-title">${def ? def.name : node.type}</div>
        <div class="prop-group">
            <label class="prop-label">节点别名</label>
            <input class="prop-input" type="text" id="prop-alias" value="${node.alias || ''}" placeholder="${def ? def.name : ''}">
        </div>
        <div class="prop-group">
            <label class="prop-label">节点ID</label>
            <input class="prop-input" type="text" value="${node.id}" disabled>
        </div>
        <div class="prop-group">
            <label class="prop-checkbox">
                <input type="checkbox" id="prop-disabled" ${node.disabled ? 'checked' : ''}>
                <span>禁用此节点</span>
            </label>
        </div>
    `;

    if (def) {
        html += `<div class="prop-section-title">参数配置</div>`;
        for (const input of def.inputs) {
            const value = node.inputs[input.name] ?? input.default ?? '';
            html += renderInputField(input, value);
        }
    }

    panel.innerHTML = html;

    // 绑定事件
    document.getElementById('prop-alias').addEventListener('input', (e) => {
        node.alias = e.target.value || null;
        renderNodes();
    });

    document.getElementById('prop-disabled').addEventListener('change', (e) => {
        node.disabled = e.target.checked;
        renderNodes();
    });

    // 参数输入事件
    panel.querySelectorAll('[data-param]').forEach(el => {
        const paramName = el.dataset.param;
        el.addEventListener('input', () => {
            if (el.type === 'checkbox') {
                node.inputs[paramName] = el.checked;
            } else if (el.type === 'number') {
                node.inputs[paramName] = parseFloat(el.value) || 0;
            } else {
                node.inputs[paramName] = el.value;
            }
        });
    });
}

function renderInputField(input, value) {
    const requiredMark = input.required ? '<span class="required">*</span>' : '';
    const desc = input.description ? `<div class="prop-description">${input.description}</div>` : '';

    if (input.type === 'dropdown' && input.options) {
        return `
            <div class="prop-group">
                <label class="prop-label">${input.label} ${requiredMark}</label>
                <select class="prop-select" data-param="${input.name}">
                    ${input.options.map(opt => `<option value="${opt}" ${opt === value ? 'selected' : ''}>${opt}</option>`).join('')}
                </select>
                ${desc}
            </div>
        `;
    } else if (input.type === 'code') {
        return `
            <div class="prop-group">
                <label class="prop-label">${input.label} ${requiredMark}</label>
                <textarea class="prop-input prop-textarea" data-param="${input.name}" rows="5">${value}</textarea>
                ${desc}
            </div>
        `;
    } else if (input.type === 'boolean') {
        return `
            <div class="prop-group">
                <label class="prop-checkbox">
                    <input type="checkbox" data-param="${input.name}" ${value ? 'checked' : ''}>
                    <span>${input.label} ${requiredMark}</span>
                </label>
                ${desc}
            </div>
        `;
    } else if (input.type === 'number') {
        return `
            <div class="prop-group">
                <label class="prop-label">${input.label} ${requiredMark}</label>
                <input class="prop-input" type="number" data-param="${input.name}" value="${value}">
                ${desc}
            </div>
        `;
    } else {
        return `
            <div class="prop-group">
                <label class="prop-label">${input.label} ${requiredMark}</label>
                <input class="prop-input" type="text" data-param="${input.name}" value="${value}">
                ${desc}
            </div>
        `;
    }
}

// ==================== 画布拖放 ====================
function initCanvasDrop() {
    const canvas = document.getElementById('canvas-container');

    canvas.addEventListener('dragover', (e) => {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'copy';
    });

    canvas.addEventListener('drop', (e) => {
        e.preventDefault();
        try {
            const data = JSON.parse(e.dataTransfer.getData('text/plain'));
            const rect = canvas.getBoundingClientRect();
            const x = e.clientX - rect.left - 80;
            const y = e.clientY - rect.top - 20;

            addNode(data.type, data.name, x, y);
        } catch (err) {
            console.error('Drop error:', err);
        }
    });

    // 点击空白处取消选中
    canvas.addEventListener('click', (e) => {
        if (e.target === canvas || e.target.id === 'nodes-container') {
            deselectNode();
        }
    });
}

function addNode(type, name, x, y) {
    const node = {
        id: generateId(),
        type: type,
        name: name,
        alias: null,
        inputs: {},
        position: { x: Math.max(0, x), y: Math.max(0, y) },
        disabled: false,
    };

    // 设置默认值
    const def = AppState.nodeDefinitions.find(d => d.type === type);
    if (def) {
        for (const input of def.inputs) {
            if (input.default !== null && input.default !== undefined) {
                node.inputs[input.name] = input.default;
            }
        }
    }

    AppState.nodes.push(node);
    renderCanvas();
    selectNode(node.id);
    setStatus(`已添加节点: ${name}`);
}

// ==================== 删除操作 ====================
function deleteSelected() {
    if (!AppState.selectedNodeId) return;
    const nodeId = AppState.selectedNodeId;

    // 删除关联连接
    AppState.connections = AppState.connections.filter(
        c => c.source_node_id !== nodeId && c.target_node_id !== nodeId
    );

    // 删除节点
    AppState.nodes = AppState.nodes.filter(n => n.id !== nodeId);

    AppState.selectedNodeId = null;
    renderCanvas();
    deselectNode();
    setStatus('节点已删除');
}

// ==================== 流程管理 ====================
function newFlow() {
    AppState.nodes = [];
    AppState.connections = [];
    AppState.variables = {};
    AppState.flowId = null;
    AppState.flowName = '新流程';
    AppState.selectedNodeId = null;
    AppState.nextNodeId = 1;
    renderCanvas();
    deselectNode();
    setStatus('新流程已创建');
}

function getFlowData() {
    return {
        id: AppState.flowId || `flow-${Date.now().toString(36)}`,
        name: AppState.flowName,
        description: '',
        version: '1.0.0',
        nodes: AppState.nodes.map(n => ({
            id: n.id,
            type: n.type,
            name: n.name,
            alias: n.alias,
            inputs: n.inputs,
            position: n.position,
            disabled: n.disabled,
        })),
        connections: AppState.connections.map(c => ({
            id: c.id,
            source_node_id: c.source_node_id,
            target_node_id: c.target_node_id,
        })),
        variables: AppState.variables,
    };
}

async function saveFlow() {
    try {
        const flow = getFlowData();
        const result = await API.saveFlow(flow);
        AppState.flowId = flow.id;
        setStatus(`流程已保存: ${flow.id}`);
        alert(`流程已保存!\nID: ${flow.id}`);
    } catch (e) {
        setStatus(`保存失败: ${e.message}`);
        alert(`保存失败: ${e.message}`);
    }
}

function loadFlowData(flow) {
    AppState.flowId = flow.id;
    AppState.flowName = flow.name;
    AppState.variables = flow.variables || {};
    AppState.nodes = (flow.nodes || []).map(n => ({
        id: n.id,
        type: n.type,
        name: n.name || '',
        alias: n.alias || null,
        inputs: n.inputs || {},
        position: n.position || { x: 0, y: 0 },
        disabled: n.disabled || false,
    }));
    AppState.connections = (flow.connections || []).map(c => ({
        id: c.id || generateConnId(),
        source_node_id: c.source_node_id,
        target_node_id: c.target_node_id,
    }));

    // 更新nextNodeId
    let maxId = 0;
    for (const n of AppState.nodes) {
        const match = n.id.match(/node-(\d+)/);
        if (match) maxId = Math.max(maxId, parseInt(match[1]));
    }
    AppState.nextNodeId = maxId + 1;

    renderCanvas();
    deselectNode();
    setStatus(`流程已加载: ${flow.name}`);
}

function showLoadModal() {
    document.getElementById('load-modal-overlay').classList.remove('hidden');
}

function hideLoadModal() {
    document.getElementById('load-modal-overlay').classList.add('hidden');
}

async function loadFromServer() {
    try {
        const result = await API.getFlows();
        const list = document.getElementById('server-flows-list');
        list.classList.remove('hidden');

        if (result.flows.length === 0) {
            list.innerHTML = '<p style="color:var(--text-secondary)">服务器上没有保存的流程</p>';
            return;
        }

        list.innerHTML = result.flows.map(f => `
            <div class="flow-item" data-flow-id="${f.id}">
                <div>
                    <div class="flow-name">${f.name}</div>
                    <div class="flow-meta">${f.id} | ${f.node_count} 节点</div>
                </div>
            </div>
        `).join('');

        list.querySelectorAll('.flow-item').forEach(item => {
            item.addEventListener('click', async () => {
                try {
                    const flow = await API.getFlow(item.dataset.flowId);
                    loadFlowData(flow);
                    hideLoadModal();
                } catch (e) {
                    alert(`加载失败: ${e.message}`);
                }
            });
        });
    } catch (e) {
        alert(`获取流程列表失败: ${e.message}`);
    }
}

function loadFromFile() {
    const input = document.getElementById('file-input');
    input.click();
    input.onchange = (e) => {
        const file = e.target.files[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = (ev) => {
            try {
                const flow = JSON.parse(ev.target.result);
                loadFlowData(flow);
                hideLoadModal();
            } catch (err) {
                alert(`文件解析失败: ${err.message}`);
            }
        };
        reader.readAsText(file);
        input.value = '';
    };
}

// ==================== 执行流程 ====================
async function runFlow() {
    if (AppState.nodes.length === 0) {
        alert('流程中没有节点，请先添加节点');
        return;
    }

    setStatus('正在执行流程...');

    try {
        // 先保存
        const flow = getFlowData();
        const saveResult = await API.saveFlow(flow);
        AppState.flowId = flow.id;

        // 执行
        const result = await API.executeFlow(flow.id, AppState.variables, true);
        showExecutionResult(result.data);
        setStatus('流程执行完成');
    } catch (e) {
        setStatus(`执行失败: ${e.message}`);
        alert(`执行失败: ${e.message}`);
    }
}

function showExecutionResult(data) {
    const modal = document.getElementById('modal-overlay');
    const title = document.getElementById('modal-title');
    const body = document.getElementById('modal-body');

    title.textContent = '执行结果';

    const statusClass = data.status === 'completed' ? 'completed' : 'failed';
    const statusText = data.status === 'completed' ? '✅ 执行成功' : '❌ 执行失败';

    let html = `
        <div>
            <span class="execution-status ${statusClass}">${statusText}</span>
            <span style="margin-left:12px;color:var(--text-secondary)">耗时: ${data.duration_ms || 0}ms</span>
        </div>
    `;

    // 变量
    if (data.variables && Object.keys(data.variables).length > 0) {
        html += `
            <div style="margin-top:16px">
                <strong>变量:</strong>
                <table class="variables-table">
                    <tr><th>变量名</th><th>值</th></tr>
                    ${Object.entries(data.variables).map(([k, v]) => `
                        <tr><td>${k}</td><td>${typeof v === 'object' ? JSON.stringify(v) : String(v)}</td></tr>
                    `).join('')}
                </table>
            </div>
        `;
    }

    // 节点日志
    if (data.node_logs && data.node_logs.length > 0) {
        html += `
            <div class="execution-log">
                <strong>节点执行日志:</strong>
                ${data.node_logs.map(log => `
                    <div class="log-entry ${log.status === 'completed' ? 'success' : 'failed'}">
                        <strong>${log.node_name || log.node_type}</strong>
                        [${log.status}]
                        ${log.error ? `<br>错误: ${log.error}` : ''}
                        ${log.duration_ms ? ` (${log.duration_ms}ms)` : ''}
                    </div>
                `).join('')}
            </div>
        `;
    }

    body.innerHTML = html;
    modal.classList.remove('hidden');
}

// ==================== 初始化 ====================
function initEventListeners() {
    document.getElementById('btn-new-flow').addEventListener('click', newFlow);
    document.getElementById('btn-save-flow').addEventListener('click', saveFlow);
    document.getElementById('btn-load-flow').addEventListener('click', showLoadModal);
    document.getElementById('btn-run-flow').addEventListener('click', runFlow);
    document.getElementById('btn-delete').addEventListener('click', deleteSelected);
    document.getElementById('btn-modal-close').addEventListener('click', () => {
        document.getElementById('modal-overlay').classList.add('hidden');
    });
    document.getElementById('btn-load-modal-close').addEventListener('click', hideLoadModal);
    document.getElementById('btn-load-server').addEventListener('click', loadFromServer);
    document.getElementById('btn-load-file').addEventListener('click', loadFromFile);

    // 键盘快捷键
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Delete' || e.key === 'Backspace') {
            if (document.activeElement.tagName !== 'INPUT' && document.activeElement.tagName !== 'TEXTAREA') {
                deleteSelected();
            }
        }
        if (e.key === 'Escape') {
            deselectNode();
            hideLoadModal();
            document.getElementById('modal-overlay').classList.add('hidden');
        }
    });
}

async function init() {
    initEventListeners();
    initCanvasDrop();
    await loadNodeDefinitions();
    setStatus('就绪 - 从左侧面板拖拽节点到画布');
}

// 启动
document.addEventListener('DOMContentLoaded', init);
