import re
from typing import Dict, Any, Optional, Union, List, Tuple, Type, TypeVar
from pathlib import Path
from mdbq.log import mylogger
from dataclasses import dataclass, field
from enum import Enum
import time

logger = mylogger.MyLogger(
    logging_mode='both',
    log_level='info',
    log_format='json',
    max_log_size=50,
    backup_count=5,
    enable_async=False,  # 是否启用异步日志
    sample_rate=1,  # 采样DEBUG/INFO日志
    sensitive_fields=[],  #  敏感字段过滤
    enable_metrics=False,  # 是否启用性能指标
)

T = TypeVar('T')  # 类型变量


class ConfigError(Exception):
    """配置相关的基础异常类
    
    Attributes:
        message: 错误消息
        file_path: 配置文件路径
        section: 配置节名称
        key: 配置键名称
    """
    def __init__(self, message: str, file_path: Optional[Union[str, Path]] = None, 
                 section: Optional[str] = None, key: Optional[str] = None):
        self.message = message
        self.file_path = str(file_path) if file_path else None
        self.section = section
        self.key = key
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        """格式化错误消息"""
        parts = [self.message]
        if self.file_path:
            parts.append(f"文件: {self.file_path}")
        if self.section:
            parts.append(f"节: [{self.section}]")
        if self.key:
            parts.append(f"键: {self.key}")
        return " | ".join(parts)


class ConfigFileNotFoundError(ConfigError):
    """当指定的配置文件不存在时抛出的异常"""
    def __init__(self, file_path: Union[str, Path]):
        super().__init__("配置文件不存在", file_path=file_path)


class ConfigReadError(ConfigError):
    """当读取配置文件失败时抛出的异常
    
    Attributes:
        original_error: 原始错误对象
    """
    def __init__(self, file_path: Union[str, Path], original_error: Exception):
        super().__init__(
            f"读取配置文件失败: {str(original_error)}",
            file_path=file_path
        )
        self.original_error = original_error


class ConfigWriteError(ConfigError):
    """当写入配置文件失败时抛出的异常
    
    Attributes:
        original_error: 原始错误对象
    """
    def __init__(self, file_path: Union[str, Path], original_error: Exception):
        super().__init__(
            f"写入配置文件失败: {str(original_error)}",
            file_path=file_path
        )
        self.original_error = original_error


class ConfigValueError(ConfigError):
    """当配置值无效时抛出的异常"""
    def __init__(self, message: str, file_path: Union[str, Path], 
                 section: Optional[str] = None, key: Optional[str] = None):
        super().__init__(message, file_path=file_path, section=section, key=key)


class ConfigSectionNotFoundError(ConfigError):
    """当指定的配置节不存在时抛出的异常"""
    def __init__(self, file_path: Union[str, Path], section: str):
        super().__init__(
            f"配置节不存在",
            file_path=file_path,
            section=section
        )


class ConfigKeyNotFoundError(ConfigError):
    """当指定的配置键不存在时抛出的异常"""
    def __init__(self, file_path: Union[str, Path], section: str, key: str):
        super().__init__(
            f"配置键不存在",
            file_path=file_path,
            section=section,
            key=key
        )


class CommentStyle(Enum):
    """配置文件支持的注释风格"""
    HASH = '#'  # Python风格注释
    DOUBLE_SLASH = '//'  # C风格注释
    SEMICOLON = ';'  # INI风格注释


@dataclass
class ConfigOptions:
    """配置解析器的选项类
    
    Attributes:
        comment_styles: 支持的注释风格列表
        encoding: 文件编码
        auto_create: 是否自动创建不存在的配置文件
        strip_values: 是否去除配置值的首尾空白
        preserve_comments: 是否保留注释
        default_section: 默认配置节名称
        separators: 支持的分隔符列表
        cache_ttl: 缓存过期时间（秒）
        validate_keys: 是否验证键名
        key_pattern: 键名正则表达式模式
        case_sensitive: 是否区分大小写
    """
    comment_styles: List[CommentStyle] = field(default_factory=lambda: [CommentStyle.HASH, CommentStyle.DOUBLE_SLASH])
    encoding: str = 'utf-8'
    auto_create: bool = False
    strip_values: bool = True
    preserve_comments: bool = True
    default_section: str = 'DEFAULT'
    separators: List[str] = field(default_factory=lambda: ['=', ':', '：'])
    cache_ttl: int = 300  # 5分钟缓存过期
    validate_keys: bool = True
    key_pattern: str = r'^[a-zA-Z0-9_\-\.]+$'
    case_sensitive: bool = False


class ConfigParser:
    """配置文件解析器，用于读取和写入配置文件
    
    Attributes:
        options: 解析器配置选项
        _config_cache: 配置缓存，用于存储已读取的配置
        _cache_timestamps: 缓存时间戳，用于管理缓存过期
        _comments_cache: 注释缓存，用于存储每个配置节的注释
        _section_map: 用于存储大小写映射
        _current_file: 当前正在处理的文件路径
    """
    
    def __init__(self, options: Optional[ConfigOptions] = None):
        self.options = options or ConfigOptions()
        self._config_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_timestamps: Dict[str, float] = {}
        self._comments_cache: Dict[str, Dict[str, List[str]]] = {}
        self._section_map: Dict[str, Dict[str, str]] = {}  # 用于存储大小写映射
        self._current_file: Optional[Path] = None  # 当前正在处理的文件路径
    
    def __enter__(self) -> 'ConfigParser':
        """进入上下文管理器
        
        Returns:
            ConfigParser: 返回当前实例
        """
        return self

    def __exit__(self, exc_type: Optional[Type[BaseException]], 
                 exc_val: Optional[BaseException], 
                 exc_tb: Optional[Any]) -> None:
        """退出上下文管理器
        
        Args:
            exc_type: 异常类型
            exc_val: 异常值
            exc_tb: 异常追踪信息
        """
        self._current_file = None

    def open(self, file_path: Union[str, Path]) -> 'ConfigParser':
        """打开配置文件
        
        Args:
            file_path: 配置文件路径
            
        Returns:
            ConfigParser: 返回当前实例，支持链式调用
            
        Raises:
            ConfigFileNotFoundError: 当配置文件不存在且未启用自动创建时
        """
        file_path = Path(file_path)
        if not file_path.exists() and not self.options.auto_create:
            raise ConfigFileNotFoundError(file_path)
        self._current_file = file_path
        return self

    def _ensure_file_open(self) -> None:
        """确保文件已打开
        
        Raises:
            ConfigError: 当文件未打开时
        """
        if self._current_file is None:
            raise ConfigError("未打开任何配置文件，请先调用 open() 方法")

    def _is_comment_line(self, line: str) -> bool:
        """判断一行是否为注释行"""
        stripped = line.strip()
        return any(stripped.startswith(style.value) for style in self.options.comment_styles)
    
    def _extract_comment(self, line: str) -> Tuple[str, str]:
        """从行中提取注释
        
        Returns:
            Tuple[str, str]: (去除注释后的行内容, 注释内容)
        """
        for style in self.options.comment_styles:
            comment_match = re.search(fr'\s+{re.escape(style.value)}.*$', line)
            if comment_match:
                return line[:comment_match.start()].strip(), comment_match.group(0)
        return line.strip(), ''
    
    def _split_key_value(self, line: str) -> Optional[Tuple[str, str]]:
        """分割配置行为键值对
        
        Args:
            line: 要分割的配置行
            
        Returns:
            Optional[Tuple[str, str]]: 键值对元组，如果无法分割则返回None
        """
        for sep in self.options.separators:
            if sep in line:
                key_part, value_part = line.split(sep, 1)
                return key_part.strip(), value_part
        
        for sep in [':', '：']:
            if sep in line:
                pattern = fr'\s*{re.escape(sep)}\s*'
                parts = re.split(pattern, line, 1)
                if len(parts) == 2:
                    return parts[0].strip(), parts[1]
        
        return None
    
    def _validate_key(self, key: str) -> bool:
        """验证键名是否合法"""
        if not self.options.validate_keys:
            return True
        return bool(re.match(self.options.key_pattern, key))
    
    def _get_cached_config(self, file_path: str) -> Optional[Dict[str, Any]]:
        """获取缓存的配置，如果过期则返回None"""
        if file_path not in self._config_cache:
            return None
        
        if file_path not in self._cache_timestamps:
            return None
        
        if time.time() - self._cache_timestamps[file_path] > self.options.cache_ttl:
            return None
        
        return self._config_cache[file_path]
    
    def _update_cache(self, file_path: str, config: Dict[str, Any]) -> None:
        """更新配置缓存"""
        self._config_cache[file_path] = config
        self._cache_timestamps[file_path] = time.time()
    
    def _normalize_section(self, section: str) -> str:
        """标准化节名称（处理大小写）"""
        if self.options.case_sensitive:
            return section
        return section.lower()
    
    def _get_original_section(self, file_path: str, normalized_section: str) -> Optional[str]:
        """获取原始节名称"""
        if self.options.case_sensitive:
            return normalized_section
        return self._section_map.get(file_path, {}).get(normalized_section)
    
    def _update_section_map(self, file_path: str, section: str) -> None:
        """更新节名称映射"""
        if not self.options.case_sensitive:
            normalized = self._normalize_section(section)
            if file_path not in self._section_map:
                self._section_map[file_path] = {}
            self._section_map[file_path][normalized] = section
    
    def _clear_cache(self, file_path: Optional[str] = None) -> None:
        """清除配置缓存"""
        if file_path:
            self._config_cache.pop(file_path, None)
            self._cache_timestamps.pop(file_path, None)
            self._comments_cache.pop(file_path, None)
            self._section_map.pop(file_path, None)
        else:
            self._config_cache.clear()
            self._cache_timestamps.clear()
            self._comments_cache.clear()
            self._section_map.clear()
    
    def _convert_value(self, value: str, target_type: Type[T]) -> T:
        """转换配置值到指定类型
        
        Args:
            value: 要转换的值
            target_type: 目标类型
            
        Returns:
            T: 转换后的值
            
        Raises:
            ConfigValueError: 当值无法转换为指定类型时
        """
        try:
            if target_type == bool:
                return bool(value.lower() in ('true', 'yes', '1', 'on'))
            elif target_type == list:
                # 支持多种分隔符的列表
                if not value.strip():
                    return []
                # 尝试不同的分隔符
                for sep in [',', ';', '|', ' ']:
                    if sep in value:
                        return [item.strip() for item in value.split(sep) if item.strip()]
                # 如果没有分隔符，则作为单个元素返回
                return [value.strip()]
            elif target_type == tuple:
                # 支持元组类型
                if not value.strip():
                    return ()
                # 尝试不同的分隔符
                for sep in [',', ';', '|', ' ']:
                    if sep in value:
                        return tuple(item.strip() for item in value.split(sep) if item.strip())
                # 如果没有分隔符，则作为单个元素返回
                return (value.strip(),)
            elif target_type == set:
                # 支持集合类型
                if not value.strip():
                    return set()
                # 尝试不同的分隔符
                for sep in [',', ';', '|', ' ']:
                    if sep in value:
                        return {item.strip() for item in value.split(sep) if item.strip()}
                # 如果没有分隔符，则作为单个元素返回
                return {value.strip()}
            elif target_type == dict:
                # 支持字典类型，格式：key1=value1,key2=value2
                if not value.strip():
                    return {}
                result = {}
                # 尝试不同的分隔符
                for sep in [',', ';', '|']:
                    if sep in value:
                        pairs = [pair.strip() for pair in value.split(sep) if pair.strip()]
                        for pair in pairs:
                            if '=' in pair:
                                key, val = pair.split('=', 1)
                                result[key.strip()] = val.strip()
                        return result
                # 如果没有分隔符，尝试单个键值对
                if '=' in value:
                    key, val = value.split('=', 1)
                    return {key.strip(): val.strip()}
                return {}
            elif target_type == int:
                # 支持十六进制、八进制、二进制
                value = value.strip().lower()
                if value.startswith('0x'):
                    return int(value, 16)
                elif value.startswith('0o'):
                    return int(value, 8)
                elif value.startswith('0b'):
                    return int(value, 2)
                return int(value)
            elif target_type == float:
                return float(value)
            elif target_type == complex:
                return complex(value)
            elif target_type == bytes:
                return value.encode('utf-8')
            elif target_type == bytearray:
                return bytearray(value.encode('utf-8'))
            elif target_type == set:
                return set(value.split(','))
            elif target_type == frozenset:
                return frozenset(value.split(','))
            elif target_type == range:
                # 支持 range 类型，格式：start:stop:step 或 start:stop
                parts = value.split(':')
                if len(parts) == 2:
                    return range(int(parts[0]), int(parts[1]))
                elif len(parts) == 3:
                    return range(int(parts[0]), int(parts[1]), int(parts[2]))
                raise ValueError("Invalid range format")
            return target_type(value)
        except (ValueError, TypeError) as e:
            raise ConfigValueError(
                f"无法将值 '{value}' 转换为类型 {target_type.__name__}",
                file_path=None,
                key=None
            )
    
    def get_value(self, file_path: Optional[Union[str, Path]] = None, key: str = None, 
                 section: Optional[str] = None, default: Any = None,
                 value_type: Optional[Type[T]] = None) -> T:
        """获取指定配置项的值
        
        Args:
            file_path: 配置文件路径，如果为None则使用当前打开的文件
            key: 配置键
            section: 配置节名称，如果为None则使用默认节
            default: 当配置项不存在时返回的默认值
            value_type: 期望的值的类型
            
        Returns:
            T: 配置值
            
        Raises:
            ConfigSectionNotFoundError: 当指定的节不存在且未提供默认值时
            ConfigKeyNotFoundError: 当指定的键不存在且未提供默认值时
            ConfigValueError: 当值无法转换为指定类型时
        """
        if file_path is None:
            self._ensure_file_open()
            file_path = self._current_file
        if not self._validate_key(key):
            raise ConfigValueError(f"无效的键名: {key}", file_path=file_path, key=key)
            
        config = self.read(file_path)
        section = section or self.options.default_section
        normalized_section = self._normalize_section(section)
        
        # 获取原始节名称
        original_section = self._get_original_section(str(file_path), normalized_section)
        if original_section is None:
            if default is not None:
                return default
            raise ConfigSectionNotFoundError(file_path, section)
            
        if key not in config[original_section]:
            if default is not None:
                return default
            raise ConfigKeyNotFoundError(file_path, original_section, key)
            
        value = config[original_section][key]
        
        if value_type is not None:
            return self._convert_value(value, value_type)
            
        return value
    
    def get_values(self, keys: List[Tuple[str, str]], 
                  file_path: Optional[Union[str, Path]] = None,
                  defaults: Optional[Dict[str, Any]] = None,
                  value_types: Optional[Dict[str, Type]] = None) -> Dict[str, Any]:
        """批量获取多个配置项的值
        
        Args:
            keys: 配置项列表，每个元素为 (section, key) 元组
            file_path: 配置文件路径，如果为None则使用当前打开的文件
            defaults: 默认值字典，格式为 {key: default_value}
            value_types: 值类型字典，格式为 {key: type}
            
        Returns:
            Dict[str, Any]: 配置值字典，格式为 {key: value}
            
        Raises:
            ConfigSectionNotFoundError: 当指定的节不存在且未提供默认值时
            ConfigKeyNotFoundError: 当指定的键不存在且未提供默认值时
            ConfigValueError: 当值无法转换为指定类型时
        """
        if file_path is None:
            self._ensure_file_open()
            file_path = self._current_file
        defaults = defaults or {}
        value_types = value_types or {}
        result = {}
        
        for section, key in keys:
            try:
                value = self.get_value(
                    file_path=file_path,
                    key=key,
                    section=section,
                    default=defaults.get(key),
                    value_type=value_types.get(key)
                )
                result[key] = value
            except (ConfigSectionNotFoundError, ConfigKeyNotFoundError) as e:
                if key in defaults:
                    result[key] = defaults[key]
                else:
                    raise e
                    
        return result

    def get_section_values(self, keys: List[str],
                          section: Optional[str] = None,
                          file_path: Optional[Union[str, Path]] = None,
                          defaults: Optional[Dict[str, Any]] = None,
                          value_types: Optional[Dict[str, Type]] = None) -> Tuple[Any, ...]:
        """获取指定节点下多个键的值元组
        
        Args:
            keys: 要获取的键列表
            section: 配置节名称，默认为 DEFAULT
            file_path: 配置文件路径，如果为None则使用当前打开的文件
            defaults: 默认值字典，格式为 {key: default_value}
            value_types: 值类型字典，格式为 {key: type}
            
        Returns:
            Tuple[Any, ...]: 按键列表顺序返回的值元组
            
        Raises:
            ConfigSectionNotFoundError: 当指定的节不存在且未提供默认值时
            ConfigKeyNotFoundError: 当指定的键不存在且未提供默认值时
            ConfigValueError: 当值无法转换为指定类型时
        """
        if file_path is None:
            self._ensure_file_open()
            file_path = self._current_file
        defaults = defaults or {}
        value_types = value_types or {}
        result = []
        
        for key in keys:
            try:
                value = self.get_value(
                    file_path=file_path,
                    key=key,
                    section=section,
                    default=defaults.get(key),
                    value_type=value_types.get(key)
                )
                result.append(value)
            except (ConfigSectionNotFoundError, ConfigKeyNotFoundError) as e:
                if key in defaults:
                    result.append(defaults[key])
                else:
                    raise e
                    
        return tuple(result)
    
    def set_value(self, key: str, value: Any,
                 section: Optional[str] = None,
                 file_path: Optional[Union[str, Path]] = None,
                 value_type: Optional[Type] = None) -> None:
        """设置指定配置项的值，保持原始文件的格式和注释
        
        Args:
            key: 配置键
            value: 要设置的值
            section: 配置节名称，如果为None则使用默认节
            file_path: 配置文件路径，如果为None则使用当前打开的文件
            value_type: 值的类型，用于验证和转换
            
        Raises:
            ConfigValueError: 当值无法转换为指定类型时
            ConfigError: 当其他配置错误发生时
        """
        if file_path is None:
            self._ensure_file_open()
            file_path = self._current_file
        if not self._validate_key(key):
            raise ConfigValueError(f"无效的键名: {key}", file_path=file_path, key=key)
            
        # 读取原始文件內容
        original_lines = []
        if file_path.exists():
            with open(file_path, 'r', encoding=self.options.encoding) as file:
                original_lines = file.readlines()
        
        # 读取当前配置
        config = self.read(file_path)
        
        if section not in config:
            config[section] = {}
            
        if value_type is not None:
            try:
                if value_type == bool:
                    if isinstance(value, str):
                        value = value.lower() in ('true', 'yes', '1', 'on')
                    else:
                        value = bool(value)
                else:
                    value = value_type(value)
            except (ValueError, TypeError) as e:
                raise ConfigValueError(
                    f"无法将值 '{value}' 转换为类型 {value_type.__name__}",
                    file_path=file_path,
                    section=section,
                    key=key
                )
        
        if isinstance(value, bool):
            value = str(value).lower()
        else:
            value = str(value)
            
        # 更新配置
        config[section][key] = value
        
        # 写入文件，保持原始格式
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding=self.options.encoding) as file:
                current_section = self.options.default_section
                section_separators = {}  # 用于存储每个section使用的分隔符
                
                # 解析原始文件，提取格式信息
                for line in original_lines:
                    stripped_line = line.strip()
                    
                    if not stripped_line:
                        file.write(line)  # 保持空行
                        continue
                        
                    if stripped_line.startswith('[') and stripped_line.endswith(']'):
                        current_section = stripped_line[1:-1]
                        file.write(line)  # 保持节标记的原始格式
                        continue
                        
                    if self._is_comment_line(stripped_line):
                        file.write(line)  # 保持注释的原始格式
                        continue
                        
                    key_value = self._split_key_value(stripped_line)
                    if key_value:
                        orig_key, orig_value = key_value
                        # 检测使用的分隔符
                        for sep in self.options.separators:
                            if sep in line:
                                section_separators.setdefault(current_section, {})[orig_key] = sep
                                break
                        
                        # 如果是当前要修改的键，则写入新值
                        if current_section == section and orig_key == key:
                            separator = section_separators.get(current_section, {}).get(orig_key, self.options.separators[0])
                            # 提取行尾注释
                            comment = ''
                            for style in self.options.comment_styles:
                                comment_match = re.search(fr'\s+{re.escape(style.value)}.*$', line)
                                if comment_match:
                                    comment = comment_match.group(0)
                                    break
                            # 写入新值并保留注释
                            file.write(f'{key}{separator}{value}{comment}\n')
                        else:
                            file.write(line)  # 保持其他行的原始格式
                    else:
                        file.write(line)  # 保持无法解析的行的原始格式
                
                # 如果section不存在，则添加新的section
                if section not in [line.strip()[1:-1] for line in original_lines if line.strip().startswith('[') and line.strip().endswith(']')]:
                    file.write(f'\n[{section}]\n')
                    file.write(f'{key}={value}\n')
            
            self._clear_cache(str(file_path))
            
        except Exception as e:
            raise ConfigWriteError(file_path, e)
    
    def read(self, file_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
        """读取配置文件内容
        
        Args:
            file_path: 配置文件路径，如果为None则使用当前打开的文件
            
        Returns:
            Dict[str, Any]: 配置字典，格式为 {section: {key: value}}
            
        Raises:
            ConfigFileNotFoundError: 当配置文件不存在且未启用自动创建时
            ConfigReadError: 当读取配置文件失败时
        """
        if file_path is None:
            self._ensure_file_open()
            file_path = self._current_file
        else:
            file_path = Path(file_path)  # 确保 file_path 是 Path 对象
        
        # 检查缓存
        cached_config = self._get_cached_config(str(file_path))
        if cached_config is not None:
            return cached_config
        
        if not file_path.exists():
            if not self.options.auto_create:
                raise ConfigFileNotFoundError(file_path)
            logger.info(f'配置文件不存在，将创建: {file_path}')
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.touch()
            return {}
        
        try:
            with open(file_path, 'r', encoding=self.options.encoding) as file:
                config = {}
                current_section = self.options.default_section
                section_comments = []
                
                for line in file:
                    stripped_line = line.strip()
                    
                    if not stripped_line or self._is_comment_line(stripped_line):
                        if self.options.preserve_comments:
                            section_comments.append(line.rstrip())
                        continue
                    
                    if stripped_line.startswith('[') and stripped_line.endswith(']'):
                        current_section = stripped_line[1:-1]
                        if not self._validate_key(current_section):
                            raise ConfigValueError(
                                f"无效的节名: {current_section}",
                                file_path=file_path,
                                section=current_section
                            )
                        self._update_section_map(str(file_path), current_section)
                        if current_section not in config:
                            config[current_section] = {}
                        if self.options.preserve_comments:
                            self._comments_cache.setdefault(str(file_path), {}).setdefault(current_section, []).extend(section_comments)
                            section_comments = []
                        continue
                    
                    key_value = self._split_key_value(stripped_line)
                    if key_value:
                        key, value = key_value
                        if not self._validate_key(key):
                            raise ConfigValueError(
                                f"无效的键名: {key}",
                                file_path=file_path,
                                section=current_section,
                                key=key
                            )
                        value, comment = self._extract_comment(value)
                        
                        if self.options.strip_values:
                            value = value.strip()
                        
                        if current_section not in config:
                            config[current_section] = {}
                        
                        config[current_section][key] = value
                        if self.options.preserve_comments and comment:
                            self._comments_cache.setdefault(str(file_path), {}).setdefault(current_section, []).append(comment)
                
                self._update_cache(str(file_path), config)
                return config
                
        except Exception as e:
            raise ConfigReadError(file_path, e)
    

def main() -> None:
    # 使用示例
    config_file = Path('/Users/xigua/spd.txt')
    
    # 方式1：使用上下文管理器
    with ConfigParser() as parser:
        parser.open(config_file)
        host, port, username, password = parser.get_section_values(
            keys=['host', 'port', 'username', 'password'],
            section='mysql'
        )
        print("方式1结果:", host, port, username, password)
        
        # 修改配置
        parser.set_value('host', 'localhost', section='mysql')
        parser.set_value('port', 3306, section='mysql')
        
        # # 读取整个配置
        # config = parser.read()
        # print("\n当前配置:")
        # for section, items in config.items():
        #     print(f"\n[{section}]")
        #     for key, value in items.items():
        #         print(f"{key} = {value}")
    
    # 方式2：链式调用
    parser = ConfigParser()
    host, port, username, password = parser.open(config_file).get_section_values(
        keys=['host', 'port', 'username', 'password'],
        section='mysql'
    )
    print("\n方式2结果:", host, port, username, password)
    
    # 方式3：传统方式
    parser = ConfigParser()
    host, port, username, password = parser.get_section_values(
        file_path=config_file,
        section='mysql',
        keys=['host', 'port', 'username', 'password']
    )
    print("\n方式3结果:", host, port, username, password)


if __name__ == '__main__':
    main()
