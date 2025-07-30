"""全局常量配置"""

from pathlib import Path

BASE_DIR = Path("/home/anytls")
DOCKER_COMPOSE_PATH = BASE_DIR / "docker-compose.yaml"
CONFIG_PATH = BASE_DIR / "config.yaml"

MIHOMO_CLIENT_CONFIG_PATH = BASE_DIR / "mihomo-outbound-proxy-config.yaml"

LISTEN_PORT = 8443
SERVICE_IMAGE = "metacubex/mihomo:latest"
