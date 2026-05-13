from .book import ParsedChapter


class ChapterSelection:
    def __init__(self) -> None:
        self._selected: dict[int, bool] = {}

    def load(self, chapters: list[ParsedChapter]) -> None:
        self._selected = {chapter.index: True for chapter in chapters}

    def toggle(self, index: int) -> bool:
        current = self._selected.get(index, False)
        self._selected[index] = not current
        return self._selected[index]

    def is_selected(self, index: int) -> bool:
        return self._selected.get(index, False)

    def selected_indexes(self) -> tuple[int, ...]:
        return tuple(
            sorted(index for index, selected in self._selected.items() if selected)
        )

    def has_chapters(self) -> bool:
        return bool(self._selected)

