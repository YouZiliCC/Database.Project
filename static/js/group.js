// 工作组相关前端交互：成员管理、项目管理、删除工作组等
(function(){
    // 通用POST请求函数（带CSRF保护）
    async function post(url, data = null){
        const token = document.querySelector('meta[name="csrf-token"]')?.content;
        const headers = { 'X-CSRFToken': token };
        if(data) headers['Content-Type'] = 'application/json';
        
        const res = await fetch(url, {
            method: 'POST',
            headers: headers,
            body: data ? JSON.stringify(data) : undefined,
            credentials: 'same-origin'
        });
        const json = await res.json().catch(()=>({}));
        if(!res.ok){ throw new Error(json.error || `请求失败 (${res.status})`); }
        return json;
    }

    // 全局函数：申请加入工作组
    window.applyToGroup = async function(gid){
        if(!confirm('确认申请加入该工作组？')) return;
        try{
            const result = await post(`/group/${gid}/apply`);
            showFlash(result.message || '申请已提交', 'success');
            setTimeout(() => location.reload(), 1000);
        }catch(e){ 
            showFlash(e.message, 'danger');
        }
    };

    // 全局函数：接受申请
    window.acceptApplication = async function(gid, gaid){
        if(!confirm('确认接受该用户的加入申请？')) return;
        try{
            const result = await post(`/group/${gid}/applications/${gaid}/accept`);
            showFlash(result.message || '已接受申请', 'success');
            // 移除该行
            const row = document.getElementById(`application-${gaid}`);
            if(row) row.remove();
            setTimeout(() => location.reload(), 1000);
        }catch(e){ 
            showFlash(e.message, 'danger');
        }
    };

    // 全局函数：拒绝申请
    window.rejectApplication = async function(gid, gaid){
        if(!confirm('确认拒绝该用户的加入申请？')) return;
        try{
            const result = await post(`/group/${gid}/applications/${gaid}/reject`);
            showFlash(result.message || '已拒绝申请', 'success');
            // 移除该行
            const row = document.getElementById(`application-${gaid}`);
            if(row) row.remove();
        }catch(e){ 
            showFlash(e.message, 'danger');
        }
    };

    // 全局函数：退出工作组
    window.leaveGroup = async function(){
        if(!confirm('确认退出当前工作组？')) return;
        try{
            await post('/user/me/leave');
            // 直接跳转，让服务器端 flash 显示
            location.reload();
        }catch(e){ 
            showFlash(e.message, 'danger');
        }
    };

    // 全局函数：移除成员
    window.removeMember = async function(gid, uid){
        if(!confirm('确认移除该成员？')) return;
        try{
            await post(`/group/${gid}/members/${uid}/remove`);
            // 直接跳转，让服务器端 flash 显示
            location.reload();
        }catch(e){ 
            showFlash(e.message, 'danger');
        }
    };

    // 全局函数：删除工作组
    window.deleteGroup = async function(gid){
        if(!confirm('确认删除该工作组？此操作将同时删除所有相关项目，且不可恢复！')) return;
        if(!confirm('再次确认：真的要删除工作组吗？')) return;
        try{
            await post(`/group/${gid}/delete`);
            // 直接跳转，让服务器端 flash 显示
            location.href = '/group';
        }catch(e){ 
            showFlash(e.message, 'danger');
        }
    };

    // 全局函数：删除项目
    window.deleteProject = async function(gid, pid){
        if(!confirm('确认删除该项目？此操作不可恢复！')) return;
        try{
            await post(`/group/${gid}/projects/${pid}/delete`);
            // 直接跳转，让服务器端 flash 显示
            location.reload();
        }catch(e){ 
            showFlash(e.message, 'danger');
        }
    };

    // 通过 data-action/data-url 属性自动处理按钮点击
    document.addEventListener('click', async (e) => {
        const t = e.target;
        if(!(t instanceof HTMLElement)) return;
        const url = t.dataset?.url;
        if(!url) return;
        
        const action = t.dataset.action;
        if(action === 'remove_member'){
            if(!confirm('确认移除该成员？')) return;
            try{ 
                await post(url); 
                // 直接跳转，让服务器端 flash 显示
                location.reload();
            }catch(err){ 
                showFlash(err.message, 'danger');
            }
        }
        else if(action === 'delete_group'){
            if(!confirm('确认删除该工作组？此操作不可恢复！')) return;
            if(!confirm('再次确认：真的要删除吗？')) return;
            try{ 
                await post(url); 
                // 直接跳转，让服务器端 flash 显示
                location.href = '/group';
            }catch(err){ 
                showFlash(err.message, 'danger');
            }
        }
        else if(action === 'delete_project'){
            if(!confirm('确认删除该项目？此操作不可恢复！')) return;
            try{ 
                await post(url); 
                // 直接跳转，让服务器端 flash 显示
                location.reload();
            }catch(err){ 
                showFlash(err.message, 'danger');
            }
        }
    });

    // 编辑表单提交确认
    const editForm = document.getElementById('edit-group-form');
    if(editForm){
        editForm.addEventListener('submit', function(e){
            if(!confirm('确认保存更改？')){ 
                e.preventDefault();
            }
        });
    }
})();



