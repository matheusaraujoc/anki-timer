from aqt import mw, gui_hooks
from aqt.qt import QAction, Qt
from .timer_dialog import StudyTimerDock

_dock = None

def toggle_timer():
    global _dock
    
    if _dock is None:
        _dock = StudyTimerDock(mw)
        mw.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, _dock)
    
    if _dock.isVisible():
        _dock.hide()
    else:
        _dock.show()

def startup_check():
    """Verifica se o timer deve ser aberto automaticamente ao iniciar."""
    # Pega o nome da pasta do addon (package name)
    config = mw.addonManager.getConfig(__name__)
    
    # Se a configuração existir e 'dock_visible' for True, abre o timer
    if config and config.get('dock_visible', False):
        toggle_timer()

# Ação no Menu
action = QAction("Timer de Estudo", mw)
action.triggered.connect(toggle_timer)
mw.form.menuTools.addAction(action)

# Gancho de inicialização (Roda quando o perfil é carregado)
gui_hooks.profile_did_open.append(startup_check)