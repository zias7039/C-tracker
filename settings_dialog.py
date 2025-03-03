# settings_dialog.py
import logging
from PyQt5.QtWidgets import (
    QDialog, QGroupBox, QFormLayout, QLineEdit, QSlider, QFontComboBox,
    QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QWidget, QSpinBox, QCheckBox,
    QColorDialog, QComboBox, QTabWidget, QGridLayout, QScrollArea, QFrame,
    QListWidget, QSizePolicy, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QSize, QTimer
from PyQt5.QtGui import QFont, QColor, QIcon


class ColorButton(QPushButton):
    """색상 선택 버튼 클래스"""
    colorChanged = pyqtSignal(str)

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


class SettingsDialog(QDialog):
    # 설정이 적용되었을 때 발생하는 시그널
    settings_applied = pyqtSignal(dict)

    def __init__(self, overlay):
        # 독립적인 대화상자로 생성 (부모 없음)
        super().__init__(None)

        # 메서드 별칭 설정 (호환성을 위해)
        self.apply_settings = self.apply_settings_method

        # 창 설정
        self.setWindowFlags(Qt.Dialog)
        self.setAttribute(Qt.WA_DeleteOnClose, False)

        # 오버레이 객체 참조 (부모-자식 관계 없음)
        self.overlay = overlay

        # 임시 설정 저장용 딕셔너리
        self.temp_settings = self.overlay.config.get_all().copy()

        # 업데이트 제한을 위한 타이머
        self.update_timer = QTimer(self)
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self.process_delayed_updates)
        self.pending_updates = {}

        # UI 초기화
        self.initUI()

        # UI 요소 이벤트 연결
        self.connect_ui_events()

    def apply_settings_method(self):
        """현재 설정 적용 (창은 닫지 않음)"""
        try:
            # 현재 설정 가져오기
            settings = self.get_current_settings()

            # 설정 적용 시그널 발생
            self.settings_applied.emit(settings)

            # 성공 메시지
            QMessageBox.information(self, "알림", "설정이 적용되었습니다.")
        except Exception as e:
            logging.error(f"설정 적용 중 오류: {e}")
            QMessageBox.critical(self, "오류", f"설정을 적용하는 중 오류가 발생했습니다: {e}")

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

        # 시각 효과 설정 그룹
        effects_group = QGroupBox("시각 효과")
        effects_layout = QVBoxLayout()

        # 시각 효과 체크박스
        self.animation_check = QCheckBox("애니메이션 효과 사용")
        self.animation_check.setChecked(self.overlay.use_animations)

        self.gradient_check = QCheckBox("그라데이션 배경 사용")
        self.gradient_check.setChecked(self.overlay.use_gradient_bg)

        self.blur_check = QCheckBox("블러 효과 사용 (일부 시스템 한정)")
        self.blur_check.setChecked(self.overlay.use_blur_effect)

        effects_layout.addWidget(self.animation_check)
        effects_layout.addWidget(self.gradient_check)
        effects_layout.addWidget(self.blur_check)

        effects_group.setLayout(effects_layout)
        design_layout.addWidget(effects_group)

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
        self.apply_button = QPushButton("적용")
        self.save_button = QPushButton("저장")
        self.cancel_button = QPushButton("취소")

        self.save_button.setDefault(True)

        button_layout.addWidget(self.reset_button)
        button_layout.addStretch(1)
        button_layout.addWidget(self.apply_button)
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
        # 버튼 이벤트
        self.reset_button.clicked.connect(self.reset_to_defaults)
        self.apply_button.clicked.connect(self.apply_settings_method)
        self.save_button.clicked.connect(self.save_and_close)
        self.cancel_button.clicked.connect(self.close)

        # 슬라이더 이벤트 - 실시간 적용 추가 (쓰로틀링 적용)
        self.width_slider.valueChanged.connect(self.update_width_label)
        self.width_slider.valueChanged.connect(
            lambda value: self.schedule_setting_update("window_width", value))

        self.height_slider.valueChanged.connect(self.update_height_label)
        self.height_slider.valueChanged.connect(
            lambda value: self.schedule_setting_update("window_height", value))

        self.opacity_slider.valueChanged.connect(self.update_opacity_label)
        self.opacity_slider.valueChanged.connect(
            lambda value: self.schedule_setting_update("opacity", value / 100.0))

        self.font_slider.valueChanged.connect(self.update_font_size_label)
        self.font_slider.valueChanged.connect(
            lambda value: self.schedule_setting_update("font_size", value))

        # 콤보박스 이벤트 - 실시간 적용
        self.font_combo.currentFontChanged.connect(
            lambda font: self.schedule_setting_update("font_name", font.family()))

        # 체크박스 이벤트 - 실시간 적용
        self.animation_check.stateChanged.connect(
            lambda state: self.schedule_setting_update("use_animations", bool(state)))
        self.gradient_check.stateChanged.connect(
            lambda state: self.schedule_setting_update("use_gradient_bg", bool(state)))
        self.blur_check.stateChanged.connect(
            lambda state: self.schedule_setting_update("use_blur_effect", bool(state)))

        # 색상 버튼 이벤트
        self.text_color_btn.colorChanged.connect(
            lambda color: self.schedule_setting_update("text_color", color))
        self.bg_color_btn.colorChanged.connect(
            lambda color: self.schedule_setting_update("background_color", color))
        self.positive_color_btn.colorChanged.connect(
            lambda color: self.schedule_setting_update("positive_color", color))
        self.negative_color_btn.colorChanged.connect(
            lambda color: self.schedule_setting_update("negative_color", color))
        self.neutral_color_btn.colorChanged.connect(
            lambda color: self.schedule_setting_update("neutral_color", color))

        # 티커 설정은 즉시 적용하지 않음 (엔터 키 입력 필요)
        self.symbol_input.returnPressed.connect(self.update_symbols)
        self.interval_spin.valueChanged.connect(
            lambda value: self.schedule_setting_update("refresh_interval", value))

    def update_symbols(self):
        """심볼 목록 업데이트 및 즉시 적용"""
        symbols = [s.strip().upper() for s in self.symbol_input.text().split(",") if s.strip()]
        self.schedule_setting_update("symbols", symbols)

    def update_width_label(self, value):
        """너비 슬라이더 값 업데이트"""
        self.width_value_label.setText(f"{value}px")
        self.temp_settings["window_width"] = value

    def update_height_label(self, value):
        """높이 슬라이더 값 업데이트"""
        self.height_value_label.setText(f"{value}px")
        self.temp_settings["window_height"] = value

    def update_opacity_label(self, value):
        """투명도 슬라이더 값 업데이트"""
        self.opacity_value_label.setText(f"{value}%")
        self.temp_settings["opacity"] = value / 100.0

    def update_font_size_label(self, value):
        """글꼴 크기 슬라이더 값 업데이트"""
        self.font_size_label.setText(f"{value}pt")
        self.temp_settings["font_size"] = value

    def update_temp_settings(self, key, value):
        """임시 설정 업데이트"""
        self.temp_settings[key] = value

    def schedule_setting_update(self, key, value):
        """설정 업데이트 예약 (쓰로틀링 적용)"""
        # 임시 설정 저장
        self.update_temp_settings(key, value)

        # 쓰로틀링을 위해 보류 중인 업데이트에 추가
        self.pending_updates[key] = value

        # 타이머가 이미 실행 중이 아니라면 시작
        if not self.update_timer.isActive():
            self.update_timer.start(300)  # 300ms 지연

    def process_delayed_updates(self):
        """지연된 설정 업데이트 처리"""
        if not self.pending_updates:
            return

        try:
            # 적용할 설정들을 하나의 딕셔너리로
            settings = self.pending_updates.copy()

            # 설정 적용 시그널 발생
            self.settings_applied.emit(settings)

            # 처리 완료된 업데이트 초기화
            self.pending_updates.clear()
        except Exception as e:
            logging.error(f"설정 일괄 적용 중 오류: {e}")

    def get_current_settings(self):
        """현재 설정 값 가져오기"""
        # 심볼 목록
        symbols = [s.strip().upper() for s in self.symbol_input.text().split(",") if s.strip()]

        # 임시 설정에 추가
        settings = self.temp_settings.copy()
        settings.update({
            "symbols": symbols,
            "font_name": self.font_combo.currentFont().family(),
            "opacity": self.opacity_slider.value() / 100.0,
            "font_size": self.font_slider.value(),
            "window_width": self.width_slider.value(),
            "window_height": self.height_slider.value(),
            "refresh_interval": self.interval_spin.value(),
            "use_animations": self.animation_check.isChecked(),
            "use_gradient_bg": self.gradient_check.isChecked(),
            "use_blur_effect": self.blur_check.isChecked(),
            # 색상 값은 이미 이벤트로 업데이트됨
        })

        return settings

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

        self.animation_check.setChecked(True)
        self.gradient_check.setChecked(True)
        self.blur_check.setChecked(False)

        self.text_color_btn.setColor("#FFFFFF")
        self.bg_color_btn.setColor("rgba(40,40,40,200)")
        self.positive_color_btn.setColor("#4CAF50")
        self.negative_color_btn.setColor("#F44336")
        self.neutral_color_btn.setColor("#FFA500")

        # 임시 설정 초기화
        self.temp_settings = {
            "text_color": "#FFFFFF",
            "background_color": "rgba(40,40,40,200)",
            "positive_color": "#4CAF50",
            "negative_color": "#F44336",
            "neutral_color": "#FFA500"
        }

    def save_and_close(self):
        """설정 저장 및 대화상자 닫기"""
        try:
            # 현재 설정 가져오기
            settings = self.get_current_settings()

            # 설정 적용 시그널 발생
            self.settings_applied.emit(settings)

            # 대화상자 닫기
            self.accept()
        except Exception as e:
            logging.error(f"설정 저장 중 오류: {e}")
            QMessageBox.critical(self, "오류", f"설정을 저장하는 중 오류가 발생했습니다: {e}")

    def closeEvent(self, event):
        """창 닫기 이벤트 처리"""
        # 설정 창 닫기 허용
        event.accept()
