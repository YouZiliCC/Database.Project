// 用户加入/退出工作组等前端交互
(function(){
    async function post(url){
        const res = await fetch(url, { method:'POST', credentials:'same-origin' });
        const data = await res.json().catch(()=>({}));
        if(!res.ok){ throw new Error(data.error || '请求失败'); }
        return data;
    }

    const joinBtn = document.getElementById('btn-join');
    const leaveBtn = document.getElementById('btn-leave');

    joinBtn?.addEventListener('click', async () => {
        try{
            const gid = joinBtn.dataset.gid;
            await post(`/users/me/join/${gid}`);
            location.reload();
        }catch(e){ alert(e.message); }
    });

    leaveBtn?.addEventListener('click', async () => {
        try{
            await post('/users/me/leave');
            location.reload();
        }catch(e){ alert(e.message); }
    });
})();


