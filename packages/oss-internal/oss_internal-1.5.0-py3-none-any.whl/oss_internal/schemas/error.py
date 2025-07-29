class EmptyDirectoryError(Exception):
    """当目录为空时抛出的异常"""
    pass

class NotADirectoryError(Exception):
    """当指定路径不是目录时抛出的异常"""
    pass

class FileNotFoundError(Exception):
    """当本地文件不存在时抛出的异常"""
    pass

class FileNotEnoughError(Exception):
    """下载文件数量不足时候抛出的异常"""
    pass