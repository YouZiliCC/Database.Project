from .base import db
from .models import User, Project, Group
from sqlalchemy import select, update, or_, func
from datetime import datetime
import logging


# 配置 Logger
logger = logging.getLogger(__name__)

# 基础数据库工具函数
def safe_commit():
    """
    安全地提交数据库事务，出错时回滚并记录错误。

    返回:
        bool: 提交是否成功。
    """
    try:
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"safe_commit Failed: {e}", exc_info=True)  # 记录详细异常信息
        return False


def safe_add(instance):
    """
    安全地添加数据库记录并提交。

    参数:
        instance: SQLAlchemy 模型实例。

    返回:
        bool: 添加并提交是否成功。
    """
    try:
        db.session.add(instance)
        return safe_commit()
    except Exception as e:
        logger.error(f"safe_add Failed: {e}", exc_info=True)
        db.session.rollback()
        return False


def safe_delete(instance):
    """
    安全地删除数据库记录并提交。

    参数:
        instance: SQLAlchemy 模型实例。

    返回:
        bool: 删除并提交是否成功。
    """
    try:
        db.session.delete(instance)
        return safe_commit()
    except Exception as e:
        logger.error(f"safe_delete Failed: {e}", exc_info=True)
        db.session.rollback()
        return False


# 用户 (User) CRUD 操作
def get_user_by_username(uname):
    """
    根据用户名获取用户。

    参数:
        uname (str): 用户名。

    返回:
        User: 匹配的用户对象，未找到则返回None。
    """
    try:
        return db.session.execute(select(User).where(User.uname == uname)).scalar_one_or_none()
    except Exception as e:
        logger.error(f"get_user_by_username Failed: {e}", exc_info=True)
        return None


def get_user_by_email(email):
    """
    根据邮箱获取用户。

    参数:
        email (str): 邮箱。

    返回:
        User: 匹配的用户对象，未找到则返回None。
    """
    try:
        return db.session.execute(select(User).where(User.email == email)).scalar_one_or_none()
    except Exception as e:
        logger.error(f"get_user_by_email Failed: {e}", exc_info=True)
        return None


def get_user_by_id(uid):
    """
    根据用户ID获取用户。

    参数:
        uid (str): 用户ID。

    返回:
        User: 匹配的用户对象，未找到则返回None。
    """
    try:
        return db.session.execute(select(User).where(User.uid == uid)).scalar_one_or_none()
    except Exception as e:
        logger.error(f"get_user_by_id Failed: {e}", exc_info=True)
        return None


def get_user_by_sid(sid):
    """
    根据学号获取用户。

    参数:
        sid (str): 学号。

    返回:
        User: 匹配的用户对象，未找到则返回None。
    """
    try:
        return db.session.execute(select(User).where(User.sid == sid)).scalar_one_or_none()
    except Exception as e:
        logger.error(f"get_user_by_sid Failed: {e}", exc_info=True)
        return None


def get_user_by_group_id(gid):
    """
    根据用户组ID获取用户列表。

    参数:
        gid (str): 用户组ID。

    返回:
        list: 匹配的用户对象列表。
    """
    try:
        return db.session.execute(select(User).where(User.gid == gid)).scalars().all()
    except Exception as e:
        logger.error(f"get_user_by_group_id Failed: {e}", exc_info=True)
        return []


def create_user(uname, email, sid, password, uinfo=None, role=0):
    """
    创建新用户。

    参数:
        uname (str): 用户名。
        email (str): 邮箱。
        sid (str): 学号。
        password (str): 原始密码。
        uinfo (str): 用户信息。

    返回:
        User: 创建成功的用户对象，失败则返回None。
    """
    try:
        # 检查用户名和邮箱是否已存在
        if any([get_user_by_username(uname), get_user_by_email(email), get_user_by_sid(sid)]):
            logger.warning(f"创建用户失败: 用户名/邮箱/学号已存在 ({uname}, {email}, {sid})")
            return None

        user = User(uname=uname, email=email, uinfo=uinfo, sid=sid, role=role)
        user.set_password(password)  # 使用模型方法设置密码哈希

        if safe_add(user):
            logger.info(f"用户 {uname} 创建成功, ID: {user.uid}")
            return user
        return None
    except Exception as e:
        logger.error(f"创建用户失败: {e}", exc_info=True)
        db.session.rollback()
        return None


def update_user(user, **kwargs):
    """
    更新用户记录。

    参数:
        user (User): 要更新的用户对象。
        **kwargs: 要更新的字段及其值。

    返回:
        bool: 更新是否成功。
    """
    if not user:
        return False
    try:
        for key, value in kwargs.items():
            if hasattr(user, key):
                if key == "password":  # 特殊处理密码更新
                    user.set_password(value)
                elif key != "uid":  # 不允许修改ID
                    setattr(user, key, value)
        return safe_commit()
    except Exception as e:
        logger.error(f"更新用户 {user.uid} 失败: {e}", exc_info=True)
        db.session.rollback()
        return False


def delete_user(user):
    """
    删除用户记录。

    参数:
        user (User): 要删除的用户对象。

    返回:
        bool: 删除是否成功。
    """
    if not user:
        return False
    try:
        return safe_delete(user)
    except Exception as e:
        logger.error(f"删除用户 {user.uid} 失败: {e}", exc_info=True)
        db.session.rollback()
        return False


def list_all_users():
    """
    列出所有用户。

    返回:
        list: 所有用户对象列表。
    """
    try:
        return db.session.execute(select(User)).scalars().all()
    except Exception as e:
        logger.error(f"list_all_users Failed: {e}", exc_info=True)
        return []

# Group
def create_group(gname, ginfo=None):
    """
    创建新用户组。

    参数:
        gname (str): 用户组名称。
        ginfo (str): 用户组信息。

    返回:
        Group: 创建成功的用户组对象，失败则返回None。
    """
    try:
        group = Group(gname=gname, ginfo=ginfo)
        if safe_add(group):
            logger.info(f"用户组 {gname} 创建成功, ID: {group.gid}")
            return group
        return None
    except Exception as e:
        logger.error(f"创建用户组失败: {e}", exc_info=True)
        db.session.rollback()
        return None


def update_group(group, **kwargs):
    """
    更新用户组记录。

    参数:
        group (Group): 要更新的用户组对象。
        **kwargs: 要更新的字段及其值。

    返回:
        bool: 更新是否成功。
    """
    if not group:
        return False
    try:
        for key, value in kwargs.items():
            if hasattr(group, key):
                if key != "gid":  # 不允许修改ID
                    setattr(group, key, value)
        return safe_commit()
    except Exception as e:
        logger.error(f"更新用户组 {group.gid} 失败: {e}", exc_info=True)
        db.session.rollback()
        return False


def delete_group(group):
    """
    删除用户组记录。

    参数:
        group (Group): 要删除的用户组对象。

    返回:
        bool: 删除是否成功。
    """
    if not group:
        return False
    try:
        return safe_delete(group)
    except Exception as e:
        logger.error(f"删除用户组 {group.gid} 失败: {e}", exc_info=True)
        db.session.rollback()
        return False


def list_all_groups():
    """
    列出所有用户组。

    返回:
        list: 所有用户组对象列表。
    """
    try:
        return db.session.execute(select(Group)).scalars().all()
    except Exception as e:
        logger.error(f"list_all_groups Failed: {e}", exc_info=True)
        return []


def get_group_by_id(gid):
    """
    根据用户组ID获取用户组。

    参数:
        gid (str): 用户组ID。

    返回:
        Group: 匹配的用户组对象，未找到则返回None。
    """
    try:
        return db.session.execute(select(Group).where(Group.gid == gid)).scalar_one_or_none()
    except Exception as e:
        logger.error(f"get_group_by_id Failed: {e}", exc_info=True)
        return None


def get_leader_by_group_id(gid):
    """
    根据用户组ID获取组长用户。

    参数:
        gid (str): 用户组ID。

    返回:
        User: 组长用户对象，未找到则返回None。
    """
    try:
        group = db.session.execute(select(Group).where(Group.gid == gid)).scalar_one_or_none()
        if group:
            return db.session.execute(select(User).where(User.uid == group.leader_id)).scalar_one_or_none()
        return None
    except Exception as e:
        logger.error(f"get_leader_by_group_id Failed: {e}", exc_info=True)
        return None


def get_users_by_group_id(gid):
    """
    根据用户组ID获取用户列表。

    参数:
        gid (str): 用户组ID。

    返回:
        list: 匹配的用户对象列表。
    """
    try:
        return db.session.execute(select(User).where(User.gid == gid)).scalars().all()
    except Exception as e:
        logger.error(f"get_users_by_group_id Failed: {e}", exc_info=True)
        return []

# Project CRUD 操作
def create_project(pname, gid, pinfo=None, port=None, docker_port=None):
    """
    创建新项目。

    参数:
        pname (str): 项目名称。
        pinfo (str): 项目描述。
        gid (str): 用户组ID。
        port (int): 项目端口。
        docker_port (int): Docker映射端口。

    返回:
        Project: 创建成功的项目对象，失败则返回None。
    """
    try:
        project = Project(pname=pname, pinfo=pinfo, gid=gid, port=port, docker_port=docker_port)
        if safe_add(project):
            logger.info(f"项目 {pname} 创建成功, ID: {project.pid}")
            return project
        return None
    except Exception as e:
        logger.error(f"创建项目失败: {e}", exc_info=True)
        db.session.rollback()
        return None


def update_project(project, **kwargs):
    """
    更新项目记录。

    参数:
        project (Project): 要更新的项目对象。
        **kwargs: 要更新的字段及其值。

    返回:
        bool: 更新是否成功。
    """
    if not project:
        return False
    try:
        for key, value in kwargs.items():
            if hasattr(project, key):
                if key != "pid":  # 不允许修改ID
                    setattr(project, key, value)
        return safe_commit()
    except Exception as e:
        logger.error(f"更新项目 {project.pid} 失败: {e}", exc_info=True)
        db.session.rollback()
        return False


def delete_project(project):
    """
    删除项目记录。

    参数:
        project (Project): 要删除的项目对象。

    返回:
        bool: 删除是否成功。
    """
    if not project:
        return False
    try:
        return safe_delete(project)
    except Exception as e:
        logger.error(f"删除项目 {project.pid} 失败: {e}", exc_info=True)
        db.session.rollback()
        return False
    

def get_project_by_id(pid):
    """
    根据项目ID获取项目。

    参数:
        pid (str): 项目ID。

    返回:
        Project: 匹配的项目对象，未找到则返回None。
    """
    try:
        return db.session.execute(select(Project).where(Project.pid == pid)).scalar_one_or_none()
    except Exception as e:
        logger.error(f"get_project_by_id Failed: {e}", exc_info=True)
        return None


def list_all_projects():
    """
    列出所有项目。

    返回:
        list: 所有项目对象列表。
    """
    try:
        return db.session.execute(select(Project)).scalars().all()
    except Exception as e:
        logger.error(f"list_all_projects Failed: {e}", exc_info=True)
        return []