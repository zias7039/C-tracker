# overlay.py
import json
import logging
import enum
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGraphicsDropShadowEffect, QStyle,
    QSystemTrayIcon, QMenu, QAction, QMessageBox, QHBoxLayout, QFrame,
    QApplication, QGraphicsOpacityEffect
)
from PyQt5.QtCore import (
    QTimer, Qt, pyqtSlot, QPropertyAnimation, QPoint,
    QSequentialAnimationGroup, QEasingCurve, QRect, QSize
)
from PyQt5.QtGui import (
    QFont, QColor, QKeySequence, QIcon, QPainter,
    QLinearGradient, QBrush, QPen, QFontMetrics
)
from PyQt5.QtWidgets import QShortcut

from price_fetcher import PriceFetcherThread
from settings_dialog import SettingsDialog
from config_manager import ConfigManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("crypto_overlay.log"),
        logging.StreamHandler()
    ]
)


class DisplayMode(enum.Enum):
    COMPACT = "compact"  # 최소 정보만 표시
    STANDARD = "standard"  # 기본 표시 모드
    DETAILED = "detailed"  # 상세 정보 표시
    CARDS = "cards"  # 각 심볼을 카드 형태로 표시


class Overlay(QWidget):
    def __init__(self):
        super().__init__()
        self.config = ConfigManager()
        self.settings_dialog = None
        self.fetcher = None
        self.tray_icon = None
        self.dragging = False
        self.price_data = {}  # 이전 가격 데이터 저장용

        # 디자인 설정 기본값
        self.display_mode = DisplayMode.STANDARD
        self.use_animations = True
        self.use_gradient_bg = True
        self.use_blur_effect = True

        # 색상 테마 기본값
        self.text_color = "#FFFFFF"
        self.background_color = "rgba(40,40,40,200)"
        self.positive_color = "#4CAF50"
        self.negative_color = "#F44336"
        self.neutral_color = "#FFA500"

        # 설정 로드
        self.load_settings()

        # UI 초기화
        self.initUI()
        self.setup_shortcuts()
        self.setup_tray_icon()

        # 가격 업데이트 타이머 설정
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_price)
        self.timer.start(self.refresh_interval * 1000)

        # 초기 가격 업데이트
        self.update_price()

        logging.info("오버레이 초기화 완료")

    def initUI(self):
        """UI 컴포넌트 초기화"""
        # 창 설정
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # 메인 레이아웃 생성
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 드래그 핸들 영역 생성 - 이 영역을 통해 창을 드래그할 수 있습니다
        self.drag_area = QFrame(self)
        self.drag_area.setMinimumHeight(10)
        self.drag_area.setStyleSheet("background-color: transparent;")
        self.drag_area.setCursor(Qt.SizeAllCursor)

        # 콘텐츠 컨테이너 생성
        self.container = QFrame(self)
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(5, 5, 5, 5)
        container_layout.setSpacing(0)

        # 라벨 생성 및 스타일 적용
        self.label = QLabel("로딩 중...", self.container)
        self.apply_label_style()
        # self.label.setFixedSize(self.window_width, self.window_height) # 이 줄 삭제
        self.label.setAlignment(Qt.AlignCenter)

        # 라벨을 컨테이너 레이아웃에 추가
        container_layout.addWidget(self.label)

        # 컴포넌트를 메인 레이아웃에 추가
        main_layout.addWidget(self.drag_area)
        main_layout.addWidget(self.container)

        # 그림자 효과 적용
        self.apply_shadow_effect()

        # 창 크기 및 위치 설정
        self.resize(self.window_width, self.window_height + 10)  # +10은 드래그 영역용
        self.move(self.window_x, self.window_y)
        self.setWindowOpacity(self.opacity_level)

        # 카드 모드용 위젯 딕셔너리
        self.card_widgets = {}

        print("Drag Area Geometry:", self.drag_area.geometry()) # 디버깅: drag_area geometry 출력
        print("Container Geometry:", self.container.geometry()) # 디버깅: container geometry 출력
        print("Overlay Geometry:", self.geometry()) # 디버깅: overlay geometry 출력


    def apply_label_style(self):
        """라벨에 스타일 적용"""
        self.label.setFont(QFont(self.font_name, self.font_size, QFont.Bold))

        # 테마에 따른 스타일 적용
        if self.use_gradient_bg:
            bg_style = "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(60,60,70,200), stop:1 rgba(30,30,40,220));"
        else:
            bg_style = f"background-color: {self.background_color};"

        self.label.setStyleSheet(f"""
            color: {self.text_color};
            {bg_style}
            border: 1px solid rgba(80,80,80,120);
            border-radius: 12px;
            padding: 12px;
        """)

    def apply_shadow_effect(self):
        """라벨에 그림자 효과 적용"""
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setOffset(3, 3)
        shadow.setColor(QColor(0, 0, 0, 180))
        self.container.setGraphicsEffect(shadow)

    def setup_shortcuts(self):
        """단축키 설정"""
        QShortcut(QKeySequence("F2"), self, self.open_settings)
        QShortcut(QKeySequence("F5"), self, self.update_price)
        QShortcut(QKeySequence("Ctrl+Q"), self, self.close)
        QShortcut(QKeySequence("Ctrl+M"), self, self.toggle_display_mode)

    def setup_tray_icon(self):
        """시스템 트레이 아이콘 설정"""
        try:
            # 트레이 아이콘 생성
            self.tray_icon = QSystemTrayIcon(self)
            self.tray_icon.setIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))

            # 트레이 메뉴 생성
            tray_menu = QMenu()

            # 메뉴 항목 추가
            show_action = QAction("표시", self)
            show_action.triggered.connect(self.show)

            settings_action = QAction("설정", self)
            settings_action.triggered.connect(self.open_settings)

            mode_menu = QMenu("표시 모드")

            compact_action = QAction("간편 모드", self)
            compact_action.triggered.connect(lambda: self.set_display_mode(DisplayMode.COMPACT))

            standard_action = QAction("표준 모드", self)
            standard_action.triggered.connect(lambda: self.set_display_mode(DisplayMode.STANDARD))

            detailed_action = QAction("상세 모드", self)
            detailed_action.triggered.connect(lambda: self.set_display_mode(DisplayMode.DETAILED))

            cards_action = QAction("카드 모드", self)
            cards_action.triggered.connect(lambda: self.set_display_mode(DisplayMode.CARDS))

            mode_menu.addAction(compact_action)
            mode_menu.addAction(standard_action)
            mode_menu.addAction(detailed_action)
            mode_menu.addAction(cards_action)

            quit_action = QAction("종료", self)
            quit_action.triggered.connect(self.close)

            # 메뉴에 항목 추가
            tray_menu.addAction(show_action)
            tray_menu.addAction(settings_action)
            tray_menu.addMenu(mode_menu)
            tray_menu.addSeparator()
            tray_menu.addAction(quit_action)

            # 트레이 아이콘에 메뉴 설정
            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.show()

        except Exception as e:
            logging.error(f"트레이 아이콘 설정 실패: {e}")

    def toggle_display_mode(self):
        """표시 모드 전환"""
        modes = list(DisplayMode)
        current_index = modes.index(self.display_mode)
        next_index = (current_index + 1) % len(modes)
        self.set_display_mode(modes[next_index])

    def set_display_mode(self, mode):
        """표시 모드 설정"""
        self.display_mode = mode
        self.config.set("display_mode", mode.value)
        self.config.save()

        # UI 업데이트
        self.update_price_display()

        # 트레이 알림 표시
        if self.tray_icon:
            self.tray_icon.showMessage(
                "표시 모드 변경",
                f"표시 모드가 '{mode.value}'로 변경되었습니다.",
                QSystemTrayIcon.Information,
                2000
            )

    def load_settings(self):
        """설정 로드"""
        self.symbols = self.config.get("symbols", ["ETHUSDT"])
        self.font_name = self.config.get("font_name", "Segoe UI")
        self.opacity_level = self.config.get("opacity", 1.0)
        self.window_x = self.config.get("window_x", 1600)
        self.window_y = self.config.get("window_y", 50)
        self.font_size = self.config.get("font_size", 12)
        self.window_width = self.config.get("window_width", 300)
        self.window_height = self.config.get("window_height", 40)
        self.refresh_interval = self.config.get("refresh_interval", 2)
        self.theme = self.config.get("theme", "dark")

        # 디자인 설정 로드
        display_mode_str = self.config.get("display_mode", "standard")
        for mode in DisplayMode:
            if mode.value == display_mode_str:
                self.display_mode = mode
                break

        self.use_animations = self.config.get("use_animations", True)
        self.use_gradient_bg = self.config.get("use_gradient_bg", True)
        self.use_blur_effect = self.config.get("use_blur_effect", True)

        # 색상 설정 로드
        self.text_color = self.config.get("text_color", "#FFFFFF")
        self.background_color = self.config.get("background_color", "rgba(40,40,40,200)")
        self.positive_color = self.config.get("positive_color", "#4CAF50")
        self.negative_color = self.config.get("negative_color", "#F44336")
        self.neutral_color = self.config.get("neutral_color", "#FFA500")

    def save_settings(self):
        """현재 설정 저장"""
        settings = {
            "symbols": self.symbols,
            "font_name": self.font_name,
            "opacity": self.opacity_level,
            "window_x": self.x(),
            "window_y": self.y(),
            "font_size": self.font_size,
            "window_width": self.window_width,
            "window_height": self.window_height,
            "refresh_interval": self.refresh_interval,
            "theme": self.theme,
            "display_mode": self.display_mode.value,
            "use_animations": self.use_animations,
            "use_gradient_bg": self.use_gradient_bg,
            "use_blur_effect": self.use_blur_effect,
            "text_color": self.text_color,
            "background_color": self.background_color,
            "positive_color": self.positive_color,
            "negative_color": self.negative_color,
            "neutral_color": self.neutral_color
        }
        self.config.update(settings)
        self.config.save()

    def apply_settings(self):
        """설정 변경 적용"""
        self.apply_label_style()

        if self.display_mode == DisplayMode.CARDS:
            self.setup_card_layout()
        else:
            # self.label.setFixedSize(self.window_width, self.window_height) # 이 줄 삭제 (더 이상 고정 크기 설정 안함)
            self.resize(self.window_width, self.window_height + 10)  # +10은 드래그 영역용

        self.setWindowOpacity(self.opacity_level)

        # 타이머 간격 업데이트
        if self.timer.isActive():
            self.timer.stop()
            self.timer.start(self.refresh_interval * 1000)

        # 가격 정보 다시 표시
        if hasattr(self, 'price_data') and self.price_data:
            self.update_price_display()

    def update_price(self):
        """가격 업데이트 시작"""
        if self.fetcher is not None and self.fetcher.isRunning():
            logging.debug("이전 가격 업데이트가 아직 진행 중입니다.")
            return

        self.fetcher = PriceFetcherThread(self.symbols)
        self.fetcher.result_ready.connect(self.update_price_slot)
        self.fetcher.error_occurred.connect(self.handle_error)
        self.fetcher.start()

    @pyqtSlot(dict)
    def update_price_slot(self, results):
        """가격 업데이트 결과 처리"""
        old_data = self.price_data.copy() if hasattr(self, 'price_data') else {}
        self.price_data = results

        self.update_price_display()

        # 가격 변동 애니메이션 적용
        if self.use_animations and old_data:
            for symbol in self.price_data:
                if symbol in old_data and old_data[symbol][0] != self.price_data[symbol][0]:
                    self.animate_price_change(symbol, old_data[symbol][0], self.price_data[symbol][0])

    def update_price_display(self):
        """선택된 표시 모드에 따라 가격 정보 표시"""
        if self.display_mode == DisplayMode.CARDS:
            self.setup_card_layout()
        else:
            self.update_standard_display()

    def update_standard_display(self):
        """일반 텍스트 기반 표시 모드 업데이트"""
        if not hasattr(self, 'price_data') or not self.price_data:
            return

        lines = []
        max_width = 0  # 최대 너비 초기화
        font_metrics = QFontMetrics(self.label.font()) # FontMetrics 객체 생성

        for symbol, (binance_price, morning_diff, kimchi) in self.price_data.items():
            if binance_price is None:
                lines.append(f"{symbol}: N/A")
            else:
                # 티커 및 가격 정보
                price_str = f"{binance_price:,.2f}"

                # 트렌드 아이콘 추가
                trend_icon = self.get_trend_icon(morning_diff)

                # 모드별 표시 내용 조정
                if self.display_mode == DisplayMode.COMPACT:
                    # 간편 모드: 심볼, 가격, 트렌드 아이콘만 표시
                    line = f"{symbol} {price_str} {trend_icon}"
                else:
                    # 표준 모드: 심볼, 가격, 변동률, 김치 프리미엄 표시
                    if morning_diff is not None:
                        if morning_diff > 0:
                            diff_str = f"<span style='color:{self.positive_color};'>▲ {morning_diff:.2f}%</span>"
                        elif morning_diff < 0:
                            diff_str = f"<span style='color:{self.negative_color};'>▼ {-morning_diff:.2f}%</span>"
                        else:
                            diff_str = f"<span style='color:{self.text_color};'>0.00%</span>"
                    else:
                        diff_str = "N/A"

                    if kimchi is not None:
                        kimchi_str = f"<span style='color:{self.neutral_color};'>{kimchi:.2f}%</span>"
                    else:
                        kimchi_str = "N/A"

                    if self.display_mode == DisplayMode.DETAILED:
                        # 상세 모드: 추가 정보 표시
                        line = (f"<div style='margin-bottom: 5px;'>"
                                f"<b>{symbol}</b>     {price_str} {trend_icon}<br/>"
                                f"<span style='font-size:90%;'>변동률: {diff_str} | 김치 프리미엄: {kimchi_str}</span>"
                                f"</div>")
                    else:
                        # 표준 모드
                        line = (f"{symbol}     {price_str}    "
                                f"{diff_str}     {kimchi_str}")

                lines.append(line)
                text_width = font_metrics.boundingRect(line).width() # 텍스트 너비 계산
                max_width = max(max_width, text_width) # 최대 너비 업데이트

        self.label.setText("<br>".join(lines))

        # 너비 조정: 텍스트 너비 + 좌우 패딩 (padding: 12px * 2) + 컨테이너 마진 (5px * 2)
        required_width = max_width + (12 * 2) + (5 * 2) + 20 # 20px 추가 여유 공간
        if required_width != self.window_width:
            self.window_width = required_width
            self.resize(self.window_width, self.window_height + 10)  # +10은 드래그 영역용
            self.label.updateGeometry() # 레이아웃 업데이트 요청


        # 필요하면 높이 조정 (기존 코드 유지)
        if len(lines) > 1:
            line_height = 30 if self.display_mode == DisplayMode.DETAILED else 24
            required_height = max(40, len(lines) * line_height)
            if required_height != self.window_height:
                self.window_height = required_height
                self.resize(self.window_width, self.window_height + 10)  # +10은 드래그 영역용

    def setup_card_layout(self):
        """카드 레이아웃 설정"""
        if not hasattr(self, 'price_data') or not self.price_data:
            return

        # 기존 카드 위젯 제거
        for widget in self.card_widgets.values():
            if widget.parent() == self.container:
                widget.setParent(None)
                widget.deleteLater()
        self.card_widgets = {}

        # 컨테이너 레이아웃 재설정
        if self.container.layout():
            while self.container.layout().count():
                item = self.container.layout().takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

        # 새 레이아웃 생성
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(5, 5, 5, 5)
        container_layout.setSpacing(5)

        # 각 심볼에 대한 카드 생성
        for symbol, (binance_price, morning_diff, kimchi) in self.price_data.items():
            card = self.create_price_card(symbol, binance_price, morning_diff, kimchi)
            container_layout.addWidget(card)
            self.card_widgets[symbol] = card

        # 창 크기 조정
        card_height = 80  # 각 카드의 높이
        margin = 10  # 여백
        total_height = len(self.price_data) * (card_height + margin) + margin
        total_width = max(300, self.window_width)

        self.window_height = total_height
        self.window_width = total_width
        self.resize(total_width, total_height + 10)  # +10은 드래그 영역용

    def create_price_card(self, symbol, price, change, premium):
        """가격 정보 카드 위젯 생성"""
        card = QFrame(self.container)
        card.setObjectName(f"card_{symbol}")
        card.setMinimumHeight(70)
        card.setMaximumHeight(80)

        # 배경색 설정
        bg_color = self.get_trend_background(change)
        card.setStyleSheet(f"""
            QFrame {{
                {bg_color}
                border-radius: 10px;
                border: 1px solid rgba(80,80,80,120);
            }}
        """)

        # 카드의 레이아웃 설정
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(12, 8, 12, 8)

        # 상단 행: 심볼 및 가격
        top_row = QHBoxLayout()

        symbol_label = QLabel(f"<b>{symbol}</b>", card)
        symbol_label.setStyleSheet(f"color: {self.text_color}; font-size: {self.font_size + 2}px;")

        trend_icon = self.get_trend_icon(change)
        price_text = "N/A" if price is None else f"{price:,.2f}"
        price_label = QLabel(f"{price_text} {trend_icon}", card)
        price_label.setStyleSheet(f"color: {self.text_color}; font-size: {self.font_size + 2}px;")
        price_label.setAlignment(Qt.AlignRight)

        top_row.addWidget(symbol_label)
        top_row.addWidget(price_label)

        # 하단 행: 변동률 및 김치 프리미엄
        bottom_row = QHBoxLayout()

        if change is not None:
            change_color = self.positive_color if change > 0 else self.negative_color if change < 0 else self.text_color
            change_text = f"▲ {change:.2f}%" if change > 0 else f"▼ {-change:.2f}%" if change < 0 else "0.00%"
            change_label = QLabel(f"변동률: <span style='color:{change_color};'>{change_text}</span>", card)
        else:
            change_label = QLabel("변동률: N/A", card)
        change_label.setStyleSheet(f"color: {self.text_color}; font-size: {self.font_size}px;")

        if premium is not None:
            premium_label = QLabel(f"김치 프리미엄: <span style='color:{self.neutral_color};'>{premium:.2f}%</span>", card)
        else:
            premium_label = QLabel("김치 프리미엄: N/A", card)
        premium_label.setStyleSheet(f"color: {self.text_color}; font-size: {self.font_size}px;")
        premium_label.setAlignment(Qt.AlignRight)

        bottom_row.addWidget(change_label)
        bottom_row.addWidget(premium_label)

        # 레이아웃에 행 추가
        card_layout.addLayout(top_row)
        card_layout.addLayout(bottom_row)

        return card

    def get_trend_background(self, value):
        """변동률에 따른 배경색 그라데이션 반환"""
        if value is None:
            return "background-color: rgba(60,60,60,200);"

        intensity = min(abs(value) * 5, 80)  # 최대 80% 투명도

        if value > 0:
            return f"background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(0,80,0,200), stop:1 rgba(30,30,40,200));"
        elif value < 0:
            return f"background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(80,0,0,200), stop:1 rgba(30,30,40,200));"
        else:
            return "background-color: rgba(50,50,60,200);"

    def get_trend_icon(self, value):
        """변동률에 따른 아이콘 반환"""
        if value is None:
            return "⚪"
        elif value > 5.0:
            return "🚀"  # 급상승
        elif value > 1.0:
            return "📈"  # 상승
        elif value < -5.0:
            return "💥"  # 급하락
        elif value < -1.0:
            return "📉"  # 하락
        else:
            return "⚖️"  # 유지

    def animate_price_change(self, symbol, old_price, new_price):
        """가격 변경 애니메이션 적용"""
        if not self.use_animations or old_price is None or new_price is None:
            return

        if self.display_mode == DisplayMode.CARDS and symbol in self.card_widgets:
            widget = self.card_widgets[symbol]
        else:
            widget = self.label

        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)

        # 플래시 애니메이션 생성
        animation = QPropertyAnimation(effect, b"opacity")
        animation.setDuration(300)
        animation.setStartValue(1.0)
        animation.setEndValue(0.5)

        animation2 = QPropertyAnimation(effect, b"opacity")
        animation2.setDuration(300)
        animation2.setStartValue(0.5)
        animation2.setEndValue(1.0)

        sequence = QSequentialAnimationGroup()
        sequence.addAnimation(animation)
        sequence.addAnimation(animation2)
        sequence.start()

    @pyqtSlot(str)
    def handle_error(self, error_message):
        """오류 처리"""
        logging.error(f"오류 발생: {error_message}")
        self.label.setText(f"<span style='color:{self.negative_color};'>오류: {error_message}</span>")

        # 사용자에게 알림
        if self.tray_icon and self.tray_icon.isSystemTrayAvailable():
            self.tray_icon.showMessage("오류", error_message, QSystemTrayIcon.Warning, 3000)

    def wheelEvent(self, event):
        """마우스 휠 이벤트 처리 - 투명도 조절"""
        delta = event.angleDelta().y() / 120
        new_opacity = self.opacity_level + (delta * 0.05)
        new_opacity = max(0.1, min(new_opacity, 1.0))
        self.opacity_level = new_opacity
        self.setWindowOpacity(self.opacity_level)
        self.save_settings()

    def mousePressEvent(self, event):
        """마우스 누름 이벤트 처리"""
        if event.button() == Qt.LeftButton:
            # 이제 drag_area 영역 체크 없이, 항상 드래그 시작
            print("Overlay Clicked!") # 디버깅 출력: 클릭 감지 확인 (전체 영역)
            self.dragging = True
            self.dragPos = event.globalPos()
            self.setWindowOpacity(self.opacity_level * 0.8)
            event.accept()
        elif event.button() == Qt.RightButton:
            self.open_settings()
            event.accept()

    def mouseMoveEvent(self, event):
        """마우스 이동 이벤트 처리"""
        if self.dragging and event.buttons() & Qt.LeftButton:
            print("Dragging...") # 디버깅 출력: 드래그 중인지 확인
            self.move(self.pos() + event.globalPos() - self.dragPos)
            self.dragPos = event.globalPos()
            event.accept()

    def mouseReleaseEvent(self, event):
        """마우스 릴리즈 이벤트 처리"""
        if event.button() == Qt.LeftButton and self.dragging:
            print("Drag Released!") # 디버깅 출력: 드래그 종료 확인
            self.dragging = False
            self.setWindowOpacity(self.opacity_level)
            self.save_settings()
            event.accept()

    def open_settings(self):
        """설정 창 열기"""
        if not self.settings_dialog:
            self.settings_dialog = SettingsDialog(self)
        self.settings_dialog.show()
        self.settings_dialog.raise_()
        self.settings_dialog.activateWindow()

    def keyPressEvent(self, event):
        """키 입력 이벤트 처리"""
        if event.key() == Qt.Key_Escape:
            self.hide()
            if self.tray_icon:
                self.tray_icon.showMessage(
                    "암호화폐 오버레이",
                    "프로그램이 트레이로 최소화되었습니다.",
                    QSystemTrayIcon.Information,
                    2000
                )
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        """창 닫기 이벤트 처리"""
        self.save_settings()
        if self.tray_icon:
            self.tray_icon.hide()
        event.accept()