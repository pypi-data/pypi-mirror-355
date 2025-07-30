from abc import ABC, abstractmethod
from typing import List


class ReportComponent(ABC):
    @property
    def class_name(self) -> str:
        return self.__class__.__name__

    @abstractmethod
    def mount(self) -> None:
        ...


class ReportComposite(ReportComponent):
    def __init__(self) -> None:
        self.__children: List[ReportComponent] = []

    def mount(self) -> None:
        for child in self.__children:
            child.mount()

    def add(self, child: ReportComponent) -> None:
        self.__children.append(child)

    def remove(self, child: ReportComponent) -> None:
        if child not in self.__children:
            raise ValueError(f"Component {child.class_name} not in children.")

        self.__children.remove(child)
