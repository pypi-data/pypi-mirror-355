import os

__author__ = "Sergey Strukov"
__copyright__ = "Copyright 2024 Sergey Strukov"
__email__ = "strukovsv@mail.ru"
__license__ = "MIT"
__title__ = "DictList2"
__version__ = "1.0.1"


def VERSION():
    """Получить версию пакета из переменной"""
    dev_version = os.environ.get("LAST_VERSION")
    return dev_version if dev_version else __version__
