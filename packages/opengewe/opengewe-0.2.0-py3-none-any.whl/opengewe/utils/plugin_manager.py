"""插件管理器模块

提供插件管理器，负责插件的加载、卸载和重载。
"""

from __future__ import annotations

import importlib
import inspect
import os
import sys
import asyncio
from pathlib import Path

# 根据Python版本导入不同的TOML解析库
try:
    import tomllib
except ImportError:
    import tomli as tomllib
import traceback
from typing import Dict, List, Type, Union, Tuple, Optional, Any, TYPE_CHECKING

from opengewe.utils.singleton import Singleton
from opengewe.utils.event_manager import EventManager
from opengewe.utils.plugin_base import PluginBase
from opengewe.logger import init_default_logger, get_logger

init_default_logger()
if TYPE_CHECKING:
    from opengewe.client import GeweClient
    from opengewe.callback.models.base import BaseMessage

# 获取插件管理器日志记录器
logger = get_logger("PluginManager")


class PluginManager(metaclass=Singleton):
    """插件管理器

    负责插件的加载、卸载和重载。
    使用单例模式确保全局只有一个插件管理器实例。
    """

    def __init__(self):
        """初始化插件管理器"""
        # 已启用的插件实例
        self.plugins: Dict[str, PluginBase] = {}
        # 所有加载过的插件类
        self.plugin_classes: Dict[str, Type[PluginBase]] = {}
        # 插件信息
        self.plugin_info: Dict[str, Dict[str, Any]] = {}

        # 客户端实例
        self.client = None

        # 初始化事件管理器
        self.event_manager = EventManager()

        # 读取配置文件中的禁用插件列表
        # 在 __init__ 方法中
        config_path = self._find_project_root() / "main_config.toml"
        try:
            with open(config_path, "rb") as f:
                main_config = tomllib.load(f)
                self.excluded_plugins = main_config.get("plugins", {}).get(
                    "disabled_plugins", []
                )
        except FileNotFoundError:
            logger.warning(f"未找到配置文件 {config_path}，使用空的禁用插件列表")
            self.excluded_plugins = []
        except Exception:
            logger.error(f"读取配置文件失败: {traceback.format_exc()}")
            self.excluded_plugins = []

    # 新增的方法
    def _find_project_root(self) -> Path:
        """查找项目根目录"""
        current_path = Path(__file__).parent

        while current_path != current_path.parent:
            if (
                (current_path / "main_config.toml").exists()
                or (current_path / "pyproject.toml").exists()
                or (current_path / "main_config_example.toml").exists()
            ):
                return current_path
            current_path = current_path.parent

        logger.warning("未找到项目根目录，使用当前工作目录")
        return Path.cwd()

    def set_client(self, client: "GeweClient") -> None:
        """设置客户端实例

        Args:
            client: GeweClient实例
        """
        self.client = client

    async def load_plugin(self, plugin: Union[Type[PluginBase], str]) -> bool:
        """加载单个插件

        Args:
            plugin: 插件类或插件名称

        Returns:
            bool: 是否成功加载插件
        """
        # 确保插件路径已正确设置
        self._ensure_plugin_paths()

        if isinstance(plugin, str):
            return await self._load_plugin_name(plugin)
        elif isinstance(plugin, type) and issubclass(plugin, PluginBase):
            return await self._load_plugin_class(plugin)
        return False

    def _ensure_plugin_paths(self) -> None:
        """确保插件路径已正确设置

        将plugins目录和plugins/utils目录添加到Python的模块搜索路径中，
        使插件可以通过'utils'模块名称直接导入桥接层
        """
        # 获取项目根目录（从当前文件向上4级目录）
        # 当前文件路径: src/opengewe/utils/plugin_manager.py
        # 项目根目录: ../../../../
        project_root = Path(__file__).parent.parent.parent.parent
        plugins_dir = project_root / "plugins"
        plugins_dir_str = str(plugins_dir.absolute())

        # 确保plugins目录存在
        if not plugins_dir.exists():
            try:
                plugins_dir.mkdir(parents=True, exist_ok=True)
                logger.info(f"插件目录不存在，已创建: {plugins_dir_str}")
                # 创建__init__.py文件以使其成为有效的Python包
                init_file = plugins_dir / "__init__.py"
                if not init_file.exists():
                    with open(init_file, "w", encoding="utf-8") as f:
                        f.write("# 插件目录\n")
                    logger.info(f"创建了插件包初始化文件: {init_file}")
            except Exception as e:
                logger.error(f"创建插件目录失败: {e}")
                logger.warning("将使用内存中的插件，不会加载文件系统中的插件")

        # 确保plugins目录在搜索路径中
        if plugins_dir_str not in sys.path:
            sys.path.insert(0, plugins_dir_str)

        # 确保plugins的父目录也在搜索路径中
        # 这样插件可以通过相对导入找到utils包
        parent_dir = str(project_root.absolute())
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)

        # 确保当前目录在搜索路径中，有些插件可能使用相对导入
        current_dir = os.getcwd()
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)

        logger.debug(f"已设置插件搜索路径: {sys.path[:5]}...")

    async def _load_plugin_class(
        self,
        plugin_class: Type[PluginBase],
        is_disabled: bool = False,
        retry_count: int = 0,
    ) -> bool:
        """加载单个插件类

        Args:
            plugin_class: 插件类
            is_disabled: 该插件是否被外部配置文件禁用
            retry_count: 当前重试次数，用于错误恢复

        Returns:
            bool: 是否成功加载插件

        Note:
            插件会在以下两种情况下被跳过加载：
            1. 当插件在外部配置中被禁用（is_disabled=True）
            2. 当插件自身的配置中设置了enable=False
        """
        max_retries = 1  # 最大重试次数
        plugin_name = plugin_class.__name__

        try:
            # 防止重复加载插件
            if plugin_name in self.plugins:
                return False

            # 安全获取插件目录名
            directory = "unknown"
            try:
                module_name = plugin_class.__module__
                if module_name.startswith("plugins."):
                    directory = module_name.split(".")[1]
                else:
                    logger.warning(f"非常规插件模块路径: {module_name}")
            except Exception as e:
                logger.error(f"获取插件目录失败: {e}")
                directory = "error"

            # 记录插件信息，即使插件被禁用也会记录
            self.plugin_info[plugin_name] = {
                "name": plugin_name,
                "description": plugin_class.description,
                "author": plugin_class.author,
                "version": plugin_class.version,
                "directory": directory,
                "enabled": False,
                "class": plugin_class,
                "error": None,  # 记录插件可能的错误信息
            }

            # 创建插件实例，以检查其自身配置
            try:
                plugin = plugin_class()

                # 检查插件自身是否在配置中设置为禁用
                plugin_self_disabled = hasattr(plugin, "enable") and not plugin.enable
            except Exception as e:
                error_msg = f"初始化插件 {plugin_name} 实例时出错: {e}"
                logger.error(error_msg)
                logger.error(traceback.format_exc())

                # 记录错误信息
                if plugin_name in self.plugin_info:
                    self.plugin_info[plugin_name]["error"] = error_msg

                # 如果未达到最大重试次数，尝试重新加载
                if retry_count < max_retries:
                    logger.warning(
                        f"尝试重新加载插件 {plugin_name}，第 {retry_count + 1} 次重试"
                    )
                    # 短暂延迟后重试
                    await asyncio.sleep(0.5)
                    return await self._load_plugin_class(
                        plugin_class, is_disabled, retry_count + 1
                    )
                return False

            # 如果插件被外部禁用或自身配置为禁用，则跳过加载
            if is_disabled or plugin_self_disabled:
                logger.info(
                    f"插件 {plugin_name} {'被配置文件禁用' if is_disabled else '在插件配置中被禁用'}, 跳过加载"
                )
                return False

            # 绑定事件处理方法
            EventManager.bind_instance(plugin)

            try:
                # 启用插件
                await plugin.on_enable(self.client)
                # 执行异步初始化
                await plugin.async_init()
            except Exception as e:
                error_msg = f"启用插件 {plugin_name} 时出错: {e}"
                logger.error(error_msg)
                logger.error(traceback.format_exc())

                # 记录错误信息
                if plugin_name in self.plugin_info:
                    self.plugin_info[plugin_name]["error"] = error_msg

                # 尝试解绑事件，确保不会留下部分绑定的事件
                try:
                    EventManager.unbind_instance(plugin)
                except Exception:
                    pass

                # 如果未达到最大重试次数，尝试重新加载
                if retry_count < max_retries:
                    logger.warning(
                        f"尝试重新加载插件 {plugin_name}，第 {retry_count + 1} 次重试"
                    )
                    # 短暂延迟后重试
                    await asyncio.sleep(0.5)
                    return await self._load_plugin_class(
                        plugin_class, is_disabled, retry_count + 1
                    )
                return False

            # 记录插件实例和类
            self.plugins[plugin_name] = plugin
            self.plugin_classes[plugin_name] = plugin_class
            self.plugin_info[plugin_name]["enabled"] = True

            # 清除错误信息（如果之前有的话）
            if "error" in self.plugin_info[plugin_name]:
                self.plugin_info[plugin_name]["error"] = None

            logger.info(f"加载插件 {plugin_name} 成功")
            return True
        except Exception as e:
            error_msg = f"加载插件 {plugin_name} 时发生错误: {e}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())

            # 记录错误信息
            if plugin_name in self.plugin_info:
                self.plugin_info[plugin_name]["error"] = error_msg

            # 如果未达到最大重试次数，尝试重新加载
            if retry_count < max_retries:
                logger.warning(
                    f"尝试重新加载插件 {plugin_name}，第 {retry_count + 1} 次重试"
                )
                # 短暂延迟后重试
                await asyncio.sleep(0.5)
                return await self._load_plugin_class(
                    plugin_class, is_disabled, retry_count + 1
                )
            return False

    async def _load_plugin_name(self, plugin_name: str) -> bool:
        """通过名称加载单个插件

        Args:
            plugin_name: 插件类名称

        Returns:
            bool: 是否成功加载插件
        """
        found = False

        try:
            plugins_dir = os.path.abspath("plugins")
            if not os.path.exists(plugins_dir):
                logger.warning(f"插件目录不存在: {plugins_dir}")
                return False

            for dirname in os.listdir(plugins_dir):
                try:
                    plugin_path = os.path.join(plugins_dir, dirname)
                    main_file = os.path.join(plugin_path, "main.py")

                    if os.path.isdir(plugin_path) and os.path.exists(main_file):
                        module = importlib.import_module(f"plugins.{dirname}.main")
                        importlib.reload(module)

                        for name, obj in inspect.getmembers(module):
                            if (
                                inspect.isclass(obj)
                                and issubclass(obj, PluginBase)
                                and obj != PluginBase
                                and obj.__name__ == plugin_name
                            ):
                                found = True
                                return await self._load_plugin_class(obj)
                except Exception:
                    logger.error(
                        f"检查 {dirname} 时发生错误:\n{traceback.format_exc()}"
                    )
                    continue
        except FileNotFoundError:
            logger.warning(f"插件目录不存在: {plugins_dir}")
            return False
        except PermissionError:
            logger.warning(f"无权限访问插件目录: {plugins_dir}")
            return False
        except Exception as e:
            logger.error(
                f"加载插件 {plugin_name} 时发生未知错误: {e}\n{traceback.format_exc()}"
            )
            return False

        if not found:
            logger.warning(f"未找到插件类 {plugin_name}")
            return False
        return False

    async def load_plugins(self, load_disabled: bool = False) -> List[str]:
        """加载所有插件

        Args:
            load_disabled: 是否加载被禁用的插件

        Returns:
            List[str]: 成功加载的插件名称列表
        """
        # 确保插件路径已正确设置
        self._ensure_plugin_paths()

        loaded_plugins = []

        try:
            # 检查插件目录是否存在
            plugins_dir = os.path.abspath("plugins")
            if not os.path.exists(plugins_dir):
                logger.warning(f"插件目录不存在: {plugins_dir}")
                return loaded_plugins

            # 检查插件目录是否可读
            if not os.access(plugins_dir, os.R_OK):
                logger.warning(f"无法读取插件目录: {plugins_dir}")
                return loaded_plugins

            for dirname in os.listdir(plugins_dir):
                plugin_path = os.path.join(plugins_dir, dirname)
                main_file = os.path.join(plugin_path, "main.py")

                if os.path.isdir(plugin_path) and os.path.exists(main_file):
                    try:
                        module = importlib.import_module(f"plugins.{dirname}.main")
                        # 重新加载模块，确保获取最新的代码
                        importlib.reload(module)

                        for name, obj in inspect.getmembers(module):
                            if (
                                inspect.isclass(obj)
                                and issubclass(obj, PluginBase)
                                and obj != PluginBase
                            ):
                                is_disabled = False
                                if not load_disabled:
                                    is_disabled = (
                                        obj.__name__ in self.excluded_plugins
                                        or dirname in self.excluded_plugins
                                    )

                                if await self._load_plugin_class(
                                    obj, is_disabled=is_disabled
                                ):
                                    loaded_plugins.append(obj.__name__)
                    except Exception:
                        logger.error(
                            f"加载 {dirname} 时发生错误:\n{traceback.format_exc()}"
                        )
        except FileNotFoundError:
            logger.warning(f"插件目录不存在: {plugins_dir}")
        except PermissionError:
            logger.warning(f"无权限访问插件目录: {plugins_dir}")
        except Exception as e:
            logger.error(f"加载插件时发生未知错误: {e}\n{traceback.format_exc()}")

        return loaded_plugins

    async def unload_plugin(self, plugin_name: str) -> bool:
        """卸载单个插件

        Args:
            plugin_name: 插件名称

        Returns:
            bool: 是否成功卸载插件
        """
        if plugin_name not in self.plugins:
            logger.warning(f"插件 {plugin_name} 未加载，无法卸载")
            return False

        # 防止卸载 ManagePlugin
        if plugin_name == "ManagePlugin":
            logger.warning("ManagePlugin 不能被卸载")
            return False

        try:
            plugin = self.plugins[plugin_name]
            # 禁用插件
            await plugin.on_disable()
            # 解绑事件处理方法
            EventManager.unbind_instance(plugin)

            # 从记录中删除插件
            del self.plugins[plugin_name]
            # 保留插件类，以便重新加载
            if plugin_name in self.plugin_info:
                self.plugin_info[plugin_name]["enabled"] = False

            logger.info(f"卸载插件 {plugin_name} 成功")
            return True
        except Exception:
            logger.error(
                f"卸载插件 {plugin_name} 时发生错误:\n{traceback.format_exc()}"
            )
            return False

    async def unload_plugins(self) -> Tuple[List[str], List[str]]:
        """卸载所有插件

        Returns:
            Tuple[List[str], List[str]]: 成功卸载的插件名称列表和失败的插件名称列表
        """
        unloaded_plugins = []
        failed_unloads = []

        for plugin_name in list(self.plugins.keys()):
            if await self.unload_plugin(plugin_name):
                unloaded_plugins.append(plugin_name)
            else:
                failed_unloads.append(plugin_name)

        return unloaded_plugins, failed_unloads

    async def reload_plugin(self, plugin_name: str) -> bool:
        """重载单个插件

        Args:
            plugin_name: 插件名称

        Returns:
            bool: 是否成功重载插件
        """
        if plugin_name not in self.plugin_classes:
            logger.warning(f"插件 {plugin_name} 未加载，无法重载")
            return False

        # 防止重载 ManagePlugin
        if plugin_name == "ManagePlugin":
            logger.warning("ManagePlugin 不能被重载")
            return False

        try:
            # 获取插件类所在的模块
            plugin_class = self.plugin_classes[plugin_name]
            module_name = plugin_class.__module__

            # 先卸载插件
            if not await self.unload_plugin(plugin_name):
                return False

            # 重新导入模块
            try:
                module = importlib.import_module(module_name)
                importlib.reload(module)
            except Exception:
                logger.error(
                    f"重新导入模块 {module_name} 失败: {traceback.format_exc()}"
                )
                return False

            # 从重新加载的模块中获取插件类
            for name, obj in inspect.getmembers(module):
                if (
                    inspect.isclass(obj)
                    and issubclass(obj, PluginBase)
                    and obj != PluginBase
                    and obj.__name__ == plugin_name
                ):
                    # 使用新的插件类重新加载
                    return await self._load_plugin_class(obj)

            logger.error(f"在重新加载的模块 {module_name} 中未找到插件类 {plugin_name}")
            return False
        except Exception:
            logger.error(
                f"重载插件 {plugin_name} 时发生错误:\n{traceback.format_exc()}"
            )
            return False

    async def reload_plugins(self) -> List[str]:
        """重载所有插件

        Returns:
            List[str]: 成功重载的插件名称列表
        """
        reloaded_plugins = []

        try:
            # 记录当前加载的插件名称，排除 ManagePlugin
            original_plugins = [
                name for name in self.plugins.keys() if name != "ManagePlugin"
            ]

            # 卸载除 ManagePlugin 外的所有插件
            for plugin_name in original_plugins:
                await self.unload_plugin(plugin_name)

            # 清除所有插件模块的缓存
            for module_name in list(sys.modules.keys()):
                if module_name.startswith("plugins.") and not module_name.endswith(
                    "ManagePlugin"
                ):
                    try:
                        del sys.modules[module_name]
                    except KeyError:
                        pass

            # 重新加载原来的插件
            for plugin_name in original_plugins:
                if await self.load_plugin(plugin_name):
                    reloaded_plugins.append(plugin_name)

            return reloaded_plugins
        except Exception:
            logger.error(f"重载插件时发生错误:\n{traceback.format_exc()}")
            return reloaded_plugins

    async def refresh_plugins(self) -> Tuple[List[str], List[str]]:
        """刷新插件

        卸载所有插件，然后从文件系统重新加载所有插件。

        Returns:
            Tuple[List[str], List[str]]: 成功加载的插件名称列表和卸载但未能重新加载的插件名称列表
        """
        # 确保插件路径已正确设置
        self._ensure_plugin_paths()

        # 记录当前加载的插件
        original_plugins = set(self.plugins.keys())
        logger.info(f"刷新插件: {original_plugins}")
        # 卸载所有插件
        unloaded, _ = await self.unload_plugins()

        # 清除模块缓存
        for module_name in list(sys.modules.keys()):
            if module_name.startswith("plugins."):
                try:
                    del sys.modules[module_name]
                except KeyError:
                    pass

        # 重新加载所有插件
        loaded_plugins = await self.load_plugins()

        # 找出卸载了但没有重新加载的插件
        not_reloaded = [p for p in unloaded if p not in loaded_plugins]

        return loaded_plugins, not_reloaded

    def get_plugin_info(
        self, plugin_name: Optional[str] = None
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """获取插件信息

        Args:
            plugin_name: 插件名称，如果为None则返回所有插件的信息

        Returns:
            Union[Dict[str, Any], List[Dict[str, Any]]]: 插件信息或所有插件的信息列表
        """
        if plugin_name is not None:
            return self.plugin_info.get(plugin_name, {})

        # 返回所有插件信息的列表
        return list(self.plugin_info.values())

    async def register_plugin(self, plugin: Union[Type[PluginBase], str]) -> bool:
        """注册插件（加载插件的别名）

        Args:
            plugin: 插件类或插件名称

        Returns:
            bool: 是否成功加载插件
        """
        return await self.load_plugin(plugin)

    async def load_plugins_from_directory(
        self, directory: str, prefix: str = ""
    ) -> List[str]:
        """从指定目录加载所有插件

        Args:
            directory: 插件目录路径
            prefix: 模块前缀

        Returns:
            List[str]: 成功加载的插件名称列表
        """
        # 确保插件路径已正确设置
        self._ensure_plugin_paths()

        loaded_plugins = []

        try:
            # 检查指定目录是否存在
            if not os.path.exists(directory):
                logger.warning(f"指定的插件目录不存在: {directory}")
                return loaded_plugins

            # 检查指定目录是否可读
            if not os.access(directory, os.R_OK):
                logger.warning(f"无法读取指定的插件目录: {directory}")
                return loaded_plugins

            # 确保指定目录在搜索路径中
            abs_directory = os.path.abspath(directory)
            if abs_directory not in sys.path:
                sys.path.insert(0, abs_directory)

            for dirname in os.listdir(directory):
                plugin_path = os.path.join(directory, dirname)
                main_file = os.path.join(plugin_path, "main.py")

                if os.path.isdir(plugin_path) and os.path.exists(main_file):
                    try:
                        # 构建模块名
                        if prefix:
                            module_name = f"{prefix}.{dirname}.main"
                        else:
                            module_name = f"{dirname}.main"

                        module = importlib.import_module(module_name)
                        importlib.reload(module)

                        for name, obj in inspect.getmembers(module):
                            if (
                                inspect.isclass(obj)
                                and issubclass(obj, PluginBase)
                                and obj != PluginBase
                            ):
                                if await self._load_plugin_class(obj):
                                    loaded_plugins.append(obj.__name__)
                    except Exception:
                        logger.error(
                            f"从 {directory} 加载 {dirname} 时发生错误:\n{traceback.format_exc()}"
                        )
        except FileNotFoundError:
            logger.warning(f"指定的插件目录不存在: {directory}")
        except PermissionError:
            logger.warning(f"无权限访问指定的插件目录: {directory}")
        except Exception as e:
            logger.error(
                f"从 {directory} 加载插件时发生未知错误: {e}\n{traceback.format_exc()}"
            )

        return loaded_plugins

    async def process_message(self, message: "BaseMessage") -> None:
        """处理消息

        将消息通过EventManager发送给所有插件的处理方法。

        Args:
            message: BaseMessage实例
        """
        if not self.client:
            logger.warning("未设置客户端实例，无法处理消息")
            return

        # 使用EventManager发送消息事件
        await EventManager.emit(message.type, self.client, message)

    async def get_failed_plugins(self) -> Dict[str, str]:
        """获取加载失败的插件列表及错误信息

        Returns:
            Dict[str, str]: 插件名称和对应的错误信息
        """
        failed_plugins = {}
        for name, info in self.plugin_info.items():
            if info.get("error") is not None:
                failed_plugins[name] = info["error"]
        return failed_plugins

    async def disable_plugin_in_config(self, plugin_name: str) -> bool:
        """在内存中禁用插件

        将插件添加到内存中的禁用列表，但不修改配置文件
        请注意：此更改仅在当前运行期间有效，重启后将从配置文件重新加载

        Args:
            plugin_name: 插件名称

        Returns:
            bool: 是否成功禁用插件
        """
        try:
            # 检查插件是否已经在禁用列表中
            if plugin_name in self.excluded_plugins:
                logger.info(f"插件 {plugin_name} 已经在禁用列表中")
                return True

            # 添加到内存中的禁用列表
            self.excluded_plugins.append(plugin_name)

            logger.info(f"已在内存中禁用插件 {plugin_name}，但此更改不会保存到配置文件")
            logger.info(
                "若要永久禁用插件，请手动编辑 main_config.toml 文件中的 plugins.disabled_plugins 列表"
            )
            return True
        except Exception as e:
            logger.error(f"禁用插件 {plugin_name} 时出错: {e}")
            logger.error(traceback.format_exc())
            return False
