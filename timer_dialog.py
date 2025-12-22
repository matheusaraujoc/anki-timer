import time
import math
from aqt import mw, gui_hooks
from aqt.qt import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QSpinBox, QLabel, QTimer, QPainter, QColor, 
    QRectF, Qt, QPen, QDockWidget, QCheckBox, QComboBox, 
    QFrame, QApplication, QFont, QPointF, QLinearGradient, QRect
)
from .state import STOPPED, RUNNING, PAUSED

# Constantes para os modos de visualização
MODE_CIRCULAR = 0
MODE_FOCUS = 1
MODE_FLIP = 2

# Configurações da Animação
ANIMATION_DURATION = 800  # Aumentado para 800ms (mais suave)
FRAME_RATE = 16           # ~60 FPS

class TimerDisplayWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.progress = 0.0
        self.remaining_seconds = 0
        self.display_mode = MODE_CIRCULAR
        self.setMinimumHeight(180)

        # Variáveis de Animação
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self._anim_tick)
        self.anim_progress = 1.0 
        self.anim_start_time = 0.0 # Para calcular delta time
        
        self.prev_mins = "00"
        self.prev_secs = "00"
        self.curr_mins = "00"
        self.curr_secs = "00"

    def set_display_mode(self, mode_index):
        self.display_mode = mode_index
        self.update()

    def update_time(self, progress, remaining_seconds):
        # Guarda o tempo antigo
        old_m, old_s = self._get_time_strings_from_seconds(math.ceil(self.remaining_seconds))
        
        self.progress = progress
        self.remaining_seconds = math.ceil(remaining_seconds)
        
        # Pega o novo tempo
        new_m, new_s = self._get_time_strings_from_seconds(self.remaining_seconds)
        
        # Se mudou e estamos no modo Flip, inicia animação
        if self.display_mode == MODE_FLIP and (new_s != old_s or new_m != old_m):
            self.prev_mins = old_m
            self.prev_secs = old_s
            self.curr_mins = new_m
            self.curr_secs = new_s
            
            # Reinicia animação baseada no tempo atual
            self.anim_start_time = time.time()
            self.anim_progress = 0.0
            
            if not self.anim_timer.isActive():
                self.anim_timer.start(FRAME_RATE)
        else:
            # Se não houver mudança de dígito, atualiza direto
            # (A menos que esteja animando, aí não tocamos no prev/curr)
            if self.anim_progress >= 1.0:
                self.curr_mins = new_m
                self.curr_secs = new_s
                self.prev_mins = new_m
                self.prev_secs = new_s
            self.update()

    def _anim_tick(self):
        # Calcula o progresso baseado no tempo real (Delta Time)
        # Isso evita que a animação "pule" ou fique rápida se o PC travar
        now = time.time()
        elapsed_ms = (now - self.anim_start_time) * 1000
        
        self.anim_progress = elapsed_ms / ANIMATION_DURATION
        
        if self.anim_progress >= 1.0:
            self.anim_progress = 1.0
            self.anim_timer.stop()
            # Finaliza o estado
            self.prev_mins = self.curr_mins
            self.prev_secs = self.curr_secs
        
        self.update()

    def _get_time_strings_from_seconds(self, seconds):
        mins, secs = divmod(int(seconds), 60)
        return f"{mins:02d}", f"{secs:02d}"

    def _get_time_strings(self):
        return self._get_time_strings_from_seconds(self.remaining_seconds)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        if self.display_mode == MODE_FLIP:
            self._draw_flip_style(painter)
            return

        # --- MODOS PADRÃO ---
        is_night = mw.pm.night_mode()
        primary_color = QColor(255, 255, 255) if is_night else QColor(0, 0, 0)
        track_color = QColor(80, 80, 80) if is_night else QColor(230, 230, 230)
        
        center = self.rect().center()
        
        # No modo normal, usamos sempre o current
        current_m, current_s = self._get_time_strings()
        text_full = f"{current_m}:{current_s}"

        if self.display_mode == MODE_CIRCULAR:
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
        font.setPointSize(60 if self.display_mode == MODE_FOCUS else 28)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, text_full)

    def _ease_in_out(self, t):
        """Função de suavização (Easing) para movimento mais natural."""
        # Sigmoid simples ou curva quadrática
        if t < 0.5:
            return 2 * t * t
        return -1 + (4 - 2 * t) * t

    def _draw_flip_style(self, painter):
        rect = self.rect()
        center_x = rect.center().x()
        center_y = rect.center().y()
        
        card_width = min(self.width() * 0.42, 140)
        card_height = min(self.height() * 0.75, 180)
        gap = 12
        radius = 12
        
        font = painter.font()
        font.setFamily("Arial") 
        font.setWeight(QFont.Weight.Bold)
        font.setPixelSize(int(card_height * 0.55)) 
        painter.setFont(font)

        rect_min = QRectF(center_x - card_width - gap, center_y - card_height/2, card_width, card_height)
        rect_sec = QRectF(center_x + gap, center_y - card_height/2, card_width, card_height)

        # Aplica Easing ao progresso linear
        visual_progress = self._ease_in_out(self.anim_progress)

        # Minutos
        if self.prev_mins != self.curr_mins and self.anim_progress < 1.0:
            self._draw_animated_card(painter, rect_min, self.prev_mins, self.curr_mins, visual_progress, radius)
        else:
            self._draw_static_card(painter, rect_min, self.curr_mins, radius)

        # Segundos
        if self.prev_secs != self.curr_secs and self.anim_progress < 1.0:
            self._draw_animated_card(painter, rect_sec, self.prev_secs, self.curr_secs, visual_progress, radius)
        else:
            self._draw_static_card(painter, rect_sec, self.curr_secs, radius)

    def _draw_static_card(self, painter, r, text, radius):
        self._draw_card_half(painter, r, text, radius, is_top=True)
        self._draw_card_half(painter, r, text, radius, is_top=False)
        self._draw_split_line(painter, r)

    def _draw_animated_card(self, painter, r, old_text, new_text, progress, radius):
        # Fundo Estático: Topo do Novo (oculto) e Base do Velho
        self._draw_card_half(painter, r, new_text, radius, is_top=True)
        self._draw_card_half(painter, r, old_text, radius, is_top=False)

        center_y = r.center().y()
        
        if progress < 0.5:
            # FASE 1: Velho descendo
            # Mapeia 0.0-0.5 para 1.0-0.0
            scale = 1.0 - (progress * 2)
            
            painter.save()
            painter.translate(r.center().x(), center_y)
            painter.scale(1.0, scale)
            painter.translate(-r.center().x(), -center_y)
            
            self._draw_card_half(painter, r, old_text, radius, is_top=True)
            self._draw_shadow(painter, r, alpha=int(progress * 220), is_top=True)
            painter.restore()
            
        else:
            # FASE 2: Novo subindo
            # Mapeia 0.5-1.0 para 0.0-1.0
            scale = (progress - 0.5) * 2
            
            painter.save()
            painter.translate(r.center().x(), center_y)
            painter.scale(1.0, scale)
            painter.translate(-r.center().x(), -center_y)
            
            self._draw_card_half(painter, r, new_text, radius, is_top=False)
            self._draw_shadow(painter, r, alpha=int((1.0 - progress) * 220), is_top=False)
            painter.restore()

        self._draw_split_line(painter, r)

    def _draw_card_half(self, painter, r, text, radius, is_top):
        painter.save()
        center_y = r.center().y()
        
        if is_top:
            clip_rect = QRectF(r.left(), r.top(), r.width(), r.height() / 2)
        else:
            clip_rect = QRectF(r.left(), center_y, r.width(), r.height() / 2)
            
        painter.setClipRect(clip_rect)

        gradient = QLinearGradient(r.topLeft(), r.bottomLeft())
        gradient.setColorAt(0.0, QColor(50, 50, 50))
        gradient.setColorAt(0.48, QColor(30, 30, 30))
        gradient.setColorAt(0.52, QColor(25, 25, 25))
        gradient.setColorAt(1.0, QColor(45, 45, 45))

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(gradient)
        painter.drawRoundedRect(r, radius, radius)

        painter.setPen(QColor(245, 245, 245))
        painter.drawText(r, Qt.AlignmentFlag.AlignCenter, text)
        painter.restore()

    def _draw_shadow(self, painter, r, alpha, is_top):
        if alpha <= 0: return
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(0, 0, 0, min(alpha, 180)))
        
        center_y = r.center().y()
        if is_top:
            rect = QRectF(r.left(), r.top(), r.width(), r.height() / 2)
        else:
            rect = QRectF(r.left(), center_y, r.width(), r.height() / 2)
        painter.drawRoundedRect(rect, 0, 0)

    def _draw_split_line(self, painter, r):
        center_y = r.center().y()
        
        # Linha central
        painter.setPen(QPen(QColor(10, 10, 10), 3))
        p1 = QPointF(r.left(), center_y)
        p2 = QPointF(r.right(), center_y)
        painter.drawLine(p1, p2)

        # Dobradiças
        hinge_w, hinge_h = 6, 10
        hinge_color = QColor(20, 20, 20)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(hinge_color)
        
        h_left = QRectF(r.left() - 2, center_y - hinge_h/2, hinge_w, hinge_h)
        h_right = QRectF(r.right() - hinge_w + 2, center_y - hinge_h/2, hinge_w, hinge_h)
        
        painter.drawRoundedRect(h_left, 2, 2)
        painter.drawRoundedRect(h_right, 2, 2)

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
        self.appearance_combo.addItems(["Modo Circular", "Modo Foco", "Modo Flip"])
        
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
        
        self._load_config()

        self.appearance_combo.currentIndexChanged.connect(self.change_appearance)
        self.loop_cb.stateChanged.connect(self._save_config)
        self.sound_cb.stateChanged.connect(self._save_config)
        self.min_input.valueChanged.connect(self._save_config)
        self.sec_input.valueChanged.connect(self._save_config)
        self.visibilityChanged.connect(self._save_config)

    def _get_config_name(self):
        return __name__.split('.')[0]

    def _load_config(self):
        self.blockSignals(True)
        
        config = mw.addonManager.getConfig(self._get_config_name())
        if not config:
            config = {}

        self.appearance_combo.setCurrentIndex(config.get('appearance', 0))
        self.loop_cb.setChecked(config.get('loop', False))
        self.sound_cb.setChecked(config.get('sound', False))
        self.min_input.setValue(config.get('minutes', 25))
        self.sec_input.setValue(config.get('seconds', 0))
        
        self.timer_display.set_display_mode(self.appearance_combo.currentIndex())
        
        self.blockSignals(False)

    def _save_config(self):
        if not self.isVisible():
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
        self.timer_display.set_display_mode(index)
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