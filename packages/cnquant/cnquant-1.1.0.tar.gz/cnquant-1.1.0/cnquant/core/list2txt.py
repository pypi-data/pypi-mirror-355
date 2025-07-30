def list2txt(data: list, filepath: str) -> None:
    """
    保存列表为txt格式文件，一行一个元素
    """
    with open(filepath, "w") as f:
        for item in data:
            f.write(f"{item}\n")
