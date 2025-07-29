"""
作者：Xiaoqiang
微信公众号：XiaoqiangClub
创建时间：2025/5/29 09:07
文件描述：Chrome绿色版下载工具
文件路径：/AutoChrome/AutoChrome/chrome_downloader.py
"""

import os
import shutil
import zipfile
import tempfile
import platform
import requests
import time
from tqdm import tqdm
from typing import Optional, Dict, Any, Literal
from .errors import ChromeDownloadError, ChromePermissionError, ChromePathError


class ChromiumDownloader:
    # Chromium最新快照版本号获取URL
    CHROMIUM_SNAPSHOT_URLS: Dict[str, str] = {
        "windows": "https://storage.googleapis.com/chromium-browser-snapshots/Win_x64/LAST_CHANGE",
        "darwin": "https://storage.googleapis.com/chromium-browser-snapshots/Mac/LAST_CHANGE",
        "linux": "https://storage.googleapis.com/chromium-browser-snapshots/Linux_x64/LAST_CHANGE",
    }
    # Chromium官方快照下载URL模板
    CHROMIUM_DOWNLOAD_URLS: Dict[str, str] = {
        "windows": "https://storage.googleapis.com/chromium-browser-snapshots/Win_x64/{rev}/chrome-win.zip",
        "darwin": "https://storage.googleapis.com/chromium-browser-snapshots/Mac/{rev}/chrome-mac.zip",
        "linux": "https://storage.googleapis.com/chromium-browser-snapshots/Linux_x64/{rev}/chrome-linux.zip",
    }

    def __init__(
            self,
            download_dir: Optional[str] = None,
            logger: Optional[Any] = None,
            custom_source: Optional[Dict[str, Dict[str, str]]] = None,
            max_retries: int = 3,
            retry_delay: float = 5.0,
            timeout: int = 60,
    ):
        """
        Chromium绿色版下载工具

        :param download_dir: 下载目录，默认为当前目录下的 chromium 文件夹
        :param logger: 日志对象
        :param custom_source: 自定义源，格式见文档
        :param max_retries: 最大重试次数
        :param retry_delay: 重试延迟时间(秒)
        :param timeout: 下载超时时间(秒)
        """
        self.system: str = platform.system().lower()
        self.download_dir: str = self._sanitize_path(download_dir or os.path.abspath("chromium"))
        self.logger: Optional[Any] = logger
        self.custom_source: Optional[Dict[str, Dict[str, str]]] = custom_source
        self.max_retries: int = max_retries
        self.retry_delay: float = retry_delay
        self.timeout: int = timeout

        # 检查并创建下载目录
        self._check_download_permissions(self.download_dir)

    @staticmethod
    def _sanitize_path(path: str) -> str:
        """
        清理和验证路径

        :param path: 原始路径
        :return: 规范化后的路径
        :raises ChromePathError: 路径无效时抛出
        """
        if not path:
            return os.path.abspath("chromium")

        # 规范化路径
        path = os.path.normpath(path)

        # 检查路径是否合法
        if not os.path.isabs(path):
            path = os.path.abspath(path)

        # 检查路径中的特殊字符
        if any(c in path for c in '<>:"|?*'):
            raise ChromePathError("下载路径包含非法字符")

        return path

    @staticmethod
    def _check_download_permissions(path: str) -> None:
        """
        检查下载权限

        :param path: 目标路径
        :raises ChromePermissionError: 权限不足时抛出
        """
        if not os.path.exists(path):
            try:
                os.makedirs(path, exist_ok=True)
            except PermissionError:
                raise ChromePermissionError(f"没有权限创建目录: {path}")

        if not os.access(path, os.W_OK):
            raise ChromePermissionError(f"没有写入权限: {path}")

    def log(self, msg: str, level: str = "info") -> None:
        """
        日志输出

        :param msg: 日志内容
        :param level: 日志等级
        """
        if self.logger:
            getattr(self.logger, level, self.logger.info)(msg)
        else:
            print(msg)

    def get_latest_chromium_revision(
            self, system: Optional[str] = None
    ) -> Optional[str]:
        """
        获取最新的 Chromium 快照版本号

        :param system: 指定系统，默认当前系统
        :return: 版本号
        :raises ChromeDownloadError: 获取版本号失败时抛出
        """
        sys_name: str = (system or self.system).lower()
        # 优先自定义源
        if self.custom_source and sys_name in {
            k.lower(): v for k, v in self.custom_source.items()
        }:
            url = self.custom_source[sys_name].get("latest")
        else:
            url = self.CHROMIUM_SNAPSHOT_URLS.get(sys_name)
        if not url:
            raise ChromeDownloadError(f"暂不支持当前系统：{sys_name}")

        for attempt in range(self.max_retries):
            try:
                resp = requests.get(url, timeout=self.timeout)
                resp.raise_for_status()
                rev = resp.text.strip()
                self.log(f"✅ 最新Chromium快照版本号：{rev}")
                return rev
            except requests.exceptions.RequestException as e:
                if attempt < self.max_retries - 1:
                    self.log(f"⚠️ 获取版本号失败，{self.retry_delay}秒后重试: {str(e)}", "warning")
                    time.sleep(self.retry_delay)
                else:
                    raise ChromeDownloadError(f"获取Chromium快照版本号失败：{str(e)}")
        return None

    def download_chromium(
            self, revision: Optional[str] = None, system: Optional[str] = None
    ) -> Optional[str]:
        """
        下载 Chromium 快照

        :param revision: 指定版本号，默认为最新版本
        :param system: 指定系统，默认为当前系统
        :return: 解压目录
        :raises ChromeDownloadError: 下载失败时抛出
        """
        sys_name: str = (system or self.system).lower()
        rev: Optional[str] = revision or self.get_latest_chromium_revision(
            system=sys_name
        )
        if not rev:
            raise ChromeDownloadError("无法获取Chromium版本号")

        # 优先自定义源
        if self.custom_source and sys_name in self.custom_source:
            url_tpl = self.custom_source[sys_name].get("download")
        else:
            url_tpl = self.CHROMIUM_DOWNLOAD_URLS.get(sys_name)
        if not url_tpl:
            raise ChromeDownloadError(f"暂不支持当前系统：{sys_name}")

        url = url_tpl.format(rev=rev)
        self.log(f"⬇️ 开始下载 Chromium 快照版：{url}")
        extract_dir = os.path.join(self.download_dir, f"chromium_{rev}")

        for attempt in range(self.max_retries):
            try:
                result = self._download_and_extract(url, extract_dir)
                if result:
                    return result
            except Exception as e:
                if attempt < self.max_retries - 1:
                    self.log(f"⚠️ 下载失败，{self.retry_delay}秒后重试: {str(e)}", "warning")
                    time.sleep(self.retry_delay)
                else:
                    raise ChromeDownloadError(f"下载Chromium失败：{str(e)}")

        return None

    def _find_chrome_exe(self, base_path: str) -> Optional[str]:
        """
        在给定路径下查找 chrome 可执行文件

        :param base_path: 基础路径
        :return: chrome可执行文件路径
        :raises ChromeDownloadError: 未找到可执行文件时抛出
        """
        if self.system == "windows":
            exe_path = os.path.join(base_path, "chrome-win", "chrome.exe")
        elif self.system == "linux":
            exe_path = os.path.join(base_path, "chrome-linux", "chrome")
        elif self.system == "darwin":
            exe_path = os.path.join(
                base_path, "chrome-mac", "Chromium.app", "Contents", "MacOS", "Chromium"
            )
        else:
            raise ChromeDownloadError(f"不支持的系统：{self.system}")

        if not os.path.exists(exe_path):
            raise ChromeDownloadError(f"未找到Chrome可执行文件：{exe_path}")

        # 确保文件有执行权限
        if self.system != "windows":
            try:
                os.chmod(exe_path, 0o755)
            except PermissionError:
                raise ChromePermissionError(f"无法设置执行权限：{exe_path}")

        return exe_path

    def _download_and_extract(
            self, url: str, extract_dir: str, desc: str = "⏳ 下载进度"
    ) -> Optional[str]:
        """
        通用下载和解压方法

        :param url: 下载地址
        :param extract_dir: 解压目录
        :param desc: 进度描述
        :return: 解压后的路径
        :raises ChromeDownloadError: 下载或解压失败时抛出
        """
        try:
            with requests.get(url, stream=True, timeout=self.timeout) as r:
                r.raise_for_status()
                total = int(r.headers.get("content-length", 0))

                # 检查磁盘空间
                free_space = shutil.disk_usage(self.download_dir).free
                if free_space < total * 2:  # 预留2倍空间用于解压
                    raise ChromeDownloadError(f"磁盘空间不足，需要至少 {total * 2 / 1024 / 1024:.1f}MB")

                with tempfile.NamedTemporaryFile(
                        delete=False, suffix=".zip"
                ) as f, tqdm(
                    total=total, unit="B", unit_scale=True, desc=desc, ncols=80
                ) as pbar:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            pbar.update(len(chunk))
                    zip_path = f.name

            self.log(f"✅ 下载完成，解压中...")

            # 清理已存在的目录
            if os.path.exists(extract_dir):
                try:
                    shutil.rmtree(extract_dir)
                except PermissionError:
                    raise ChromePermissionError(f"无法删除已存在的目录：{extract_dir}")

            # 解压文件
            try:
                with zipfile.ZipFile(zip_path, "r") as zip_ref, tqdm(
                        total=len(zip_ref.infolist()), desc="⏳ 解压进度", ncols=80
                ) as pbar:
                    for member in zip_ref.infolist():
                        zip_ref.extract(member, extract_dir)
                        pbar.update(1)
            except zipfile.BadZipFile:
                raise ChromeDownloadError("下载的文件已损坏")
            except PermissionError:
                raise ChromePermissionError(f"解压时权限不足：{extract_dir}")

            # 清理临时文件
            try:
                os.remove(zip_path)
            except PermissionError:
                self.log(f"⚠️ 无法删除临时文件：{zip_path}", "warning")

            self.log(f"✅ 解压完成，路径：{extract_dir}")
            return extract_dir

        except requests.exceptions.RequestException as e:
            raise ChromeDownloadError(f"下载失败：{str(e)}")
        except Exception as e:
            raise ChromeDownloadError(f"处理文件时出错：{str(e)}")

    def download(
            self,
            revision: Optional[str] = None,
            system: Optional[Literal["windows", "linux", "darwin"]] = None,
            download_dir: Optional[str] = None,
            return_chromium_path: bool = False,
    ) -> Optional[str]:
        """
        下载 Chrome 浏览器

        :param revision: 指定 Chromium 快照版本号，默认为最新版本
        :param system: 指定系统，默认为自动识别
        :param download_dir: 指定下载路径，默认为 None 使用初始化时指定的下载路径
        :param return_chromium_path: 是否返回 Chromium 可执行文件路径
        :return: 下载路径或 Chromium 可执行文件路径
        :raises ChromeDownloadError: 下载失败时抛出
        """
        try:
            sys_name: str = (system or self.system).lower()
            if download_dir:
                self.download_dir = self._sanitize_path(download_dir)
                self._check_download_permissions(self.download_dir)

            # 优先自定义源
            if self.custom_source:
                self.log("🔍 使用自定义源进行下载")
                custom_rev = revision or self.get_latest_chromium_revision(sys_name)
                if custom_rev:
                    path = self.download_chromium(custom_rev, sys_name)
                    if path:
                        return self._handle_download_result(path, return_chromium_path)

            # 官方主源
            path = self.download_chromium(revision, sys_name)
            if path:
                return self._handle_download_result(path, return_chromium_path)

            raise ChromeDownloadError(f"下载失败，请稍后重试！当前系统：{sys_name}")

        except (ChromeDownloadError, ChromePermissionError, ChromePathError) as e:
            self.log(f"❌ {str(e)}", "error")
            raise

    def _handle_download_result(
            self, path: str, return_chromium_path: bool
    ) -> Optional[str]:
        """
        处理下载结果，返回路径或 Chromium 可执行文件路径

        :param path: 下载或解压路径
        :param return_chromium_path: 是否返回chrome可执行文件路径
        :return: 路径或chrome可执行文件路径
        :raises ChromeDownloadError: 处理失败时抛出
        """
        if return_chromium_path:
            try:
                chrome_path = self._find_chrome_exe(path)
                if chrome_path and os.path.exists(chrome_path):
                    self.log(f"✅ 找到 chrome 可执行文件：{chrome_path}")
                    return chrome_path
            except Exception as e:
                raise ChromeDownloadError(f"处理Chrome可执行文件时出错：{str(e)}")

            raise ChromeDownloadError(
                f"未找到 chrome 的可执行文件，请前往存放路径手动查找：{path}"
            )

        self.log(f"✅ Chrome下载完成，存放路径：{path}")
        return path
