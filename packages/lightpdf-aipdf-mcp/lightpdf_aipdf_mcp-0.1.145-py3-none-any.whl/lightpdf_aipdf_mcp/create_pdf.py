"""根据用户输入请求创建PDF文件的接口"""
from dataclasses import dataclass
from typing import Optional
import os
import uuid
import httpx
from .common import Logger, FileHandler, BaseResult, BaseApiClient
from .editor import Editor, EditResult, EditType

@dataclass
class CreatePdfResult(BaseResult):
    """PDF创建结果数据类"""
    pass

class PDFCreator(BaseApiClient):
    """PDF文档创建器"""
    def __init__(self, logger: Logger, file_handler: FileHandler):
        super().__init__(logger, file_handler)
        self.api_base_url = f"https://{self.api_endpoint}/tasks/llm/chats"
        # 语言代码到语言名称的映射
        self.language_map = {
            "zh": "简体中文", "en": "English", "de": "Deutsch", "es": "Español",
            "fr": "Français", "ja": "日本語", "pt": "Português", "zh-tw": "繁體中文",
            "ar": "العربية", "cs": "Čeština", "da": "Dansk", "fi": "Suomi",
            "el": "Ελληνικά", "hu": "Magyar", "it": "Italiano", "nl": "Nederlands",
            "no": "Norsk", "pl": "Polski", "sv": "Svenska", "tr": "Türkçe"
        }

    async def create_pdf_from_prompt(
        self, 
        prompt: str, 
        language: str,
        enable_web_search: bool = False,
        original_name: Optional[str] = None
    ) -> CreatePdfResult:
        """
        根据用户输入请求创建PDF文件。

        参数：
            prompt (str): 用户的输入请求或提示词，仅支持文字描述，不支持文件附件等。
            language (str): 生成PDF的语言，必需参数。
            enable_web_search (bool): 是否启用联网搜索，默认False。
            original_name (Optional[str]): 可选，原始文件名。
        返回：
            CreatePdfResult: 包含生成结果的信息。
        """
        tex_path = None
        try:
            # 1. 根据prompt生成latex代码
            latex_code = await self._generate_latex_code(prompt, language, enable_web_search)
            if not latex_code:
                return CreatePdfResult(
                    success=False,
                    file_path="",
                    error_message="生成的latex代码为空",
                    original_name=original_name
                )

            # 2. 保存latex_code为本地.tex文件
            tex_path = await self._save_latex_to_file(latex_code)

            # 3. 调用Editor.edit_pdf并传递oss://tex2pdf参数生成PDF
            result = await self._convert_tex_to_pdf(tex_path, original_name)
            
            # 转换EditResult到CreatePdfResult
            return CreatePdfResult(
                success=result.success,
                file_path=result.file_path,
                error_message=result.error_message,
                download_url=result.download_url,
                original_name=result.original_name,
                task_id=result.task_id
            )

        except Exception as e:
            return CreatePdfResult(
                success=False,
                file_path="",
                error_message=f"PDF创建过程中发生错误: {e}",
                original_name=original_name
            )
        finally:
            # 清理临时文件
            if tex_path and os.path.exists(tex_path):
                self._schedule_file_cleanup(tex_path)

    async def _generate_latex_code(self, prompt: str, language: str, enable_web_search: bool) -> str:
        """根据用户输入生成LaTeX代码"""
        lang_str = self.language_map.get(language)
        await self.logger.log("debug", f"开始为语言 {lang_str} 生成LaTeX代码，联网搜索: {enable_web_search}")
        
        # 这里应该是实际的代码生成逻辑
        # 暂时返回空字符串，需要后续实现
        async with httpx.AsyncClient(timeout=3600.0) as client:
            template_variables = {
                "PROMPT": prompt
            }
            if lang_str:
                template_variables["LANGUAGE"] = lang_str

            headers = {"X-API-KEY": self.api_key}
            data = {
                "po": "lightpdf",
                "response_type": 0,
                "template_id": "48a62054-9cf0-483d-9787-b31afc32e079",
                "template_variables": template_variables
            }
            if enable_web_search:
                # 获取真实的用户信息
                plugin_options = await self._get_real_user_info(language)
                data["plugins"] = [
                    {
                        "function": {
                            "id": 1001,
                            "options": plugin_options
                        },
                        "callback": None
                    }
                ]

            await self.logger.log("debug", f"正在提交生成LaTeX代码...{data}")
            response = await client.post(self.api_base_url, json=data, headers=headers)

            task_id = await self._handle_api_response(response, "生成LaTeX代码")
            await self.logger.log("debug", f"生成LaTeX代码，task_id: {task_id}")

            content = await self._wait_for_task(client, task_id, "生成LaTeX代码", is_raw=True)

            return content.get("text", "")

    async def _save_latex_to_file(self, latex_code: str) -> str:
        """保存LaTeX代码到临时文件"""
        temp_dir = "./tmp"
        os.makedirs(temp_dir, exist_ok=True)
        tex_filename = f"latex_code_{uuid.uuid4().hex}.tex"
        tex_path = os.path.join(temp_dir, tex_filename)
        
        # 清理markdown代码块标记
        cleaned_code = self._clean_latex_code(latex_code)
        
        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(cleaned_code)
        
        return tex_path

    def _clean_latex_code(self, latex_code: str) -> str:
        """清理LaTeX代码中的markdown标记"""
        if not latex_code:
            return latex_code
        
        # 去除首行和尾行的markdown代码块标记
        lines = latex_code.strip().split('\n')
        
        # 检查并移除首行的```latex标记
        if lines and lines[0].strip().startswith('```'):
            lines = lines[1:]
        
        # 检查并移除尾行的```标记
        if lines and lines[-1].strip() == '```':
            lines = lines[:-1]
        
        # 重新组合代码
        cleaned_code = '\n'.join(lines)
        
        return cleaned_code.strip()

    async def _get_real_user_info(self, language: str) -> dict:
        """获取真实的用户信息"""
        import platform
        import socket
        
        # 获取真实的用户代理字符串
        system = platform.system()
        version = platform.version()
        architecture = platform.machine()
        
        # 构建更真实的User-Agent
        if system == "Darwin":  # macOS
            user_agent = f"Mozilla/5.0 (Macintosh; Intel Mac OS X {version.replace('.', '_')}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        elif system == "Windows":
            user_agent = f"Mozilla/5.0 (Windows NT {version}; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        elif system == "Linux":
            user_agent = f"Mozilla/5.0 (X11; Linux {architecture}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        else:
            user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        
        # 获取真实的IP地址
        local_ip = self._get_local_ip()
        
        # 根据语言参数动态生成accept_language
        accept_language = self._get_accept_language(language)
        
        return {
            "user_agent": user_agent,
            "accept_language": accept_language,
            "ip": local_ip
        }

    def _get_accept_language(self, language: str) -> str:
        """根据语言代码生成对应的accept_language字符串"""
        # 语言代码到HTTP Accept-Language的映射
        language_codes = {
            "zh": "zh-CN,zh;q=0.9,en;q=0.8",
            "en": "en-US,en;q=0.9",
            "de": "de-DE,de;q=0.9,en;q=0.8",
            "es": "es-ES,es;q=0.9,en;q=0.8",
            "fr": "fr-FR,fr;q=0.9,en;q=0.8",
            "ja": "ja-JP,ja;q=0.9,en;q=0.8",
            "pt": "pt-PT,pt;q=0.9,en;q=0.8",
            "zh-tw": "zh-TW,zh;q=0.9,en;q=0.8",
            "ar": "ar-SA,ar;q=0.9,en;q=0.8",
            "cs": "cs-CZ,cs;q=0.9,en;q=0.8",
            "da": "da-DK,da;q=0.9,en;q=0.8",
            "fi": "fi-FI,fi;q=0.9,en;q=0.8",
            "el": "el-GR,el;q=0.9,en;q=0.8",
            "hu": "hu-HU,hu;q=0.9,en;q=0.8",
            "it": "it-IT,it;q=0.9,en;q=0.8",
            "nl": "nl-NL,nl;q=0.9,en;q=0.8",
            "no": "no-NO,no;q=0.9,en;q=0.8",
            "pl": "pl-PL,pl;q=0.9,en;q=0.8",
            "sv": "sv-SE,sv;q=0.9,en;q=0.8",
            "tr": "tr-TR,tr;q=0.9,en;q=0.8"
        }
        
        return language_codes.get(language, "en-US,en;q=0.9")

    def _get_local_ip(self) -> str:
        """获取本地IP地址的稳定方法"""
        import socket
        
        # 方法1: 尝试连接外部DNS服务器
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                # 使用多个DNS服务器进行尝试
                for dns_server in ["8.8.8.8", "1.1.1.1", "208.67.222.222", "114.114.114.114", "101.101.101.101", "1.2.4.8"]:
                    try:
                        s.connect((dns_server, 80))
                        ip = s.getsockname()[0]
                        # 验证是否为私有IP地址
                        if self._is_valid_local_ip(ip):
                            return ip
                    except Exception:
                        continue
        except Exception:
            pass
        
        # 方法2: 获取本机所有网络接口
        try:
            hostname = socket.gethostname()
            ip_list = socket.gethostbyname_ex(hostname)[2]
            for ip in ip_list:
                if self._is_valid_local_ip(ip):
                    return ip
        except Exception:
            pass
        
        # 方法3: 遍历网络接口
        try:
            import subprocess
            import platform
            
            if platform.system() == "Windows":
                # Windows系统
                result = subprocess.run(['ipconfig'], capture_output=True, text=True)
                for line in result.stdout.split('\n'):
                    if 'IPv4' in line and 'Address' in line:
                        ip = line.split(':')[-1].strip()
                        if self._is_valid_local_ip(ip):
                            return ip
            else:
                # Unix/Linux/macOS系统
                result = subprocess.run(['hostname', '-I'], capture_output=True, text=True)
                if result.returncode == 0:
                    ips = result.stdout.strip().split()
                    for ip in ips:
                        if self._is_valid_local_ip(ip):
                            return ip
        except Exception:
            pass
        
        # 方法4: 尝试绑定本地socket
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.bind(('', 0))
                ip = s.getsockname()[0]
                if self._is_valid_local_ip(ip):
                    return ip
        except Exception:
            pass
        
        # 最后的后备方案
        return "127.0.0.1"
    
    def _is_valid_local_ip(self, ip: str) -> bool:
        """验证IP地址是否为有效的本地IP"""
        import ipaddress

        try:
            ip_obj = ipaddress.ip_address(ip)
            # 排除回环地址和链路本地地址
            if ip_obj.is_loopback or ip_obj.is_link_local:
                return False
            # 接受私有地址和公网地址
            return True
        except ValueError:
            return False

    async def _convert_tex_to_pdf(self, tex_path: str, original_name: Optional[str]) -> EditResult:
        """将TEX文件转换为PDF"""
        editor = Editor(self.logger, self.file_handler)
        extra_params = {"pages": '[{"url": "oss://tex2pdf", "oss_file": ""}]'}
        
        tex_filename = os.path.basename(tex_path)
        return await editor.edit_pdf(
            tex_path, 
            edit_type=EditType.EDIT, 
            extra_params=extra_params, 
            original_name=original_name or tex_filename
        )

    def _schedule_file_cleanup(self, file_path: str, delay: int = 300):
        """安排文件清理"""
        import threading
        
        def delayed_remove(path):
            try:
                os.remove(path)
            except Exception:
                pass
        
        timer = threading.Timer(delay, delayed_remove, args=(file_path,))
        timer.daemon = True
        timer.start()
