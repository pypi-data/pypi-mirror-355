from PySide6.QtWidgets import (
    QLabel,
    QLineEdit,
    QRadioButton
)

from .components import TFlexFrame


class TLabeledInput(TFlexFrame):
    def __init__(
        self,
        text,
        *args,
        flex='h',
        size_policy='',
        **kwargs
    ):
        super().__init__(
            *args,
            flex=flex,
            size_policy=size_policy,
            **kwargs
        )

        self.label = QLabel(text)
        self.input = QLineEdit()
        self.add_widget(self.label)
        self.add_widget(self.input)

    
    @property
    def text(self):
        return self.label.text()


    @text.setter
    def text(self, value):
        self.label.setText(value)


    @property
    def value(self):
        return self.input.text()


    @value.setter
    def value(self, value):
        return self.input.setText(value)


class RadioMenu(TFlexFrame):
    def __init__(
        self,
        label,
        *args,
        options=[],
        default='',
        size_policy='',
        **kwargs
    ):
        super().__init__(
            *args,
            label=label,
            size_policy=size_policy,
            **kwargs
        )

        self.options = options
        if default:
            self.value = default


    @property
    def options(self):
        return [option.text() for option in self.children]


    @options.setter
    def options(self, options: list[str]):
        selection = self.value
        self.clear_widgets()
        self.populate(
            QRadioButton,
            [{'text': option} for option in options]
        )
        self.value = selection


    @property
    def value(self):
        for option in self.children:
            if option.isChecked():
                return option.text()


    @value.setter
    def value(self, value):
        if value in self.options:
            for option in self.children:
                if option.text() == value:
                    option.setChecked()

