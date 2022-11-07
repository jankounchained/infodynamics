''' 
Base classes
'''

from abc import ABCMeta


class BaseMetric(metaclass=ABCMeta):
    def __init__(self) -> None:
        pass

class BaseCalculator(metaclass=ABCMeta):
    def __init__(self) -> None:
        pass