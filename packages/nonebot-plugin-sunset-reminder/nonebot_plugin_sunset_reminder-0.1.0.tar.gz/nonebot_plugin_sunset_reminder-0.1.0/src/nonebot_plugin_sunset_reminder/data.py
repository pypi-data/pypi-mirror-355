class Data:
    def __init__(self):
        self._data = {}

    def get(self, key, default=None):
        return self._data.get(key, default)

    def set(self, key, value):
        self._data[key] = value

    def remove(self, key):
        if key in self._data:
            del self._data[key]

    def clear(self):
        self._data.clear()

    def items(self):
        return self._data.items()


data_set = Data()


def get_data(key, default=None):
    """获取数据"""
    return data_set.get(key, default)


def set_data(key, value):
    """设置数据"""
    data_set.set(key, value)


def remove_data(key):
    """删除数据"""
    data_set.remove(key)


def clear_data():
    """清除所有数据"""
    data_set.clear()


def get_all_data():
    """获取所有数据"""
    return data_set.items()
