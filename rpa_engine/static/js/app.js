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

// ==================== 调度管理模块 ====================

const SchedulerAPI = {
    listSchedules(status = null) {
        const query = status ? `?status=${status}` : '';
        return API.request('GET', `/api/schedules${query}`);
    },
    getSchedule(id) { return API.request('GET', `/api/schedules/${id}`); },
    createSchedule(data) { return API.request('POST', '/api/schedules', data); },
    updateSchedule(id, data) { return API.request('PUT', `/api/schedules/${id}`, data); },
    deleteSchedule(id) { return API.request('DELETE', `/api/schedules/${id}`); },
    pauseSchedule(id) { return API.request('POST', `/api/schedules/${id}/pause`); },
    resumeSchedule(id) { return API.request('POST', `/api/schedules/${id}/resume`); },
    triggerSchedule(id) { return API.request('POST', `/api/schedules/${id}/trigger`, {}); },
    startScheduler() { return API.request('POST', '/api/scheduler/start'); },
    stopScheduler() { return API.request('POST', '/api/scheduler/stop'); },
    getSchedulerStatus() { return API.request('GET', '/api/scheduler/status'); },
    getHistory(scheduleId = null, limit = 100) {
        const params = new URLSearchParams();
        if (scheduleId) params.set('schedule_id', scheduleId);
        params.set('limit', limit);
        return API.request('GET', `/api/history?${params}`);
    },
    clearHistory(scheduleId = null) {
        const query = scheduleId ? `?schedule_id=${scheduleId}` : '';
        return API.request('DELETE', `/api/history${query}`);
    },
};

// Tab切换
function initTabs() {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const tab = btn.dataset.tab;

            // 切换按钮状态
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            // 切换内容
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            document.getElementById(`tab-${tab}`).classList.add('active');

            // 加载对应数据
            if (tab === 'scheduler') loadSchedules();
            if (tab === 'history') loadHistory();
        });
    });
}

// 调度列表
async function loadSchedules() {
    try {
        const { schedules, total } = await SchedulerAPI.listSchedules();
        const container = document.getElementById('schedule-list');

        if (total === 0) {
            container.innerHTML = '<div class="empty-state"><p>暂无调度任务，点击"新建调度"创建</p></div>';
            return;
        }

        container.innerHTML = schedules.map(s => `
            <div class="schedule-card" data-id="${s.id}">
                <div class="schedule-card-header">
                    <div>
                        <h4>${escHtml(s.name)}</h4>
                        ${s.description ? `<small style="color:var(--text-secondary)">${escHtml(s.description)}</small>` : ''}
                    </div>
                    <div class="schedule-card-actions">
                        <span class="tag-${s.trigger_type} schedule-tag">${getTriggerLabel(s.trigger_type)}</span>
                        <span class="schedule-status-badge status-${s.status}">${getStatusLabel(s.status)}</span>
                    </div>
                </div>
                <div class="schedule-card-meta">
                    <span>📄 流程: ${escHtml(s.flow_id)}</span>
                    ${s.cron_expression ? `<span>⏰ Cron: <code>${escHtml(s.cron_expression)}</code></span>` : ''}
                    ${s.interval_seconds ? `<span>🔁 间隔: ${s.interval_seconds}秒</span>` : ''}
                    ${s.trigger_type === 'webhook' ? `<span>🔗 <span class="webhook-url">POST /api/webhooks/${s.webhook_token}</span></span>` : ''}
                    ${s.last_run_at ? `<span>📅 上次: ${formatTime(s.last_run_at)}</span>` : ''}
                    ${s.next_run_at ? `<span>⏭ 下次: ${formatTime(s.next_run_at)}</span>` : ''}
                </div>
                <div class="schedule-stats">
                    <span>执行: ${s.run_count}次</span>
                    <span class="stat-success">✓ 成功: ${s.success_count}</span>
                    <span class="stat-fail">✗ 失败: ${s.fail_count}</span>
                </div>
                <div class="schedule-card-actions" style="margin-top: 10px;">
                    ${s.status === 'active' ?
                        `<button class="btn btn-sm btn-secondary" onclick="pauseSchedule('${s.id}')">⏸ 暂停</button>` :
                        `<button class="btn btn-sm btn-success" onclick="resumeSchedule('${s.id}')">▶ 恢复</button>`
                    }
                    <button class="btn btn-sm btn-primary" onclick="triggerSchedule('${s.id}')">▶ 手动执行</button>
                    <button class="btn btn-sm btn-secondary" onclick="viewScheduleHistory('${s.id}')">📋 历史</button>
                    <button class="btn btn-sm btn-danger" onclick="deleteSchedule('${s.id}')">🗑 删除</button>
                </div>
            </div>
        `).join('');

        // 更新历史过滤器
        updateHistoryFilter(schedules);

    } catch (e) {
        console.error('加载调度列表失败:', e);
    }
}

async function pauseSchedule(id) {
    try {
        await SchedulerAPI.pauseSchedule(id);
        loadSchedules();
    } catch (e) { alert('暂停失败: ' + e.message); }
}

async function resumeSchedule(id) {
    try {
        await SchedulerAPI.resumeSchedule(id);
        loadSchedules();
    } catch (e) { alert('恢复失败: ' + e.message); }
}

async function triggerSchedule(id) {
    try {
        await SchedulerAPI.triggerSchedule(id);
        alert('任务已触发执行');
        loadSchedules();
    } catch (e) { alert('触发失败: ' + e.message); }
}

async function deleteSchedule(id) {
    if (!confirm('确定删除此调度任务？')) return;
    try {
        await SchedulerAPI.deleteSchedule(id);
        loadSchedules();
    } catch (e) { alert('删除失败: ' + e.message); }
}

function viewScheduleHistory(scheduleId) {
    // 切换到历史tab并过滤
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelector('[data-tab="history"]').classList.add('active');
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    document.getElementById('tab-history').classList.add('active');

    const filter = document.getElementById('history-filter');
    filter.value = scheduleId;
    loadHistory();
}

// 新建调度弹窗
function showScheduleModal() {
    document.getElementById('schedule-modal-overlay').classList.remove('hidden');
    document.getElementById('schedule-modal-title').textContent = '新建调度任务';

    // 加载流程列表到下拉框
    loadFlowsForSchedule();

    // 重置表单
    document.getElementById('schedule-form').reset();
    document.getElementById('sched-max-retries').value = '0';
    document.getElementById('sched-retry-delay').value = '60';
    document.getElementById('sched-timeout').value = '3600';
    showTriggerConfig('cron');
}

function hideScheduleModal() {
    document.getElementById('schedule-modal-overlay').classList.add('hidden');
}

async function loadFlowsForSchedule() {
    try {
        const { flows } = await API.getFlows();
        const select = document.getElementById('sched-flow-id');
        select.innerHTML = '<option value="">选择流程...</option>' +
            flows.map(f => `<option value="${f.id}">${escHtml(f.name)} (${f.node_count}节点)</option>`).join('');

        // 也更新历史过滤器
        const filter = document.getElementById('history-filter');
        filter.innerHTML = '<option value="">全部任务</option>' +
            flows.map(f => `<option value="${f.id}">${escHtml(f.name)}</option>`).join('');
    } catch (e) {
        console.error('加载流程列表失败:', e);
    }
}

function showTriggerConfig(type) {
    document.querySelectorAll('.trigger-config').forEach(el => el.classList.add('hidden'));
    const config = document.getElementById(`trigger-config-${type}`);
    if (config) config.classList.remove('hidden');
}

async function submitSchedule(e) {
    e.preventDefault();

    const triggerType = document.getElementById('sched-trigger-type').value;
    const data = {
        name: document.getElementById('sched-name').value,
        description: document.getElementById('sched-description').value || null,
        flow_id: document.getElementById('sched-flow-id').value,
        trigger_type: triggerType,
        max_retries: parseInt(document.getElementById('sched-max-retries').value) || 0,
        retry_delay_seconds: parseInt(document.getElementById('sched-retry-delay').value) || 60,
        timeout: parseInt(document.getElementById('sched-timeout').value) || 3600,
    };

    // 解析初始变量
    const varsStr = document.getElementById('sched-variables').value.trim();
    if (varsStr) {
        try { data.initial_variables = JSON.parse(varsStr); }
        catch { alert('初始变量JSON格式错误'); return; }
    } else {
        data.initial_variables = {};
    }

    // 根据触发类型填充配置
    if (triggerType === 'cron') {
        data.cron_expression = document.getElementById('sched-cron').value;
        if (!data.cron_expression) { alert('请输入Cron表达式'); return; }
    } else if (triggerType === 'interval') {
        data.interval_seconds = parseInt(document.getElementById('sched-interval').value);
        if (!data.interval_seconds || data.interval_seconds <= 0) { alert('请输入有效的间隔秒数'); return; }
    } else if (triggerType === 'once') {
        const runAt = document.getElementById('sched-run-at').value;
        if (!runAt) { alert('请选择执行时间'); return; }
        data.run_at = new Date(runAt).toISOString();
    } else if (triggerType === 'webhook') {
        data.webhook_secret = document.getElementById('sched-webhook-secret').value || null;
    } else if (triggerType === 'file_watch') {
        data.watch_path = document.getElementById('sched-watch-path').value;
        if (!data.watch_path) { alert('请输入监控路径'); return; }
        data.watch_pattern = document.getElementById('sched-watch-pattern').value || '*';
        data.watch_recursive = document.getElementById('sched-watch-recursive').checked;
        const eventsSelect = document.getElementById('sched-watch-events');
        data.watch_events = Array.from(eventsSelect.selectedOptions).map(o => o.value);
        if (data.watch_events.length === 0) data.watch_events = ['created'];
    }

    try {
        await SchedulerAPI.createSchedule(data);
        hideScheduleModal();
        loadSchedules();
    } catch (e) {
        alert('创建失败: ' + e.message);
    }
}

// 执行历史
async function loadHistory() {
    try {
        const filter = document.getElementById('history-filter').value;
        const { history, total } = await SchedulerAPI.getHistory(filter || null, 100);
        const container = document.getElementById('history-list');

        if (total === 0) {
            container.innerHTML = '<div class="empty-state"><p>暂无执行记录</p></div>';
            return;
        }

        container.innerHTML = history.reverse().map(h => `
            <div class="history-card">
                <div class="history-card-header">
                    <h4>任务: ${escHtml(h.schedule_id)}</h4>
                    <span class="schedule-tag tag-${h.trigger_type}">${getTriggerLabel(h.trigger_type)}</span>
                </div>
                <div class="history-card-detail">
                    <span>状态: <span class="status-badge ${h.status}">${h.status}</span></span>
                    <span>开始: ${formatTime(h.started_at)}</span>
                    ${h.completed_at ? `<span>完成: ${formatTime(h.completed_at)}</span>` : ''}
                    ${h.duration_ms !== null ? `<span>耗时: ${h.duration_ms}ms</span>` : ''}
                    ${h.retry_count > 0 ? `<span>重试: ${h.retry_count}次</span>` : ''}
                    ${h.trigger_info ? `<span>触发: ${escHtml(h.trigger_info)}</span>` : ''}
                </div>
                ${h.error ? `<div class="history-error">❌ ${escHtml(h.error)}</div>` : ''}
            </div>
        `).join('');

    } catch (e) {
        console.error('加载历史失败:', e);
    }
}

function updateHistoryFilter(schedules) {
    // 仅更新调度任务下拉（流程下拉在loadFlowsForSchedule中处理）
}

async function refreshSchedulerStatus() {
    try {
        const status = await SchedulerAPI.getSchedulerStatus();
        const statusEl = document.getElementById('scheduler-status');
        const infoEl = document.getElementById('scheduler-info');
        const startBtn = document.getElementById('btn-start-scheduler');
        const stopBtn = document.getElementById('btn-stop-scheduler');

        if (status.is_running) {
            statusEl.textContent = '● 运行中';
            statusEl.classList.add('running');
            infoEl.textContent = `调度器: 运行中 | 任务: ${status.active}/${status.total_schedules}`;
            startBtn.classList.add('hidden');
            stopBtn.classList.remove('hidden');
        } else {
            statusEl.textContent = '● 未启动';
            statusEl.classList.remove('running');
            infoEl.textContent = '调度器: 未启动';
            startBtn.classList.remove('hidden');
            stopBtn.classList.add('hidden');
        }
    } catch (e) {
        console.error('获取调度器状态失败:', e);
    }
}

// 工具函数
function getTriggerLabel(type) {
    const labels = {
        cron: '⏰ Cron', interval: '🔁 间隔', once: '🔂 单次',
        webhook: '🔗 Webhook', file_watch: '📁 文件监控', manual: '🖱 手动'
    };
    return labels[type] || type;
}

function getStatusLabel(status) {
    const labels = { active: '运行中', paused: '已暂停', completed: '已完成', failed: '失败' };
    return labels[status] || status;
}

function formatTime(isoStr) {
    if (!isoStr) return '-';
    try {
        const d = new Date(isoStr);
        return d.toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' });
    } catch { return isoStr; }
}

function escHtml(str) {
    if (!str) return '';
    return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

// 调度管理事件绑定
function initSchedulerEvents() {
    // Tab切换
    initTabs();

    // 新建调度
    document.getElementById('btn-add-schedule').addEventListener('click', showScheduleModal);
    document.getElementById('btn-schedule-modal-close').addEventListener('click', hideScheduleModal);
    document.getElementById('btn-schedule-cancel').addEventListener('click', hideScheduleModal);
    document.getElementById('schedule-form').addEventListener('submit', submitSchedule);

    // 触发类型切换
    document.getElementById('sched-trigger-type').addEventListener('change', (e) => {
        showTriggerConfig(e.target.value);
    });

    // Cron预设
    document.getElementById('cron-presets').addEventListener('change', (e) => {
        if (e.target.value) document.getElementById('sched-cron').value = e.target.value;
    });

    // 调度器控制
    document.getElementById('btn-start-scheduler').addEventListener('click', async () => {
        try {
            await SchedulerAPI.startScheduler();
            refreshSchedulerStatus();
        } catch (e) { alert('启动失败: ' + e.message); }
    });

    document.getElementById('btn-stop-scheduler').addEventListener('click', async () => {
        try {
            await SchedulerAPI.stopScheduler();
            refreshSchedulerStatus();
        } catch (e) { alert('停止失败: ' + e.message); }
    });

    // 历史
    document.getElementById('btn-refresh-history').addEventListener('click', loadHistory);
    document.getElementById('btn-clear-history').addEventListener('click', async () => {
        if (!confirm('确定清空所有执行历史？')) return;
        await SchedulerAPI.clearHistory();
        loadHistory();
    });
    document.getElementById('history-filter').addEventListener('change', loadHistory);

    // 定期刷新调度器状态
    refreshSchedulerStatus();
    setInterval(refreshSchedulerStatus, 30000);
}

// 修改init函数以包含调度器初始化
const _originalInit = typeof init === 'function' ? init : null;

// 拦截init，在原始init之后追加调度器事件绑定
document.addEventListener('DOMContentLoaded', () => {
    // 延迟执行以确保原有初始化完成
    setTimeout(() => {
        initSchedulerEvents();
    }, 100);
});
