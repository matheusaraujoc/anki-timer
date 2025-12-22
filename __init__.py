from aqt import mw
from aqt.qt import QAction, Qt
from .timer_dialog import StudyTimerDock

# Mantém a referência para evitar garbage collection
_dock = None

def toggle_timer():
    global _dock
    
    # Cria o dock apenas se ele ainda não existir
    if _dock is None:
        _dock = StudyTimerDock(mw)
        # Adiciona à área direita do Anki (RightDockWidgetArea)
        mw.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, _dock)
    
    # Alterna visibilidade
    if _dock.isVisible():
        _dock.hide()
    else:
        _dock.show()

# Criação da ação no menu Ferramentas
action = QAction("TTimer de Estudo", mw)
action.triggered.connect(toggle_timer)
mw.form.menuTools.addAction(action)