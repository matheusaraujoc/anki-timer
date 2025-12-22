import time
import math
from aqt import mw, gui_hooks
from aqt.qt import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QSpinBox, QLabel, QTimer, QPainter, QColor, 
    QRectF, Qt, QPen, QDockWidget, QCheckBox, QComboBox, 
    QFrame, QApplication, QFont, QPointF, QLinearGradient, QRect,
    QColorDialog
)
from .state import STOPPED, RUNNING, PAUSED

# Constantes para os Modos de Visualização
MODE_CIRCULAR = 0
MODE_FOCUS = 1
MODE_FLIP = 2
MODE_LINEAR = 3 

# Constantes para os Modos de Operação
OP_MODE_TIMER = 0      
OP_MODE_STOPWATCH = 1  

# Configurações da Animação
ANIMATION_DURATION = 800
FRAME_RATE = 16 

class TimerDisplayWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.progress = 0.0
        self.display_seconds = 0
        self.display_mode = MODE_CIRCULAR
        self.setMinimumHeight(180)
        
        self.custom_text_color = None
        self.custom_ring_color = None

        # Dados de Ciclos
        self.show_cycles = False
        self.current_cycle = 1
        self.total_cycles = 0 

        # Variáveis de Animação
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self._anim_tick)
        self.anim_progress = 1.0 
        self.anim_start_time = 0.0
        
        # Estados anteriores para animação (Strings)
        self.prev_h = "00"
        self.prev_m = "00"
        self.prev_s = "00"
        
        self.curr_h = "00"
        self.curr_m = "00"
        self.curr_s = "00"

    def set_display_mode(self, mode_index):
        self.display_mode = mode_index
        self.update()
        
    def set_custom_colors(self, text_col, ring_col):
        self.custom_text_color = text_col
        self.custom_ring_color = ring_col
        self.update()

    def set_cycle_info(self, active, current, total):
        self.show_cycles = active
        self.current_cycle = current
        self.total_cycles = total
        self.update()

    def update_time(self, progress, seconds_to_show):
        old_h, old_m, old_s = self._get_time_parts(math.floor(self.display_seconds))
        
        self.progress = progress
        self.display_seconds = seconds_to_show
        
        new_h, new_m, new_s = self._get_time_parts(self.display_seconds)
        
        needs_anim = False
        if self.display_mode == MODE_FLIP:
            if new_s != old_s or new_m != old_m or new_h != old_h:
                needs_anim = True

        if needs_anim:
            self.prev_h, self.prev_m, self.prev_s = old_h, old_m, old_s
            self.curr_h, self.curr_m, self.curr_s = new_h, new_m, new_s
            
            self.anim_start_time = time.time()
            self.anim_progress = 0.0
            
            if not self.anim_timer.isActive():
                self.anim_timer.start(FRAME_RATE)
        else:
            if self.anim_progress >= 1.0:
                self.curr_h, self.curr_m, self.curr_s = new_h, new_m, new_s
                self.prev_h, self.prev_m, self.prev_s = new_h, new_m, new_s
            self.update()

    def _anim_tick(self):
        now = time.time()
        elapsed_ms = (now - self.anim_start_time) * 1000
        self.anim_progress = elapsed_ms / ANIMATION_DURATION
        
        if self.anim_progress >= 1.0:
            self.anim_progress = 1.0
            self.anim_timer.stop()
            self.prev_h, self.prev_m, self.prev_s = self.curr_h, self.curr_m, self.curr_s
        
        self.update()

    def _get_time_parts(self, total_seconds):
        val = int(total_seconds)
        hours, remainder = divmod(val, 3600)
        mins, secs = divmod(remainder, 60)
        return f"{hours:02d}", f"{mins:02d}", f"{secs:02d}"

    def _get_formatted_text(self):
        h_str, m_str, s_str = self._get_time_parts(self.display_seconds)
        if int(h_str) > 0:
            return f"{h_str}:{m_str}:{s_str}"
        return f"{m_str}:{s_str}"

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        if self.display_mode == MODE_FLIP:
            self._draw_flip_style(painter)
        elif self.display_mode == MODE_LINEAR:
            self._draw_linear_style(painter)
        else:
            self._draw_standard_modes(painter)

        if self.show_cycles:
            self._draw_cycle_counter(painter)

    def _draw_standard_modes(self, painter):
        is_night = mw.pm.night_mode()
        
        if self.custom_text_color:
            primary_color = self.custom_text_color
        else:
            primary_color = QColor(255, 255, 255) if is_night else QColor(0, 0, 0)
            
        track_color = QColor(80, 80, 80) if is_night else QColor(230, 230, 230)
        
        rect = self.rect()
        center_x = rect.center().x()
        center_y = rect.center().y()
        if self.show_cycles:
            center_y -= 15

        text_full = self._get_formatted_text()

        if self.display_mode == MODE_CIRCULAR:
            avail_height = rect.height() - (30 if self.show_cycles else 0)
            size = min(rect.width(), avail_height) - 40
            
            circ_rect = QRectF(center_x - size/2, center_y - size/2, size, size)

            painter.setPen(QPen(track_color, 2))
            painter.drawEllipse(circ_rect)

            if self.progress > 0:
                if self.custom_ring_color:
                    prog_color = self.custom_ring_color
                else:
                    prog_color = QColor(10, 132, 255)

                pen = QPen(prog_color, 8)
                pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                painter.setPen(pen)
                span_angle = int(-360 * self.progress * 16)
                painter.drawArc(circ_rect, 90 * 16, span_angle)

        painter.setPen(primary_color) 
        font = painter.font()
        font.setBold(True)
        
        base_size = 60 if self.display_mode == MODE_FOCUS else 28
        if len(text_full) > 5: 
            base_size = int(base_size * 0.75)
            
        font.setPointSize(base_size)
        painter.setFont(font)
        
        text_rect = QRectF(0, center_y - 50, rect.width(), 100)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, text_full)

    def _draw_linear_style(self, painter):
        is_night = mw.pm.night_mode()
        
        if self.custom_text_color:
            text_color = self.custom_text_color
        else:
            text_color = QColor(255, 255, 255) if is_night else QColor(0, 0, 0)
            
        track_bg = QColor(60, 60, 60) if is_night else QColor(220, 220, 220)
        
        if self.custom_ring_color:
            bar_color = self.custom_ring_color
        else:
            bar_color = QColor(10, 132, 255) 

        rect = self.rect()
        
        bar_height = 12
        bar_margin = 20
        bar_y = 15 
        
        track_rect = QRectF(bar_margin, bar_y, rect.width() - (bar_margin*2), bar_height)
        
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(track_bg)
        painter.drawRoundedRect(track_rect, bar_height/2, bar_height/2)
        
        if self.progress > 0:
            fill_width = track_rect.width() * self.progress
            fill_width = max(fill_width, bar_height) 
            
            fill_rect = QRectF(track_rect.x(), track_rect.y(), fill_width, track_rect.height())
            painter.setBrush(bar_color)
            painter.drawRoundedRect(fill_rect, bar_height/2, bar_height/2)

        text_full = self._get_formatted_text()
        
        painter.setPen(text_color)
        font = painter.font()
        font.setBold(True)
        font.setPointSize(48 if len(text_full) <= 5 else 36) 
        painter.setFont(font)
        
        text_y_pos = bar_y + bar_height + 20
        text_rect = QRectF(0, text_y_pos, rect.width(), rect.height() - text_y_pos)
        
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, text_full)

    def _draw_cycle_counter(self, painter):
        is_night = mw.pm.night_mode()
        text_color = QColor(150, 150, 150) if is_night else QColor(100, 100, 100)
        
        rect = self.rect()
        font = painter.font()
        font.setBold(False)
        font.setPointSize(10)
        painter.setFont(font)
        painter.setPen(text_color)
        
        if self.total_cycles > 0:
            text = f"Ciclo: {self.current_cycle:02d} / {self.total_cycles:02d}"
        else:
            text = f"Ciclo: {self.current_cycle:02d}"
            
        bottom_rect = QRectF(0, rect.height() - 25, rect.width(), 25)
        painter.drawText(bottom_rect, Qt.AlignmentFlag.AlignCenter, text)

    def _ease_in_out(self, t):
        if t < 0.5: return 2 * t * t
        return -1 + (4 - 2 * t) * t

    def _draw_flip_style(self, painter):
        rect = self.rect()
        center_x = rect.center().x()
        center_y = rect.center().y()
        if self.show_cycles:
            center_y -= 15

        has_hours = int(self.curr_h) > 0 or int(self.prev_h) > 0
        
        avail_height = rect.height() - (30 if self.show_cycles else 0)
        
        if has_hours:
            card_width = min(self.width() * 0.28, 90)
            gap = 8
        else:
            card_width = min(self.width() * 0.42, 140)
            gap = 12
            
        card_height = min(avail_height * 0.75, 180)
        radius = 10
        
        font = painter.font()
        font.setFamily("Arial") 
        font.setWeight(QFont.Weight.Bold)
        
        # --- CORREÇÃO DA FONTE PARA FLIP ---
        # Calcula tamanho base pela altura
        pixel_size = int(card_height * 0.55)
        # Se tiver horas, limita o tamanho da fonte pela LARGURA da placa
        # para evitar que números como '0' ou '8' fiquem espremidos.
        if has_hours:
            pixel_size = min(pixel_size, int(card_width * 0.75))
            
        font.setPixelSize(pixel_size) 
        painter.setFont(font)

        if has_hours:
            total_w = (3 * card_width) + (2 * gap)
            start_x = center_x - (total_w / 2)
            
            rect_hour = QRectF(start_x, center_y - card_height/2, card_width, card_height)
            rect_min = QRectF(start_x + card_width + gap, center_y - card_height/2, card_width, card_height)
            rect_sec = QRectF(start_x + (card_width + gap)*2, center_y - card_height/2, card_width, card_height)
        else:
            rect_min = QRectF(center_x - card_width - gap/2, center_y - card_height/2, card_width, card_height)
            rect_sec = QRectF(center_x + gap/2, center_y - card_height/2, card_width, card_height)

        visual_progress = self._ease_in_out(self.anim_progress)

        if has_hours:
            if self.prev_h != self.curr_h and self.anim_progress < 1.0:
                self._draw_animated_card(painter, rect_hour, self.prev_h, self.curr_h, visual_progress, radius)
            else:
                self._draw_static_card(painter, rect_hour, self.curr_h, radius)

        if self.prev_m != self.curr_m and self.anim_progress < 1.0:
            self._draw_animated_card(painter, rect_min, self.prev_m, self.curr_m, visual_progress, radius)
        else:
            self._draw_static_card(painter, rect_min, self.curr_m, radius)

        if self.prev_s != self.curr_s and self.anim_progress < 1.0:
            self._draw_animated_card(painter, rect_sec, self.prev_s, self.curr_s, visual_progress, radius)
        else:
            self._draw_static_card(painter, rect_sec, self.curr_s, radius)

    def _draw_static_card(self, painter, r, text, radius):
        self._draw_card_half(painter, r, text, radius, is_top=True)
        self._draw_card_half(painter, r, text, radius, is_top=False)
        self._draw_split_line(painter, r)

    def _draw_animated_card(self, painter, r, old_text, new_text, progress, radius):
        self._draw_card_half(painter, r, new_text, radius, is_top=True)
        self._draw_card_half(painter, r, old_text, radius, is_top=False)

        center_y = r.center().y()
        
        if progress < 0.5:
            scale = 1.0 - (progress * 2)
            painter.save()
            painter.translate(r.center().x(), center_y)
            painter.scale(1.0, scale)
            painter.translate(-r.center().x(), -center_y)
            self._draw_card_half(painter, r, old_text, radius, is_top=True)
            self._draw_shadow(painter, r, alpha=int(progress * 220), is_top=True)
            painter.restore()
        else:
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
        
        margin = 2.0 
        if is_top:
            clip_rect = QRectF(r.left()-margin, r.top()-margin, r.width()+margin*2, (center_y - r.top()) + margin)
        else:
            clip_rect = QRectF(r.left()-margin, center_y, r.width()+margin*2, (r.bottom() - center_y) + margin)
            
        painter.setClipRect(clip_rect)

        gradient = QLinearGradient(r.topLeft(), r.bottomLeft())
        gradient.setColorAt(0.0, QColor(50, 50, 50))
        gradient.setColorAt(0.48, QColor(30, 30, 30))
        gradient.setColorAt(0.52, QColor(25, 25, 25))
        gradient.setColorAt(1.0, QColor(45, 45, 45))

        painter.setPen(QPen(QColor(10, 10, 10), 1.5))
        painter.setBrush(gradient)
        painter.drawRoundedRect(r, radius, radius)

        if self.custom_text_color:
            painter.setPen(self.custom_text_color)
        else:
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
        painter.setPen(QPen(QColor(5, 5, 5), 3))
        p1 = QPointF(r.left()+1, center_y)
        p2 = QPointF(r.right()-1, center_y)
        painter.drawLine(p1, p2)
        
        hinge_w, hinge_h = 6, 10
        hinge_color = QColor(20, 20, 20)
        painter.setPen(QPen(QColor(5, 5, 5), 1))
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
        self.current_cycle = 1

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

        mode_layout = QHBoxLayout()
        self.lbl_op_mode = QLabel("Modo:")
        self.op_mode_combo = QComboBox()
        self.op_mode_combo.addItems(["Temporizador", "Cronômetro"])
        self.op_mode_combo.currentIndexChanged.connect(self.change_op_mode)
        mode_layout.addWidget(self.lbl_op_mode)
        mode_layout.addWidget(self.op_mode_combo)
        
        self.lbl_appearance = QLabel("Aparência:")
        self.appearance_combo = QComboBox()
        self.appearance_combo.addItems(["Modo Circular", "Modo Foco", "Modo Flip", "Modo Linear"])
        
        loop_layout = QHBoxLayout()
        self.loop_cb = QCheckBox("Reiniciar auto")
        self.loop_cb.stateChanged.connect(self.toggle_loop_options)
        
        self.cycles_spin = QSpinBox()
        self.cycles_spin.setRange(0, 999)
        self.cycles_spin.setToolTip("0 = Infinito")
        self.cycles_spin.setSuffix(" ciclos")
        self.cycles_spin.setEnabled(False)
        self.cycles_spin.valueChanged.connect(self._save_config)
        
        loop_layout.addWidget(self.loop_cb)
        loop_layout.addWidget(self.cycles_spin)

        self.sound_cb = QCheckBox("Alerta sonoro")
        self.sound_cb.stateChanged.connect(self._save_config)
        
        colors_layout = QHBoxLayout()
        self.btn_text_color = QPushButton("Cor Texto")
        self.btn_text_color.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_text_color.clicked.connect(self.pick_text_color)
        
        self.btn_ring_color = QPushButton("Cor Barra")
        self.btn_ring_color.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_ring_color.clicked.connect(self.pick_ring_color)
        
        colors_layout.addWidget(self.btn_text_color)
        colors_layout.addWidget(self.btn_ring_color)

        self.btn_reset_colors = QPushButton("↺ Resetar Cores")
        self.btn_reset_colors.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_reset_colors.clicked.connect(self.reset_colors)

        settings_layout.addLayout(mode_layout)
        settings_layout.addWidget(self.lbl_appearance)
        settings_layout.addWidget(self.appearance_combo)
        settings_layout.addLayout(colors_layout)
        settings_layout.addWidget(self.btn_reset_colors)
        settings_layout.addLayout(loop_layout)
        settings_layout.addWidget(self.sound_cb)

        # --- Display ---
        self.timer_display = TimerDisplayWidget()
        
        # --- Inputs ---
        input_layout = QHBoxLayout()
        self.hour_input = QSpinBox()
        self.hour_input.setRange(0, 99)
        self.hour_input.setSuffix("h")
        self.hour_input.setToolTip("Horas")
        
        self.min_input = QSpinBox()
        self.min_input.setRange(0, 999)
        self.min_input.setSuffix("m")
        self.min_input.setToolTip("Minutos")
        
        self.sec_input = QSpinBox()
        self.sec_input.setRange(0, 59)
        self.sec_input.setSuffix("s")
        self.sec_input.setToolTip("Segundos")
        
        input_layout.addWidget(self.hour_input)
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
        self.hour_input.valueChanged.connect(self._save_config)
        self.min_input.valueChanged.connect(self._save_config)
        self.sec_input.valueChanged.connect(self._save_config)
        self.visibilityChanged.connect(self._save_config)

    def _get_config_name(self):
        return __name__.split('.')[0]

    def _load_config(self):
        self.blockSignals(True)
        
        config = mw.addonManager.getConfig(self._get_config_name())
        if not config: config = {}

        self.op_mode_combo.setCurrentIndex(config.get('op_mode', OP_MODE_TIMER))
        self.appearance_combo.setCurrentIndex(config.get('appearance', 0))
        self.loop_cb.setChecked(config.get('loop', False))
        self.cycles_spin.setValue(config.get('cycles', 0))
        self.sound_cb.setChecked(config.get('sound', False))
        
        self.hour_input.setValue(config.get('hours', 0))
        self.min_input.setValue(config.get('minutes', 25))
        self.sec_input.setValue(config.get('seconds', 0))
        
        col_text = config.get('custom_text_color')
        col_ring = config.get('custom_ring_color')
        q_text = QColor(col_text) if col_text else None
        q_ring = QColor(col_ring) if col_ring else None
        
        self.timer_display.set_custom_colors(q_text, q_ring)
        self.timer_display.set_display_mode(self.appearance_combo.currentIndex())
        self.update_inputs_state()
        self.toggle_loop_options(self.loop_cb.isChecked())
        
        self.blockSignals(False)

    def _save_config(self):
        if not self.isVisible(): pass

        text_hex = self.timer_display.custom_text_color.name() if self.timer_display.custom_text_color else None
        ring_hex = self.timer_display.custom_ring_color.name() if self.timer_display.custom_ring_color else None

        config = {
            'op_mode': self.op_mode_combo.currentIndex(),
            'appearance': self.appearance_combo.currentIndex(),
            'loop': self.loop_cb.isChecked(),
            'cycles': self.cycles_spin.value(),
            'sound': self.sound_cb.isChecked(),
            'hours': self.hour_input.value(),
            'minutes': self.min_input.value(),
            'seconds': self.sec_input.value(),
            'dock_visible': self.isVisible(),
            'custom_text_color': text_hex,
            'custom_ring_color': ring_hex
        }
        mw.addonManager.writeConfig(self._get_config_name(), config)

    def toggle_loop_options(self, checked):
        self.cycles_spin.setEnabled(checked)
        self.update_display_cycle_info()
        self._save_config()

    def update_display_cycle_info(self):
        show = self.loop_cb.isChecked() and self.op_mode_combo.currentIndex() == OP_MODE_TIMER
        total = self.cycles_spin.value()
        self.timer_display.set_cycle_info(show, self.current_cycle, total)

    def change_op_mode(self, index):
        self.stop()
        self.update_inputs_state()
        self._save_config()

    def update_inputs_state(self):
        is_timer = (self.op_mode_combo.currentIndex() == OP_MODE_TIMER)
        self.hour_input.setEnabled(is_timer)
        self.min_input.setEnabled(is_timer)
        self.sec_input.setEnabled(is_timer)
        self.loop_cb.setEnabled(is_timer)
        self.cycles_spin.setEnabled(is_timer and self.loop_cb.isChecked())
        
        if not is_timer:
            self.timer_display.update_time(0.0, 0.0)
        else:
            total = (self.hour_input.value() * 3600) + (self.min_input.value() * 60) + self.sec_input.value()
            self.timer_display.update_time(0.0, total)
        
        self.update_display_cycle_info()

    def pick_text_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.timer_display.custom_text_color = color
            self.timer_display.update()
            self._save_config()

    def pick_ring_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.timer_display.custom_ring_color = color
            self.timer_display.update()
            self._save_config()

    def reset_colors(self):
        self.timer_display.custom_text_color = None
        self.timer_display.custom_ring_color = None
        self.timer_display.update()
        self._save_config()

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
        
        btn_style = f"""
            QPushButton {{ 
                background-color: {btn_bg}; 
                color: {text_color}; 
                border: 1px solid #888; 
                border-radius: 3px;
                padding: 4px;
            }}
            QPushButton:hover {{ background-color: {btn_hover}; }}
        """
        self.btn_text_color.setStyleSheet(btn_style)
        self.btn_ring_color.setStyleSheet(btn_style)
        self.btn_reset_colors.setStyleSheet(btn_style)

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
                if self.current_cycle > self.cycles_spin.value() and self.cycles_spin.value() > 0:
                    self.current_cycle = 1
                
                self.update_display_cycle_info()

                if self.op_mode_combo.currentIndex() == OP_MODE_TIMER:
                    h = self.hour_input.value()
                    m = self.min_input.value()
                    s = self.sec_input.value()
                    self.total_seconds = (h * 3600) + (m * 60) + s
                    
                    if self.total_seconds == 0: return
                    self.elapsed_seconds = 0.0
                    self.timer_display.update_time(0.0, self.total_seconds)
                else:
                    self.total_seconds = 0
                    self.elapsed_seconds = 0.0
                    self.timer_display.update_time(0.0, 0.0)
            
            self.state = RUNNING
            self.last_tick = time.time()
            self.timer.start(200)
            self.btn_start.setText("PAUSAR")

    def stop(self):
        self.state = STOPPED
        self.timer.stop()
        self.elapsed_seconds = 0.0
        self.btn_start.setText("INICIAR")
        self.current_cycle = 1
        self.update_display_cycle_info()
        
        if self.op_mode_combo.currentIndex() == OP_MODE_TIMER:
            h = self.hour_input.value()
            m = self.min_input.value()
            s = self.sec_input.value()
            total = (h * 3600) + (m * 60) + s
            self.timer_display.update_time(0.0, total)
        else:
            self.timer_display.update_time(0.0, 0.0)

    def _tick(self):
        if self.state != RUNNING: return
        now = time.time()
        delta = now - self.last_tick
        self.elapsed_seconds += delta
        self.last_tick = now
        
        if self.op_mode_combo.currentIndex() == OP_MODE_TIMER:
            remaining = max(self.total_seconds - self.elapsed_seconds, 0)
            if self.total_seconds > 0:
                progress = min(self.elapsed_seconds / self.total_seconds, 1.0)
            else:
                progress = 0
            self.timer_display.update_time(progress, math.ceil(remaining))
            
            if remaining <= 0:
                if self.sound_cb.isChecked():
                    QApplication.beep()
                
                if self.loop_cb.isChecked():
                    target_cycles = self.cycles_spin.value()
                    if target_cycles == 0 or self.current_cycle < target_cycles:
                        self.elapsed_seconds = 0.0
                        self.last_tick = time.time() 
                        self.current_cycle += 1
                        self.update_display_cycle_info()
                    else:
                        self.stop()
                else:
                    self.stop()
        else:
            current_secs = self.elapsed_seconds
            progress = 1.0 
            self.timer_display.update_time(progress, math.floor(current_secs))