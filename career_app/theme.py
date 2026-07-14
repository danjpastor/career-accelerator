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

def stylesheet():
    c = COLORS
    return f"""
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
    }}
    QPushButton#Nav {{
        text-align: left;
        border: none;
        background: transparent;
        color: {c['muted']};
        padding: 13px 15px;
        border-radius: 9px;
    }}
    QPushButton#Nav:hover {{
        background: #14233b;
        color: white;
    }}
    QPushButton#Nav:checked {{
        background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #563c9f, stop:1 #47307f);
        color: white;
        border-left: 3px solid #a98bff;
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
    QPushButton#Secondary {{
        background: {c['panel_alt']};
        border: 1px solid {c['border']};
        color: {c['text']};
        font-weight: 600;
        padding: 9px 12px;
    }}
    QPushButton#Link {{
        background: transparent;
        border: none;
        color: {c['blue']};
        font-weight: 700;
        padding: 5px;
    }}
    QFrame#SidebarCard QLabel#Tiny {{
        color: {c['muted']};
        font-weight: 700;
        letter-spacing: 0.4px;
    }}
    """
