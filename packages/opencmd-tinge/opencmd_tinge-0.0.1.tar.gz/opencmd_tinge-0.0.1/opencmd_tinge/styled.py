from typing import List, Optional
from rich.text import Text
from rich.style import Style
from rich.console import Console
from io import StringIO
from .styles import *

class StyledText:
    def __init__(self):
        self.parts: List[Text] = []
        self.curr_line: Optional[Text] = None
        self.indent: int = 0
        self.pending_newlines: int = 0

    def indent_(self, spaces: int) -> 'StyledText':
        self.indent = spaces
        return self

    def space(self, n: int = 1) -> 'StyledText':
        self._ensure_line_start()
        self.curr_line.append(" " * n)
        return self

    def newline(self) -> 'StyledText':
        if self.curr_line is not None:
            self.parts.append(self.curr_line)
            self.curr_line = None
        self.pending_newlines += 1
        return self

    def _ensure_line_start(self):
        if self.curr_line is None:
            self.curr_line = Text(" " * self.indent)
        if self.pending_newlines > 0:
            for _ in range(self.pending_newlines):
                self.parts.append(Text(""))
            self.pending_newlines = 0

    def with_(self, *styles: Style) -> 'StyledTextBuilder':
        return StyledTextBuilder(self, styles)

    def text(self, content: str) -> 'StyledText':
        self._ensure_line_start()
        self.curr_line.append(content)
        return self

    def render(self) -> Text:
        if self.curr_line is not None:
            self.parts.append(self.curr_line)
            self.curr_line = None
        final = Text()
        for part in self.parts:
            final.append(part)
            final.append("\n")
        return final

    def to_string(self) -> str:
        if self.curr_line is not None:
            self.parts.append(self.curr_line)
            self.curr_line = None
        console = Console(file=StringIO(), force_terminal=True, width=100)
        console.print(self.render(), end="")
        return console.file.getvalue()

    def red(self, text: str) -> 'StyledText':
        return self.with_(Red).text(text)

    def grey(self, text: str) -> 'StyledText':
        return self.with_(Grey).text(text)

    def bold(self, text: str) -> 'StyledText':
        return self.with_(Bold).text(text)


class StyledTextBuilder:
    def __init__(self, parent: StyledText, styles: List[Style]):
        self.parent = parent
        self.style = Style()
        for s in styles:
            self.style += s

    def text(self, content: str) -> StyledText:
        self.parent._ensure_line_start()
        self.parent.curr_line.append(Text(content, style=self.style))
        return self.parent
