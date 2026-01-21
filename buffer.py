from collections import deque


class RingBuffer:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.buffer = deque(maxlen=capacity)

    def add(self, item):
        """Add item to the buffer (removes oldest if full)"""
        self.buffer.append(item)

    def get(self):
        """Get the current buffer as a list"""
        return list(self.buffer)

    def __str__(self):
        return str(self.buffer)

    def __len__(self):
        return len(self.buffer)

    def get_white_space_before_prev_word(self) -> str:
        chars = self.get()
        if not chars:
            return ""

        i = len(chars) - 1

        # 1. Skip trailing whitespace
        while i >= 0 and chars[i].isspace():
            i -= 1

        # 2. Skip the previous word
        while i >= 0 and not chars[i].isspace():
            i -= 1

        # 3. Collect whitespace before the word
        end = i
        while i >= 0 and chars[i].isspace():
            i -= 1

        start = i + 1
        return ''.join(chars[start:end + 1])

    def get_trailing_white_space(self) -> str:
        chars: list[str] = self.get()
        if len(chars) == 0:
            return ""
        upper = len(chars) - 1
        if not chars[upper].isspace():
            return ""
        lower = len(chars) - 1
        while lower > 0 and chars[lower].isspace():
            lower -= 1
        if lower > 0:
            lower += 1
        elif lower == 0 and not chars[lower].isspace():
            lower += 1

        return ''.join(chars[lower:upper+1])

    def should_captlize_prev_word(self, captilize_after=[]) -> bool:
        chars: list[str] = self.get()
        target_range = RingBuffer._get_prev_word_range(chars)
        if target_range is None:
            return False
        lower, _ = target_range
        if lower == 0:
            return False
        lower -= 1
        while lower > 0:
            if not chars[lower].isspace():
                break
            lower -= 1
        return chars[lower] in captilize_after

    def get_prev_word(self) -> str:
        chars = self.get()
        target = RingBuffer._get_prev_word_range(chars)
        if target is None:
            return ""
        lower, upper = target
        return ''.join(chars[lower:upper+1])

    @staticmethod
    def _get_prev_word_range(chars: list[str]):
        if len(chars) == 0:
            return None
        upper = len(chars) - 1

        while upper > 0 and chars[upper] == " ":
            upper -= 1
        if upper < 0 or chars[upper] == " ":
            return None
        lower = 0
        for i in range(upper, 0, -1):
            if chars[i] == ' ':
                lower = i+1
                break
        return (lower, upper)

    def clear(self):
        self.buffer.clear()

    def backspace(self):
        if not self.is_empty():
            return self.buffer.pop()

    def is_empty(self):
        return len(self.buffer) == 0

    def get_last(self):
        """Get the last inserted value"""
        if not self.is_empty():
            return self.buffer[-1]
        else:
            return None  # Return None if buffer is empty
