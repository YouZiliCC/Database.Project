// 管理员仪表盘前端逻辑：异步拉取列表 + 操作确认模态 + 统计数据
(function () {
    const resultEl = document.getElementById('admin-result');
    const btnUsers = document.getElementById('btn-users');
    const btnProjects = document.getElementById('btn-projects');
    const btnGroups = document.getElementById('btn-groups');

    const modal = document.getElementById('confirm-modal');
    const confirmText = document.getElementById('confirm-text');
    const btnCancel = document.getElementById('confirm-cancel');
    const btnOk = document.getElementById('confirm-ok');

    let pendingAction = null;

    // 统计元素
    const statUsers = document.getElementById('stat-users');
    const statGroups = document.getElementById('stat-groups');
    const statProjects = document.getElementById('stat-projects');

    // 格式化描述文本：截断过长文本并添加省略号
    function formatDescription(text, maxLength = 50) {
        if (!text) return '<span class="text-muted">无</span>';
        const escaped = String(text).replace(/[<>&"']/g, c => ({
            '<': '&lt;', '>': '&gt;', '&': '&amp;', '"': '&quot;', "'": '&#39;'
        }[c]));
        if (escaped.length <= maxLength) return `<span class="description">${escaped}</span>`;
        return `<span class="description" title="${escaped}">${escaped.substring(0, maxLength)}...</span>`;
    }

    function showLoading() {
        resultEl.innerHTML = '<div class="spinner" aria-label="加载中"></div>';
    }

    async function fetchJson(endpoint) {
        const res = await fetch(endpoint, { credentials: 'same-origin' });
        if (!res.ok) throw new Error('请求失败 ' + res.status);
        return await res.json();
    }

    // 加载统计数据
    async function loadStats() {
        try {
            const [users, groups, projects] = await Promise.all([
                fetchJson(btnUsers?.dataset.endpoint || '/api/users'),
                fetchJson(btnGroups?.dataset.endpoint || '/api/groups'),
                fetchJson(btnProjects?.dataset.endpoint || '/api/projects')
            ]);
            if(statUsers) statUsers.textContent = users.length || 0;
            if(statGroups) statGroups.textContent = groups.length || 0;
            if(statProjects) statProjects.textContent = projects.length || 0;
        } catch (e) {
            console.error('加载统计失败:', e);
        }
    }

    function renderUsers(users) {
        if (!Array.isArray(users) || users.length === 0) {
            resultEl.innerHTML = '<p class="empty">暂无用户</p>';
            return;
        }
        const rows = users.map(u => `
            <tr>
                <td><a href="/user/${u.uid}">${u.uname}</a></td>
                <td>${u.email ?? ''}</td>
                <td>${u.sid ?? ''}</td>
                <td>${u.is_admin ? '<span class="badge badge-admin">是</span>' : '否'}</td>
                <td>
                    <button class="btn btn-sm btn-danger" data-action="del_user" data-id="${u.uid}">删除</button>
                    <button class="btn btn-sm" data-action="reset_password" data-id="${u.uid}">重置密码</button>
                </td>
            </tr>
        `).join('');
        resultEl.innerHTML = `
            <h3>用户管理</h3>
            <div class="table-wrap">
                <table class="table">
                    <thead>
                        <tr><th>用户名</th><th>邮箱</th><th>学号</th><th>管理员</th><th>操作</th></tr>
                    </thead>
                    <tbody>${rows}</tbody>
                </table>
            </div>
        `;
    }

    function renderProjects(projects) {
        if (!Array.isArray(projects) || projects.length === 0) {
            resultEl.innerHTML = '<p class="empty">暂无项目</p>';
            return;
        }
        const rows = projects.map(p => `
            <tr>
                <td><a href="/project/${p.pid}">${p.pname}</a></td>
                <td>${formatDescription(p.pinfo, 50)}</td>
                <td>${p.gname ?? ''}</td>
                <td><code>${p.port ?? ''}</code></td>
                <td><code>${p.docker_port ?? ''}</code></td>
                <td>
                    <button class="btn btn-sm btn-danger" data-action="del_projects" data-id="${p.pid}">删除</button>
                </td>
            </tr>
        `).join('');
        resultEl.innerHTML = `
            <h3>项目管理</h3>
            <div class="table-wrap">
                <table class="table">
                    <thead>
                        <tr><th>项目名</th><th>描述</th><th>组名</th><th>端口</th><th>容器端口</th><th>操作</th></tr>
                    </thead>
                    <tbody>${rows}</tbody>
                </table>
            </div>
        `;
    }

    function renderGroups(groups) {
        if (!Array.isArray(groups) || groups.length === 0) {
            resultEl.innerHTML = '<p class="empty">暂无工作组</p>';
            return;
        }
        const rows = groups.map(g => `
            <tr>
                <td><a href="/group/${g.gid}">${g.gname}</a></td>
                <td>${formatDescription(g.ginfo, 50)}</td>
                <td>${g.users?.length ?? 0}</td>
                <td>${g.projects?.length ?? 0}</td>
                <td>
                    <button class="btn btn-sm btn-danger" data-action="del_group" data-id="${g.gid}">删除</button>
                </td>
            </tr>
        `).join('');
        resultEl.innerHTML = `
            <h3>工作组管理</h3>
            <div class="table-wrap">
                <table class="table">
                    <thead>
                        <tr><th>组名</th><th>简介</th><th>成员数</th><th>项目数</th><th>操作</th></tr>
                    </thead>
                    <tbody>${rows}</tbody>
                </table>
            </div>
        `;
    }

    async function loadUsers() {
        try {
            showLoading();
            const data = await fetchJson(btnUsers.dataset.endpoint);
            renderUsers(data);
        } catch (e) {
            resultEl.innerHTML = `<p class="error">加载失败：${e.message}</p>`;
        }
    }

    async function loadProjects() {
        try {
            showLoading();
            const data = await fetchJson(btnProjects.dataset.endpoint);
            renderProjects(data);
        } catch (e) {
            resultEl.innerHTML = `<p class="error">加载失败：${e.message}</p>`;
        }
    }

    async function loadGroups() {
        try {
            showLoading();
            const data = await fetchJson(btnGroups.dataset.endpoint);
            renderGroups(data);
        } catch (e) {
            resultEl.innerHTML = `<p class="error">加载失败：${e.message}</p>`;
        }
    }

    function openConfirm(text, action) {
        confirmText.textContent = text;
        pendingAction = action;
        modal.classList.remove('hidden');
    }
    
    function closeConfirm() {
        modal.classList.add('hidden');
        pendingAction = null;
    }

    async function post(url) {
        const token = document.querySelector('meta[name="csrf-token"]')?.content;
        const res = await fetch(url, { 
            method: 'POST', 
            credentials: 'same-origin',
            headers: token ? { 'X-CSRFToken': token } : {}
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) throw new Error(data.error || '请求失败');
        return data;
    }

    // 事件绑定
    if (btnUsers) btnUsers.addEventListener('click', loadUsers);
    if (btnProjects) btnProjects.addEventListener('click', loadProjects);
    if (btnGroups) btnGroups.addEventListener('click', loadGroups);

    resultEl?.addEventListener('click', (e) => {
        const target = e.target;
        if (!(target instanceof HTMLElement)) return;
        const action = target.dataset.action;
        const id = target.dataset.id;
        if (!action || !id) return;

        // 映射到后端路由（蓝图 admin）
        let url = '';
        switch (action) {
            case 'del_user':
                url = `/admin/del_user/${id}`;
                return openConfirm('确认删除该用户？此操作不可恢复！', () => doAction(url, loadUsers));
            case 'reset_password':
                url = `/admin/reset_password/${id}`;
                return openConfirm('确认重置该用户密码为默认密码？', () => doAction(url, loadUsers));
            case 'del_group':
                url = `/admin/del_group/${id}`;
                return openConfirm('确认删除该工作组？此操作不可恢复！', () => doAction(url, loadGroups));
            case 'del_projects':
                url = `/admin/del_projects/${id}`;
                return openConfirm('确认删除该项目？此操作不可恢复！', () => doAction(url, loadProjects));
        }
    });

    async function doAction(url, refresh) {
        try {
            btnOk.disabled = true;
            await post(url);
            closeConfirm();
            showFlash('操作成功', 'success');
            await Promise.all([refresh(), loadStats()]);
        } catch (e) {
            showFlash('操作失败：' + e.message, 'danger');
        } finally {
            btnOk.disabled = false;
        }
    }

    btnCancel?.addEventListener('click', closeConfirm);
    btnOk?.addEventListener('click', () => {
        if (pendingAction) pendingAction();
    });

    // 页面加载时获取统计数据
    loadStats();
})();