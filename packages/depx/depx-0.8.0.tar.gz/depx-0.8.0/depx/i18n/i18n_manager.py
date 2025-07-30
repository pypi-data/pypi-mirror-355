"""
国际化管理器

负责语言切换和文本翻译
"""

import locale
import logging
import os
from pathlib import Path
from typing import Dict, Optional

import yaml

logger = logging.getLogger(__name__)


class I18nManager:
    """国际化管理器"""

    def __init__(self):
        self._translations: Dict[str, Dict] = {}
        self._current_language = "en"
        self._fallback_language = "en"
        self._load_translations()

    def _load_translations(self):
        """加载所有语言文件"""
        i18n_dir = Path(__file__).parent

        # 加载支持的语言文件
        for lang_file in i18n_dir.glob("*.yaml"):
            if lang_file.stem in ["en", "zh"]:
                try:
                    with open(lang_file, "r", encoding="utf-8") as f:
                        self._translations[lang_file.stem] = yaml.safe_load(f)
                    logger.debug(f"已加载语言文件: {lang_file.stem}")
                except Exception as e:
                    logger.warning(f"加载语言文件失败 {lang_file}: {e}")

    def set_language(self, language: str, silent: bool = False) -> bool:
        """
        设置当前语言

        Args:
            language: 语言代码 (en, zh)
            silent: 是否静默模式（不显示警告）

        Returns:
            是否设置成功
        """
        if language in self._translations:
            self._current_language = language
            logger.info(f"语言已切换到: {language}")
            return True
        else:
            if not silent:
                logger.warning(f"不支持的语言: {language}")
            return False

    def get_current_language(self) -> str:
        """获取当前语言"""
        return self._current_language

    def get_text(self, key: str, **kwargs) -> str:
        """
        获取翻译文本

        Args:
            key: 文本键，支持点号分隔的嵌套键 (如 "cli.scan.help")
            **kwargs: 格式化参数

        Returns:
            翻译后的文本
        """
        # 尝试从当前语言获取
        text = self._get_nested_value(
            self._translations.get(self._current_language, {}), key
        )

        # 如果没找到，尝试从备用语言获取
        if text is None:
            text = self._get_nested_value(
                self._translations.get(self._fallback_language, {}), key
            )

        # 如果还是没找到，返回键本身
        if text is None:
            logger.warning(f"未找到翻译文本: {key}")
            return key

        # 格式化文本
        try:
            return text.format(**kwargs) if kwargs else text
        except Exception as e:
            logger.warning(f"文本格式化失败 {key}: {e}")
            return text

    def _get_nested_value(self, data: dict, key: str):
        """获取嵌套字典中的值"""
        keys = key.split(".")
        current = data

        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return None

        return current

    def auto_detect_language(self) -> str:
        """
        智能检测系统语言

        检测优先级：
        1. DEPX_LANG 环境变量
        2. LANG 环境变量
        3. LC_ALL 环境变量
        4. 系统默认 locale
        5. 终端语言设置
        6. 回退到英文

        Returns:
            检测到的语言代码
        """
        detection_methods = [
            self._detect_from_depx_env,
            self._detect_from_lang_env,
            self._detect_from_lc_env,
            self._detect_from_system_locale,
            self._detect_from_terminal,
        ]

        for method in detection_methods:
            try:
                detected_lang = method()
                if detected_lang and detected_lang in self._translations:
                    logger.debug(
                        f"语言检测成功: {detected_lang} (方法: {method.__name__})"
                    )
                    return detected_lang
                elif detected_lang:
                    logger.debug(
                        f"检测到不支持的语言: {detected_lang} (方法: {method.__name__})"
                    )
            except Exception as e:
                logger.debug(f"语言检测方法 {method.__name__} 失败: {e}")

        logger.debug(f"所有检测方法失败，使用回退语言: {self._fallback_language}")
        return self._fallback_language

    def _detect_from_depx_env(self) -> Optional[str]:
        """从 DEPX_LANG 环境变量检测"""
        return os.environ.get("DEPX_LANG")

    def _detect_from_lang_env(self) -> Optional[str]:
        """从 LANG 环境变量检测"""
        lang = os.environ.get("LANG", "")
        return self._parse_locale_string(lang)

    def _detect_from_lc_env(self) -> Optional[str]:
        """从 LC_ALL 环境变量检测"""
        lc_all = os.environ.get("LC_ALL", "")
        return self._parse_locale_string(lc_all)

    def _detect_from_system_locale(self) -> Optional[str]:
        """从系统默认 locale 检测"""
        try:
            system_locale = locale.getdefaultlocale()[0]
            return self._parse_locale_string(system_locale or "")
        except Exception:
            return None

    def _detect_from_terminal(self) -> Optional[str]:
        """从终端设置检测"""
        try:
            # 尝试检测终端的语言设置
            import subprocess

            result = subprocess.run(
                ["locale"], capture_output=True, text=True, timeout=2
            )
            if result.returncode == 0:
                for line in result.stdout.split("\n"):
                    if line.startswith("LANG="):
                        lang_value = line.split("=", 1)[1].strip('"')
                        return self._parse_locale_string(lang_value)
        except Exception:
            pass
        return None

    def _parse_locale_string(self, locale_str: str) -> Optional[str]:
        """
        解析 locale 字符串，提取语言代码

        支持的格式：
        - zh_CN.UTF-8 -> zh
        - en_US.UTF-8 -> en
        - zh-CN -> zh
        - en-US -> en
        - zh -> zh
        - en -> en
        """
        if not locale_str:
            return None

        # 转换为小写并清理
        locale_str = locale_str.lower().strip()

        # 中文检测 (支持各种中文变体)
        chinese_indicators = [
            "zh",
            "zh_cn",
            "zh_tw",
            "zh_hk",
            "zh_sg",
            "zh-cn",
            "zh-tw",
            "zh-hk",
            "zh-sg",
            "chinese",
            "china",
            "taiwan",
            "hongkong",
        ]

        for indicator in chinese_indicators:
            if locale_str.startswith(indicator):
                return "zh"

        # 英文检测
        english_indicators = [
            "en",
            "en_us",
            "en_gb",
            "en_ca",
            "en_au",
            "en-us",
            "en-gb",
            "en-ca",
            "en-au",
            "english",
            "american",
            "british",
        ]

        for indicator in english_indicators:
            if locale_str.startswith(indicator):
                return "en"

        return None


# 全局实例
_i18n_manager = I18nManager()


def get_text(key: str, **kwargs) -> str:
    """获取翻译文本的便捷函数"""
    return _i18n_manager.get_text(key, **kwargs)


def set_language(language: str, silent: bool = False) -> bool:
    """设置语言的便捷函数"""
    return _i18n_manager.set_language(language, silent)


def get_current_language() -> str:
    """获取当前语言的便捷函数"""
    return _i18n_manager.get_current_language()


def auto_detect_and_set_language():
    """自动检测并设置语言"""
    detected_lang = _i18n_manager.auto_detect_language()
    _i18n_manager.set_language(detected_lang, silent=True)
    return detected_lang


def get_language_detection_info() -> Dict[str, str]:
    """
    获取语言检测的详细信息，用于调试

    Returns:
        包含各种检测方法结果的字典
    """
    info = {}

    # 环境变量
    info["DEPX_LANG"] = os.environ.get("DEPX_LANG", "未设置")
    info["LANG"] = os.environ.get("LANG", "未设置")
    info["LC_ALL"] = os.environ.get("LC_ALL", "未设置")

    # 系统 locale
    try:
        system_locale = locale.getdefaultlocale()
        info["system_locale"] = f"{system_locale[0]} / {system_locale[1]}"
    except Exception as e:
        info["system_locale"] = f"检测失败: {e}"

    # 终端 locale
    try:
        import subprocess

        result = subprocess.run(["locale"], capture_output=True, text=True, timeout=2)
        if result.returncode == 0:
            info["terminal_locale"] = result.stdout.strip()
        else:
            info["terminal_locale"] = "命令执行失败"
    except Exception as e:
        info["terminal_locale"] = f"检测失败: {e}"

    # 最终检测结果
    info["detected_language"] = _i18n_manager.auto_detect_language()
    info["current_language"] = _i18n_manager.get_current_language()

    return info
