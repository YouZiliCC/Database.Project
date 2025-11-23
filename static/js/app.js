// 全局脚本：闪存自动消失、列表搜索、分页
(function(){
    // 闪存自动隐藏
    const flashes = document.querySelectorAll('[role="alert"]');
    if(flashes.length){ setTimeout(()=> flashes.forEach(f=> f.remove()), 4000); }

    // 客户端Flash消息显示函数
    window.showFlash = function(message, category = 'info'){
        // 检查是否已存在 flash-container
        let container = document.querySelector('.max-w-7xl.mx-auto.px-4.mt-4');
        if (!container) {
            container = document.createElement('div');
            container.className = 'max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-4';
            const main = document.querySelector('main');
            if (main) {
                main.parentElement.insertBefore(container, main);
            } else {
                document.body.insertBefore(container, document.body.firstChild);
            }
        }

        // Determine classes based on category
        let classes = 'rounded-md p-4 mb-4 border ';
        let iconClass = '';
        if (category === 'error') {
            classes += 'bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-200 border-red-200 dark:border-red-800';
            iconClass = 'fa-circle-exclamation';
        } else if (category === 'success') {
            classes += 'bg-green-50 dark:bg-green-900/30 text-green-700 dark:text-green-200 border-green-200 dark:border-green-800';
            iconClass = 'fa-circle-check';
        } else {
            classes += 'bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-200 border-blue-200 dark:border-blue-800';
            iconClass = 'fa-circle-info';
        }

        // 创建 flash 消息元素
        const flash = document.createElement('div');
        flash.className = classes;
        flash.setAttribute('role', 'alert');
        flash.innerHTML = `
            <div class="flex">
                <div class="flex-shrink-0">
                    <i class="fa-solid ${iconClass}"></i>
                </div>
                <div class="ml-3">
                    <p class="text-sm font-medium">${message}</p>
                </div>
            </div>
        `;
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

    // 列表搜索（页面内简单过滤）——支持 ul/li 列表和卡片网格（.card/.project-card）
    const searchInputs = document.querySelectorAll('[data-list-search]');
    // Updated selector to include Tailwind classes if needed, but keeping generic classes is safer
    const LIST_ITEM_SELECTOR = 'li, .card, .project-card, .group-card, .list-item, .item';
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
            if(pager) pager.innerHTML = ''; // Clear pager instead of removing to keep layout stable if needed
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
            pager.className = 'pager mt-8 flex justify-center gap-2';
            wrapper.appendChild(pager);
        }
        pager.innerHTML = '';
        
        // Previous Button
        if (pages > 1) {
             // Simple numbered pagination
            for(let p=1; p<=pages; p++){
                const btn = document.createElement('button');
                // Tailwind classes for pagination buttons
                const baseClasses = 'relative inline-flex items-center px-4 py-2 border text-sm font-medium rounded-md focus:z-10 focus:outline-none focus:ring-1 focus:ring-primary-500 focus:border-primary-500';
                const activeClasses = 'z-10 bg-primary-50 border-primary-500 text-primary-600';
                const inactiveClasses = 'bg-white border-gray-300 text-gray-500 hover:bg-gray-50 dark:bg-gray-800 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700';
                
                btn.className = `${baseClasses} ${p === current ? activeClasses : inactiveClasses}`;
                btn.textContent = p;
                btn.addEventListener('click', () => {
                    wrapper.setAttribute('data-page', String(p));
                    applyPagination(list);
                    // Scroll to top of list
                    list.scrollIntoView({ behavior: 'smooth', block: 'start' });
                });
                pager.appendChild(btn);
            }
        }
        
        renderEmptyState(wrapper, total === 0);
    }

    function renderEmptyState(wrapper, isEmpty){
        let empty = wrapper.querySelector('.empty-state-msg');
        if(isEmpty){
            if(!empty){
                empty = document.createElement('div');
                empty.className = 'empty-state-msg text-center py-12';
                empty.innerHTML = `
                    <i class="fa-solid fa-folder-open text-4xl text-gray-400 mb-4"></i>
                    <h3 class="mt-2 text-sm font-medium text-gray-900 dark:text-white">没有找到匹配项</h3>
                `;
                wrapper.appendChild(empty);
            }
        }else{
            empty?.remove();
        }
    }

    // 初始应用分页（支持常见列表容器，包括项目网格 .project-list）
    document.querySelectorAll('ul[list], ul.list, .list, .project-list, .group-list').forEach(el => applyPagination(el));

    // 列表排序
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
                
                // Toggle Tailwind error classes
                if (!valid) {
                    ctrl.classList.add('border-red-300', 'text-red-900', 'placeholder-red-300', 'focus:ring-red-500', 'focus:border-red-500');
                    ctrl.classList.remove('border-gray-300', 'focus:ring-primary-500', 'focus:border-primary-500');
                } else {
                    ctrl.classList.remove('border-red-300', 'text-red-900', 'placeholder-red-300', 'focus:ring-red-500', 'focus:border-red-500');
                    ctrl.classList.add('border-gray-300', 'focus:ring-primary-500', 'focus:border-primary-500');
                }
                
                if(!valid) ok = false;
            });
            if(!ok){
                e.preventDefault();
                showFlash('请检查表单输入是否完整、长度是否达标', 'error');
            }
        });
    });
})();


