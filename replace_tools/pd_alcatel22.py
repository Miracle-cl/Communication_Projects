import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime


def get_idref(s):
	idref = s.split('ID "')[1].split('}')[0]
	idref = idref.replace('", cellRef ', '_')
	return idref



now = datetime.now()
date = now.strftime('%Y-%m-%d')
supplier = '卡特'
path = '/home/baili/Documents/import/alcatel/OMC'
omc = '1'

bsc_path = path + omc + '/RnlAlcatelBSC.csv'
df_bsc = pd.read_csv(bsc_path, sep=';', header=1, encoding='utf8')
df_bsc = df_bsc.loc[:,['RnlAlcatelBSCInstanceIdentifier','UserLabel']]
df_bsc = df_bsc.rename(index=str, columns={'RnlAlcatelBSCInstanceIdentifier':'bsc_no', 'UserLabel':'bsc'})
df_bsc.bsc_no = df_bsc.bsc_no.astype(str)


cell_path = path + omc + '/Cell.csv'
df_cell = pd.read_csv(cell_path, sep=';', header=1, encoding='utf8')
df_cell = df_cell.loc[:,['CellInstanceIdentifier','RnlSupportingSector','CellGlobalIdentity','BsIdentityCode',
					'UserLabel','BCCHFrequency']]
df_cell.CellInstanceIdentifier = df_cell.CellInstanceIdentifier.map(get_idref) #idref
df_cell.RnlSupportingSector = df_cell.RnlSupportingSector.map(lambda x: x.split('bsc ')[1].split(',')[0]) #bsc_no
# get: lac ci lac_ci ncc bcc
df_cell.lac_ci = df_cell.CellGlobalIdentity.map(lambda x: x.split('lac ')[1][:-1].replace('}, ci ', '_'))
df_cell.lac = df_cell.lac_ci.map(lambda x: x.split('_')[0])
df_cell.ci = df_cell.lac_ci.map(lambda x: x.split('_')[1])
df_cell.ncc = df_cell.BsIdentityCode.map(lambda x: x.split('ncc ')[1].split(',')[0])
df_cell.bcc = df_cell.BsIdentityCode.map(lambda x: x[-2])
df_cell.BCCHFrequency = df_cell.BCCHFrequency.astype(str)
df_cell.insert(3, 'lac', df_cell.lac)
df_cell.insert(4, 'ci', df_cell.ci)
df_cell.insert(5, 'lac_ci', df_cell.lac_ci)
df_cell.insert(6, 'ncc', df_cell.ncc)
df_cell.insert(7, 'bcc', df_cell.bcc)
# UserLabel-english_name; BCCHFrequency-bcch
df_cell = df_cell.drop(['CellGlobalIdentity', 'BsIdentityCode'], axis=1)
df_cell = df_cell.rename(index=str, columns={"CellInstanceIdentifier": "idref", "RnlSupportingSector": "bsc_no",
						"UserLabel": "english_name", "BCCHFrequency": "freq"})
df_cell = pd.merge(df_cell, df_bsc, how='left', on='bsc_no')
df_cell = df_cell.drop('bsc_no', axis=1)


EXTcell_path = path + omc + '/ExternalOmcCell.csv'
df_extcell = pd.read_csv(EXTcell_path, sep=';', header=1, encoding='utf8')
df_extcell = df_extcell.loc[:,['ExternalOmcCellInstanceIdentifier','CellGlobalIdentity','BsIdentityCode','UserLabel',
					'BCCHFrequency']]
df_extcell.ExternalOmcCellInstanceIdentifier = df_extcell.ExternalOmcCellInstanceIdentifier.map(get_idref) #idref
# get: lac ci lac_ci ncc bcc
df_extcell.lac_ci = df_extcell.CellGlobalIdentity.map(lambda x: x.split('lac ')[1][:-1].replace('}, ci ', '_'))
df_extcell.lac = df_extcell.lac_ci.map(lambda x: x.split('_')[0])
df_extcell.ci = df_extcell.lac_ci.map(lambda x: x.split('_')[1])
df_extcell.ncc = df_extcell.BsIdentityCode.map(lambda x: x.split('ncc ')[1].split(',')[0])
df_extcell.bcc = df_extcell.BsIdentityCode.map(lambda x: x[-2])
df_extcell.BCCHFrequency = df_extcell.BCCHFrequency.astype(str)
df_extcell.insert(3, 'lac', df_extcell.lac)
df_extcell.insert(4, 'ci', df_extcell.ci)
df_extcell.insert(5, 'lac_ci', df_extcell.lac_ci)
df_extcell.insert(6, 'ncc', df_extcell.ncc)
df_extcell.insert(7, 'bcc', df_extcell.bcc)
# UserLabel-english_name; BCCHFrequency-bcch
df_extcell = df_extcell.drop(['CellGlobalIdentity', 'BsIdentityCode'], axis=1)
df_extcell = df_extcell.rename(index=str, columns={"ExternalOmcCellInstanceIdentifier": "idref",
						"UserLabel": "english_name", "BCCHFrequency": "freq"})
df_extcell.insert(8, 'bsc', '')

df_cell = df_cell.append(df_extcell, ignore_index=True)


adjacency_path = path + omc + '/Adjacency.csv'
adjacency = pd.read_csv(adjacency_path, sep=';', header=1, encoding='utf8')
adjacency = adjacency.loc[:,['HoMargin','AdjacencyInstanceIdentifier']]
# 删除HoMargin为127的行
adjacency = adjacency[adjacency.HoMargin != 127]
# get: idref, aidref
adjacency.idref = adjacency.AdjacencyInstanceIdentifier.map(lambda x: x.split('applicationID "')[1].split('}')[0].replace('", cellRef ', '_'))
adjacency.aidref = adjacency.AdjacencyInstanceIdentifier.map(lambda x: x.split('targetCell { applicationID "')[1][:-2].replace('", cellRef ', '_'))
adjacency.insert(0, 'idref', adjacency.idref)
adjacency.insert(1, 'aidref', adjacency.aidref)
adjacency = adjacency.drop(['HoMargin','AdjacencyInstanceIdentifier'], axis=1)


df_cell_local = df_cell.loc[:,['idref','bsc','english_name','lac','ci','lac_ci']]
adjacency = pd.merge(adjacency, df_cell_local, how='left', on='idref')
adjacency = adjacency.loc[:,['idref', 'bsc', 'english_name', 'lac', 'ci', 'lac_ci', 'aidref']]
df_cell_adj = df_cell.loc[:,['idref','bsc','english_name','lac','ci','lac_ci','freq','ncc','bcc']]
df_cell_adj = df_cell_adj.rename(index=str, columns={'idref': 'aidref', 'bsc': 'absc', 'english_name': 'adj_english_name',
								'lac': 'alac', 'ci': 'aci', 'lac_ci': 'adj_lac_ci'})
adjacency = pd.merge(adjacency, df_cell_adj, how='left', on='aidref')
adjacency.seq = range(len(adjacency))
adjacency.insert(0, 'seq', adjacency.seq)
adjacency.insert(1, 'date', date)
adjacency.insert(2, 'supplier', supplier)
adjacency.insert(3, 'omc', omc)
adjacency.insert(6, 'bcf', '')
adjacency.insert(7, 'seg', '')
adjacency.insert(8, 'bts', '')
adjacency.insert(10, 'mcc', '')
adjacency.insert(11, 'mnc', '')
adjacency.insert(15, 'aindex', '')
adjacency.insert(18, 'abcf', '')
adjacency.insert(19, 'aseg', '')
adjacency.insert(20, 'abts', '')
adjacency.insert(28, 'remark', '')


# adjacency.to_csv('/Users/chenlie/Downloads/alcatel22.csv', encoding='utf8')
sql = 'mysql+pymysql://llr:chenlie@127.0.0.1:3306/mydb?charset=utf8'
engine = create_engine(sql)
# if_exists: replace表示替换重建新表； append表示追加数据
# index=False表示删除索引
adjacency.to_sql('two_two', engine, if_exists='append', index=False)
