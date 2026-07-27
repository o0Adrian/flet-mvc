from flet_mvc import FletModel, computed, data


class CounterModel(FletModel):
    @data
    def count(self) -> int:
        """Store the number of button clicks."""
        return 0

    @computed
    def message(self) -> str:
        """Recompute automatically after count changes."""
        count = self.count.value
        word = "time" if count == 1 else "times"
        return f"You clicked {count} {word}."
