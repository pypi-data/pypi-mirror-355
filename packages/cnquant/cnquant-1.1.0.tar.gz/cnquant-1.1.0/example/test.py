import cnquant

# 添加黑名单数据
# cnquant.blacklist.insert_blacklist()
# 查询股票黑名单【这里是mysql数据库】
df = cnquant.blacklist.get_blacklist_symbols()
print(df)


