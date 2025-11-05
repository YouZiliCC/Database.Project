"""
图片上传和处理工具模块
提供图片上传、验证、压缩和保存的统一接口。
"""
import os
import logging
from typing import Tuple
from werkzeug.datastructures import FileStorage
from PIL import Image


logger = logging.getLogger(__name__)

# 默认配置
DEFAULT_ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
DEFAULT_MAX_SIZE_MB = 5  # 最大文件大小（MB）
DEFAULT_MAX_DIMENSION = 960  # 最大宽高度（像素）
DEFAULT_QUALITY = 85  # JPEG/WebP 压缩质量（1-100）


def allowed_file(filename: str, allowed_extensions: set = None) -> bool:
    """检查文件扩展名是否允许

    Args:
        filename: 文件名
        allowed_extensions: 允许的扩展名集合，默认为 DEFAULT_ALLOWED_EXTENSIONS

    Returns:
        bool: 是否允许该文件类型
    """
    if allowed_extensions is None:
        allowed_extensions = DEFAULT_ALLOWED_EXTENSIONS
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions


def get_file_size_mb(file: FileStorage) -> float:
    """获取文件大小（MB）

    Args:
        file: 上传的文件对象

    Returns:
        float: 文件大小（MB）
    """
    file.seek(0, os.SEEK_END)
    size_bytes = file.tell()
    file.seek(0)  # 重置指针到开头
    return size_bytes / (1024 * 1024)


def compress_image(
    image: Image.Image, max_dimension: int = DEFAULT_MAX_DIMENSION
) -> Image.Image:
    """压缩图片，保持宽高比

    Args:
        image: PIL Image 对象
        max_dimension: 最大宽高度

    Returns:
        Image: 压缩后的图片对象
    """
    # 如果图片尺寸超过限制，等比例缩小
    width, height = image.size
    if width > max_dimension or height > max_dimension:
        if width > height:
            new_width = max_dimension
            new_height = int(height * (max_dimension / width))
        else:
            new_height = max_dimension
            new_width = int(width * (max_dimension / height))

        logger.info(f"压缩图片: {width}x{height} -> {new_width}x{new_height}")
        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

    return image


def save_uploaded_image(
    file: FileStorage,
    save_folder: str,
    filename: str,
    max_size_mb: float = DEFAULT_MAX_SIZE_MB,
    max_dimension: int = DEFAULT_MAX_DIMENSION,
    quality: int = DEFAULT_QUALITY,
    allowed_extensions: set = None,
    convert_to_format: str = "PNG",
) -> Tuple[bool, str]:
    """保存上传的图片文件，自动压缩和格式转换

    Args:
        file: 上传的文件对象
        save_folder: 保存目录路径
        filename: 保存的文件名（不含扩展名）
        max_size_mb: 最大文件大小（MB），超过则拒绝
        max_dimension: 最大宽度或高度（像素），超过则自动压缩
        allowed_extensions: 允许的文件扩展名集合
        convert_to_format: 转换为的目标格式（PNG/JPEG/WEBP）

    Returns:
        Tuple[bool, str]: (是否成功, 消息或错误信息)
    """
    if not file or not file.filename:
        return False, "没有选择文件"

    # 检查文件扩展名
    if not allowed_file(file.filename, allowed_extensions):
        return (
            False,
            f"不支持的图片格式，仅支持: {', '.join(allowed_extensions or DEFAULT_ALLOWED_EXTENSIONS)}",
        )

    # 检查文件大小
    file_size = get_file_size_mb(file)
    if file_size > max_size_mb:
        return False, f"文件过大（{file_size:.2f}MB），最大允许 {max_size_mb}MB"

    try:
        # 读取图片
        image = Image.open(file.stream)

        # 如果是 RGBA 模式且要转为 JPEG，先转换为 RGB
        if convert_to_format.upper() == "JPEG" and image.mode in ("RGBA", "LA", "P"):
            # 创建白色背景
            background = Image.new("RGB", image.size, (255, 255, 255))
            if image.mode == "P":
                image = image.convert("RGBA")
            background.paste(
                image, mask=image.split()[-1] if image.mode == "RGBA" else None
            )
            image = background

        # 压缩图片
        image = compress_image(image, max_dimension)

        # 确保保存目录存在
        os.makedirs(save_folder, exist_ok=True)

        # 构造保存路径（使用目标格式的扩展名）
        ext = convert_to_format.lower()
        if ext == "jpg":
            ext = "jpeg"
        save_path = os.path.join(save_folder, f"{filename}.{ext}")

        # 保存图片
        save_kwargs = {}
        if convert_to_format.upper() in ("JPEG", "WEBP"):
            save_kwargs["quality"] = quality
            save_kwargs["optimize"] = True

        image.save(save_path, format=convert_to_format.upper(), **save_kwargs)

        logger.info(
            f"图片保存成功: {save_path}, 尺寸: {image.size}, 原始大小: {file_size:.2f}MB"
        )
        return True, "图片上传成功"

    except Exception as e:
        logger.error(f"保存图片失败: {str(e)}", exc_info=True)
        return False, f"图片处理失败: {str(e)}"


def delete_image(folder: str, filename_without_ext: str) -> bool:
    """删除图片文件（尝试删除所有可能的格式）

    Args:
        folder: 图片所在目录
        filename_without_ext: 文件名（不含扩展名）

    Returns:
        bool: 是否成功删除至少一个文件
    """
    deleted = False
    for ext in ["png", "jpg", "jpeg", "webp", "gif"]:
        file_path = os.path.join(folder, f"{filename_without_ext}.{ext}")
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.debug(f"删除图片: {file_path}")
                deleted = True
            except Exception as e:
                logger.error(f"删除图片失败: {file_path}, {str(e)}")
    return deleted
