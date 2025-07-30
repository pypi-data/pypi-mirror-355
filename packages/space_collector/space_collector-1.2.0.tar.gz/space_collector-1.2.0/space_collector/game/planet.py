from dataclasses import dataclass


@dataclass
class Planet:
    x: int
    y: int
    size: int
    id: int
    collected_by: int = -1
    saved: bool = False

    def state(self) -> dict:
        return {
            "id": self.id,
            "x": self.x,
            "y": self.y,
            "size": self.size,
            "collected_by": self.collected_by,
            "saved": self.saved,
        }

    def radar_result(self) -> str:
        return f"P {self.id} {int(self.x)} {int(self.y)} {self.collected_by} {int(self.saved)}"
