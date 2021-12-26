from dataclasses import dataclass, field


@dataclass
class Item:
    prefixes: dict = field(default_factory=dict)
    suffixes: dict = field(default_factory=dict)
    implicits: dict = field(default_factory=dict)