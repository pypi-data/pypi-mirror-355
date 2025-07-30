import re


def format_filename(filename, replace=' '):
    """
    去除文件名特殊字符
    """
    return re.sub(re.compile(
        '[/\\\:*?"<>|]')
        , replace,
        filename
    )
