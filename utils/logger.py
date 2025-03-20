import logging
import logging.config

class LoggerConfigurator:
    """
    Configures the logging for the application.
    """
    def __init__(self):
        self.config = {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'standard': {
                    'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
                },
            },
            'handlers': {
                'default': {
                    'level': 'INFO',
                    'formatter': 'standard',
                    'class': 'logging.StreamHandler',
                    'stream': 'ext://sys.stdout',  # Default is stderr
                },
            },
            'loggers': {
                '': {  # root logger
                    'handlers': ['default'],
                    'level': 'INFO',
                    'propagate': True
                },
                '__main__': {  # if __name__ == '__main__'
                    'level': 'DEBUG',
                    'propagate': True
                },
            }
        }
        logging.config.dictConfig(self.config)
        self.logger = logging.getLogger(__name__)

    def get_logger(self):
        """
        Returns the configured logger.
        """
        return self.logger
