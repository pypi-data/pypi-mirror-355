import contextlib
import logging
import os
import json
from collections.abc import AsyncIterator
from typing import Optional

import anyio
import click
import httpx
import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.types import Receive, Scope, Send

# ---------------------------------------------------------------------------
# OpenStack helpers
# ---------------------------------------------------------------------------
async def get_instances(filter_value: str = "", limit: int = 100, detail_level: str = "basic", **kwargs) -> list[dict]:
    """Get OpenStack instances with filtering and detail level options.
    
    Args:
        filter_value: Optional filter for instance name or ID
        limit: Maximum number of instances to return
        detail_level: Level of detail to return (basic, detailed, full)
        **kwargs: Additional keyword arguments for OpenStack connection
        
    Returns:
        List of instance dictionaries with information based on detail_level
        
    Raises:
        Exception: If OpenStack connection or query fails
    """
    from openstack import connection
    
    # 使用anyio在线程池中运行阻塞操作
    def get_instances():
        # 认证配置
        conn = connection.Connection(
            **kwargs
        )
        
        # 获取所有虚拟机实例
        servers = list(conn.compute.servers())
        
        # 应用过滤器
        if filter_value:
            servers = [s for s in servers if filter_value.lower() in s.name.lower() or filter_value in s.id]
        
        # 应用限制
        servers = servers[:limit]
        
        # 根据详细程度准备结果
        results = []
        for server in servers:
            if detail_level == "basic":
                instance_info = {
                    "id": server.id,
                    "name": server.name,
                    "status": server.status
                }
            elif detail_level == "detailed":
                instance_info = {
                    "id": server.id,
                    "name": server.name,
                    "status": server.status,
                    "flavor": getattr(server, "flavor", {}).get("id", "未知"),
                    "image": getattr(server, "image", {}).get("id", "未知"),
                    "addresses": getattr(server, "addresses", {}),
                    "created_at": getattr(server, "created_at", "未知")
                }
            else:  # full
                # 将服务器对象转换为字典
                instance_info = {k: v for k, v in server.to_dict().items() if v is not None}
            
            results.append(instance_info)
        
        return results
    
    # 在线程池中执行阻塞操作
    return await anyio.to_thread.run_sync(get_instances)


async def get_volumes(filter_value: str = "", limit: int = 100, detail_level: str = "basic", **kwargs) -> list[dict]:
    """Get OpenStack Cinder volumes with filtering and detail level options.
    
    Args:
        filter_value: Optional filter for volume name or ID
        limit: Maximum number of volumes to return
        detail_level: Level of detail to return (basic, detailed, full)
        **kwargs: Additional keyword arguments for OpenStack connection
        
    Returns:
        List of volume dictionaries with information based on detail_level
        
    Raises:
        Exception: If OpenStack connection or query fails
    """
    from openstack import connection
    
    # 使用anyio在线程池中运行阻塞操作
    def get_volumes():
        # 认证配置
        conn = connection.Connection(
            **kwargs
        )
        
        # 获取所有卷
        volumes = list(conn.block_storage.volumes())
        
        # 应用过滤器
        if filter_value:
            volumes = [v for v in volumes if (
                (v.name and filter_value.lower() in v.name.lower()) or 
                filter_value in v.id
            )]
        
        # 应用限制
        volumes = volumes[:limit]
        
        # 根据详细程度准备结果
        results = []
        for volume in volumes:
            if detail_level == "basic":
                volume_info = {
                    "id": volume.id,
                    "name": volume.name,
                    "status": volume.status,
                    "size": volume.size
                }
            elif detail_level == "detailed":
                volume_info = {
                    "id": volume.id,
                    "name": volume.name,
                    "status": volume.status,
                    "size": volume.size,
                    "volume_type": getattr(volume, "volume_type", "未知"),
                    "bootable": getattr(volume, "bootable", False),
                    "created_at": getattr(volume, "created_at", "未知"),
                    "attachments": getattr(volume, "attachments", []),
                    "availability_zone": getattr(volume, "availability_zone", "未知")
                }
            else:  # full
                # 将卷对象转换为字典
                volume_info = {k: v for k, v in volume.to_dict().items() if v is not None}
            
            results.append(volume_info)
        
        return results
    
    # 在线程池中执行阻塞操作
    return await anyio.to_thread.run_sync(get_volumes)


def format_instances_summary(instances: list[dict], detail_level: str = "basic") -> str:
    """格式化OpenStack实例信息为人类可读的摘要。
    
    Args:
        instances: OpenStack实例信息列表
        detail_level: 详细程度 (basic, detailed, full)
        
    Returns:
        格式化后的文本摘要
    """
    if not instances:
        return "未找到符合条件的OpenStack实例。"
    
    # 基本摘要信息
    summary = f"找到 {len(instances)} 个OpenStack实例:\n\n"
    for idx, instance in enumerate(instances, 1):
        summary += f"{idx}. ID: {instance['id']}\n"
        summary += f"   名称: {instance['name']}\n"
        summary += f"   状态: {instance['status']}\n"
        
        # 根据详细程度添加额外信息
        if detail_level != "basic":
            if "created_at" in instance:
                summary += f"   创建时间: {instance['created_at']}\n"
            if "flavor" in instance and instance["flavor"] != "未知":
                summary += f"   规格: {instance['flavor']}\n"
            if "addresses" in instance:
                summary += f"   网络地址: {json.dumps(instance['addresses'], ensure_ascii=False)}\n"
        
        summary += "\n"
    
    return summary


def format_volumes_summary(volumes: list[dict], detail_level: str = "basic") -> str:
    """格式化OpenStack卷信息为人类可读的摘要。
    
    Args:
        volumes: OpenStack卷信息列表
        detail_level: 详细程度 (basic, detailed, full)
        
    Returns:
        格式化后的文本摘要
    """
    if not volumes:
        return "未找到符合条件的OpenStack卷。"
    
    # 基本摘要信息
    summary = f"找到 {len(volumes)} 个OpenStack卷:\n\n"
    for idx, volume in enumerate(volumes, 1):
        summary += f"{idx}. ID: {volume['id']}\n"
        summary += f"   名称: {volume['name'] or '未命名'}\n"
        summary += f"   状态: {volume['status']}\n"
        summary += f"   大小: {volume['size']} GB\n"
        
        # 根据详细程度添加额外信息
        if detail_level != "basic":
            if "created_at" in volume:
                summary += f"   创建时间: {volume['created_at']}\n"
            if "volume_type" in volume:
                summary += f"   卷类型: {volume['volume_type']}\n"
            if "bootable" in volume:
                summary += f"   可启动: {'是' if volume['bootable'] == 'true' else '否'}\n"
            if "availability_zone" in volume:
                summary += f"   可用区: {volume['availability_zone']}\n"
            if "attachments" in volume and volume["attachments"]:
                summary += f"   挂载信息: {json.dumps(volume['attachments'], ensure_ascii=False)}\n"
        
        summary += "\n"
    
    return summary


async def process_instance_query(
    ctx, 
    filter_value: str = "", 
    limit: int = 100, 
    detail_level: str = "basic",
    get_instances_func = None
) -> Optional[list[types.TextContent]]:
    """处理OpenStack实例查询的完整流程。
    
    Args:
        ctx: MCP请求上下文
        filter_value: 实例筛选条件
        limit: 返回结果数量限制
        detail_level: 详细程度
        get_instances_func: 获取实例的函数
        
    Returns:
        返回格式化的结果或None（如果出现错误）
        
    Raises:
        ValueError: 如果查询过程中出现错误
    """
    await ctx.session.send_log_message(
        level="info",
        data=f"正在获取OpenStack实例信息...",
        logger="openstack",
        related_request_id=ctx.request_id,
    )
    
    try:
        # 异步运行OpenStack查询
        if get_instances_func:
            instances = await get_instances_func(filter_value, limit, detail_level)
        else:
            instances = await get_instances(filter_value, limit, detail_level)
        
        # 发送成功消息
        await ctx.session.send_log_message(
            level="info",
            data=f"成功获取到 {len(instances)} 个OpenStack实例",
            logger="openstack",
            related_request_id=ctx.request_id,
        )
        
        # 使用格式化函数生成摘要
        summary = format_instances_summary(instances, detail_level)
        
        return [
            types.TextContent(type="text", text=summary),
        ]
        
    except Exception as err:
        # 发送错误信息
        error_message = f"获取OpenStack实例信息失败: {str(err)}"
        await ctx.session.send_log_message(
            level="error",
            data=error_message,
            logger="openstack",
            related_request_id=ctx.request_id,
        )
        raise ValueError(error_message)


async def process_volume_query(
    ctx, 
    filter_value: str = "", 
    limit: int = 100, 
    detail_level: str = "basic",
    get_volumes_func = None
) -> Optional[list[types.TextContent]]:
    """处理OpenStack卷查询的完整流程。
    
    Args:
        ctx: MCP请求上下文
        filter_value: 卷筛选条件
        limit: 返回结果数量限制
        detail_level: 详细程度
        get_volumes_func: 获取卷的函数
        
    Returns:
        返回格式化的结果或None（如果出现错误）
        
    Raises:
        ValueError: 如果查询过程中出现错误
    """
    await ctx.session.send_log_message(
        level="info",
        data=f"正在获取OpenStack卷信息...",
        logger="openstack",
        related_request_id=ctx.request_id,
    )
    
    try:
        # 异步运行OpenStack查询
        if get_volumes_func:
            volumes = await get_volumes_func(filter_value, limit, detail_level)
        else:
            volumes = await get_volumes(filter_value, limit, detail_level)
        
        # 发送成功消息
        await ctx.session.send_log_message(
            level="info",
            data=f"成功获取到 {len(volumes)} 个OpenStack卷",
            logger="openstack",
            related_request_id=ctx.request_id,
        )
        
        # 使用格式化函数生成摘要
        summary = format_volumes_summary(volumes, detail_level)
        
        return [
            types.TextContent(type="text", text=summary),
        ]
        
    except Exception as err:
        # 发送错误信息
        error_message = f"获取OpenStack卷信息失败: {str(err)}"
        await ctx.session.send_log_message(
            level="error",
            data=error_message,
            logger="openstack",
            related_request_id=ctx.request_id,
        )
        raise ValueError(error_message)


async def get_networks(filter_value: str = "", limit: int = 100, detail_level: str = "basic", **kwargs) -> list[dict]:
    """Get OpenStack Neutron networks with filtering and detail level options.
    
    Args:
        filter_value: Optional filter for network name or ID
        limit: Maximum number of networks to return
        detail_level: Level of detail to return (basic, detailed, full)
        **kwargs: Additional keyword arguments for OpenStack connection
        
    Returns:
        List of network dictionaries with information based on detail_level
        
    Raises:
        Exception: If OpenStack connection or query fails
    """
    from openstack import connection
    
    # 使用anyio在线程池中运行阻塞操作
    def get_networks():
        # 认证配置
        conn = connection.Connection(
            **kwargs
        )
        
        # 获取所有网络
        networks = list(conn.network.networks())
        
        # 应用过滤器
        if filter_value:
            networks = [n for n in networks if (
                (n.name and filter_value.lower() in n.name.lower()) or 
                filter_value in n.id
            )]
        
        # 应用限制
        networks = networks[:limit]
        
        # 根据详细程度准备结果
        results = []
        for network in networks:
            # 将网络对象转换为字典以便更可靠地访问属性
            network_dict = network.to_dict()
            
            if detail_level == "basic":
                network_info = {
                    "id": network_dict.get("id", "未知"),
                    "name": network_dict.get("name", "未知"),
                    "status": network_dict.get("status", "未知"),
                    "is_shared": network_dict.get("shared", False),
                    "is_external": network_dict.get("router:external", False)
                }
            elif detail_level == "detailed":
                network_info = {
                    "id": network_dict.get("id", "未知"),
                    "name": network_dict.get("name", "未知"),
                    "status": network_dict.get("status", "未知"),
                    "is_shared": network_dict.get("shared", False),
                    "is_external": network_dict.get("router:external", False),
                    "mtu": network_dict.get("mtu", None),
                    "subnets": network_dict.get("subnets", []),
                    "availability_zones": network_dict.get("availability_zones", []),
                    "created_at": network_dict.get("created_at", "未知"),
                    "project_id": network_dict.get("project_id", "未知")
                }
            else:  # full
                # 使用完整的网络字典
                network_info = network_dict.copy()  # 创建副本以避免修改原始数据
                # 确保is_external字段存在，便于统一处理
                if "router:external" in network_info:
                    network_info["is_external"] = network_info["router:external"]
                # 过滤掉None值
                network_info = {k: v for k, v in network_info.items() if v is not None}
            
            results.append(network_info)
        
        return results
    
    # 在线程池中执行阻塞操作
    return await anyio.to_thread.run_sync(get_networks)


async def get_images(filter_value: str = "", limit: int = 100, detail_level: str = "basic", **kwargs) -> list[dict]:
    """Get OpenStack Glance images with filtering and detail level options.
    
    Args:
        filter_value: Optional filter for image name or ID
        limit: Maximum number of images to return
        detail_level: Level of detail to return (basic, detailed, full)
        **kwargs: Additional keyword arguments for OpenStack connection
        
    Returns:
        List of image dictionaries with information based on detail_level
        
    Raises:
        Exception: If OpenStack connection or query fails
    """
    from openstack import connection
    
    # 使用anyio在线程池中运行阻塞操作
    def get_images():
        # 认证配置
        conn = connection.Connection(
            **kwargs
        )
        
        # 获取所有镜像
        images = list(conn.image.images())
        
        # 应用过滤器
        if filter_value:
            images = [i for i in images if (
                (i.name and filter_value.lower() in i.name.lower()) or 
                filter_value in i.id
            )]
        
        # 应用限制
        images = images[:limit]
        
        # 根据详细程度准备结果
        results = []
        for image in images:
            if detail_level == "basic":
                image_info = {
                    "id": image.id,
                    "name": image.name,
                    "status": image.status,
                    "size": getattr(image, "size", 0),
                    "disk_format": getattr(image, "disk_format", "未知")
                }
            elif detail_level == "detailed":
                image_info = {
                    "id": image.id,
                    "name": image.name,
                    "status": image.status,
                    "size": getattr(image, "size", 0),
                    "disk_format": getattr(image, "disk_format", "未知"),
                    "container_format": getattr(image, "container_format", "未知"),
                    "min_disk": getattr(image, "min_disk", 0),
                    "min_ram": getattr(image, "min_ram", 0),
                    "created_at": getattr(image, "created_at", "未知"),
                    "updated_at": getattr(image, "updated_at", "未知"),
                    "visibility": getattr(image, "visibility", "未知"),
                    "protected": getattr(image, "protected", False),
                    "owner_id": getattr(image, "owner_id", "未知")
                }
            else:  # full
                # 将镜像对象转换为字典
                image_info = {k: v for k, v in image.to_dict().items() if v is not None}
            
            results.append(image_info)
        
        return results
    
    # 在线程池中执行阻塞操作
    return await anyio.to_thread.run_sync(get_images)


def format_networks_summary(networks: list[dict], detail_level: str = "basic") -> str:
    """格式化OpenStack网络信息为人类可读的摘要。
    
    Args:
        networks: OpenStack网络信息列表
        detail_level: 详细程度 (basic, detailed, full)
        
    Returns:
        格式化后的文本摘要
    """
    if not networks:
        return "未找到符合条件的OpenStack网络。"
    
    # 基本摘要信息
    summary = f"找到 {len(networks)} 个OpenStack网络:\n\n"
    for idx, network in enumerate(networks, 1):
        summary += f"{idx}. ID: {network['id']}\n"
        summary += f"   名称: {network['name'] or '未命名'}\n"
        summary += f"   状态: {network['status']}\n"
        summary += f"   共享: {'是' if network.get('is_shared') else '否'}\n"
        
        # 处理外部网络标志，可能是is_external或router:external
        is_external = network.get('is_external', network.get('router:external', False))
        summary += f"   外部网络: {'是' if is_external else '否'}\n"
        
        # 根据详细程度添加额外信息
        if detail_level != "basic":
            if "created_at" in network:
                summary += f"   创建时间: {network['created_at']}\n"
            if "mtu" in network and network["mtu"]:
                summary += f"   MTU: {network['mtu']}\n"
            if "subnets" in network and network["subnets"]:
                summary += f"   子网: {', '.join(network['subnets'])}\n"
            if "availability_zones" in network and network["availability_zones"]:
                summary += f"   可用区: {', '.join(network['availability_zones'])}\n"
            if "project_id" in network:
                summary += f"   项目ID: {network['project_id']}\n"
        
        summary += "\n"
    
    return summary


def format_images_summary(images: list[dict], detail_level: str = "basic") -> str:
    """格式化OpenStack镜像信息为人类可读的摘要。
    
    Args:
        images: OpenStack镜像信息列表
        detail_level: 详细程度 (basic, detailed, full)
        
    Returns:
        格式化后的文本摘要
    """
    if not images:
        return "未找到符合条件的OpenStack镜像。"
    
    # 基本摘要信息
    summary = f"找到 {len(images)} 个OpenStack镜像:\n\n"
    for idx, image in enumerate(images, 1):
        summary += f"{idx}. ID: {image['id']}\n"
        summary += f"   名称: {image['name'] or '未命名'}\n"
        summary += f"   状态: {image['status']}\n"
        
        # 格式化镜像大小
        size_mb = image.get('size', 0) / (1024 * 1024) if image.get('size') else 0
        if size_mb > 1024:
            size_gb = size_mb / 1024
            summary += f"   大小: {size_gb:.2f} GB\n"
        else:
            summary += f"   大小: {size_mb:.2f} MB\n"
            
        summary += f"   格式: {image.get('disk_format', '未知')}\n"
        
        # 根据详细程度添加额外信息
        if detail_level != "basic":
            if "container_format" in image:
                summary += f"   容器格式: {image['container_format']}\n"
            if "min_disk" in image:
                summary += f"   最小磁盘: {image['min_disk']} GB\n"
            if "min_ram" in image:
                summary += f"   最小内存: {image['min_ram']} MB\n"
            if "created_at" in image:
                summary += f"   创建时间: {image['created_at']}\n"
            if "visibility" in image:
                summary += f"   可见性: {image['visibility']}\n"
            if "protected" in image:
                summary += f"   受保护: {'是' if image['protected'] else '否'}\n"
            if "owner_id" in image:
                summary += f"   所有者ID: {image['owner_id']}\n"
        
        summary += "\n"
    
    return summary


async def process_network_query(
    ctx, 
    filter_value: str = "", 
    limit: int = 100, 
    detail_level: str = "basic",
    get_networks_func = None
) -> Optional[list[types.TextContent]]:
    """处理OpenStack网络查询的完整流程。
    
    Args:
        ctx: MCP请求上下文
        filter_value: 网络筛选条件
        limit: 返回结果数量限制
        detail_level: 详细程度
        get_networks_func: 获取网络的函数
        
    Returns:
        返回格式化的结果或None（如果出现错误）
        
    Raises:
        ValueError: 如果查询过程中出现错误
    """
    await ctx.session.send_log_message(
        level="info",
        data=f"正在获取OpenStack网络信息...",
        logger="openstack",
        related_request_id=ctx.request_id,
    )
    
    try:
        # 异步运行OpenStack查询
        if get_networks_func:
            networks = await get_networks_func(filter_value, limit, detail_level)
        else:
            networks = await get_networks(filter_value, limit, detail_level)
        
        # 发送成功消息
        await ctx.session.send_log_message(
            level="info",
            data=f"成功获取到 {len(networks)} 个OpenStack网络",
            logger="openstack",
            related_request_id=ctx.request_id,
        )
        
        # 使用格式化函数生成摘要
        summary = format_networks_summary(networks, detail_level)
        
        return [
            types.TextContent(type="text", text=summary),
        ]
        
    except Exception as err:
        # 发送错误信息
        error_message = f"获取OpenStack网络信息失败: {str(err)}"
        await ctx.session.send_log_message(
            level="error",
            data=error_message,
            logger="openstack",
            related_request_id=ctx.request_id,
        )
        raise ValueError(error_message)


async def process_image_query(
    ctx, 
    filter_value: str = "", 
    limit: int = 100, 
    detail_level: str = "basic",
    get_images_func = None
) -> Optional[list[types.TextContent]]:
    """处理OpenStack镜像查询的完整流程。
    
    Args:
        ctx: MCP请求上下文
        filter_value: 镜像筛选条件
        limit: 返回结果数量限制
        detail_level: 详细程度
        get_images_func: 获取镜像的函数
        
    Returns:
        返回格式化的结果或None（如果出现错误）
        
    Raises:
        ValueError: 如果查询过程中出现错误
    """
    await ctx.session.send_log_message(
        level="info",
        data=f"正在获取OpenStack镜像信息...",
        logger="openstack",
        related_request_id=ctx.request_id,
    )
    
    try:
        # 异步运行OpenStack查询
        if get_images_func:
            images = await get_images_func(filter_value, limit, detail_level)
        else:
            images = await get_images(filter_value, limit, detail_level)
        
        # 发送成功消息
        await ctx.session.send_log_message(
            level="info",
            data=f"成功获取到 {len(images)} 个OpenStack镜像",
            logger="openstack",
            related_request_id=ctx.request_id,
        )
        
        # 使用格式化函数生成摘要
        summary = format_images_summary(images, detail_level)
        
        return [
            types.TextContent(type="text", text=summary),
        ]
        
    except Exception as err:
        # 发送错误信息
        error_message = f"获取OpenStack镜像信息失败: {str(err)}"
        await ctx.session.send_log_message(
            level="error",
            data=error_message,
            logger="openstack",
            related_request_id=ctx.request_id,
        )
        raise ValueError(error_message)


@click.command()
@click.option("--port", default=8000, help="Port to listen on for HTTP")
@click.option(
    "--log-level",
    default="INFO",
    help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
)
@click.option(
    "--json-response",
    is_flag=True,
    default=False,
    help="Enable JSON responses instead of SSE streams",
)
@click.option(
    "--auth-url",
    default="http://127.0.0.1:5000/v3",
    required=True,
    help="OpenStack认证URL",
)
@click.option(
    "--username",
    default="admin",
    required=True,
    help="OpenStack用户名",
)
@click.option(
    "--password",
    default="admin",
    required=True,
    help="OpenStack密码",
)
@click.option(
    "--project-name",
    default="admin",
    help="OpenStack项目名称",
)
@click.option(
    "--user-domain-name",
    default="Default",
    help="OpenStack用户域名",
)
@click.option(
    "--project-domain-name",
    default="Default",
    help="OpenStack项目域名",
)
def main(
    port: int, 
    log_level: str, 
    json_response: bool,
    auth_url: str,
    username: str,
    password: str,
    project_name: str,
    user_domain_name: str,
    project_domain_name: str
) -> int:
    """Run an MCP OpenStack server using Streamable HTTP transport."""

    # ---------------------- Configure logging ----------------------
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger("openstack-server")

    # ---------------------- Create MCP Server ----------------------
    app = Server("mcp-streamable-http-openstack")

    # OpenStack认证配置
    openstack_config = {
        "auth_url": auth_url,
        "username": username,
        "password": password,
        "project_name": project_name,
        "user_domain_name": user_domain_name,
        "project_domain_name": project_domain_name
    }
    
    # 更新get_instances函数以使用配置
    async def get_instances_with_config(filter_value: str = "", limit: int = 100, detail_level: str = "basic") -> list[dict]:
        """使用命令行配置获取OpenStack实例。"""
        return await get_instances(
            filter_value=filter_value,
            limit=limit,
            detail_level=detail_level,
            **openstack_config
        )
        
    # 更新get_volumes函数以使用配置
    async def get_volumes_with_config(filter_value: str = "", limit: int = 100, detail_level: str = "basic") -> list[dict]:
        """使用命令行配置获取OpenStack卷。"""
        return await get_volumes(
            filter_value=filter_value,
            limit=limit,
            detail_level=detail_level,
            **openstack_config
        )
        
    # 更新get_networks函数以使用配置
    async def get_networks_with_config(filter_value: str = "", limit: int = 100, detail_level: str = "basic") -> list[dict]:
        """使用命令行配置获取OpenStack网络。"""
        return await get_networks(
            filter_value=filter_value,
            limit=limit,
            detail_level=detail_level,
            **openstack_config
        )
        
    # 更新get_images函数以使用配置
    async def get_images_with_config(filter_value: str = "", limit: int = 100, detail_level: str = "basic") -> list[dict]:
        """使用命令行配置获取OpenStack镜像。"""
        return await get_images(
            filter_value=filter_value,
            limit=limit,
            detail_level=detail_level,
            **openstack_config
        )

    # ---------------------- Tool implementation -------------------
    @app.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
        """Handle the tool calls."""
        ctx = app.request_context
        
        # 处理OpenStack实例查询工具
        if name == "get_instances":
            filter_value = arguments.get("filter", "")
            limit = arguments.get("limit", 100)  # 默认最多返回100个实例
            detail_level = arguments.get("detail_level", "basic")
            
            return await process_instance_query(
                ctx, 
                filter_value, 
                limit, 
                detail_level, 
                get_instances_func=get_instances_with_config
            )
        
        # 处理OpenStack卷查询工具
        elif name == "get_volumes":
            filter_value = arguments.get("filter", "")
            limit = arguments.get("limit", 100)  # 默认最多返回100个卷
            detail_level = arguments.get("detail_level", "basic")
            
            return await process_volume_query(
                ctx, 
                filter_value, 
                limit, 
                detail_level, 
                get_volumes_func=get_volumes_with_config
            )
        
        # 处理OpenStack网络查询工具
        elif name == "get_networks":
            filter_value = arguments.get("filter", "")
            limit = arguments.get("limit", 100)  # 默认最多返回100个网络
            detail_level = arguments.get("detail_level", "basic")
            
            return await process_network_query(
                ctx, 
                filter_value, 
                limit, 
                detail_level, 
                get_networks_func=get_networks_with_config
            )
        
        # 处理OpenStack镜像查询工具
        elif name == "get_images":
            filter_value = arguments.get("filter", "")
            limit = arguments.get("limit", 100)  # 默认最多返回100个镜像
            detail_level = arguments.get("detail_level", "basic")
            
            return await process_image_query(
                ctx, 
                filter_value, 
                limit, 
                detail_level, 
                get_images_func=get_images_with_config
            )
        
        else:
            raise ValueError(f"Unknown tool: {name}")

    # ---------------------- Tool registry -------------------------
    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        """Expose available tools to the LLM."""
        return [
            types.Tool(
                name="get_instances",
                description="获取OpenStack虚拟机实例的详细信息",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "filter": {
                            "type": "string",
                            "description": "筛选条件，如实例名称或ID",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "返回结果的最大数量",
                        },
                        "detail_level": {
                            "type": "string",
                            "enum": ["basic", "detailed", "full"],
                            "description": "返回信息的详细程度",
                            "default": "basic"
                        }
                    },
                },
            ),
            types.Tool(
                name="get_volumes",
                description="获取OpenStack存储卷(Cinder)的详细信息",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "filter": {
                            "type": "string",
                            "description": "筛选条件，如卷名称或ID",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "返回结果的最大数量",
                        },
                        "detail_level": {
                            "type": "string",
                            "enum": ["basic", "detailed", "full"],
                            "description": "返回信息的详细程度",
                            "default": "basic"
                        }
                    },
                },
            ),
            types.Tool(
                name="get_networks",
                description="获取OpenStack网络的详细信息",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "filter": {
                            "type": "string",
                            "description": "筛选条件，如网络名称或ID",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "返回结果的最大数量",
                        },
                        "detail_level": {
                            "type": "string",
                            "enum": ["basic", "detailed", "full"],
                            "description": "返回信息的详细程度",
                            "default": "basic"
                        }
                    },
                },
            ),
            types.Tool(
                name="get_images",
                description="获取OpenStack镜像的详细信息",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "filter": {
                            "type": "string",
                            "description": "筛选条件，如镜像名称或ID",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "返回结果的最大数量",
                        },
                        "detail_level": {
                            "type": "string",
                            "enum": ["basic", "detailed", "full"],
                            "description": "返回信息的详细程度",
                            "default": "basic"
                        }
                    },
                },
            )
        ]

    # ---------------------- Session manager -----------------------
    session_manager = StreamableHTTPSessionManager(
        app=app,
        event_store=None,  # 无状态；不保存历史事件
        json_response=json_response,
        stateless=True,
    )

    async def handle_streamable_http(scope: Scope, receive: Receive, send: Send) -> None:  # noqa: D401,E501
        await session_manager.handle_request(scope, receive, send)

    # ---------------------- Lifespan Management --------------------
    @contextlib.asynccontextmanager
    async def lifespan(app: Starlette) -> AsyncIterator[None]:
        async with session_manager.run():
            logger.info("OpenStack MCP server started! 🚀")
            try:
                yield
            finally:
                logger.info("OpenStack MCP server shutting down…")

    # ---------------------- ASGI app + Uvicorn ---------------------
    starlette_app = Starlette(
        debug=False,
        routes=[Mount("/openstack", app=handle_streamable_http)],
        lifespan=lifespan,
    )

    import uvicorn

    uvicorn.run(starlette_app, host="0.0.0.0", port=port)

    return 0


if __name__ == "__main__":
    main()
