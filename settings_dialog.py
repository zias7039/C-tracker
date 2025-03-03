# settings_dialog.py
from PyQt5.QtWidgets import (
    QDialog, QGroupBox, QFormLayout, QLineEdit, QSlider, QFontComboBox,
    QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QWidget, QSpinBox, QCheckBox,
    QColorDialog, QComboBox, QTabWidget, QGridLayout, QScrollArea, QFrame,
    QListWidget, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QSize
from PyQt5.QtGui import QFont, QColor, QIcon


class ColorButton(QPushButton):
    """색상 선택 버튼 클래스"""

    def __init__(self, color="#FFFFFF", parent=None):
        super().__init__(parent)
        self.setColor(color)
        self.clicked.connect(self.pickColor)
        self.setMinimumSize(30, 30)
        self.setMaximumSize(30, 30)

    def setColor(self, color):
        self.color = color
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                border: 1px solid #555;
                border-radius: 3px;
            }}
            QPushButton:hover {{
                border: 2px solid #999;
            }}
        """)

    def pickColor(self):
        color = QColorDialog.getColor(QColor(self.color), self.parent(), "색상 선택")
        if color.isValid():
            self.setColor(color.name())
            self.colorChanged.emit(color.name())

    colorChanged = pyqtSignal(str)


class SettingsDialog(QDialog):
    def __init__(self, overlay):
        # 부모-자식 관계를 끊기 위해 None으로 설정
        super().__init__(None)
        self.overlay = overlay
        self.initUI()

        # UI 요소 이벤트 연결
        self.connect_ui_events()

    def initUI(self):
        """UI 초기화"""
        self.setWindowTitle("설정")
        self.resize(600, 450)  # 창 크기 증가

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        # 탭 위젯 생성
        self.tab_widget = QTabWidget()

        # 일반 설정 탭
        general_tab = QWidget()
        general_layout = QVBoxLayout(general_tab)
        general_layout.setContentsMargins(15, 15, 15, 15)

        # 티커 설정 그룹
        ticker_group = QGroupBox("티커 설정")
        ticker_layout = QFormLayout()

        self.symbol_input = QLineEdit()
        self.symbol_input.setText(", ".join(self.overlay.symbols))
        self.symbol_input.setPlaceholderText("예: BTCUSDT, ETHUSDT, SOLUSDT")
        ticker_layout.addRow("티커 입력:", self.symbol_input)

        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 60)
        self.interval_spin.setValue(self.overlay.refresh_interval)
        self.interval_spin.setSuffix(" 초")
        ticker_layout.addRow("새로고침 간격:", self.interval_spin)

        ticker_group.setLayout(ticker_layout)
        general_layout.addWidget(ticker_group)

        # 위치 및 크기 설정 그룹
        position_group = QGroupBox("위치 및 크기")
        position_layout = QGridLayout()

        self.width_slider = QSlider(Qt.Horizontal)
        self.width_slider.setRange(100, 600)
        self.width_slider.setValue(self.overlay.window_width)
        self.width_value_label = QLabel(f"{self.overlay.window_width}px")

        self.height_slider = QSlider(Qt.Horizontal)
        self.height_slider.setRange(40, 500)
        self.height_slider.setValue(self.overlay.window_height)
        self.height_value_label = QLabel(f"{self.overlay.window_height}px")

        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(10, 100)
        self.opacity_slider.setValue(int(self.overlay.opacity_level * 100))
        self.opacity_value_label = QLabel(f"{int(self.overlay.opacity_level * 100)}%")

        position_layout.addWidget(QLabel("창 너비:"), 0, 0)
        position_layout.addWidget(self.width_slider, 0, 1)
        position_layout.addWidget(self.width_value_label, 0, 2)

        position_layout.addWidget(QLabel("창 높이:"), 1, 0)
        position_layout.addWidget(self.height_slider, 1, 1)
        position_layout.addWidget(self.height_value_label, 1, 2)

        position_layout.addWidget(QLabel("투명도:"), 2, 0)
        position_layout.addWidget(self.opacity_slider, 2, 1)
        position_layout.addWidget(self.opacity_value_label, 2, 2)

        position_group.setLayout(position_layout)
        general_layout.addWidget(position_group)

        general_layout.addStretch(1)  # 여백 추가

        # 디자인 설정 탭
        design_tab = QWidget()
        design_layout = QVBoxLayout(design_tab)
        design_layout.setContentsMargins(15, 15, 15, 15)

        # 글꼴 설정 그룹
        font_group = QGroupBox("글꼴 설정")
        font_layout = QGridLayout()

        self.font_combo = QFontComboBox()
        self.font_combo.setCurrentFont(QFont(self.overlay.font_name))

        self.font_slider = QSlider(Qt.Horizontal)
        self.font_slider.setRange(8, 30)
        self.font_slider.setValue(self.overlay.font_size)
        self.font_size_label = QLabel(f"{self.overlay.font_size}pt")

        font_layout.addWidget(QLabel("글꼴:"), 0, 0)
        font_layout.addWidget(self.font_combo, 0, 1, 1, 2)

        font_layout.addWidget(QLabel("크기:"), 1, 0)
        font_layout.addWidget(self.font_slider, 1, 1)
        font_layout.addWidget(self.font_size_label, 1, 2)

        font_group.setLayout(font_layout)
        design_layout.addWidget(font_group)

        # 표시 모드 설정
        display_group = QGroupBox("표시 모드")
        display_layout = QVBoxLayout()

        self.mode_combo = QComboBox()
        self.mode_combo.addItem("간편 모드 - 기본 정보만 표시", "compact")
        self.mode_combo.addItem("표준 모드 - 일반 표시", "standard")
        self.mode_combo.addItem("상세 모드 - 자세한 정보 표시", "detailed")
        self.mode_combo.addItem("카드 모드 - 개별 카드 표시", "cards")

        # 현재 선택된 모드 설정
        for i in range(self.mode_combo.count()):
            if self.mode_combo.itemData(i) == self.overlay.display_mode.value:
                self.mode_combo.setCurrentIndex(i)
                break

        display_layout.addWidget(QLabel("표시 모드:"))
        display_layout.addWidget(self.mode_combo)

        # 시각 효과 체크박스
        self.animation_check = QCheckBox("애니메이션 효과 사용")
        self.animation_check.setChecked(self.overlay.use_animations)

        self.gradient_check = QCheckBox("그라데이션 배경 사용")
        self.gradient_check.setChecked(self.overlay.use_gradient_bg)

        self.blur_check = QCheckBox("블러 효과 사용 (일부 시스템 한정)")
        self.blur_check.setChecked(self.overlay.use_blur_effect)

        display_layout.addWidget(self.animation_check)
        display_layout.addWidget(self.gradient_check)
        display_layout.addWidget(self.blur_check)

        display_group.setLayout(display_layout)
        design_layout.addWidget(display_group)

        # 색상 설정 그룹
        color_group = QGroupBox("색상 설정")
        color_layout = QGridLayout()

        # 텍스트 색상
        self.text_color_btn = ColorButton(self.overlay.text_color)
        color_layout.addWidget(QLabel("텍스트 색상:"), 0, 0)
        color_layout.addWidget(self.text_color_btn, 0, 1)

        # 배경 색상
        self.bg_color_btn = ColorButton(self.overlay.background_color)
        color_layout.addWidget(QLabel("배경 색상:"), 1, 0)
        color_layout.addWidget(self.bg_color_btn, 1, 1)

        # 상승 색상
        self.positive_color_btn = ColorButton(self.overlay.positive_color)
        color_layout.addWidget(QLabel("상승 색상:"), 2, 0)
        color_layout.addWidget(self.positive_color_btn, 2, 1)

        # 하락 색상
        self.negative_color_btn = ColorButton(self.overlay.negative_color)
        color_layout.addWidget(QLabel("하락 색상:"), 3, 0)
        color_layout.addWidget(self.negative_color_btn, 3, 1)

        # 중립 색상
        self.neutral_color_btn = ColorButton(self.overlay.neutral_color)
        color_layout.addWidget(QLabel("중립 색상:"), 4, 0)
        color_layout.addWidget(self.neutral_color_btn, 4, 1)

        color_group.setLayout(color_layout)
        design_layout.addWidget(color_group)

        design_layout.addStretch(1)  # 여백 추가

        # 정보 탭
        info_tab = QWidget()
        info_layout = QVBoxLayout(info_tab)
        info_layout.setContentsMargins(15, 15, 15, 15)

        # 프로그램 정보
        info_text = QLabel("""
            <h2>암호화폐 오버레이</h2>
            <p>이 프로그램은 데스크톱 화면에 실시간 암호화폐 가격 정보를 표시합니다.</p>
            <h3>사용 방법:</h3>
            <ul>
                <li><b>F2</b>: 설정 창 열기</li>
                <li><b>F5</b>: 가격 정보 새로고침</li>
                <li><b>Esc</b>: 트레이로 최소화</li>
                <li><b>Ctrl+Q</b>: 프로그램 종료</li>
                <li><b>Ctrl+M</b>: 표시 모드 변경</li>
                <li>마우스 휠: 투명도 조절</li>
                <li>좌클릭 드래그: 창 이동</li>
                <li>우클릭: 설정 창 열기</li>
            </ul>
            <p>가격 정보는 Binance API를 통해 가져오며, 자정과 오전 9시 사이에는 전날 데이터를 기준으로 변동률을 계산합니다.</p>
        """)
        info_text.setWordWrap(True)
        info_text.setTextFormat(Qt.RichText)

        info_scroll = QScrollArea()
        info_scroll.setWidget(info_text)
        info_scroll.setWidgetResizable(True)

        info_layout.addWidget(info_scroll)

        # 탭 추가
        self.tab_widget.addTab(general_tab, "일반 설정")
        self.tab_widget.addTab(design_tab, "디자인 설정")
        self.tab_widget.addTab(info_tab, "정보")

        main_layout.addWidget(self.tab_widget)

        # 버튼 영역
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 10, 0, 0)

        self.reset_button = QPushButton("기본값으로 복원")
        self.save_button = QPushButton("저장")
        self.cancel_button = QPushButton("취소")

        self.save_button.setDefault(True)

        button_layout.addWidget(self.reset_button)
        button_layout.addStretch(1)
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.save_button)

        main_layout.addLayout(button_layout)

        # 모던 스타일 적용
        self.apply_modern_style()

    def apply_modern_style(self):
        """모던 스타일 적용"""
        # 다크 테마 스타일시트
        self.setStyleSheet("""
            QDialog {
                background-color: #2B2B2B;
                color: #EEEEEE;
            }
            QLabel {
                color: #EEEEEE;
            }
            QGroupBox {
                background-color: #333333;
                border-radius: 5px;
                border: 1px solid #444444;
                color: #EEEEEE;
                font-weight: bold;
                margin-top: 12px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
                color: #7AB1FF;
            }
            QPushButton {
                background-color: #505050;
                color: #EEEEEE;
                border: 1px solid #606060;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #606060;
            }
            QPushButton:pressed {
                background-color: #404040;
            }
            QLineEdit, QSpinBox, QComboBox, QFontComboBox {
                background-color: #3A3A3A;
                color: #EEEEEE;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 4px;
                selection-background-color: #4A90E2;
            }
            QTabWidget::pane {
                border: 1px solid #444444;
                background-color: #2B2B2B;
                border-radius: 3px;
            }
            QTabBar::tab {
                background-color: #3A3A3A;
                color: #EEEEEE;
                padding: 8px 12px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected, QTabBar::tab:hover {
                background-color: #505050;
            }
            QTabBar::tab:selected {
                border-bottom: 2px solid #7AB1FF;
            }
            QSlider::groove:horizontal {
                border: 1px solid #444444;
                background: #3A3A3A;
                height: 8px;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #7AB1FF;
                border: 1px solid #5A8ADB;
                width: 16px;
                margin: -4px 0;
                border-radius: 8px;
            }
            QSlider::handle:horizontal:hover {
                background: #5A8ADB;
            }
            QCheckBox {
                color: #EEEEEE;
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
            QScrollArea {
                border: 1px solid #444444;
                border-radius: 3px;
            }
        """)

    def connect_ui_events(self):
        """UI 이벤트 연결"""
        # 일반 설정 이벤트
        self.symbol_input.textChanged.connect(self.update_overlay_preview)
        self.interval_spin.valueChanged.connect(self.update_overlay_preview)

        # 위치 및 크기 설정 이벤트
        self.width_slider.valueChanged.connect(self.update_width_label)
        self.width_slider.valueChanged.connect(self.update_overlay_preview)

        self.height_slider.valueChanged.connect(self.update_height_label)
        self.height_slider.valueChanged.connect(self.update_overlay_preview)

        self.opacity_slider.valueChanged.connect(self.update_opacity_label)
        self.opacity_slider.valueChanged.connect(self.update_overlay_preview)

        # 디자인 설정 이벤트
        self.font_combo.currentFontChanged.connect(self.update_overlay_preview)

        self.font_slider.valueChanged.connect(self.update_font_size_label)
        self.font_slider.valueChanged.connect(self.update_overlay_preview)

        self.mode_combo.currentIndexChanged.connect(self.update_overlay_preview)

        self.animation_check.stateChanged.connect(self.update_overlay_preview)
        self.gradient_check.stateChanged.connect(self.update_overlay_preview)
        self.blur_check.stateChanged.connect(self.update_overlay_preview)

        # 색상 버튼 이벤트
        self.text_color_btn.colorChanged.connect(lambda color: self.update_color("text", color))
        self.bg_color_btn.colorChanged.connect(lambda color: self.update_color("background", color))
        self.positive_color_btn.colorChanged.connect(lambda color: self.update_color("positive", color))
        self.negative_color_btn.colorChanged.connect(lambda color: self.update_color("negative", color))
        self.neutral_color_btn.colorChanged.connect(lambda color: self.update_color("neutral", color))

        # 버튼 이벤트
        self.reset_button.clicked.connect(self.reset_to_defaults)
        self.save_button.clicked.connect(self.save_and_close)
        self.cancel_button.clicked.connect(self.reject)

    def update_width_label(self, value):
        self.width_value_label.setText(f"{value}px")

    def update_height_label(self, value):
        self.height_value_label.setText(f"{value}px")

    def update_opacity_label(self, value):
        self.opacity_value_label.setText(f"{value}%")

    def update_font_size_label(self, value):
        self.font_size_label.setText(f"{value}pt")

    def update_color(self, color_type, color):
        """색상 변경 처리"""
        if color_type == "text":
            self.overlay.text_color = color
        elif color_type == "background":
            self.overlay.background_color = color
        elif color_type == "positive":
            self.overlay.positive_color = color
        elif color_type == "negative":
            self.overlay.negative_color = color
        elif color_type == "neutral":
            self.overlay.neutral_color = color

        self.update_overlay_preview()

    def update_overlay_preview(self):
        """UI 변경 시 오버레이 미리보기 업데이트"""
        try:
            # 티커 입력 처리
            syms = self.symbol_input.text()
            self.overlay.symbols = [s.strip().upper() for s in syms.split(",") if s.strip()]

            # 폰트 및 크기 설정
            self.overlay.font_name = self.font_combo.currentFont().family()
            self.overlay.font_size = self.font_slider.value()

            # 창 크기 설정
            self.overlay.window_width = self.width_slider.value()
            self.overlay.window_height = self.height_slider.value()

            # 투명도 설정
            self.overlay.opacity_level = self.opacity_slider.value() / 100.0

            # 새로고침 간격 설정
            self.overlay.refresh_interval = self.interval_spin.value()

            # 표시 모드 설정
            mode_value = self.mode_combo.currentData()
            for mode in self.overlay.DisplayMode:
                if mode.value == mode_value:
                    self.overlay.display_mode = mode
                    break

            # 시각 효과 설정
            self.overlay.use_animations = self.animation_check.isChecked()
            self.overlay.use_gradient_bg = self.gradient_check.isChecked()
            self.overlay.use_blur_effect = self.blur_check.isChecked()

            # 설정 즉시 적용
            self.overlay.apply_settings()

            # 변경된 심볼이 있으면 가격 업데이트
            self.overlay.update_price()

        except Exception as e:
            logging.error(f"설정 미리보기 업데이트 중 오류: {e}")

    def reset_to_defaults(self):
        """기본 설정으로 복원"""
        # 기본값 설정
        self.symbol_input.setText("BTCUSDT, ETHUSDT")
        self.interval_spin.setValue(2)

        self.width_slider.setValue(300)
        self.height_slider.setValue(40)
        self.opacity_slider.setValue(100)

        self.font_combo.setCurrentFont(QFont("Segoe UI"))
        self.font_slider.setValue(12)

        for i in range(self.mode_combo.count()):
            if self.mode_combo.itemData(i) == "standard":
                self.mode_combo.setCurrentIndex(i)
                break

        self.animation_check.setChecked(True)
        self.gradient_check.setChecked(True)
        self.blur_check.setChecked(False)

        self.text_color_btn.setColor("#FFFFFF")
        self.bg_color_btn.setColor("rgba(40,40,40,200)")
        self.positive_color_btn.setColor("#4CAF50")
        self.negative_color_btn.setColor("#F44336")
        self.neutral_color_btn.setColor("#FFA500")

        # 미리보기 업데이트
        self.update_overlay_preview()

    def save_and_close(self):
        """설정 저장 및 대화상자 닫기"""
        # 현재 설정 적용
        self.update_overlay_preview()

        # 설정 저장
        self.overlay.save_settings()

        # 대화상자만 닫기 (accept 대신 hide 사용)
        self.hide()

    def accept(self):
        """확인 버튼 기본 동작 재정의"""
        self.save_and_close()
        # 주의: super().accept()를 호출하지 않음

    def reject(self):
        """취소 버튼 기본 동작 재정의"""
        self.hide()
        # 주의: super().reject()를 호출하지 않음

    def closeEvent(self, event):
        """창 닫기 이벤트 처리"""
        self.hide()
        event.ignore()  # 부모 창에 이벤트가 전파되지 않도록 방지