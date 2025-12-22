import time
import math
from aqt import mw, gui_hooks
from aqt.qt import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QSpinBox, QLabel, QTimer, QPainter, QColor, 
    QRectF, Qt, QPen, QDockWidget, QCheckBox, QComboBox, 
    QFrame, QApplication
)
from .state import STOPPED, RUNNING, PAUSED

class TimerDisplayWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.progress = 0.0
        self.remaining_text = "00:00"
        self.minimal_mode = False
        self.setMinimumHeight(180)

    def set_minimal_mode(self, is_minimal):
        self.minimal_mode = is_minimal
        self.update()

    def update_time(self, progress, remaining_seconds):
        self.progress = progress
        display_seconds = math.ceil(remaining_seconds)
        mins, secs = divmod(int(display_seconds), 60)
        self.remaining_text = f"{mins:02d}:{secs:02d}"
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        is_night = mw.pm.night_mode()
        primary_color = QColor(255, 255, 255) if is_night else QColor(0, 0, 0)
        track_color = QColor(80, 80, 80) if is_night else QColor(230, 230, 230)
        
        center = self.rect().center()
        
        if not self.minimal_mode:
            size = min(self.width(), self.height()) - 40
            rect = QRectF(center.x() - size/2, center.y() - size/2, size, size)

            painter.setPen(QPen(track_color, 2))
            painter.drawEllipse(rect)

            if self.progress > 0:
                pen = QPen(QColor(10, 132, 255), 8)
                pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                painter.setPen(pen)
                span_angle = int(-360 * self.progress * 16)
                painter.drawArc(rect, 90 * 16, span_angle)

        painter.setPen(primary_color) 
        font = painter.font()
        font.setBold(True)
        font.setPointSize(48 if self.minimal_mode else 28)
        painter.setFont(font)
        
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.remaining_text)

class StudyTimerDock(QDockWidget):
    def __init__(self, parent=None):
        super().__init__("Timer de Estudo", parent)
        self.setObjectName("StudyTimerDock")
        self.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetClosable | 
                         QDockWidget.DockWidgetFeature.DockWidgetMovable)

        self.container = QWidget()
        self.main_layout = QVBoxLayout(self.container)
        self.main_layout.setContentsMargins(5, 5, 5, 5) 
        self.main_layout.setSpacing(5)
        
        self.state = STOPPED
        self.total_seconds = 0
        self.elapsed_seconds = 0.0
        self.last_tick = None

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)

        # --- Settings Button ---
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.addStretch()
        
        self.settings_btn = QPushButton("⛭")
        self.settings_btn.setFixedSize(20, 20)
        self.settings_btn.setFlat(True)
        self.settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.settings_btn.clicked.connect(self.toggle_settings)
        
        header_layout.addWidget(self.settings_btn)

        # --- Settings Panel ---
        self.settings_panel = QFrame()
        self.settings_panel.setVisible(False)
        settings_layout = QVBoxLayout(self.settings_panel)
        settings_layout.setContentsMargins(5, 5, 5, 5)

        self.lbl_appearance = QLabel("Aparência:")
        
        self.appearance_combo = QComboBox()
        self.appearance_combo.addItems(["Modo Circular", "Modo Foco"])
        
        self.loop_cb = QCheckBox("Reiniciar auto")
        self.sound_cb = QCheckBox("Alerta sonoro")
        
        settings_layout.addWidget(self.lbl_appearance)
        settings_layout.addWidget(self.appearance_combo)
        settings_layout.addWidget(self.loop_cb)
        settings_layout.addWidget(self.sound_cb)

        # --- Display ---
        self.timer_display = TimerDisplayWidget()
        
        # --- Inputs ---
        input_layout = QHBoxLayout()
        self.min_input = QSpinBox()
        self.min_input.setRange(0, 999)
        self.min_input.setSuffix("m")
        
        self.sec_input = QSpinBox()
        self.sec_input.setRange(0, 59)
        self.sec_input.setSuffix("s")
        
        input_layout.addWidget(self.min_input)
        input_layout.addWidget(self.sec_input)

        # --- Buttons ---
        self.btn_start = QPushButton("INICIAR")
        self.btn_start.setFixedHeight(35)
        self.btn_start.clicked.connect(self.toggle_start)
        
        self.btn_stop = QPushButton("PARAR")
        self.btn_stop.setFlat(True)
        self.btn_stop.setFixedHeight(30)
        self.btn_stop.clicked.connect(self.stop)

        # Build
        self.main_layout.addLayout(header_layout)
        self.main_layout.addWidget(self.settings_panel)
        self.main_layout.addWidget(self.timer_display)
        self.main_layout.addLayout(input_layout)
        self.main_layout.addWidget(self.btn_start)
        self.main_layout.addWidget(self.btn_stop)
        self.main_layout.addStretch()

        self.setWidget(self.container)

        self.update_theme_styles()
        gui_hooks.theme_did_change.append(self.update_theme_styles)
        
        # 1. Carrega as configurações PRIMEIRO
        self._load_config()

        # 2. Só DEPOIS conecta os sinais de salvar
        # Isso evita que o timer salve valores padrão enquanto está carregando
        self.appearance_combo.currentIndexChanged.connect(self.change_appearance)
        self.loop_cb.stateChanged.connect(self._save_config)
        self.sound_cb.stateChanged.connect(self._save_config)
        self.min_input.valueChanged.connect(self._save_config)
        self.sec_input.valueChanged.connect(self._save_config)
        self.visibilityChanged.connect(self._save_config)

    def _get_config_name(self):
        # Garante o nome correto do pacote (pasta)
        return __name__.split('.')[0]

    def _load_config(self):
        # Bloqueia sinais para evitar loops de salvamento durante o load
        self.blockSignals(True)
        
        config = mw.addonManager.getConfig(self._get_config_name())
        # Se não houver config (config.json faltando), usa defaults mas não quebra
        if not config:
            config = {}

        self.appearance_combo.setCurrentIndex(config.get('appearance', 0))
        self.loop_cb.setChecked(config.get('loop', False))
        self.sound_cb.setChecked(config.get('sound', False))
        self.min_input.setValue(config.get('minutes', 25))
        self.sec_input.setValue(config.get('seconds', 0))
        
        # Atualiza visual
        self.timer_display.set_minimal_mode(self.appearance_combo.currentIndex() == 1)
        
        self.blockSignals(False)

    def _save_config(self):
        if not self.isVisible():
            # Pequena proteção: se estiver oculto mas for chamado, 
            # garantimos que 'dock_visible' seja False, a menos que seja fechamento do Anki
            pass

        config = {
            'appearance': self.appearance_combo.currentIndex(),
            'loop': self.loop_cb.isChecked(),
            'sound': self.sound_cb.isChecked(),
            'minutes': self.min_input.value(),
            'seconds': self.sec_input.value(),
            'dock_visible': self.isVisible()
        }
        mw.addonManager.writeConfig(self._get_config_name(), config)

    def update_theme_styles(self):
        is_night = mw.pm.night_mode()
        
        bg_panel = "#2c2c2c" if is_night else "#f0f0f0"
        text_color = "#ffffff" if is_night else "#000000"
        btn_bg = "#3a3a3a" if is_night else "#e0e0e0"
        btn_hover = "#555555" if is_night else "#cccccc"
        
        settings_color = "rgba(255, 255, 255, 0.4)" if is_night else "rgba(0, 0, 0, 0.4)"
        settings_hover = "rgba(255, 255, 255, 1.0)" if is_night else "rgba(0, 0, 0, 1.0)"

        self.settings_btn.setStyleSheet(f"""
            QPushButton {{ 
                color: {settings_color}; 
                border: none; 
                font-size: 14px; 
                padding: 0px;
            }}
            QPushButton:hover {{ 
                color: {settings_hover};
            }}
        """)

        self.settings_panel.setStyleSheet(f"""
            QFrame {{ 
                background-color: {bg_panel}; 
                border-radius: 6px; 
            }}
            QLabel, QCheckBox {{ color: {text_color}; }}
        """)

        self.btn_start.setStyleSheet(f"""
            QPushButton {{ 
                background-color: {btn_bg}; 
                color: {text_color}; 
                border: 1px solid #888; 
                font-weight: bold; 
                border-radius: 4px;
            }}
            QPushButton:hover {{ background-color: {btn_hover}; }}
        """)

        self.btn_stop.setStyleSheet(f"color: {text_color}; opacity: 0.7;")
        self.timer_display.update()

    def toggle_settings(self):
        self.settings_panel.setVisible(not self.settings_panel.isVisible())

    def change_appearance(self, index):
        self.timer_display.set_minimal_mode(index == 1)
        self._save_config()

    def toggle_start(self):
        if self.state == RUNNING:
            self.state = PAUSED
            self.btn_start.setText("RETOMAR")
        else:
            if self.state == STOPPED:
                self.total_seconds = (self.min_input.value() * 60) + self.sec_input.value()
                if self.total_seconds == 0: return
                self.elapsed_seconds = 0.0
                self.timer_display.update_time(0.0, self.total_seconds)
            
            self.state = RUNNING
            self.last_tick = time.time()
            self.timer.start(200)
            self.btn_start.setText("PAUSAR")

    def stop(self):
        self.state = STOPPED
        self.timer.stop()
        self.elapsed_seconds = 0.0
        self.btn_start.setText("INICIAR")
        self.timer_display.update_time(0, 0)

    def _tick(self):
        if self.state != RUNNING: return
        now = time.time()
        delta = now - self.last_tick
        self.elapsed_seconds += delta
        self.last_tick = now
        remaining = max(self.total_seconds - self.elapsed_seconds, 0)
        
        if self.total_seconds > 0:
            progress = min(self.elapsed_seconds / self.total_seconds, 1.0)
        else:
            progress = 0

        self.timer_display.update_time(progress, remaining)
        
        if remaining <= 0:
            if self.sound_cb.isChecked():
                QApplication.beep()

            if self.loop_cb.isChecked():
                self.elapsed_seconds = 0.0
                self.last_tick = time.time() 
            else:
                self.stop()