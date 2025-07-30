import datetime

import cnquant
import os.path
from pathlib import Path

# 先获取群晖SynologyDrive文件夹，要么C盘，要么D盘
SynologyDrive = Path.home() / 'SynologyDrive'
if not SynologyDrive.exists():
    SynologyDrive = Path(r'D:\SynologyDrive')

data_directory = os.path.join(str(SynologyDrive), r'01项目记录\小牛A股工具箱\小牛A股工具箱\data')
config_directory = os.path.join(str(SynologyDrive), r'01项目记录\小牛A股工具箱\config')
temp_directory = os.path.join(str(SynologyDrive), r'01项目记录\小牛A股工具箱\temp')

# -------------------- 执行路径设置 (必须在其他操作之前) --------------------

print("正在为 cnquant 配置自定义路径...")
cnquant.set_data_path(data_directory)
cnquant.set_config_path(config_directory)
cnquant.set_temp_path(temp_directory)
print("路径配置完毕！\n" + "="*50)


# -------------------- 现在可以开始正常使用 cnquant 的功能了 --------------------
print("\n开始更新数据...")
# 使用多线程更新数据，所有文件都会被保存到上面设置的路径中
cnquant.multithread_update_data(thread_num=2)
# 发送邮件提醒
cnquant.send_email(mail='33688114@qq.com', title=f'{datetime.date.today().isoformat()}日股票data数据更新完毕', content=f'{datetime.date.today().isoformat()}日股票data数据更新完毕')
print("\n数据更新完成！")


