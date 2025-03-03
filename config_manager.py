# config_manager.py
import os
import json
import logging
from typing import Dict, Any, List, Optional


class ConfigManager:
    """
    설정 관리를 위한 클래스.
    싱글톤 패턴을 사용하여 애플리케이션 전체에서 설정을 일관되게 관리합니다.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._config_path = self._get_config_path()
        self._default_config = {
            "symbols": ["ETHUSDT", "BTCUSDT"],
            "font_name": "Segoe UI",
            "opacity": 1.0,
            "window_x": 1600,
            "window_y": 50,
            "font_size": 12,
            "window_width": 300,
            "window_height": 40,
            "refresh_interval": 2,
            "theme": "dark",
            "language": "ko",
            "enable_alerts": False,
            "price_alerts": {}
        }
        self._config = {}
        self.load()
        self._initialized = True

    def _get_config_path(self) -> str:
        """
        설정 파일 경로를 반환합니다.
        """
        home_dir = os.path.expanduser("~")
        config_dir = os.path.join(home_dir, ".myCryptoOverlay")
        os.makedirs(config_dir, exist_ok=True)
        return os.path.join(config_dir, "settings.json")

    def load(self) -> None:
        """
        설정 파일에서 설정을 로드합니다.
        """
        try:
            if os.path.exists(self._config_path):
                with open(self._config_path, "r", encoding="utf-8") as f:
                    self._config = json.load(f)
                logging.info("설정 로드 완료")
            else:
                self._config = self._default_config.copy()
                self.save()
        except Exception as e:
            logging.error(f"설정 로드 실패: {e}")
            self._config = self._default_config.copy()

    def save(self) -> None:
        """
        현재 설정을 파일에 저장합니다.
        """
        try:
            with open(self._config_path, "w", encoding="utf-8") as f:
                json.dump(self._config, f, ensure_ascii=False, indent=2)
            logging.info("설정 저장 완료")
        except Exception as e:
            logging.error(f"설정 저장 실패: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        설정 값을 가져옵니다.

        Args:
            key: 설정 키
            default: 키가 존재하지 않을 경우 반환할 기본값

        Returns:
            설정 값 또는 기본값
        """
        return self._config.get(key, self._default_config.get(key, default))

    def set(self, key: str, value: Any) -> None:
        """
        설정 값을 설정합니다.

        Args:
            key: 설정 키
            value: 설정 값
        """
        self._config[key] = value

    def update(self, settings: Dict[str, Any]) -> None:
        """
        여러 설정을 한번에 업데이트합니다.

        Args:
            settings: 업데이트할 설정 딕셔너리
        """
        self._config.update(settings)

    def get_all(self) -> Dict[str, Any]:
        """
        모든 설정을 딕셔너리로 반환합니다.

        Returns:
            설정 딕셔너리
        """
        return self._config.copy()

    def reset(self) -> None:
        """
        설정을 기본값으로 초기화합니다.
        """
        self._config = self._default_config.copy()
        self.save()

# 사용 예시:
# from config_manager import ConfigManager
#
# config = ConfigManager()
# symbols = config.get("symbols")
#
# # 설정 변경
# config.set("refresh_interval", 5)
# config.save()