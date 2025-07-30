"""AnyTLS 服务核心管理逻辑"""

import logging
import os
import shutil
import subprocess
import sys
import uuid
from typing import Optional

import yaml
from rich.console import Console
from rich.syntax import Syntax

from anytls.core import constants, utils


class AnyTLSManager:
    """封装 AnyTLS 服务管理的所有逻辑"""

    def __init__(self):
        """初始化管理器"""
        self.console = Console()
        self.compose_cmd: Optional[list[str]] = None

    def _get_compose_cmd(self) -> list[str]:
        """检测并返回可用的 docker compose 命令，并缓存结果。"""
        if self.compose_cmd:
            return self.compose_cmd

        try:
            # 优先使用 "docker compose" (V2)
            utils.run_command(
                ["docker", "compose", "version"],
                capture_output=True,
                install_docker=True,
                skip_execution_logging=True,
                propagate_exception=True,
            )
            self.compose_cmd = ["docker", "compose"]
            logging.debug("检测到 Docker Compose V2 (docker compose)，将使用此命令。")
            return self.compose_cmd
        except (subprocess.CalledProcessError, FileNotFoundError):
            # 回退到 "docker-compose" (V1)
            logging.debug("未检测到 'docker compose' (V2)，尝试 'docker-compose' (V1)...")
            try:
                utils.run_command(
                    ["docker-compose", "--version"],
                    capture_output=True,
                    install_docker=True,
                    skip_execution_logging=True,
                    propagate_exception=True,
                )
                self.compose_cmd = ["docker-compose"]
                logging.debug("检测到 Docker Compose V1 (docker-compose)，将使用此命令。")
                return self.compose_cmd
            except (subprocess.CalledProcessError, FileNotFoundError):
                # 两个都找不到，这个异常将在 _check_dependencies 中被捕获并处理
                raise FileNotFoundError("未找到 'docker compose' 或 'docker-compose'。")

    @staticmethod
    def _ensure_service_installed():
        """确保服务已安装，否则退出"""
        if not constants.DOCKER_COMPOSE_PATH.is_file():
            logging.error(f"配置文件 ({constants.DOCKER_COMPOSE_PATH}) 未找到。")
            logging.error("请先运行 'install' 命令来安装服务。")
            sys.exit(1)

    @staticmethod
    def _get_domain_from_config() -> str:
        """从 docker-compose.yaml 文件中解析出域名"""
        if not constants.DOCKER_COMPOSE_PATH.exists():
            logging.error(
                f"配置文件 {constants.DOCKER_COMPOSE_PATH} 不存在。您是否已经安装了服务？"
            )
            sys.exit(1)

        with constants.DOCKER_COMPOSE_PATH.open("r") as f:
            data = yaml.safe_load(f)
            container_name = data["services"]["anytls-inbound"]["container_name"]
            domain = container_name.split("anytls-inbound-")[-1]
            if not domain:
                raise ValueError
            return domain

    def _check_dependencies(self, auto_install: bool = False) -> bool:
        """
        检查 Docker 和 Docker Compose 是否安装。
        :param auto_install: 如果为 True，当 Docker 未安装时，会提示并尝试自动安装。
        :return: 如果 Docker 之前未安装，并且本次成功安装了，则返回 True。否则返回 False。
        """
        logging.info("正在检查 Docker 和 Docker Compose 环境...")
        try:
            utils.run_command(["docker", "--version"], capture_output=True, install_docker=True)
            self._get_compose_cmd()  # 检测并缓存 docker compose 命令
            logging.info("Docker 和 Docker Compose 已安装。")
            return False  # 已安装，未执行安装
        except (FileNotFoundError, subprocess.CalledProcessError):
            logging.warning("未检测到 Docker 或 Docker Compose。")
            if auto_install:
                logging.info("开始自动安装 Docker 和 Docker Compose...")
                utils.run_command(["/bin/bash", "-c", utils.DOCKER_INSTALL_SCRIPT])
                logging.info(
                    "安装完成。您可能需要重新登录或运行 `newgrp docker` "
                    "以便非 root 用户无需 sudo 即可运行 docker。"
                )
                return True  # 执行了安装
            else:
                # 如果不是在主安装流程中，仅检查而不安装
                logging.error("请先运行 'install' 命令来安装所有依赖。")
                sys.exit(1)
        except Exception as e:
            logging.error(e)
            # 在这种未知错误下，我们应该退出而不是继续
            sys.exit(1)

    def _check_certbot(self, auto_install: bool = False) -> bool:
        """
        检查 Certbot 是否安装。
        :param auto_install: 如果为 True，当 certbot 未安装时，会尝试自动安装。
        :return: 如果 Certbot 之前未安装，并且本次成功安装了，则返回 True。否则返回 False。
        """
        logging.info("正在检查 Certbot 是否安装...")
        if shutil.which("certbot"):
            logging.info("Certbot 已安装。")
            return False  # Certbot 已存在，未进行安装

        logging.warning("未检测到 Certbot。Certbot 是申请 HTTPS 证书所必需的。")

        if not auto_install:
            # 如果不是在主安装流程中，仅检查而不安装
            logging.error("请先运行 'install' 命令来安装所有依赖。")
            sys.exit(1)

        logging.info("将自动为您安装 Certbot。")

        logging.info("正在尝试使用 Snap 安装 Certbot...")
        try:
            utils.run_command("sudo snap install core".split())
            utils.run_command("sudo snap refresh core".split())
            utils.run_command("sudo snap install --classic certbot".split())
            utils.run_command("sudo ln -s /snap/bin/certbot /usr/bin/certbot".split(), check=False)
            logging.info("Certbot 安装成功！")
            return True  # 进行了安装
        except Exception as e:
            logging.error(f"使用 Snap 安装 Certbot 失败: {e}")
            logging.error("您的系统可能不支持 Snap，或安装过程中出现错误。")
            logging.error("请参考 https://certbot.eff.org/instructions 手动安装后重试。")
            sys.exit(1)

    def install(self, domain: str, password: Optional[str], ip: Optional[str]):
        """安装并启动 AnyTLS 服务"""
        # --- 步骤 1: 初始检查和依赖安装 ---
        logging.info("--- 步骤 1/4: 开始环境检查与依赖安装 ---")

        # 检查并安装 Docker & Certbot
        # 如果安装了任何一个，脚本需要重启以加载新环境
        docker_installed_now = self._check_dependencies(auto_install=True)
        certbot_installed_now = self._check_certbot(auto_install=True)

        if docker_installed_now or certbot_installed_now:
            logging.warning("依赖项已成功安装。为了使环境更改完全生效，脚本将自动重新执行。")
            logging.warning("如果脚本没有自动重启，请手动重新运行您刚才执行的命令。")
            try:
                os.execv(sys.executable, [sys.executable] + sys.argv)
            except Exception as e:
                logging.error(f"脚本自动重启失败: {e}")
                logging.error("请手动重新运行您刚才执行的命令以继续安装。")
                sys.exit(1)

            # execv会替换当前进程，所以下面的代码在新进程中才会执行
            return  # 在当前进程中，到此为止

        logging.info("--- 所有依赖均已满足 ---")

        logging.info(f"--- 步骤 2/4: 开始安装 AnyTLS 服务 (域名: {domain}) ---")
        if constants.BASE_DIR.exists():
            logging.warning(f"工作目录 {constants.BASE_DIR} 已存在。继续操作将可能覆盖现有配置。")
            if self.console.input("是否继续？ (y/n): ").lower() != "y":
                logging.info("安装已取消。")
                return

        public_ip = ip or utils.get_public_ip()
        service_password = password or utils.generate_password()

        logging.info(f"--- 步骤 3/4: 申请证书与生成配置 ---")
        logging.info(f"正在为域名 {domain} 申请 Let's Encrypt 证书...")
        try:
            utils.run_command(
                [
                    "certbot",
                    "certonly",
                    "--standalone",
                    "--register-unsafely-without-email",
                    "--agree-tos",
                    "--non-interactive",
                    "-d",
                    domain,
                ],
                propagate_exception=True,
            )
            logging.info("证书申请成功。")
        except (FileNotFoundError, subprocess.CalledProcessError) as e:
            logging.error(f"证书申请失败: {e}")
            logging.error("请检查：")
            logging.error(f"  1. 域名 '{domain}' 是否正确解析到本机 IP 地址 ({public_ip})。")
            logging.error("  2. 服务器防火墙是否已放开 80 端口。")
            sys.exit(1)

        logging.info(f"正在创建工作目录: {constants.BASE_DIR}")
        constants.BASE_DIR.mkdir(exist_ok=True)

        # 创建 Mihomo 配置
        mihomo_cfg_dict = {
            "listeners": [
                {
                    "name": f"anytls-in-{uuid.uuid4()}",
                    "type": "anytls",
                    "port": constants.LISTEN_PORT,
                    "listen": "0.0.0.0",
                    "users": {f"user_{uuid.uuid4().hex[:8]}": service_password},
                    "certificate": f"/etc/letsencrypt/live/{domain}/fullchain.pem",
                    "private-key": f"/etc/letsencrypt/live/{domain}/privkey.pem",
                }
            ]
        }

        with constants.CONFIG_PATH.open("w", encoding="utf8") as f:
            yaml.dump(mihomo_cfg_dict, f, sort_keys=False)
        logging.info(f"已生成配置文件: {constants.CONFIG_PATH}")

        # 创建 Docker Compose 配置
        docker_compose_cfg_dict = {
            "services": {
                "anytls-inbound": {
                    "image": constants.SERVICE_IMAGE,
                    "container_name": f"anytls-inbound-{domain}",
                    "restart": "always",
                    "ports": [f"{constants.LISTEN_PORT}:{constants.LISTEN_PORT}"],
                    "working_dir": "/app/proxy-inbound/",
                    "volumes": [
                        "/etc/letsencrypt/:/etc/letsencrypt/",
                        "./config.yaml:/app/proxy-inbound/config.yaml",
                    ],
                    "command": ["-f", "config.yaml", "-d", "/"],
                }
            }
        }
        with constants.DOCKER_COMPOSE_PATH.open("w", encoding="utf8") as f:
            yaml.dump(docker_compose_cfg_dict, f, sort_keys=False)
        logging.info(f"已生成 Docker Compose 文件: {constants.DOCKER_COMPOSE_PATH}")

        compose_cmd = self._get_compose_cmd()
        logging.info("--- 步骤 4/4: 启动服务 ---")
        logging.info("正在拉取最新的 Docker 镜像...")
        utils.run_command(compose_cmd + ["pull"], cwd=constants.BASE_DIR)
        logging.info("正在启动服务...")
        utils.run_command(compose_cmd + ["down"], cwd=constants.BASE_DIR, check=False)
        utils.run_command(compose_cmd + ["up", "-d"], cwd=constants.BASE_DIR)

        logging.info("--- AnyTLS 服务安装并启动成功！ ---")

        # 打印客户端配置
        client_config_dict = {
            "name": domain,
            "type": "anytls",
            "server": public_ip,
            "port": constants.LISTEN_PORT,
            "password": service_password,
            "client_fingerprint": "chrome",
            "udp": True,
            "idle_session_check_interval": 30,
            "idle_session_timeout": 30,
            "min_idle_session": 0,
            "sni": domain,
            "alpn": ["h2", "http/1.1"],
            "skip_cert_verify": False,
        }

        client_yaml = yaml.dump([client_config_dict], sort_keys=False)
        self.console.print("\n" + "=" * 20 + " 客户端配置信息[mihomo] " + "=" * 20)
        self.console.print(Syntax(client_yaml, "yaml"))
        self.console.print("=" * 58 + "\n")

        self.console.print(f"详见客户端配置文档：{constants.MIHOMO_ANYTLS_DOCS}\n")

    def remove(self):
        """停止并移除 AnyTLS 服务和相关文件"""
        logging.info("--- 开始卸载 AnyTLS 服务 ---")
        if not constants.BASE_DIR.exists():
            logging.warning(f"工作目录 {constants.BASE_DIR} 不存在，可能服务未安装或已被移除。")
            return

        domain = self._get_domain_from_config()
        logging.info(f"检测到正在管理的域名为: {domain}")

        compose_cmd = self._get_compose_cmd()
        logging.info("正在停止并移除 Docker 容器...")
        utils.run_command(compose_cmd + ["down", "--volumes"], cwd=constants.BASE_DIR, check=False)

        logging.info(f"正在删除工作目录: {constants.BASE_DIR}")
        shutil.rmtree(constants.BASE_DIR)

        logging.info(f"正在删除 {domain} 的 Let's Encrypt 证书...")
        utils.run_command(
            ["certbot", "delete", "--cert-name", domain, "--non-interactive"], check=False
        )
        logging.info("--- AnyTLS 服务已成功卸载。 ---")

    def start(self):
        """启动服务"""
        self._ensure_service_installed()
        logging.info("正在启动 AnyTLS 服务...")
        compose_cmd = self._get_compose_cmd()
        utils.run_command(compose_cmd + ["up", "-d"], cwd=constants.BASE_DIR)
        logging.info("AnyTLS 服务已启动。")

    def stop(self):
        """停止服务"""
        self._ensure_service_installed()
        logging.info("正在停止 AnyTLS 服务...")
        compose_cmd = self._get_compose_cmd()
        utils.run_command(compose_cmd + ["down"], cwd=constants.BASE_DIR)
        logging.info("AnyTLS 服务已停止。")

    def update(self):
        """更新服务（拉取新镜像并重启）"""
        self._ensure_service_installed()
        logging.info("--- 开始更新 AnyTLS 服务 ---")
        compose_cmd = self._get_compose_cmd()
        logging.info("正在拉取最新的 Docker 镜像...")
        utils.run_command(compose_cmd + ["pull"], cwd=constants.BASE_DIR)
        logging.info("正在使用新镜像重启服务...")
        utils.run_command(compose_cmd + ["down"], cwd=constants.BASE_DIR, check=False)
        utils.run_command(compose_cmd + ["up", "-d"], cwd=constants.BASE_DIR)
        logging.info("--- AnyTLS 服务更新完成。 ---")

    def log(self):
        """查看服务日志"""
        self._ensure_service_installed()
        logging.info("正在显示服务日志... (按 Ctrl+C 退出)")
        compose_cmd = self._get_compose_cmd()
        utils.run_command(compose_cmd + ["logs", "-f"], cwd=constants.BASE_DIR, stream_output=True)

    def check(self):
        """检查服务状态并打印客户端配置"""
        self._ensure_service_installed()
        self.console.print("\n--- 开始检查 AnyTLS 服务状态 ---")

        # rich Components
        from rich.table import Table

        table = Table(title="AnyTLS 服务状态一览")
        table.add_column("检查项", justify="right", style="cyan", no_wrap=True)
        table.add_column("状态", style="magenta")

        try:
            # 1. 获取域名
            domain = self._get_domain_from_config()
            table.add_row("管理域名", domain)

            # 2. 检查 Docker 容器状态
            container_name = f"anytls-inbound-{domain}"
            try:
                result = utils.run_command(
                    [
                        "docker",
                        "ps",
                        "--filter",
                        f"name={container_name}",
                        "--format",
                        "{{.Status}}",
                    ],
                    capture_output=True,
                    check=True,
                )
                status_output = result.stdout.strip()
                if "Up" in status_output:
                    container_status = f"[green]✔ 正在运行[/green] ({status_output})"
                elif status_output:
                    container_status = f"[yellow]❗ 已停止[/yellow] ({status_output})"
                else:
                    container_status = "[red]❌ 未找到容器[/red]"
            except (subprocess.CalledProcessError, FileNotFoundError):
                container_status = "[red]❌ 检查失败 (Docker 命令错误)[/red]"
            table.add_row("服务容器状态", container_status)

            # 3. 检查配置文件
            if constants.CONFIG_PATH.exists() and constants.DOCKER_COMPOSE_PATH.exists():
                config_status = "[green]✔ 正常[/green]"
            else:
                config_status = "[red]❌ 缺失[/red]"
            table.add_row("核心配置文件", config_status)

            # 获取公网 IP
            public_ip = utils.get_public_ip()
        except Exception as e:
            self.console.print(f"[red]检查过程中出现错误: {e}[/red]")
            return

        self.console.print(table)

        # 4. 基于实时服务端配置生成并打印客户端配置
        try:
            # 从 config.yaml 获取密码和端口
            with constants.CONFIG_PATH.open("r", encoding="utf8") as f:
                server_config = yaml.safe_load(f)

            listener_config = server_config["listeners"][0]
            port = listener_config["port"]
            # users 的 key 是随机的，所以我们直接取第一个 value
            password = list(listener_config["users"].values())[0]

            client_config_dict = {
                "name": domain,  # 'domain' from earlier in this method
                "type": "anytls",
                "server": public_ip,
                "port": port,
                "password": password,
                "client_fingerprint": "chrome",
                "udp": True,
                "idle_session_check_interval": 30,
                "idle_session_timeout": 30,
                "min_idle_session": 0,
                "sni": domain,
                "alpn": ["h2", "http/1.1"],
                "skip_cert_verify": False,
            }

            client_yaml = yaml.dump([client_config_dict], sort_keys=False)
            self.console.print("\n" + "=" * 20 + " 客户端配置信息[mihomo] " + "=" * 20)
            self.console.print(Syntax(client_yaml, "yaml"))
            self.console.print("=" * 58 + "\n")
            self.console.print(f"详见客户端配置文档：{constants.MIHOMO_ANYTLS_DOCS}\n")

        except FileNotFoundError:
            self.console.print("\n[yellow]配置文件未找到，无法生成客户端配置。[/yellow]")
            self.console.print(
                "[yellow]可能是通过旧版本安装的。可以尝试重新运行 'install' 命令以生成。[/yellow]"
            )
            self.console.print("=" * 58 + "\n")
        except Exception as e:
            self.console.print(f"\n[red]生成客户端配置时出错: {e}[/red]")
            self.console.print("=" * 58 + "\n")
