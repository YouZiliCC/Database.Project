// 全局脚本：闪存自动消失、主题切换、列表搜索
(function(){
    // 闪存自动隐藏
    const flashes = document.querySelectorAll('.flash');
    if(flashes.length){ setTimeout(()=> flashes.forEach(f=> f.remove()), 4000); }

    // 主题切换（localStorage 持久化）
    const THEME_KEY = 'app_theme';
    const root = document.documentElement;
    const current = localStorage.getItem(THEME_KEY) || 'light';
    if(current === 'dark') root.classList.add('theme-dark');
    const toggleBtn = document.getElementById('theme-toggle');
    toggleBtn?.addEventListener('click', () => {
        const isDark = root.classList.toggle('theme-dark');
        localStorage.setItem(THEME_KEY, isDark ? 'dark' : 'light');
    });

    // 列表搜索（页面内简单过滤）
    const searchInputs = document.querySelectorAll('[data-list-search]');
    searchInputs.forEach(input => {
        const targetSelector = input.getAttribute('data-list-target');
        const list = document.querySelector(targetSelector);
        if(!list) return;
        input.addEventListener('input', () => {
            const q = input.value.trim().toLowerCase();
            list.querySelectorAll('li').forEach(li => {
                const text = li.textContent.toLowerCase();
                li.style.display = text.includes(q) ? '' : 'none';
            });
            applyPagination(list);
        });
    });

    // 前端分页：在列表容器上添加 data-page-size
    function applyPagination(list){
        const pageSizeAttr = list.getAttribute('data-page-size');
        const pageSize = pageSizeAttr ? parseInt(pageSizeAttr, 10) : 0;
        const items = Array.from(list.querySelectorAll('li')).filter(li => li.style.display !== 'none');
        const wrapper = list.parentElement;
        let pager = wrapper.querySelector('.pager');
        if(!pageSize || items.length <= pageSize){
            // 无需分页
            items.forEach(li => li.style.removeProperty('display'));
            if(pager) pager.remove();
            renderEmptyState(wrapper, items.length === 0);
            return;
        }
        const total = items.length;
        const pages = Math.ceil(total / pageSize);
        const current = Math.min(parseInt(wrapper.getAttribute('data-page') || '1', 10), pages) || 1;
        // 显示当前页
        items.forEach((li, idx) => {
            const pageIndex = Math.floor(idx / pageSize) + 1;
            li.style.display = (pageIndex === current) ? '' : 'none';
        });
        // 渲染分页器
        if(!pager){
            pager = document.createElement('div');
            pager.className = 'pager';
            wrapper.appendChild(pager);
        }
        pager.innerHTML = '';
        for(let p=1; p<=pages; p++){
            const btn = document.createElement('button');
            btn.className = 'btn pager-btn' + (p===current ? ' active' : '');
            btn.textContent = p;
            btn.addEventListener('click', () => {
                wrapper.setAttribute('data-page', String(p));
                applyPagination(list);
            });
            pager.appendChild(btn);
        }
        renderEmptyState(wrapper, total === 0);
    }

    function renderEmptyState(wrapper, isEmpty){
        let empty = wrapper.querySelector('.empty');
        if(isEmpty){
            if(!empty){
                empty = document.createElement('div');
                empty.className = 'empty';
                empty.textContent = '暂无数据';
                wrapper.appendChild(empty);
            }
        }else{
            empty?.remove();
        }
    }

    // 初始应用分页
    document.querySelectorAll('ul[list], ul.list').forEach(ul => applyPagination(ul));

    // 列表排序：通过 data-sort-target 指定列表，select 使用 value: name-asc/name-desc
    document.querySelectorAll('[data-sort-target]').forEach(select => {
        const target = document.querySelector(select.getAttribute('data-sort-target'));
        if(!target) return;
        select.addEventListener('change', () => sortList(target, select.value));
        // 初始
        sortList(target, select.value);
    });

    function sortList(list, mode){
        const items = Array.from(list.querySelectorAll('li'));
        const visible = items.filter(li => li.style.display !== 'none');
        const hidden = items.filter(li => li.style.display === 'none');
        const [key, dir] = (mode || 'name-asc').split('-');
        const getText = (li) => (li.textContent || '').trim().toLowerCase();
        visible.sort((a, b) => {
            const ta = getText(a);
            const tb = getText(b);
            if(ta < tb) return dir === 'asc' ? -1 : 1;
            if(ta > tb) return dir === 'asc' ? 1 : -1;
            return 0;
        });
        list.innerHTML = '';
        visible.concat(hidden).forEach(li => list.appendChild(li));
        applyPagination(list);
    }

    // 多选与导出 CSV + 视图切换
    document.addEventListener('change', (e) => {
        const t = e.target;
        if(!(t instanceof HTMLInputElement)) return;
        if(t.matches('[data-select-all]')){
            const target = document.querySelector(t.getAttribute('data-list-target'));
            target?.querySelectorAll('[data-select-item]').forEach((cb) => { cb.checked = t.checked; });
        }
    });
    document.addEventListener('click', (e) => {
        const t = e.target;
        if(!(t instanceof HTMLElement)) return;
        if(t.matches('[data-export-csv]')){
            const target = document.querySelector(t.getAttribute('data-list-target'));
            if(!target) return;
            const rows = [];
            target.querySelectorAll('li').forEach(li => {
                const cb = li.querySelector('[data-select-item]');
                if(cb && cb.checked){ rows.push((li.innerText || '').trim()); }
            });
            if(rows.length === 0){ alert('请先勾选要导出的项'); return; }
            const csv = '\uFEFF' + rows.map(r => '"' + r.replace(/"/g,'""') + '"').join('\n');
            const blob = new Blob([csv], { type:'text/csv;charset=utf-8;' });
            const a = document.createElement('a');
            a.href = URL.createObjectURL(blob);
            a.download = 'export.csv';
            a.click();
            URL.revokeObjectURL(a.href);
        }
        if(t.matches('[data-view-toggle]')){
            const target = document.querySelector(t.getAttribute('data-list-target'));
            if(!target) return;
            target.classList.toggle('as-table');
        }
    });
    // 基础前端校验（必填与最小长度）。使用 data-validate="required|min:6" 声明
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', (e) => {
            let ok = true;
            const controls = form.querySelectorAll('[data-validate]');
            controls.forEach(ctrl => {
                const rules = (ctrl.getAttribute('data-validate') || '').split('|');
                let valid = true;
                rules.forEach(rule => {
                    if(rule === 'required' && !String(ctrl.value || '').trim()) valid = false;
                    if(rule.startsWith('min:')){
                        const n = parseInt(rule.split(':')[1], 10) || 0;
                        if(String(ctrl.value || '').length < n) valid = false;
                    }
                });
                ctrl.classList.toggle('invalid', !valid);
                if(!valid) ok = false;
            });
            if(!ok){
                e.preventDefault();
                alert('请检查表单输入是否完整、长度是否达标');
            }
        });
    });
})();


