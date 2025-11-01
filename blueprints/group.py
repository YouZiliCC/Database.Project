from functools import wraps
from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    jsonify,
    abort,
)
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Length
from database.actions import *
from blueprints.project import ProjectForm
import logging

group_bp = Blueprint("group", __name__)
logger = logging.getLogger(__name__)


# -------------------------------------------------------------------------------------------
# Group Forms
# -------------------------------------------------------------------------------------------
class GroupForm(FlaskForm):
    gname = StringField(
        "工作组名称", validators=[DataRequired(), Length(min=3, max=50)]
    )
    ginfo = TextAreaField("工作组描述", validators=[Length(max=2000)])
    submit = SubmitField("保存")


class ChangeLeaderForm(FlaskForm):
    new_leader_name = SelectField("更换组长为", validators=[DataRequired()])
    submit = SubmitField("确认更换")


# -------------------------------------------------------------------------------------------
# Group Decorators
# -------------------------------------------------------------------------------------------
def group_required(func):
    """工作组成员权限装饰器"""

    @wraps(func)
    def decorated(*args, **kwargs):
        gid = str(kwargs.get("gid"))
        if any(
            [
                not current_user.is_authenticated,
                not current_user.gid,
                str(current_user.gid) != str(gid),
            ]
        ):
            abort(403, description="需要工作组成员权限才能访问此页面")
        return func(*args, **kwargs)

    return decorated


def leader_required(func):
    """工作组组长权限装饰器"""

    @wraps(func)
    def decorated(*args, **kwargs):
        gid = str(kwargs.get("gid"))
        group = get_group_by_gid(gid)
        if any(
            [
                not current_user.is_authenticated,
                not current_user.gid,
                str(current_user.gid) != str(gid),
                str(group.leader_id) != str(current_user.uid),
            ]
        ):
            abort(403, description="需要工作组组长权限才能访问此页面")
        return func(*args, **kwargs)

    return decorated


# -------------------------------------------------------------------------------------------
# Group Views
# -------------------------------------------------------------------------------------------
@group_bp.route("/", methods=["GET"])
def group_list():
    """工作组列表页面"""
    groups = list_all_groups()
    return render_template("group/list.html", groups=groups)


@group_bp.route("/<uuid:gid>", methods=["GET"])
def group_detail(gid):
    """工作组详情页面"""
    gid = str(gid)
    group = get_group_by_gid(gid)
    if not group:
        abort(404, description="工作组不存在")
    return render_template("group/detail.html", group=group)


@group_bp.route("/my_group", methods=["GET"])
@login_required
def my_group():
    """当前用户所属工作组页面"""
    group = get_group_by_gid(current_user.gid)
    if not group:
        flash("您当前未加入任何工作组", "warning")
        return redirect(url_for("group.group_list"))
    return redirect(url_for("group.group_detail", gid=group.gid))


# -------------------------------------------------------------------------------------------
# Group Member Actions
# -------------------------------------------------------------------------------------------
# TODO: users management
@group_bp.route("/<uuid:gid>/members", methods=["GET", "POST"])
@login_required
@group_required
def group_members(gid):
    """工作组成员管理"""
    gid = str(gid)
    group = get_group_by_gid(gid)
    if not group:
        return jsonify({"error": "工作组不存在"}), 404
    pass


# TODO: accept member, as a button in member management page, under remove member
@group_bp.route("/<uuid:gid>/members/<uuid:uid>/accept", methods=["POST"])
@login_required
@leader_required
def accept_member(gid, uid):
    """接受工作组成员"""
    gid = str(gid)
    # group = get_group_by_gid(gid)
    # if not group:
    #     return jsonify({"error": "工作组不存在"}), 404
    # user = get_user_by_uid(uid)
    # if not user:
    #     return jsonify({"error": "用户不存在"}), 404
    # if not add_user_to_group(user, group):
    #     logger.warning(f"添加用户失败: {user.uname} to group {group.gname} by user {current_user.uname}")
    #     return jsonify({"error": "添加用户失败"}), 500
    # logger.info(f"用户已成功加入工作组: {user.uname} to group {group.gname} by user {current_user.uname}")
    # return jsonify({"message": "用户已成功加入工作组"}), 200


# TODO: remove member, as a button in member management page
@group_bp.route("/<uuid:gid>/members/<uuid:uid>/remove", methods=["POST"])
@login_required
@leader_required
def remove_member(gid, uid):
    """移除工作组成员"""
    gid = str(gid)
    group = get_group_by_gid(gid)
    if not group:
        return jsonify({"error": "工作组不存在"}), 404
    user = get_user_by_uid(uid)
    if not user:
        return jsonify({"error": "用户不存在"}), 404
    if not update_user(user, gid=None):
        logger.warning(
            f"移除用户失败: {user.uname} from group {group.gname} by user {current_user.uname}"
        )
        return jsonify({"error": "移除用户失败"}), 500
    logger.info(
        f"用户已成功移除工作组: {user.uname} from group {group.gname} by user {current_user.uname}"
    )
    return jsonify({"message": "用户已成功移除工作组"}), 200


# TODO: 模态窗口
@group_bp.route("/<uuid:gid>/change_leader", methods=["GET", "POST"])
@login_required
@leader_required
def leader_change(gid):
    """工作组组长更换"""
    gid = str(gid)
    group = get_group_by_gid(gid)
    users = group.users if group else []
    if not group:
        return jsonify({"error": "工作组不存在"}), 404
    form = ChangeLeaderForm()
    form.new_leader_name.choices = [(user.uname, user.uname) for user in users]
    if form.validate_on_submit():
        new_leader = get_user_by_uname(form.new_leader_name.data)
        if not new_leader:
            return jsonify({"error": "新组长不存在"}), 400
        if not update_group(group, leader_id=new_leader.uid):
            logger.warning(f"更换组长失败: {group.gname} by user {current_user.uname}")
            return jsonify({"error": "更换组长失败"}), 500
        logger.info(f"组长更换成功: {group.gname} by user {current_user.uname}")
        return jsonify({"message": "组长更换成功"}), 200
    return render_template("group/change_leader.html", form=form, group=group)


# -------------------------------------------------------------------------------------------
# Group Project Actions
# -------------------------------------------------------------------------------------------
# TODO: project management
@group_bp.route("/<uuid:gid>/projects", methods=["GET", "POST"])
@login_required
@leader_required
def group_projects(gid):
    """工作组项目管理"""
    gid = str(gid)
    group = get_group_by_gid(gid)
    if not group:
        return jsonify({"error": "工作组不存在"}), 404
    pass


# TODO: 单独页面
@group_bp.route("/<uuid:gid>/projects/create", methods=["GET", "POST"])
@login_required
@leader_required
def project_create(gid):
    """创建工作组项目"""
    gid = str(gid)
    group = get_group_by_gid(gid)
    if not group:
        flash("工作组不存在", "warning")
        return redirect(url_for("group.group_list"))
    form = ProjectForm()
    if form.validate_on_submit():
        project = create_project(
            pname=form.pname.data,
            pinfo=form.pinfo.data,
            gid=group.gid,
            port=form.port.data,
            docker_port=form.docker_port.data,
        )
        if not project:
            flash("创建项目失败，请重试", "danger")
            logger.warning(
                f"创建项目失败: {form.pname.data} by user {current_user.uname}"
            )
            return render_template("project/create.html", form=form, group=group)
        flash("项目创建成功！", "success")
        logger.info(f"创建项目成功: {form.pname.data} by user {current_user.uname}")
        return redirect(url_for("group.group_detail", gid=group.gid))


@group_bp.route("/<uuid:gid>/projects/<uuid:pid>/delete", methods=["POST"])
@login_required
@leader_required
def project_delete(gid, pid):
    """删除工作组项目"""
    gid = str(gid)
    group = get_group_by_gid(gid)
    if not group:
        return jsonify({"error": "工作组不存在"}), 404
    project = get_project_by_pid(pid)
    if not project or str(project.gid) != str(gid):
        return jsonify({"error": "项目不存在"}), 404
    if not delete_project(project):
        logger.warning(f"删除项目失败: {project.pname} by user {current_user.uname}")
        return jsonify({"error": "删除项目失败"}), 500
    logger.info(f"删除项目成功: {project.pname} by user {current_user.uname}")
    return jsonify({"message": "项目已成功删除"}), 200


# -------------------------------------------------------------------------------------------
# Group Actions
# -------------------------------------------------------------------------------------------
@group_bp.route("/create", methods=["GET", "POST"])
@login_required
def group_create():
    """创建工作组页面"""
    if current_user.gid:
        abort(403, description="您已属于某个工作组，无法创建新工作组")
    form = GroupForm()
    if form.validate_on_submit():
        group = create_group(
            gname=form.gname.data,
            ginfo=form.ginfo.data,
            leader_id=current_user.uid,
        )
        if not group:
            flash("创建工作组失败，请重试", "danger")
            logger.warning(f"创建工作组失败: {form.gname.data}")
            return render_template("group/create.html", form=form)
        # 将当前用户加入新创建的工作组
        if not update_user(current_user, gid=group.gid):
            flash("将用户加入工作组失败，请联系管理员", "danger")
            logger.error(f"将用户 {current_user.uname} 加入工作组 {group.gname} 失败")
            return render_template("group/create.html", form=form)
        flash("工作组创建成功！您已成为该组成员", "success")
        logger.info(f"创建工作组成功: {form.gname.data} by user {current_user.uname}")
        return redirect(url_for("group.group_detail", gid=group.gid))
    return render_template("group/create.html", form=form)


@group_bp.route("/<uuid:gid>/edit", methods=["GET", "POST"])
@login_required
@group_required
def group_edit(gid):
    """工作组编辑页面"""
    gid = str(gid)
    group = get_group_by_gid(gid)
    if not group:
        flash("工作组不存在", "warning")
        return redirect(url_for("group.group_list"))
    form = GroupForm(obj=group)
    if form.validate_on_submit():
        updated_group = update_group(
            group,
            gname=form.gname.data,
            ginfo=form.ginfo.data,
        )
        if not updated_group:
            flash("更新工作组信息失败，请重试", "danger")
            logger.warning(f"更新工作组信息失败: {form.gname.data}")
            return render_template("group/edit.html", form=form, group=group)
        flash("工作组信息更新成功", "success")
        logger.info(
            f"更新工作组信息成功: {form.gname.data} by user {current_user.uname}"
        )
        return redirect(url_for("group.group_detail", gid=gid))
    return render_template("group/edit.html", form=form, group=group)


@group_bp.route("/<uuid:gid>/delete", methods=["POST"])
@login_required
@leader_required
def group_delete(gid):
    """删除工作组"""
    gid = str(gid)
    group = get_group_by_gid(gid)
    if not group:
        return jsonify({"error": "工作组不存在"}), 404
    if not delete_group(group):
        logger.warning(f"删除工作组失败: {group.gname} by user {current_user.uname}")
        return jsonify({"error": "删除工作组失败"}), 500
    logger.info(f"删除工作组成功: {group.gname} by user {current_user.uname}")
    return jsonify({"message": "工作组已成功删除"}), 200  # 自动清空用户的gid字段


# TODO: IMAGE upload (WAITING)
@group_bp.route("/<uuid:gid>/upload_image", methods=["POST"])
@login_required
@group_required
def group_upload_image(gid):
    """上传工作组图片"""
    gid = str(gid)
    group = get_group_by_gid(gid)
    if not group:
        return jsonify({"error": "工作组不存在"}), 404
    pass
