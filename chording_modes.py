import enum


class ChordingMode(enum.Enum):
    CHARA_CHORDER = "charachorder"
    FUZZY_CHIPS = "fuzzy chips"

    @staticmethod
    def parse(value: str) -> "ChordingMode":
        modes = [member.value for member in ChordingMode]
        if value in modes:
            return ChordingMode(value)
        print(f"{value} is not a valid mode: {modes}")
        print(f"defaulting to {ChordingMode.CHARA_CHORDER.value}")
        return ChordingMode.CHARA_CHORDER
