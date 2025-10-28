前端整理说明

目的
- 统一项目模板结构，减少重复的 HTML 代码。
- 规范静态资源引用（通过 `url_for('static', filename=...)`）。

主要变更
- `templates/base.html`
  - 将站点的基础布局（doctype、head、header/nav、footer）集中到 `base.html`。
  - 新增模板块：`{% block head %}`（保留）和 `{% block scripts %}`（用于注入每页脚本）。

- `templates/project/project_detail.html`
  - 从完整 HTML 页面重构为继承 `base.html` 的模板，仅保留 `content` 区块。

- `templates/project/terminal.html`
  - 从完整 HTML 页面重构为继承 `base.html` 的模板。
  - 把 `terminal.js` 移到 `{% block scripts %}` 中加载（通过 `url_for('static', filename='js/terminal.js')`）。

为何这样做
- 减少重复代码，方便后续统一修改头部/脚本/样式。
- 更清晰的模板继承关系，更易维护。

如何引用静态资源
- CSS/JS/图片均使用 Flask 推荐的方式：
  - 样式：`<link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">`
  - 脚本：`<script src="{{ url_for('static', filename='js/your.js') }}"></script>`（或通过 `{% block scripts %}` 注入）
  - 图片：`<img src="{{ url_for('static', filename='img/xxx.png') }}">`

注意事项
- 我没有修改后端逻辑或路由。
- `base.html` 中使用了 `current_user`（与原来模板相同），请确保 Flask 的上下文中有该变量（项目中已有使用）。

后续建议（可选）
- 若要进一步前端构建（如使用 webpack/Vite 或 SASS），建议在 `static/` 下新增 `src/` 和 `dist/` 并使用构建脚本输出到 `static/dist/`，然后通过 `url_for('static', filename='dist/app.min.js')` 引用。

若需要我可以：
- 把所有模板强制统一改成 `extends 'base.html'`（目前仅剩少数页面已经完成重构）。
- 添加更完整的导航样式和响应式支持（CSS 微调）。
