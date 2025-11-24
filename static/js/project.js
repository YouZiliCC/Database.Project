(function(){
    // 检查是否需要登录并重定向
    function checkAuthAndRedirect(status) {
        if(status === 401) {
            showFlash('请先登录', 'warning');
            setTimeout(() => {
                window.location.href = `/auth/login?next=${encodeURIComponent(window.location.pathname)}`;
            }, 1000);
            return true;
        }
        return false;
    }

    // helper POST with CSRF
    async function post(url, data=null){
        const token = document.querySelector('meta[name="csrf-token"]')?.content;
        const headers = { 
            'X-CSRFToken': token,
            'Accept': 'application/json'  // 明确表示这是 AJAX 请求
        };
        if(data) headers['Content-Type'] = 'application/json';
        const res = await fetch(url, {
            method: 'POST',
            headers: headers,
            body: data ? JSON.stringify(data) : undefined,
            credentials: 'same-origin'
        });
        
        // 处理未登录情况 (401 Unauthorized)
        if(checkAuthAndRedirect(res.status)) {
            throw new Error('需要登录');
        }
        
        const json = await res.json().catch(()=>({}));
        if(!res.ok) throw new Error(json.message || `请求失败 (${res.status})`);
        return json;
    }

    // Toggle comment panel (Modal)
    window.toggleCommentPanel = function(){
        const panel = document.getElementById('comment-panel');
        if(!panel) return;
        
        const backdrop = document.getElementById('modal-backdrop');
        const content = document.getElementById('modal-content');

        if(panel.style.display === 'none' || !panel.style.display){
            // Open
            panel.style.display = 'block';
            // Trigger reflow
            panel.offsetHeight; 
            
            if(backdrop) {
                backdrop.classList.remove('opacity-0');
                backdrop.classList.add('opacity-100');
            }
            if(content) {
                content.classList.remove('opacity-0', 'translate-y-4', 'sm:translate-y-0', 'sm:scale-95');
                content.classList.add('opacity-100', 'translate-y-0', 'sm:scale-100');
            }
        }else{
            // Close
            if(backdrop) {
                backdrop.classList.remove('opacity-100');
                backdrop.classList.add('opacity-0');
            }
            if(content) {
                content.classList.remove('opacity-100', 'translate-y-0', 'sm:scale-100');
                content.classList.add('opacity-0', 'translate-y-4', 'sm:translate-y-0', 'sm:scale-95');
            }
            
            setTimeout(() => {
                panel.style.display = 'none';
            }, 300);
        }
    }

    window.toggleProjectStar = async function(pid){
        try{
            const res = await post(`/project/${pid}/star`);
            const btn = document.querySelector('#project-star-btn');
            const count = document.querySelector('#project-star-count');
            
            if(res.starred){
                // Switch to Starred state
                btn.classList.remove('bg-white', 'text-gray-400', 'hover:text-yellow-400', 'dark:bg-gray-800', 'dark:text-gray-500', 'dark:hover:text-yellow-400');
                btn.classList.add('bg-yellow-400', 'text-white', 'hover:bg-yellow-500');
            }else{
                // Switch to Unstarred state
                btn.classList.remove('bg-yellow-400', 'text-white', 'hover:bg-yellow-500');
                btn.classList.add('bg-white', 'text-gray-400', 'hover:text-yellow-400', 'dark:bg-gray-800', 'dark:text-gray-500', 'dark:hover:text-yellow-400');
            }
            
            if(count) count.textContent = res.star_count || 0;
            showFlash(res.message || '操作成功', 'success');
        }catch(e){ 
            // 如果是"需要登录"错误，不显示消息（已在post函数中处理）
            if(e.message !== '需要登录') {
                showFlash(e.message, 'danger');
            }
        }
    }

    window.postProjectComment = async function(pid){
        const textarea = document.querySelector('#comment-input');
        if(!textarea) return showFlash('找不到评论输入框', 'warning');
        const content = (textarea.value || '').trim();
        if(!content) return showFlash('评论不能为空', 'warning');
        try{
            const res = await post(`/project/${pid}/comment`, { content });
            if(res && res.comment){
                // 刷新页面以显示新评论（确保教师评论排序正确）
                window.location.reload();
            }
        }catch(e){ 
            if(e.message !== '需要登录') {
                showFlash(e.message, 'danger');
            }
        }
    }

    // Edit comment
    window.editComment = function(pcid, pid){
        const commentItem = document.querySelector(`[data-comment-id="${pcid}"]`);
        if(!commentItem) return;
        
        const commentBody = commentItem.querySelector('.comment-body');
        const originalContent = commentBody.getAttribute('data-original-content') || commentBody.textContent;
        
        // 创建编辑界面
        const editHtml = `
            <div class="comment-edit-form mt-3 animate-fade-in-up">
                <div class="relative rounded-md shadow-sm">
                    <textarea class="comment-edit-textarea shadow-sm focus:ring-primary-500 focus:border-primary-500 block w-full sm:text-sm border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white p-3 resize-none transition-all duration-200" rows="3">${escapeHtml(originalContent)}</textarea>
                </div>
                <div class="comment-edit-actions flex space-x-3 justify-end mt-3">
                    <button class="inline-flex items-center px-3 py-1.5 border border-gray-300 shadow-sm text-xs font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 dark:bg-gray-700 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-600 transition-colors duration-200" onclick="cancelEditComment('${pcid}')">
                        取消
                    </button>
                    <button class="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 shadow-sm transition-colors duration-200" onclick="saveComment('${pcid}', '${pid}')">
                        保存
                    </button>
                </div>
            </div>
        `;
        
        commentBody.style.display = 'none';
        commentBody.insertAdjacentHTML('afterend', editHtml);
    }

    // Save edited comment
    window.saveComment = async function(pcid, pid){
        const commentItem = document.querySelector(`[data-comment-id="${pcid}"]`);
        if(!commentItem) return;
        
        const textarea = commentItem.querySelector('.comment-edit-textarea');
        const newContent = (textarea?.value || '').trim();
        
        if(!newContent) return showFlash('评论内容不能为空', 'warning');
        
        try{
            const token = document.querySelector('meta[name="csrf-token"]')?.content;
            const res = await fetch(`/project/${pid}/comment/${pcid}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': token,
                    'Accept': 'application/json'
                },
                body: JSON.stringify({ content: newContent }),
                credentials: 'same-origin'
            });
            
            // 处理未登录情况
            if(checkAuthAndRedirect(res.status)) return;
            
            const data = await res.json();
            if(!res.ok) throw new Error(data.message || '更新失败');
            
            // 刷新页面
            window.location.reload();
        }catch(e){ 
            if(e.message !== '需要登录') {
                showFlash(e.message, 'danger');
            }
        }
    }

    // Cancel edit
    window.cancelEditComment = function(pcid){
        const commentItem = document.querySelector(`[data-comment-id="${pcid}"]`);
        if(!commentItem) return;
        
        const editForm = commentItem.querySelector('.comment-edit-form');
        const commentBody = commentItem.querySelector('.comment-body');
        
        if(editForm) editForm.remove();
        if(commentBody) commentBody.style.display = '';
    }

    // Delete comment
    window.deleteComment = async function(pcid, pid){
        if(!confirm('确定要删除这条评论吗？')) return;
        
        try{
            const token = document.querySelector('meta[name="csrf-token"]')?.content;
            const res = await fetch(`/project/${pid}/comment/${pcid}`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': token,
                    'Accept': 'application/json'
                },
                credentials: 'same-origin'
            });
            
            // 处理未登录情况
            if(checkAuthAndRedirect(res.status)) return;
            
            const data = await res.json();
            if(!res.ok) throw new Error(data.message || '删除失败');
            
            showFlash(data.message || '评论已删除', 'success');
            // 刷新页面
            setTimeout(() => window.location.reload(), 500);
        }catch(e){ 
            if(e.message !== '需要登录') {
                showFlash(e.message, 'danger');
            }
        }
    }

    function escapeHtml(unsafe) {
        return unsafe
             .replace(/&/g, "&amp;")
             .replace(/</g, "&lt;")
             .replace(/>/g, "&gt;")
             .replace(/\"/g, "&quot;")
             .replace(/\'/g, "&#039;");
    }

    // Toggle sidebar visibility (responsive)
    window.toggleSidebar = function(){
        const sidebar = document.getElementById('project-sidebar');
        const toggleIcon = document.getElementById('sidebar-toggle-icon');
        if(!sidebar) return;
        
        if(sidebar.classList.contains('sidebar-open')){
            sidebar.classList.remove('sidebar-open');
            if(toggleIcon) toggleIcon.textContent = '📋';
        }else{
            sidebar.classList.add('sidebar-open');
            if(toggleIcon) toggleIcon.textContent = '✕';
        }
    }

    // Close sidebar when clicking outside on mobile
    document.addEventListener('click', function(e){
        if(window.innerWidth > 1600) return; // Only on mobile
        
        const sidebar = document.getElementById('project-sidebar');
        const toggleBtn = document.getElementById('sidebar-toggle');
        
        if(!sidebar || !sidebar.classList.contains('sidebar-open')) return;
        
        // If click is outside sidebar and toggle button, close sidebar
        if(!sidebar.contains(e.target) && !toggleBtn.contains(e.target)){
            sidebar.classList.remove('sidebar-open');
            const toggleIcon = document.getElementById('sidebar-toggle-icon');
            if(toggleIcon) toggleIcon.textContent = '📋';
        }
    });

    // ==================== Docker 状态管理 ====================
    
    // 更新状态徽章显示和按钮状态
    function updateStatusBadge(status) {
        const el = document.getElementById('project-status');
        if(!el) return;
        
        el.className = 'status-badge';
        
        // 获取所有按钮
        const startBtn = document.getElementById('project-start-btn');
        const stopBtn = document.getElementById('project-stop-btn');
        const removeBtn = document.getElementById('project-remove-btn');
        const terminalBtn = document.getElementById('terminal-btn');
        
        if(status === 'running'){
            el.textContent = '运行中';
            el.classList.add('badge-success');
            // 运行中：禁用启动，启用停止和删除，显示 WebShell
            if(startBtn) startBtn.disabled = true;
            if(stopBtn) stopBtn.disabled = false;
            if(removeBtn) removeBtn.disabled = false;
            if(terminalBtn) terminalBtn.style.display = 'flex';
        }else if(status === 'starting'){
            el.textContent = '启动中';
            el.classList.add('badge-warning');
            // 启动中：禁用所有按钮，隐藏 WebShell
            if(startBtn) startBtn.disabled = true;
            if(stopBtn) stopBtn.disabled = true;
            if(removeBtn) removeBtn.disabled = true;
            if(terminalBtn) terminalBtn.style.display = 'none';
        }else{
            el.textContent = '已停止';
            el.classList.add('badge-secondary');
            // 已停止：启用启动，禁用停止，启用删除，隐藏 WebShell
            if(startBtn) startBtn.disabled = false;
            if(stopBtn) stopBtn.disabled = true;
            if(removeBtn) removeBtn.disabled = false;
            if(terminalBtn) terminalBtn.style.display = 'none';
        }
    }

    // 获取项目 Docker 状态
    async function fetchProjectStatus(pid){
        try{
            const res = await fetch(`/project/${pid}/docker/status`, {
                headers: { 'Accept': 'application/json' }
            });
            
            if(res.status === 401){
                checkAuthAndRedirect(401);
                return null;
            }
            
            const data = await res.json().catch(()=>({}));
            if(res.ok && data.status){
                updateStatusBadge(data.status);
                return data.status;
            }
        }catch(e){
            console.error('获取状态失败:', e);
        }
        return null;
    }

    // 启动/重启项目
    window.startProject = async function(pid){
        const startBtn = document.getElementById('project-start-btn');
        const stopBtn = document.getElementById('project-stop-btn');
        const removeBtn = document.getElementById('project-remove-btn');
        
        // 禁用所有按钮
        if(startBtn) startBtn.disabled = true;
        if(stopBtn) stopBtn.disabled = true;
        if(removeBtn) removeBtn.disabled = true;
        
        try{
            updateStatusBadge('starting');
            const res = await post(`/project/${pid}/start`);
            
            if(res.status) updateStatusBadge(res.status);
            showFlash(res.message || '启动已开始', 'info');

            // 轮询状态直到完成（最多2分钟）
            const startTime = Date.now();
            const timeout = 120000; // 2分钟
            
            while(Date.now() - startTime < timeout){
                await new Promise(r => setTimeout(r, 3000)); // 每3秒检查一次
                const status = await fetchProjectStatus(pid);
                
                if(status && status !== 'starting'){
                    // 启动完成
                    if(status === 'running'){
                        showFlash('容器启动成功！', 'success');
                    }else{
                        showFlash('容器未能启动，请查看日志', 'warning');
                    }
                    break;
                }
            }
        }catch(e){
            if(e.message !== '需要登录'){
                showFlash(e.message, 'danger');
            }
            // 出错时恢复按钮状态
            if(startBtn) startBtn.disabled = false;
            if(removeBtn) removeBtn.disabled = false;
        }
    }

    // 停止项目容器
    window.stopProject = async function(pid){
        const startBtn = document.getElementById('project-start-btn');
        const stopBtn = document.getElementById('project-stop-btn');
        const removeBtn = document.getElementById('project-remove-btn');
        
        // 临时禁用按钮
        if(stopBtn) stopBtn.disabled = true;
        
        try{
            const res = await post(`/project/${pid}/docker/stop`);
            
            if(res.status) updateStatusBadge(res.status);
            showFlash(res.message || '容器已停止', 'success');
        }catch(e){
            if(e.message !== '需要登录'){
                showFlash(e.message, 'danger');
            }
            // 出错时恢复按钮（假设仍在运行）
            if(stopBtn) stopBtn.disabled = false;
        }
    }

    // 删除项目容器
    window.removeProject = async function(pid){
        if(!confirm('⚠️ 确定要删除容器吗？\n\n此操作将永久删除容器及其数据，无法恢复！')){
            return;
        }

        const startBtn = document.getElementById('project-start-btn');
        const stopBtn = document.getElementById('project-stop-btn');
        const removeBtn = document.getElementById('project-remove-btn');
        
        // 临时禁用所有按钮
        if(startBtn) startBtn.disabled = true;
        if(stopBtn) stopBtn.disabled = true;
        if(removeBtn) removeBtn.disabled = true;
        
        try{
            const res = await post(`/project/${pid}/docker/remove`);
            
            if(res.status) updateStatusBadge(res.status);
            showFlash(res.message || '容器已删除', 'success');
        }catch(e){
            if(e.message !== '需要登录'){
                showFlash(e.message, 'danger');
            }
            // 出错时根据可能的状态恢复按钮
            // 假设删除失败，容器可能还在，恢复按钮状态
            if(startBtn) startBtn.disabled = false;
            if(removeBtn) removeBtn.disabled = false;
        }
    }

    // 页面加载时获取初始状态
    document.addEventListener('DOMContentLoaded', function(){
        const statusEl = document.getElementById('project-status');
        if(!statusEl) return;
        
        // 从 URL 中提取 pid
        const pathParts = window.location.pathname.split('/').filter(Boolean);
        const pid = pathParts[pathParts.indexOf('project') + 1];
        
        if(pid && pid.length > 20){ // 简单验证是 UUID
            fetchProjectStatus(pid);
        }
    });

})();

