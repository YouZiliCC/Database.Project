// 用户相关前端交互：加入/退出工作组、删除账号等
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

    // 用户加入工作组
    const joinBtn = document.getElementById('btn-join');
    joinBtn?.addEventListener('click', async () => {
        try{
            const gid = joinBtn.dataset.gid;
            await post(`/user/me/join/${gid}`);
            // 直接跳转，让服务器端 flash 显示
            location.reload();
        }catch(e){ 
            showFlash(e.message, 'danger');
        }
    });

    // 用户退出工作组
    const leaveBtn = document.getElementById('btn-leave');
    leaveBtn?.addEventListener('click', async () => {
        if(!confirm('确认退出当前工作组？')) return;
        try{
            await post('/user/me/leave');
            // 直接跳转，让服务器端 flash 显示
            location.reload();
        }catch(e){ 
            showFlash(e.message, 'danger');
        }
    });

    // 全局函数：退出工作组（供模板调用）
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

    // 全局函数：删除用户（管理员）
    window.deleteUser = async function(uid){
        if(!confirm('确认删除该用户？此操作不可恢复！')) return;
        try{
            await post(`/admin/del_user/${uid}`);
            // 直接跳转，让服务器端 flash 显示
            location.href = '/user';
        }catch(e){ 
            showFlash(e.message, 'danger');
        }
    };

    // 编辑表单提交确认
    const editForm = document.getElementById('edit-user-form');
    if(editForm){
        editForm.addEventListener('submit', function(e){
            if(!confirm('确认保存更改？')){ 
                e.preventDefault();
            }
        });
    }

    // 确认删除账号
    window.confirmDeleteAccount = async function(){
        if(!confirm('确认删除账号？此操作将永久删除您的所有数据，且不可恢复！')) return;
        if(!confirm('再次确认：真的要删除账号吗？')) return;
        try{
            await post('/user/me/delete');
            // 直接跳转，让服务器端 flash 显示
            location.href = '/';
        }catch(e){ 
            showFlash(e.message, 'danger');
        }
    };
})();



