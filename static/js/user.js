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
            alert('成功加入工作组！');
            location.reload();
        }catch(e){ alert(e.message); }
    });

    // 用户退出工作组
    const leaveBtn = document.getElementById('btn-leave');
    leaveBtn?.addEventListener('click', async () => {
        if(!confirm('确认退出当前工作组？')) return;
        try{
            await post('/user/me/leave');
            alert('已退出工作组');
            location.reload();
        }catch(e){ alert(e.message); }
    });

    // 全局函数：退出工作组（供模板调用）
    window.leaveGroup = async function(){
        if(!confirm('确认退出当前工作组？')) return;
        try{
            await post('/user/me/leave');
            alert('已退出工作组');
            location.reload();
        }catch(e){ alert(e.message); }
    };

    // 全局函数：删除用户（管理员）
    window.deleteUser = async function(uid){
        if(!confirm('确认删除该用户？此操作不可恢复！')) return;
        try{
            await post(`/admin/del_user/${uid}`);
            alert('用户删除成功');
            location.href = '/user';
        }catch(e){ alert(e.message); }
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
            alert('账号已删除');
            location.href = '/';
        }catch(e){ alert(e.message); }
    };
})();



