import abc


class BaseService(abc.ABC):
    @abc.abstractmethod
    def execute(self, *args, **kwargs):
        ...
