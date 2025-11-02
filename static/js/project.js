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

    // Toggle comment panel
    window.toggleCommentPanel = function(){
        const panel = document.getElementById('comment-panel');
        if(!panel) return;
        if(panel.style.display === 'none' || !panel.style.display){
            panel.style.display = 'block';
            // animate in
            setTimeout(() => panel.classList.add('show'), 10);
        }else{
            panel.classList.remove('show');
            setTimeout(() => panel.style.display = 'none', 300);
        }
    }

    window.toggleProjectStar = async function(pid){
        try{
            const res = await post(`/project/${pid}/star`);
            const btn = document.querySelector('#project-star-btn');
            const icon = btn?.querySelector('.star-icon');
            const count = document.querySelector('#project-star-count');
            
            if(res.starred){
                btn?.classList.add('starred');
                if(icon) icon.textContent = '★';
            }else{
                btn?.classList.remove('starred');
                if(icon) icon.textContent = '☆';
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
            <div class="comment-edit-form">
                <textarea class="comment-edit-textarea">${escapeHtml(originalContent)}</textarea>
                <div class="comment-edit-actions">
                    <button class="btn btn-sm btn-primary" onclick="saveComment('${pcid}', '${pid}')">保存</button>
                    <button class="btn btn-sm btn-secondary" onclick="cancelEditComment('${pcid}')">取消</button>
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

})();

