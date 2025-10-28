// 组内成员管理与组长更换等前端交互（基础结构，接口已在后端定义）
(function(){
    async function post(url, body){
        const res = await fetch(url, {
            method:'POST',
            headers: body ? { 'Content-Type':'application/json' } : undefined,
            body: body ? JSON.stringify(body) : undefined,
            credentials:'same-origin'
        });
        const data = await res.json().catch(()=>({}));
        if(!res.ok){ throw new Error(data.error || '请求失败'); }
        return data;
    }

    // 示例：在需要的页面中，通过 data-action/data-url 来声明行为
    document.addEventListener('click', async (e) => {
        const t = e.target;
        if(!(t instanceof HTMLElement)) return;
        const url = t.dataset?.url;
        if(!url) return;
        if(t.dataset.action === 'remove_member'){
            if(!confirm('确认移除该成员？')) return;
            try{ await post(url); location.reload(); }catch(err){ alert(err.message); }
        }
        if(t.dataset.action === 'delete_group'){
            if(!confirm('确认删除该工作组？')) return;
            try{ await post(url); location.href = '/groups'; }catch(err){ alert(err.message); }
        }
        if(t.dataset.action === 'delete_project'){
            if(!confirm('确认删除该项目？')) return;
            try{ await post(url); location.href = '/projects'; }catch(err){ alert(err.message); }
        }
    });
})();


