COLORS = {
    "bg": "#08111f",
    "sidebar": "#0b1627",
    "panel": "#101a2b",
    "panel_alt": "#131f33",
    "panel_hover": "#182844",
    "border": "#24344d",
    "text": "#f7f9fd",
    "muted": "#9aa9bf",
    "purple": "#8b5cf6",
    "purple_soft": "#6d4cc7",
    "purple_dark": "#402b73",
    "blue": "#4c8dff",
    "green": "#4fd08b",
    "orange": "#ff9d54",
    "gold": "#f5c451",
    "red": "#ef6577",
    "cyan": "#54c9c2",
}

def stylesheet(scale: float = 1.0):
    c = COLORS
    raw = f"""
    QWidget {{
        background: {c['bg']};
        color: {c['text']};
        font-family: "Segoe UI";
        font-size: 9.8pt;
    }}
    QMainWindow {{
        background: {c['bg']};
    }}
    QFrame#Sidebar {{
        background: {c['sidebar']};
        border-right: 1px solid {c['border']};
    }}
    QFrame#Card {{
        background: {c['panel']};
        border: 1px solid {c['border']};
        border-radius: 13px;
    }}
    QFrame#SoftPanel {{
        background: {c['panel_alt']};
        border: 1px solid {c['border']};
        border-radius: 10px;
    }}
    QFrame#SidebarCard {{
        background: {c['panel']};
        border: 1px solid {c['border']};
        border-radius: 12px;
    }}
    QLabel {{
        background: transparent;
        border: none;
    }}
    QLabel#Hero {{
        font-size: 23pt;
        font-weight: 700;
    }}
    QLabel#SectionTitle {{
        font-size: 14pt;
        font-weight: 700;
    }}
    QLabel#CardTitle {{
        font-size: 11pt;
        font-weight: 700;
    }}
    QLabel#Muted {{
        color: {c['muted']};
    }}
    QLabel#Tiny {{
        color: {c['muted']};
        font-size: 8.5pt;
    }}
    QPushButton {{
        background: {c['panel_alt']};
        border: 1px solid {c['border']};
        border-radius: 9px;
        padding: 9px 12px;
    }}
    QPushButton:hover {{
        background: {c['panel_hover']};
        border: 1px solid {c['purple_soft']};
        color: white;
    }}
    QPushButton:pressed {{
        background: #0d1728;
        border: 1px solid {c['purple']};
        padding-top: 11px;
        padding-bottom: 7px;
    }}
    QPushButton:disabled {{
        background: #0d1625;
        border: 1px solid #1b293d;
        color: #66758c;
    }}
    QPushButton#Primary {{
        background: {c['purple']};
        color: white;
        font-weight: 700;
        border: none;
        padding: 11px 14px;
    }}
    QPushButton#Primary:hover {{
        background: #9d75f7;
        border: 1px solid #c4b0ff;
    }}
    QPushButton#Primary:pressed {{
        background: #7444e8;
        border: 1px solid #d0c0ff;
        padding-top: 13px;
        padding-bottom: 9px;
    }}
    QPushButton#Nav {{
        text-align: left;
        border: none;
        background: transparent;
        color: {c['muted']};
        padding: 9px 14px;
        border-radius: 9px;
    }}
    QPushButton#Nav:hover {{
        background: #1a2d4b;
        color: white;
        border-left: 3px solid {c['purple_soft']};
    }}
    QPushButton#Nav:pressed {{
        background: #101d32;
        color: white;
        border-left: 3px solid {c['purple']};
        padding-top: 11px;
        padding-bottom: 7px;
    }}
    QPushButton#Nav:checked {{
        background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #563c9f, stop:1 #47307f);
        color: white;
        border-left: 3px solid #a98bff;
    }}
    QPushButton#Nav:checked:hover {{
        background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #6549b4, stop:1 #52378f);
        border-left: 3px solid #c4b0ff;
    }}
    QLineEdit, QTextEdit, QComboBox, QListWidget, QTableWidget, QSpinBox {{
        background: {c['panel_alt']};
        border: 1px solid {c['border']};
        border-radius: 8px;
        padding: 7px;
        selection-background-color: #50348d;
    }}
    QListWidget {{
        background: transparent;
        border: none;
        padding: 0;
    }}
    QListWidget::item {{
        background: transparent;
        border: none;
        padding: 6px 2px;
    }}
    QListWidget::item:hover {{
        background: {c['panel_alt']};
        border-radius: 6px;
    }}
    QListWidget#SprintBacklogList::item {{
        padding: 9px 10px;
        margin: 2px 0;
        border: 1px solid transparent;
        border-left: 4px solid transparent;
        border-radius: 7px;
    }}
    QListWidget#SprintBacklogList::item:hover {{
        background: {c['panel_hover']};
        border: 1px solid {c['border']};
        border-left: 4px solid {c['purple_soft']};
    }}
    QListWidget#SprintBacklogList::item:selected,
    QListWidget#SprintBacklogList::item:selected:active,
    QListWidget#SprintBacklogList::item:selected:!active {{
        background: qlineargradient(
            x1:0,y1:0,x2:1,y2:0,
            stop:0 {c['purple_dark']},
            stop:1 #2b2547
        );
        color: white;
        border: 1px solid {c['purple_soft']};
        border-left: 5px solid #b9a4ff;
        border-radius: 7px;
        font-weight: 700;
    }}
    QCheckBox {{
        spacing: 9px;
        padding: 4px 2px;
        background: transparent;
    }}
    QCheckBox::indicator {{
        width: 17px;
        height: 17px;
    }}
    QProgressBar {{
        background: {c['panel_alt']};
        border: none;
        border-radius: 4px;
        min-height: 8px;
        max-height: 8px;
        text-align: center;
        color: transparent;
    }}
    QProgressBar::chunk {{
        background: {c['purple']};
        border-radius: 4px;
    }}
    QScrollArea {{
        border: none;
        background: transparent;
    }}
    QScrollBar:vertical {{
        background: transparent;
        width: 10px;
        margin: 2px;
    }}
    QScrollBar::handle:vertical {{
        background: #31405c;
        min-height: 28px;
        border-radius: 5px;
    }}
    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {{
        height: 0;
    }}

    QPushButton#WorkspaceOpen {{
        background: #172940;
        border: 1px solid {c['border']};
        border-radius: 7px;
        color: {c['blue']};
        font-weight: 700;
        padding: 2px 8px;
        min-height: 26px;
        max-height: 28px;
    }}
    QPushButton#WorkspaceOpen:hover {{
        background: #244164;
        border: 1px solid {c['purple_soft']};
        color: white;
    }}
    QPushButton#WorkspaceOpen:pressed {{
        background: #0d1728;
        border: 1px solid {c['purple']};
        color: white;
        padding-top: 4px;
        padding-bottom: 0px;
    }}

    QPushButton#Secondary {{
        background: {c['panel_alt']};
        border: 1px solid {c['border']};
        color: {c['text']};
        font-weight: 600;
        padding: 9px 12px;
    }}
    QPushButton#Secondary:hover {{
        background: #1b2d4b;
        border: 1px solid {c['purple_soft']};
        color: white;
    }}
    QPushButton#Secondary:pressed {{
        background: #0d1728;
        border: 1px solid {c['purple']};
        padding-top: 11px;
        padding-bottom: 7px;
    }}
    QPushButton#Link {{
        background: transparent;
        border: 1px solid transparent;
        color: {c['blue']};
        font-weight: 700;
        padding: 5px;
    }}
    QPushButton#Link:hover {{
        background: #14233b;
        border: 1px solid {c['border']};
        color: #86b1ff;
    }}
    QPushButton#Link:pressed {{
        background: #0d1728;
        border: 1px solid {c['purple_soft']};
        color: white;
        padding-top: 7px;
        padding-bottom: 3px;
    }}

    QPushButton#Danger {{
        background: #7f1d2d;
        border: 1px solid #c74257;
        color: white;
        font-weight: 700;
        padding: 10px 13px;
    }}
    QPushButton#Danger:hover {{
        background: #a4293e;
        border: 1px solid #ff7187;
        color: white;
    }}
    QPushButton#Danger:pressed {{
        background: #5f1421;
        border: 1px solid #ff7187;
        padding-top: 12px;
        padding-bottom: 8px;
    }}

    QPushButton[dashboardAction="true"] {{
        padding-top: 4px;
        padding-bottom: 4px;
        padding-left: 10px;
        padding-right: 10px;
    }}
    QPushButton[dashboardAction="true"]:pressed {{
        padding-top: 5px;
        padding-bottom: 3px;
    }}

    QFrame#SidebarCard QLabel#Tiny {{
        color: {c['muted']};
        font-weight: 700;
        letter-spacing: 0.4px;
    }}
    """
    from career_app.ui.responsive import scaled_stylesheet
    return scaled_stylesheet(raw, scale)

