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
        if (!text) return '<span class="text-gray-400 dark:text-gray-500">无</span>';
        const escaped = String(text).replace(/[<>&"']/g, c => ({
            '<': '&lt;', '>': '&gt;', '&': '&amp;', '"': '&quot;', "'": '&#39;'
        }[c]));
        if (escaped.length <= maxLength) return `<span class="truncate" title="${escaped}">${escaped}</span>`;
        return `<span class="truncate" title="${escaped}">${escaped.substring(0, maxLength)}...</span>`;
    }

    function showLoading() {
        resultEl.innerHTML = `
            <div class="flex justify-center items-center h-64">
                <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
            </div>
        `;
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
            resultEl.innerHTML = '<div class="p-8 text-center text-gray-500 dark:text-gray-400">暂无用户</div>';
            return;
        }
        const rows = users.map(u => `
            <tr class="hover:bg-gray-50 dark:hover:bg-gray-700">
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                    <a href="/user/${u.uid}" class="text-primary-600 hover:text-primary-900 dark:text-primary-400 dark:hover:text-primary-300">${u.uname}</a>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">${u.email ?? ''}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">${u.sid ?? ''}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                    ${u.is_admin ? '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200">是</span>' : '否'}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                    ${u.is_teacher ? '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200">是</span>' : '否'}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <button class="text-red-600 hover:text-red-900 dark:text-red-400 dark:hover:text-red-300 mr-3" data-action="del_user" data-id="${u.uid}">删除</button>
                    <button class="text-indigo-600 hover:text-indigo-900 dark:text-indigo-400 dark:hover:text-indigo-300" data-action="reset_password" data-id="${u.uid}">重置密码</button>
                </td>
            </tr>
        `).join('');
        resultEl.innerHTML = `
            <div class="px-4 py-5 sm:px-6 border-b border-gray-200 dark:border-gray-700">
                <h3 class="text-lg leading-6 font-medium text-gray-900 dark:text-white">用户管理</h3>
            </div>
            <div class="overflow-x-auto">
                <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                    <thead class="bg-gray-50 dark:bg-gray-700">
                        <tr>
                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">用户名</th>
                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">邮箱</th>
                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">学号</th>
                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Admin</th>
                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Teacher</th>
                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">操作</th>
                        </tr>
                    </thead>
                    <tbody class="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                        ${rows}
                    </tbody>
                </table>
            </div>
        `;
    }

    function renderProjects(projects) {
        if (!Array.isArray(projects) || projects.length === 0) {
            resultEl.innerHTML = '<div class="p-8 text-center text-gray-500 dark:text-gray-400">暂无项目</div>';
            return;
        }
        const rows = projects.map(p => `
            <tr class="hover:bg-gray-50 dark:hover:bg-gray-700">
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                    <a href="/project/${p.pid}" class="text-primary-600 hover:text-primary-900 dark:text-primary-400 dark:hover:text-primary-300">${p.pname}</a>
                </td>
                <td class="px-6 py-4 text-sm text-gray-500 dark:text-gray-400 max-w-xs truncate">${formatDescription(p.pinfo, 50)}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">${p.gname ?? ''}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400"><code class="bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded text-xs">${p.port ?? ''}</code></td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400"><code class="bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded text-xs">${p.docker_port ?? ''}</code></td>
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <button class="text-red-600 hover:text-red-900 dark:text-red-400 dark:hover:text-red-300" data-action="del_projects" data-id="${p.pid}">删除</button>
                </td>
            </tr>
        `).join('');
        resultEl.innerHTML = `
            <div class="px-4 py-5 sm:px-6 border-b border-gray-200 dark:border-gray-700">
                <h3 class="text-lg leading-6 font-medium text-gray-900 dark:text-white">项目管理</h3>
            </div>
            <div class="overflow-x-auto">
                <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                    <thead class="bg-gray-50 dark:bg-gray-700">
                        <tr>
                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">项目名</th>
                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">简介</th>
                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">组名</th>
                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">端口</th>
                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">容器端口</th>
                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">操作</th>
                        </tr>
                    </thead>
                    <tbody class="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                        ${rows}
                    </tbody>
                </table>
            </div>
        `;
    }

    function renderGroups(groups) {
        if (!Array.isArray(groups) || groups.length === 0) {
            resultEl.innerHTML = '<div class="p-8 text-center text-gray-500 dark:text-gray-400">暂无工作组</div>';
            return;
        }
        const rows = groups.map(g => `
            <tr class="hover:bg-gray-50 dark:hover:bg-gray-700">
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                    <a href="/group/${g.gid}" class="text-primary-600 hover:text-primary-900 dark:text-primary-400 dark:hover:text-primary-300">${g.gname}</a>
                </td>
                <td class="px-6 py-4 text-sm text-gray-500 dark:text-gray-400 max-w-xs truncate">${formatDescription(g.ginfo, 50)}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">${g.users?.length ?? 0}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">${g.projects?.length ?? 0}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <button class="text-red-600 hover:text-red-900 dark:text-red-400 dark:hover:text-red-300" data-action="del_group" data-id="${g.gid}">删除</button>
                </td>
            </tr>
        `).join('');
        resultEl.innerHTML = `
            <div class="px-4 py-5 sm:px-6 border-b border-gray-200 dark:border-gray-700">
                <h3 class="text-lg leading-6 font-medium text-gray-900 dark:text-white">工作组管理</h3>
            </div>
            <div class="overflow-x-auto">
                <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                    <thead class="bg-gray-50 dark:bg-gray-700">
                        <tr>
                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">组名</th>
                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">简介</th>
                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">成员数</th>
                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">项目数</th>
                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">操作</th>
                        </tr>
                    </thead>
                    <tbody class="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                        ${rows}
                    </tbody>
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
            resultEl.innerHTML = `<div class="p-4 text-red-600 bg-red-50 dark:bg-red-900/20 dark:text-red-400 rounded-md">加载失败：${e.message}</div>`;
        }
    }

    async function loadProjects() {
        try {
            showLoading();
            const data = await fetchJson(btnProjects.dataset.endpoint);
            renderProjects(data);
        } catch (e) {
            resultEl.innerHTML = `<div class="p-4 text-red-600 bg-red-50 dark:bg-red-900/20 dark:text-red-400 rounded-md">加载失败：${e.message}</div>`;
        }
    }

    async function loadGroups() {
        try {
            showLoading();
            const data = await fetchJson(btnGroups.dataset.endpoint);
            renderGroups(data);
        } catch (e) {
            resultEl.innerHTML = `<div class="p-4 text-red-600 bg-red-50 dark:bg-red-900/20 dark:text-red-400 rounded-md">加载失败：${e.message}</div>`;
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