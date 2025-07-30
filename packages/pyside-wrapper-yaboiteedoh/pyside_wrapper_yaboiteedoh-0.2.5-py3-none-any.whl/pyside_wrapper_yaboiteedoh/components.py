from PySide6.QtCore import (
    Qt,
    Signal,
    QObject
)
from PySide6.QtGui import (
    QAction,
    QKeySequence
)
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QFrame,
    QSizePolicy,
    QScrollArea,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QCheckBox
)


PRIORITIES = {
    'low': QAction.Priority.LowPriority,
    'normal': QAction.Priority.NormalPriority,
    'high': QAction.Priority.HighPriority
}

FRAME_SHAPES = {
    'none': QFrame.Shape.NoFrame,
    'box': QFrame.Shape.Box,
    'panel': QFrame.Shape.Panel,
    'styled': QFrame.Shape.StyledPanel,
    'hline': QFrame.Shape.HLine,
    'vline': QFrame.Shape.VLine,
    'win': QFrame.Shape.WinPanel
}

SHADOW_STYLES = {
    'plain': QFrame.Shadow.Plain,
    'raised': QFrame.Shadow.Raised,
    'sunken': QFrame.Shadow.Sunken
}


class TAction(QAction):
    def __init__(
        self,
        text,
        func=None,
        shortcut=None,
        priority='normal',
        connection_type=Qt.AutoConnection,
        parent=None,
        menu=None,
        group=None,
        auto_repeat=False,
        checkable=False
    ):
        super().__init__(
            text,
            parent
        )
        if group:
            self.setActionGroup(group)
        if auto_repeat:
            self.setAutoRepeat(auto_repeat)
        if checkable:
            self.setCheckable(checkable)
        if menu:
            self.setMenu(menu)
        if priority:
            self.setPriority(PRIORITIES[priority])
        if shortcut:
            self.setShortcut(QKeySequence(shortcut))
        if func:
            self.triggered.connect(func, type=connection_type)
        if parent:
            parent.addAction(self)


    def ping(self):
        self.triggered.emit()


class TApp(QObject):
    def __init__(
        self,
        title='Teedoh Pyside Wrapper Application',
        geometry=[]
    ):
        super().__init__()

        self.app = QApplication([])
        self.window = QMainWindow()

        self.menu = self.window.menuBar()
        self.file_menu = self.menu.addMenu('&File')

        self.force_close = TAction(
            'Exit Application',
            shortcut='Ctrl+d',
            priority='high',
            connection_type=Qt.DirectConnection,
            parent=self.file_menu,
            func=self.window.close
        )
        if title:
            self.window.setWindowTitle(title)
        if geometry:
            self.window.setGeometry(*geometry)

        self.window.show()
        self.window.setWindowState(Qt.WindowMaximized)


    def surrender(self):
        self.window.setCentralWidget(self.sender())


    def exec(self):
        self.app.exec()


class TFlexFrame(QFrame):
    greedy = Signal()

    def __init__(
        self,
        *args,
        flex='v',
        max_columns=None,
        style_class=None,
        scrollbar=None,
        size_policy='xy',
        label=None,
        accept_drops=False,
        frame_style=['none', 'plain', 0, 0],
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        
        if accept_drops:
            self.setAcceptDrops(True)

        if frame_style:
            frame_shape, shadow_style, line_width, mid_line_width = frame_style
            self.setFrameStyle(
                FRAME_SHAPES[frame_shape] | SHADOW_STYLES[shadow_style]
            )
            self.setLineWidth(line_width)
            self.setMidLineWidth(mid_line_width)

        if size_policy is not None:
            match size_policy:
                case 'xy':
                    self.size_policy = [
                        QSizePolicy.Policy.Expanding,
                        QSizePolicy.Policy.Expanding
                    ]
                case 'x':
                    self.size_policy = [
                        QSizePolicy.Policy.Expanding,
                        QSizePolicy.Policy.Minimum
                    ]
                case 'y':
                    self.size_policy = [
                        QSizePolicy.Policy.Minimum,
                        QSizePolicy.Policy.Expanding
                    ]
                case '':
                    self.size_policy = [
                        QSizePolicy.Policy.Minimum,
                        QSizePolicy.Policy.Minimum
                    ]

        self.flex = flex
        self.style_class = style_class
        self.cur_row = 0
        self.cur_column = 0
        self.max_columns = max_columns

        self._children = []

        self.main_layout = QVBoxLayout(self)
        self.container = QWidget()

        match self.flex:
            case 'v':
                self.layout = QVBoxLayout()
            case 'h':
                self.layout = QHBoxLayout()
            case _:
                self.layout = QGridLayout()

        self.container.setLayout(self.layout)
        self.setSizePolicy(*self.size_policy)
        self.container.setSizePolicy(*self.size_policy)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        if label:
            self.label = QLabel(label)
            self.main_layout.addWidget(self.label)

        if scrollbar is not None:
            self.scroll = QScrollArea()
            self.scroll.setWidgetResizable(True)
            self.scroll.setWidget(self.container)
            match scrollbar:
                case 'v':
                    self.scroll.setVerticalScrollBarPolicy(
                        Qt.ScrollBarPolicy.ScrollBarAsNeeded
                    )
                    self.scroll.setHorizontalScrollBarPolicy(
                        Qt.ScrollBarPolicy.ScrollBarAlwaysOff
                    )
                case 'h':
                    self.scroll.setVerticalScrollBarPolicy(
                        Qt.ScrollBarPolicy.ScrollBarAlwaysOff
                    )
                    self.scroll.setHorizontalScrollBarPolicy(
                        Qt.ScrollBarPolicy.ScrollBarAsNeeded
                    )
                case 'both':
                    self.scroll.setVerticalScrollBarPolicy(
                        Qt.ScrollBarPolicy.ScrollBarAsNeeded
                    )
                    self.scroll.setHorizontalScrollBarPolicy(
                        Qt.ScrollBarPolicy.ScrollBarAsNeeded
                    )
            self.main_layout.addWidget(self.scroll)
        else:
            self.main_layout.addWidget(self.container)

        self.setLayout(self.main_layout)


    def populate(
        self,
        blueprint_class,
        objs
    ):
        self.clear_widgets()
        for obj in objs:
            o = blueprint_class(**obj)
            self.add_widget(o)

    
    def add_widget(self, widget, stretch=0):
        match self.flex:
            case 'v' | 'h':
                print(widget, len(self.children))
                self.layout.addWidget(widget, stretch=stretch)
            case _:
                print(widget, self.cur_row, self.cur_column)
                self.layout.addWidget(widget, self.cur_row, self.cur_column)
     
                self.cur_column += 1

                if self.max_columns:
                    if self.cur_column >= self.max_columns:
                        self.cur_row += 1
                        self.cur_column = 0

        self._children.append(widget)
        return widget


    def remove_widget(self, widget):
        self.cur_column = 0
        self.cur_row = 0

        for child in self.children:
            self.layout.removeWidget(child)
            self._children.remove(child)

            if child == widget:
                child.setParent(None)
                child.deleteLater()
            else:
                self.add_widget(child)
        self.update()


    def clear_widgets(self):
        for child in self.children:
            self._children.remove(child)
            child.setParent(None)
            child.deleteLater()

        self.cur_column = 0
        self.cur_row = 0
        self._children = []


    def center_widget(self, widget):
        i = self.layout.indexOf(widget)
        self.layout.setAlignment(widget, Qt.AlignmentFlag.AlignCenter)


    def focus_widget(self, widget):
        for child in self.children:
            child.setHidden(True)
            if child == widget:
                child.setHidden(False)


    @property
    def children(self):
        return [child for child in self._children]


class TCheckBox(QCheckBox):
    def __init__(
        self,
        *args,
        text=None,
        **kwargs
    ):
        super().__init__(*args, **kwargs)

        if text:
            self.text = text


    @property
    def text(self):
        return self.text()


    @text.setter
    def text(self, value):
        self.setText(value)


    @property
    def checked(self):
        return self.checkState() == Qt.CheckState.Checked


    @checked.setter
    def checked(self, value):
        if value:
            state = Qt.CheckState.Checked
        else:
            state = Qt.CheckState.Unchecked
        self.setCheckState(state)


