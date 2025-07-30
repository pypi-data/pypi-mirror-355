class TqZqTimeoutError(Exception):
    """
    初始化、启动时的超时报错
    """

    def __init__(self, message):
        super().__init__(message)
        self.message = message


class TqZqHealthCheckError(Exception):
    """
    进程健康检查报错
    """

    def __init__(self, message):
        super().__init__(message)
        self.message = message
