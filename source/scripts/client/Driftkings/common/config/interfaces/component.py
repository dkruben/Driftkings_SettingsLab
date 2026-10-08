from .simple import ConfigInterface

__all__ = ('DriftkingsConfigInterface',)


class DriftkingsConfigInterface(ConfigInterface):
    def init(self):
        self.author = 'by Driftkings'
        self.modsGroup = 'Driftkings'
        super(DriftkingsConfigInterface, self).init()
