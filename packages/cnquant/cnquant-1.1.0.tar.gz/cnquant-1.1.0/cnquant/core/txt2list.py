def txt2list(file_path):
    with open(file_path, mode='r') as f:
        lines = f.readlines()
    # 转换成列表
    return [line.strip() for line in lines]
