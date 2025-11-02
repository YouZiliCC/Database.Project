// 全局脚本：闪存自动消失、主题切换、列表搜索
(function(){
    // 闪存自动隐藏
    const flashes = document.querySelectorAll('.flash');
    if(flashes.length){ setTimeout(()=> flashes.forEach(f=> f.remove()), 4000); }

    // 客户端Flash消息显示函数
    window.showFlash = function(message, category = 'info'){
        // 检查是否已存在 flash-container
        let container = document.querySelector('.flash-container');
        if (!container) {
            // 创建容器并插入到 main 元素开头
            container = document.createElement('div');
            container.className = 'flash-container';
            const main = document.querySelector('main');
            if (main) {
                main.insertBefore(container, main.firstChild);
            } else {
                document.body.insertBefore(container, document.body.firstChild);
            }
        }

        // 创建 flash 消息元素
        const flash = document.createElement('div');
        flash.className = `flash ${category}`;
        flash.textContent = message;
        flash.style.opacity = '0';
        flash.style.transform = 'translateY(-10px)';
        flash.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
        
        // 添加到容器
        container.appendChild(flash);

        // 平滑滚动到页面顶部
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });

        // 触发动画
        setTimeout(() => {
            flash.style.opacity = '1';
            flash.style.transform = 'translateY(0)';
        }, 10);

        // 4秒后自动移除
        setTimeout(() => {
            flash.style.opacity = '0';
            flash.style.transform = 'translateY(-10px)';
            setTimeout(() => flash.remove(), 300);
        }, 4000);
    };

    // 主题切换（localStorage 持久化）
    // 注意：主题的初始应用已在 base.html 的 <head> 中完成，这里只处理切换
    const THEME_KEY = 'app_theme';
    const root = document.documentElement;
    const toggleBtn = document.getElementById('theme-toggle');
    toggleBtn?.addEventListener('click', () => {
        const isDark = root.classList.toggle('theme-dark');
        localStorage.setItem(THEME_KEY, isDark ? 'dark' : 'light');
    });

    // 列表搜索（页面内简单过滤）——支持 ul/li 列表和卡片网格（.card/.project-card）
    const searchInputs = document.querySelectorAll('[data-list-search]');
    const LIST_ITEM_SELECTOR = 'li, .card, .project-card, .list-item, .item';
    searchInputs.forEach(input => {
        const targetSelector = input.getAttribute('data-list-target');
        const list = document.querySelector(targetSelector);
        if(!list) return;
        input.addEventListener('input', () => {
            const q = input.value.trim().toLowerCase();
            const items = Array.from(list.querySelectorAll(LIST_ITEM_SELECTOR)).length ?
                Array.from(list.querySelectorAll(LIST_ITEM_SELECTOR)) : Array.from(list.children);
            items.forEach(el => {
                const text = (el.textContent || '').toLowerCase();
                el.style.display = text.includes(q) ? '' : 'none';
            });
            applyPagination(list);
        });
    });

    // 前端分页：在列表容器上添加 data-page-size
    function applyPagination(list){
        const pageSizeAttr = list.getAttribute('data-page-size');
        const pageSize = pageSizeAttr ? parseInt(pageSizeAttr, 10) : 0;
        const rawItems = Array.from(list.querySelectorAll(LIST_ITEM_SELECTOR));
        const items = (rawItems.length ? rawItems : Array.from(list.children)).filter(el => el.style.display !== 'none');
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

    // 初始应用分页（支持常见列表容器，包括项目网格 .project-list）
    document.querySelectorAll('ul[list], ul.list, .list, .project-list').forEach(el => applyPagination(el));

    // 列表排序：通过 data-sort-target 指定列表，select 使用 value: name-asc/name-desc
    document.querySelectorAll('[data-sort-target]').forEach(select => {
        const target = document.querySelector(select.getAttribute('data-sort-target'));
        if(!target) return;
        select.addEventListener('change', () => sortList(target, select.value));
        // 初始
        sortList(target, select.value);
    });

    function sortList(list, mode){
        const raw = Array.from(list.querySelectorAll(LIST_ITEM_SELECTOR));
        const items = raw.length ? raw : Array.from(list.children);
        const visible = items.filter(el => el.style.display !== 'none');
        const hidden = items.filter(el => el.style.display === 'none');
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
            if(rows.length === 0){ 
                showFlash('请先勾选要导出的项', 'warning'); 
                return; 
            }
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
                showFlash('请检查表单输入是否完整、长度是否达标', 'warning');
            }
        });
    });
})();


