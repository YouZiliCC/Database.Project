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

    // 全局函数：加入工作组
    window.joinGroup = async function(gid){
        if(!confirm('确认加入该工作组？')) return;
        try{
            await post(`/user/me/join/${gid}`);
            alert('成功加入工作组！');
            location.reload();
        }catch(e){ alert(e.message); }
    };

    // 全局函数：退出工作组
    window.leaveGroup = async function(){
        if(!confirm('确认退出当前工作组？')) return;
        try{
            await post('/user/me/leave');
            alert('已退出工作组');
            location.reload();
        }catch(e){ alert(e.message); }
    };

    // 全局函数：移除成员
    window.removeMember = async function(gid, uid){
        if(!confirm('确认移除该成员？')) return;
        try{
            await post(`/group/${gid}/members/${uid}/remove`);
            alert('成员已移除');
            location.reload();
        }catch(e){ alert(e.message); }
    };

    // 全局函数：删除工作组
    window.deleteGroup = async function(gid){
        if(!confirm('确认删除该工作组？此操作将同时删除所有相关项目，且不可恢复！')) return;
        if(!confirm('再次确认：真的要删除工作组吗？')) return;
        try{
            await post(`/group/${gid}/delete`);
            alert('工作组已删除');
            location.href = '/group';
        }catch(e){ alert(e.message); }
    };

    // 全局函数：删除项目
    window.deleteProject = async function(gid, pid){
        if(!confirm('确认删除该项目？此操作不可恢复！')) return;
        try{
            await post(`/group/${gid}/projects/${pid}/delete`);
            alert('项目已删除');
            location.reload();
        }catch(e){ alert(e.message); }
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
                alert('成员已移除');
                location.reload(); 
            }catch(err){ alert(err.message); }
        }
        else if(action === 'delete_group'){
            if(!confirm('确认删除该工作组？此操作不可恢复！')) return;
            if(!confirm('再次确认：真的要删除吗？')) return;
            try{ 
                await post(url); 
                alert('工作组已删除');
                location.href = '/group'; 
            }catch(err){ alert(err.message); }
        }
        else if(action === 'delete_project'){
            if(!confirm('确认删除该项目？此操作不可恢复！')) return;
            try{ 
                await post(url); 
                alert('项目已删除');
                location.reload(); 
            }catch(err){ alert(err.message); }
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



