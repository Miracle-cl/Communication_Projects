import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime


now = datetime.now()
date = now.strftime('%Y-%m-%d')
supplier = '爱立信'
path = '/home/baili/Documents/import/'
# path = '/Users/chenlie/Downloads/ericsson'

def sixteen_to_ten(s):
	# 16进制转为10进制，s为string
	s = str(int(s,16))
	if len(s) == 1:
		s = '0' + s
	return s


def bsic_xx(s):
	# 补全bsic
	if len(s) == 1:
		s = '0'	+ s
	return s




rlnrp_path = path + 'ericsson' + '/RLNRP.csv'
rlnrp = pd.read_csv(rlnrp_path, encoding='utf8')
rlnrp = rlnrp.drop(['BSC','DIR','CAND','CS','KHYST','KOFFSETP','KOFFSETN','LHYST','LOFFSETP',
					'LOFFSETN','TRHYST','TROFFSETP','AWOFFSET','BQOFFSET','HIHYST','LOHYST',
					'OFFSETP','OFFSETN','BQOFFSETAFR','BQOFFSETAWB','TROFFSETN'], axis=1)
rlnrp = rlnrp.drop_duplicates(subset=['CELL','CELLR'])

rxtcp_path = path + 'ericsson' + '/RXTCP_RXOTG.csv'
rxtcp = pd.read_csv(rxtcp_path, encoding='utf8')
rxtcp = rxtcp.drop(['BSC','CHGR'], axis=1)
rxtcp = rxtcp.drop_duplicates(subset='CELL')

result = pd.merge(rlnrp, rxtcp, how='left', on='CELL')

rxtcp_adj = rxtcp.rename(index=str, columns={"MO": "abcf", "CELL": "CELLR"})
result = pd.merge(result, rxtcp_adj, how='left', on='CELLR')
result = result.rename(index=str, columns={"MO": "bcf"})


rldep_path = path + 'ericsson' + '/RLDEP.csv'
rldep = pd.read_csv(rldep_path, encoding='utf8')
rldep = rldep.drop(['AGBLK','MFRMS','IRC','TYPE','BCCHTYPE','FNOFFSET','XRANGE','CSYSTYPE',
					'CELLIND','RAC','RIMNACC','GAN','DFI','BSIC'], axis=1)
rldep.lac = rldep.CGI.map(lambda x: x.split('-')[2])
rldep.ci = rldep.CGI.map(lambda x: x.split('-')[3])
rldep.insert(2, 'lac', rldep.lac)
rldep.insert(3, 'ci', rldep.ci)
rldep = rldep.drop('CGI', axis=1)
rldep = rldep.rename(index=str, columns={"BSC": "bsc", "BCCHNO": "bcch", "NCC": "ncc", "BCC": "bcc"})
rldep.bcch = rldep.bcch.astype(str)
rldep.ncc = rldep.ncc.astype(str)
rldep.bcc = rldep.bcc.astype(str)

rldepext_path = path + 'ericsson' + '/RLDEP_EXT.csv'
rldepext = pd.read_csv(rldepext_path, encoding='utf8')
rldepext = rldepext.drop(['AGBLK','MFRMS','IRC','TYPE','BCCHTYPE','FNOFFSET','XRANGE','CSYSTYPE',
					'CELLIND','RAC','RIMNACC','GAN','DFI'], axis=1)
rldepext = rldepext.rename(index=str, columns={"BSC": "bsc", "BSIC": "bsic", "BCCHNO": "bcch"})
# 去除空值
rldepext = rldepext.dropna(axis=0, how='any')
rldepext.bsic = rldepext.bsic.map(int).astype(str)
rldepext.bcch = rldepext.bcch.map(int).astype(str)
# rldepext.bsic = rldepext.bsic.astype(str)
rldepext.bsic = rldepext.bsic.map(bsic_xx)
rldepext.ncc = rldepext.bsic.map(lambda x: x[0])
rldepext.bcc = rldepext.bsic.map(lambda x: x[-1])
rldepext.insert(5, 'ncc', rldepext.ncc)
rldepext.insert(6, 'bcc', rldepext.bcc)
rldepext.lac = rldepext.CGI.map(lambda x: x.split('-')[2])
rldepext.ci = rldepext.CGI.map(lambda x: x.split('-')[3])
rldepext.insert(2, 'lac', rldepext.lac)
rldepext.insert(3, 'ci', rldepext.ci)
rldepext = rldepext.drop(['CGI','bsic'], axis=1)

rldep = rldep.append(rldepext, ignore_index=True)
rldep.insert(4, 'lac_ci', rldep.lac+'_'+rldep.ci)
#去重 : 去重之后 english_name -17189; lac-ci -17169
rldep = rldep.drop_duplicates(subset='CELL')
# bsc 转为正确格式
rldep.bsc = rldep.bsc.map(lambda x: x[:3]+sixteen_to_ten(x[3]))

rldep_local = rldep.drop(['bcch','ncc','bcc'],axis=1)
rldep_adj = rldep.rename(index=str, columns={"bsc": "absc", "CELL": "CELLR", "lac": "alac",
						"ci": "aci", "lac_ci": "adj_lac_ci", "bcch": "freq"})

result = pd.merge(result, rldep_local, how='left', on='CELL')
result = pd.merge(result, rldep_adj, how='left', on='CELLR')
result = result.rename(index=str, columns={"CELL": "english_name", "CELLR": "adj_english_name"})

result = result.loc[:,['bsc','bcf','english_name','lac','ci','lac_ci','absc','abcf','adj_english_name','alac','aci','adj_lac_ci','freq','ncc','bcc']]
result.seq = range(len(result))
result.insert(0,'seq',result.seq)
result.insert(1,'date',date)
result.insert(2,'supplier',supplier)
result.insert(3,'omc','')
result.insert(4,'idref','')
result.insert(7,'seg','')
result.insert(8,'bts','')
result.insert(10,'mcc','460')
result.insert(11,'mnc','00')
result.insert(15,'aindex','')
result.insert(16,'aidref','')
result.insert(19,'aseg','')
result.insert(20,'abts','')
result.insert(28,'remark','')

sql = 'mysql+pymysql://llr:chenlie@127.0.0.1:3306/mydb?charset=utf8'
engine = create_engine(sql)
# if_exists: replace表示替换重建新表； append表示追加数据
# index=False表示删除索引
result.to_sql('two_two', engine, if_exists='replace', index=False)
