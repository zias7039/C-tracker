# utils.py
import os
import logging
import sys

# Global logger instance
logger = None


def setup_logging():
    """로깅 설정 및 로거 인스턴스 반환"""
    global logger

    if logger is not None:
        return logger

    # 로그 디렉토리 생성
    log_dir = os.path.join(os.path.expanduser("~"), ".myCryptoOverlay", "logs")
    os.makedirs(log_dir, exist_ok=True)

    # 로그 파일 경로
    log_file = os.path.join(log_dir, "crypto_overlay.log")

    # 로거 설정
    logger = logging.getLogger("crypto_overlay")
    logger.setLevel(logging.INFO)

    # 파일 핸들러
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)

    # 콘솔 핸들러
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)

    # 포맷 설정
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # 핸들러 추가
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.info("로깅 시스템 초기화 완료")
    return logger


def get_config_path():
    """설정 파일 경로를 반환합니다."""
    home_dir = os.path.expanduser("~")
    config_dir = os.path.join(home_dir, ".myCryptoOverlay")
    os.makedirs(config_dir, exist_ok=True)
    return os.path.join(config_dir, "settings.json")


# 로거 초기화
logger = setup_logging()