import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime

now = datetime.now()
date = now.strftime('%Y-%m-%d')
path = '/home/baili/Documents/import/'
supplier = '华为'

excelfile2 = path + 'huawei' + '/4-2.xlsx'
enbiddf = pd.read_excel(excelfile2, '查询eNodeB功能配置', encoding='utf8')
enbiddf = enbiddf.drop(['FileName','MML命令','执行结果','eNodeB名称','引用的应用标识','用户标签','网元资源模型版本','产品版本'], axis=1)
enbiddf = enbiddf.rename(index=str, columns={"NAME": "name", "eNodeB标识": "enbid"})
enbiddf.enbid = enbiddf.enbid.astype(str)


excelfile31 = path + 'huawei' + '/4G-2G-waibu_1.xlsx'
waibu1 = pd.read_excel(excelfile31, '查询GERAN外部小区', encoding='utf8')
waibu1 = waibu1.drop(['FileName','NAME','MML命令','执行结果','移动国家码','移动网络码','路由区域码配置指示','路由区域码','频段指示','支持DTM指示',
					'小区名称','GERAN小区CS与PS切换能力指示','Ultra-Flash CSFB能力指示','漫游区域允许切换标识','ANR 标识','控制模式'], axis=1)
# waibu1 = waibu1.rename(index=str, columns={"GERAN小区标识": "ci", "位置区域码": "lac", "GERAN频点": "bcch", "网络色码": "ncc", "基站色码": "bcc"})

excelfile32 = path + 'huawei' + '/4G-2G-waibu_2.xlsx'
waibu2 = pd.read_excel(excelfile32, '查询GERAN外部小区', encoding='utf8')
waibu2 = waibu2.drop(['FileName','NAME','MML命令','执行结果','移动国家码','移动网络码','路由区域码配置指示','路由区域码','频段指示','支持DTM指示',
					'小区名称','GERAN小区CS与PS切换能力指示','Ultra-Flash CSFB能力指示','漫游区域允许切换标识','ANR 标识','控制模式'], axis=1)
# waibu2 = waibu2.rename(index=str, columns={"GERAN小区标识": "ci", "位置区域码": "lac", "GERAN频点": "bcch", "网络色码": "ncc", "基站色码": "bcc"})

excelfile33 = path + 'huawei' + '/4G-2G-waibu_3.xlsx'
waibu3 = pd.read_excel(excelfile33, '查询GERAN外部小区', encoding='utf8')
waibu3 = waibu3.drop(['FileName','NAME','MML命令','执行结果','移动国家码','移动网络码','路由区域码配置指示','路由区域码','频段指示','支持DTM指示',
					'小区名称','GERAN小区CS与PS切换能力指示','Ultra-Flash CSFB能力指示','漫游区域允许切换标识','ANR 标识','控制模式'], axis=1)


waibu = waibu1.append([waibu2,waibu3], ignore_index=True)
waibu = waibu.rename(index=str, columns={"GERAN小区标识": "ci", "位置区域码": "lac", "GERAN频点": "bcch", "网络色码": "ncc", "基站色码": "bcc"})
waibu.ci = waibu.ci.astype(str)
waibu.lac = waibu.lac.astype(str)
waibu.bcch = waibu.bcch.astype(str)
waibu.ncc = waibu.ncc.astype(str)
waibu.bcc = waibu.bcc.astype(str)
waibu.insert(5, 'lac_ci', waibu.lac+'_'+waibu.ci)
waibu = waibu.drop(['lac','ci'], axis=1)
#去重
waibu = waibu.drop_duplicates(subset='lac_ci')


excelfile11 = path + 'huawei' + '/4G-2G-linqu_5.xlsx'
data = pd.read_excel(excelfile11, '查询GERAN邻区关系', encoding='utf8')
# 删除多余列
data = data.drop(['FileName','MML命令','执行结果','ANR 标识','本地小区名称','重叠覆盖标识','邻区测量优先级','控制模式'], axis=1)

# 修改列名
data = data.rename(index=str, columns={"NAME": "name", "本地小区标识": "lte_xqbs", "移动国家码": "mcc", "移动网络码": "mnc",
										"位置区域码": "lac", "GERAN小区标识": "ci", "邻区小区名称": "gsm_xqmc", "禁止删除标识": "normvflag",
										"禁止切换标识": "nohoflag", "盲切换优先级": "blindhopriority"})

data.mcc = '460'
data.mnc = '00'
data.lac = data.lac.astype(str)
data.ci = data.ci.astype(str)
data.lte_xqbs = data.lte_xqbs.astype(str)
data.blindhopriority = data.blindhopriority.astype(str)
data.insert(6, 'lac_ci', data.lac+'_'+data.ci)
data.insert(2, 'english_name_four', data.name+'_'+data.lte_xqbs)

result = pd.merge(data, enbiddf, how='left', on='name')
result.insert(12, 'ecgi', '460-00-'+result.enbid+'-'+result.lte_xqbs)

result = pd.merge(result, waibu, how='left', on='lac_ci')
# result = result.loc[:,['name','lte_xqbs','english_name_four','mcc','mnc','lac','ci','lac_ci','normvflag','nohoflag','blindhopriority','gsm_xqmc','ecgi','enbid','bcch','ncc','bcc']]
result = result.loc[:,['enbid','ecgi','name','lte_xqbs','english_name_four','mcc','mnc','lac','ci','lac_ci','bcch','ncc','bcc','gsm_xqmc','normvflag','nohoflag','blindhopriority']]

result.seq = range(len(result))
result.insert(0,'seq',result.seq)
result.insert(1, 'date', date)
result.insert(2, 'supplier', supplier)
result.insert(20, 'new_lac', '')
result.insert(21, 'new_ci', '')
result.insert(22, 'remark', '')


sql = 'mysql+pymysql://llr:chenlie@127.0.0.1:3306/mydb?charset=utf8'
engine = create_engine(sql)
result.to_sql('four_two_new', engine, if_exists='append', index=False)
