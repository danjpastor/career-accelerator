from pathlib import Path

COLORS = {
    # Data Career Accelerator rebrand palette. These values are deliberately
    # centralized so every existing page inherits the new visual system while
    # keeping its current layout and behavior unchanged.
    "bg": "#080F1D",
    "sidebar": "#090F1B",
    "panel": "#0E192B",
    "panel_alt": "#121F34",
    "panel_hover": "#182A46",
    "border": "#263754",
    "text": "#FFFFFF",
    "muted": "#A8B4C8",
    "purple": "#8A5CFF",
    "purple_soft": "#A56CFF",
    "purple_dark": "#4D2E84",
    "magenta": "#FF4DB8",
    "blue": "#39B0FF",
    "green": "#4FD08B",
    "orange": "#FF8A3D",
    "gold": "#F5C451",
    "red": "#FF657D",
    "cyan": "#39B0FF",
    # Course-style widgets use these semantic aliases.
    "surface": "#0C1627",
    "surface_alt": "#111D31",
}

def stylesheet(scale: float = 1.0, content_scale: float = 1.0):
    c = COLORS
    chevron_path = (
        Path(__file__).resolve().parent.parent / "assets" / "chevron-down.svg"
    ).as_posix()
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
        background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #070D18, stop:1 {c['sidebar']});
        border-right: 1px solid #2A2444;
    }}
    QFrame#Card {{
        background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 #101D31, stop:1 {c['panel']});
        border: 1px solid {c['border']};
        border-radius: 13px;
    }}
    QFrame#SoftPanel {{
        background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 #14233B, stop:1 {c['panel_alt']});
        border: 1px solid {c['border']};
        border-radius: 10px;
    }}
    QFrame#SidebarCard {{
        background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 #111C31, stop:1 #0D1728);
        border: 1px solid #2D3658;
        border-radius: 12px;
    }}
    QFrame#BrandBanner {{
        background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #351536, stop:0.42 #20143B, stop:0.72 #151A38, stop:1 #251536);
        border: 1px solid #D05AAA;
        border-radius: 13px;
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
        background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {c['magenta']}, stop:1 {c['purple']});
        color: white;
        font-weight: 700;
        border: 1px solid #B66CFF;
        padding: 11px 14px;
    }}
    QPushButton#Primary:hover {{
        background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #FF6BC6, stop:1 #A477FF);
        border: 1px solid #E0B5FF;
    }}
    QPushButton#Primary:pressed {{
        background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #D6379A, stop:1 #6F42D8);
        border: 1px solid #F3C5FF;
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
        background: #17243C;
        color: white;
        border-left: 3px solid {c['magenta']};
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
                    stop:0 #3A174F, stop:0.58 #512677, stop:1 #342358);
        color: white;
        border: 1px solid #7E4FC4;
        border-left: 3px solid {c['magenta']};
    }}
    QPushButton#Nav:checked:hover {{
        background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #4A1C66, stop:0.58 #673294, stop:1 #44306E);
        border: 1px solid #A46CEC;
        border-left: 3px solid #FF72C9;
    }}
    QLineEdit, QTextEdit, QComboBox, QListWidget, QTableWidget, QSpinBox {{
        background: {c['panel_alt']};
        border: 1px solid {c['border']};
        border-radius: 8px;
        padding: 7px;
        selection-background-color: #6B2F94;
    }}
    QComboBox {{
        padding: 7px 34px 7px 10px;
        min-height: 20px;
        background: {c['panel_alt']};
        border: 1px solid {c['border']};
        border-radius: 9px;
    }}
    QComboBox:hover {{
        background: {c['panel_hover']};
        border: 1px solid {c['purple_soft']};
    }}
    QComboBox:focus, QComboBox:on {{
        background: #17253b;
        border: 1px solid {c['magenta']};
    }}
    QComboBox::drop-down {{
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 30px;
        background: #17243a;
        border: none;
        border-left: 1px solid {c['border']};
        border-top-right-radius: 8px;
        border-bottom-right-radius: 8px;
    }}
    QComboBox::drop-down:hover {{
        background: #223552;
    }}
    QComboBox::down-arrow {{
        image: url({chevron_path});
        width: 12px;
        height: 8px;
    }}
    QComboBox QAbstractItemView {{
        background: #111d30;
        color: {c['text']};
        border: 1px solid {c['border']};
        border-radius: 9px;
        padding: 5px;
        outline: 0;
        selection-background-color: #5F2D85;
        selection-color: white;
    }}
    QComboBox QAbstractItemView::item {{
        min-height: 26px;
        padding: 5px 8px;
        border-radius: 6px;
    }}
    QComboBox QAbstractItemView::item:hover {{
        background: {c['panel_hover']};
    }}
    QListWidget {{
        background: transparent;
        border: none;
        padding: 0;
    }}
    QListWidget::item, QTreeWidget::item, QTreeView::item {{
        background: transparent;
        border: none;
        min-height: 20px;
        padding: 6px 4px;
    }}
    QTableWidget::item, QTableView::item {{
        padding: 5px 7px;
    }}
    QHeaderView::section {{
        background: #17243a;
        color: {c['text']};
        border: none;
        border-right: 1px solid {c['border']};
        border-bottom: 1px solid {c['border']};
        min-height: 20px;
        padding: 6px 8px;
        font-weight: 700;
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
        background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {c['magenta']}, stop:1 {c['purple']});
        border-radius: 4px;
    }}
    QSlider::groove:horizontal {{
        height: 6px;
        background: #1c2b42;
        border-radius: 3px;
    }}
    QSlider::sub-page:horizontal {{
        background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {c['magenta']}, stop:1 {c['purple']});
        border-radius: 3px;
    }}
    QSlider::add-page:horizontal {{
        background: #1c2b42;
        border-radius: 3px;
    }}
    QSlider::handle:horizontal {{
        background: #FF8AD3;
        border: 2px solid {c['purple_dark']};
        width: 16px;
        height: 16px;
        margin: -6px 0;
        border-radius: 8px;
    }}
    QSlider::handle:horizontal:hover {{
        background: white;
        border: 2px solid {c['purple']};
    }}
    QScrollArea {{
        border: none;
        background: transparent;
    }}
    QScrollBar:vertical {{
        background: transparent;
        width: 12px;
        margin: 3px 2px;
        border: none;
    }}
    QScrollBar::handle:vertical {{
        background: #34415C;
        min-height: 34px;
        border: 2px solid transparent;
        border-radius: 5px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {c['purple_soft']};
    }}
    QScrollBar::handle:vertical:pressed {{
        background: {c['purple']};
    }}
    QScrollBar:horizontal {{
        background: transparent;
        height: 12px;
        margin: 2px 3px;
        border: none;
    }}
    QScrollBar::handle:horizontal {{
        background: #34415C;
        min-width: 34px;
        border: 2px solid transparent;
        border-radius: 5px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background: {c['purple_soft']};
    }}
    QScrollBar::handle:horizontal:pressed {{
        background: {c['purple']};
    }}
    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical,
    QScrollBar::add-line:horizontal,
    QScrollBar::sub-line:horizontal {{
        width: 0;
        height: 0;
        border: none;
        background: transparent;
    }}
    QScrollBar::add-page:vertical,
    QScrollBar::sub-page:vertical,
    QScrollBar::add-page:horizontal,
    QScrollBar::sub-page:horizontal {{
        background: transparent;
        border: none;
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
    QStatusBar {{
        background: #070D18;
        color: {c['muted']};
        border-top: 1px solid #1D2B43;
    }}
    QToolTip {{
        background: #121F34;
        color: white;
        border: 1px solid {c['purple_soft']};
        padding: 5px 8px;
        border-radius: 6px;
    }}
    """
    from career_app.ui.responsive import scaled_stylesheet
    return scaled_stylesheet(raw, scale, content_scale)

