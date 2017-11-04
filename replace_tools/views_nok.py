from django.shortcuts import render
from django import forms
from django.http import HttpResponse
from django.http import JsonResponse
from django.http import HttpResponseRedirect
#from django.core.servers.basehttp import FileWrapper
from replace import rp_support
from wsgiref.util import FileWrapper
from datetime import datetime
import csv



def nokia22_update(request):
	#数据库信息
	db = rp_support.get_db()
	cursor = db.cursor()

	"""nokia2-2 指令"""
	"""替换站指令"""
	order_update = []
	#读取替换计划中的信息
	sql_replaceplan = "select * from replace_plan where state = '替换站'"
	cursor.execute(sql_replaceplan)
	res_replaceplan = cursor.fetchall()
	if res_replaceplan:
		replaceplan = {}
		for tup in res_replaceplan:
			old_lac_ci = tup[3] + '_' + tup[4]
			#old_english_name = tup[5]
			new_lac_ci = tup[6] + '_' + tup[7]
			new_bsc = tup[9]
			new_seg = tup[10]
			key = old_lac_ci
			replaceplan[key] = [new_lac_ci, new_bsc, new_seg]

		#根据replaceplan中的信息读取two_two表中的相关信息，并生成列表
		for key, value in replaceplan.items():
			old_lac_ci = key
			old_lac = key[:4]
			old_ci = key[5:]
			new_lac_ci = value[0]
			new_lac = value[0][:4]
			new_ci = value[0][5:]
			new_bsc =value[1]
			new_seg =value[2]
			#针对本站为替换站，目标站在或不在替换计划中
			#20170913 - 如果是倒回站，slq1要修改为
			#sql1 = "select * from two_two where lac='%s' and ci='%s'" % (new_lac, new_ci)
			sql1 = "select * from two_two where lac='%s' and ci='%s'" % (old_lac, old_ci)
			cursor.execute(sql1)
			res1 = cursor.fetchall()
			for tup in res1:
				#bsc = tup[5]
				alac = tup[22]
				aci = tup[23]
				adj_lac_ci = alac + '_' + aci
				cell = tup[9]
				cellr = tup[21]
				freq = tup[25]
				ncc = tup[26]
				bcc = tup[27]
				remark = '-'
				#bsic = tup[26] + tup[27]
				if adj_lac_ci not in replaceplan:
					if int(freq) < 125:
						update1 = 'ZEAC:SEG=%s::LAC=%s,CI=%s:NCC=%s,BCC=%s,FREQ=%s:PMRG=6,LMRG=3,QMRG=0,SL=-95,DRT=-85,RAC=1;' % (new_seg, alac, aci, ncc, bcc, freq)
					else:
						update1 = 'ZEAC:SEG=%s::LAC=%s,CI=%s:NCC=%s,BCC=%s,FREQ=%s:PMRG=3,LMRG=3,QMRG=0,SL=-95,DRT=-85,RAC=1;' % (new_seg, alac, aci, ncc, bcc, freq)
					order_update.append([new_bsc, update1, remark])
				else: #elif adj_lac_ci in replaceplan: 使用前提：数据库及时更新过
					sql1_1 = "select * from replace_plan where old_lac='%s' and old_ci='%s'" % (alac, aci)
					cursor.execute(sql1_1)
					res1_1 = cursor.fetchall()
					for tup in res1_1:
						new_alac = tup[6]
						new_aci = tup[7]
						if int(freq) < 125:
							update2 = 'ZEAC:SEG=%s::LAC=%s,CI=%s:NCC=%s,BCC=%s,FREQ=%s:PMRG=6,LMRG=3,QMRG=0,SL=-95,DRT=-85,RAC=1;' % (new_seg, new_alac, new_aci, ncc, bcc, freq)
						else:
							update2 = 'ZEAC:SEG=%s::LAC=%s,CI=%s:NCC=%s,BCC=%s,FREQ=%s:PMRG=3,LMRG=3,QMRG=0,SL=-95,DRT=-85,RAC=1;' % (new_seg, new_alac, new_aci, ncc, bcc, freq)
						if [new_bsc, update2, remark] not in order_update:
							order_update.append([new_bsc, update2, remark])
			#针对目标站为替换站
			#使用前提：原站的数据已更新，即数据库更新过
			sql2 = "select * from two_two where supplier='诺基亚' and alac='%s' and aci='%s'" % (old_lac, old_ci)
			cursor.execute(sql2)
			res2 = cursor.fetchall()
			for tup in res2:
				bsc = tup[5]
				seg = tup[7]
				alac = tup[22]
				aci = tup[23]
				remark = '-'
				update3 = 'ZEAM:SEG=%s::LAC=%s,CI=%s:NEWLAC=%s,NEWCI=%s;' % (seg, alac, aci, new_lac, new_ci)
				order_update.append([bsc, update3, remark])

	"""倒回站指令"""
	sql_back = "select * from replace_plan where state = '倒回站'"
	cursor.execute(sql_back)
	res_back = cursor.fetchall()
	if res_back:
		back = {}
		for tup in res_back:
			back_oldlacci = tup[3] + '_' + tup[4]
			#old_english_name = tup[5]
			back_newlacci = tup[6] + '_' + tup[7]
			back_new_bsc = tup[9]
			back_new_seg = tup[10]
			key = back_oldlacci
			back[key] = [back_newlacci, back_new_bsc, back_new_seg]

		#根据replaceplan中的信息读取two_two表中的相关信息，并生成列表
		for key, value in back.items():
			back_oldlacci = key
			bold_lac = key[:4]
			bold_ci = key[5:]
			bnew_lac_ci = value[0]
			bnew_lac = value[0][:4]
			bnew_ci = value[0][5:]
			bnew_bsc =value[1]
			bnew_seg =value[2]


			#针对目标站为替换站
			#使用前提：原站的数据已更新，即数据库更新过
			sql2 = "select * from two_two where supplier='诺基亚' and alac='%s' and aci='%s'" % (bnew_lac, bnew_ci)
			cursor.execute(sql2)
			res2 = cursor.fetchall()
			for tup in res2:
				bsc = tup[5]
				seg = tup[7]
				alac = tup[22]
				aci = tup[23]
				remark = 'revert'
				update3 = 'ZEAM:SEG=%s::LAC=%s,CI=%s:NEWLAC=%s,NEWCI=%s;' % (seg, alac, aci, bold_lac, bold_ci)
				order_update.append([bsc, update3, remark])

			sql2 = "select * from two_two where supplier='诺基亚' and lac='%s' and ci='%s'" % (bnew_lac, bnew_ci)
			cursor.execute(sql2)
			res2 = cursor.fetchall()
			for tup in res2:
				bsc = tup[5]
				seg = tup[7]
				alac = tup[22]
				aci = tup[23]
				remark = 'revert'
				update3 = 'ZEAD:SEG=%s::LAC=%s,CI=%s;' % (seg, alac, aci)
				order_update.append([bsc, update3, remark])


	"""分裂站指令"""
	#读取替换计划中的信息
	sql_replaceplan = "select * from replace_plan where state = '分裂站'"
	cursor.execute(sql_replaceplan)
	res_replaceplan = cursor.fetchall()
	if res_replaceplan:
		replaceplan = {}
		for tup in res_replaceplan:
			old_lac_ci = tup[3] + '_' + tup[4]
			#old_english_name = tup[5]
			new_lac_ci = tup[6] + '_' + tup[7]
			new_bsc = tup[9]
			new_seg = tup[10]
			freq = tup[13]
			ncc = tup[14]
			bcc = tup[15]
			key = old_lac_ci
			replaceplan[key] = [new_lac_ci, new_bsc, new_seg, freq, ncc, bcc]

		#根据replaceplan中的信息读取two_two表中的相关信息，并生成列表
		for key, value in replaceplan.items():
			old_lac_ci = key
			old_lac = key[:4]
			old_ci = key[5:]
			new_lac_ci = value[0]
			new_lac = value[0][:4]
			new_ci = value[0][5:]
			new_bsc =value[1]
			new_seg =value[2]
			new_freq = value[3]
			new_ncc = value[4]
			new_bcc = value[5]
			#针对本站为替换站，目标站在或不在替换计划中
			#20170913 - 如果是倒回站，slq1要修改为
			#sql1 = "select * from two_two where lac='%s' and ci='%s'" % (new_lac, new_ci)
			sql1 = "select * from two_two where lac='%s' and ci='%s'" % (old_lac, old_ci)
			cursor.execute(sql1)
			res1 = cursor.fetchall()
			for tup in res1:
				#bsc = tup[5]
				alac = tup[22]
				aci = tup[23]
				adj_lac_ci = alac + '_' + aci
				cell = tup[9]
				cellr = tup[21]
				freq = tup[25]
				ncc = tup[26]
				bcc = tup[27]
				remark = '-'
				#bsic = tup[26] + tup[27]
				if adj_lac_ci not in replaceplan:
					if int(freq) < 125:
						update1 = 'ZEAC:SEG=%s::LAC=%s,CI=%s:NCC=%s,BCC=%s,FREQ=%s:PMRG=6,LMRG=3,QMRG=0,SL=-95,DRT=-85,RAC=1;' % (new_seg, alac, aci, ncc, bcc, freq)
					else:
						update1 = 'ZEAC:SEG=%s::LAC=%s,CI=%s:NCC=%s,BCC=%s,FREQ=%s:PMRG=3,LMRG=3,QMRG=0,SL=-95,DRT=-85,RAC=1;' % (new_seg, alac, aci, ncc, bcc, freq)
					order_update.append([new_bsc, update1, remark])
				else: #elif adj_lac_ci in replaceplan: 使用前提：数据库及时更新过
					sql1_1 = "select * from replace_plan where old_lac='%s' and old_ci='%s'" % (alac, aci)
					cursor.execute(sql1_1)
					res1_1 = cursor.fetchall()
					for tup in res1_1:
						new_alac = tup[6]
						new_aci = tup[7]
						if int(freq) < 125:
							update2 = 'ZEAC:SEG=%s::LAC=%s,CI=%s:NCC=%s,BCC=%s,FREQ=%s:PMRG=6,LMRG=3,QMRG=0,SL=-95,DRT=-85,RAC=1;' % (new_seg, new_alac, new_aci, ncc, bcc, freq)
						else:
							update2 = 'ZEAC:SEG=%s::LAC=%s,CI=%s:NCC=%s,BCC=%s,FREQ=%s:PMRG=3,LMRG=3,QMRG=0,SL=-95,DRT=-85,RAC=1;' % (new_seg, new_alac, new_aci, ncc, bcc, freq)
						if [new_bsc, update2, remark] not in order_update:
							order_update.append([new_bsc, update2, remark])
			#针对目标站为替换站
			#使用前提：原站的数据已更新，即数据库更新过
			sql2 = "select * from two_two where supplier='诺基亚' and alac='%s' and aci='%s'" % (old_lac, old_ci)
			cursor.execute(sql2)
			res2 = cursor.fetchall()
			for tup in res2:
				bsc = tup[5]
				seg = tup[7]
				# alac = tup[22]
				# aci = tup[23]
				remark = '-'
				if int(new_freq) < 125:
					update3 = 'ZEAC:SEG=%s::LAC=%s,CI=%s:NCC=%s,BCC=%s,FREQ=%s:PMRG=6,LMRG=3,QMRG=0,SL=-95,DRT=-85,RAC=1;' % (seg, new_lac, new_ci, new_ncc, new_bcc, new_freq)
				else:
					update3 = 'ZEAC:SEG=%s::LAC=%s,CI=%s:NCC=%s,BCC=%s,FREQ=%s:PMRG=3,LMRG=3,QMRG=0,SL=-95,DRT=-85,RAC=1;' % (seg, new_lac, new_ci, new_ncc, new_bcc, new_freq)
				order_update.append([bsc, update3, remark])

	cursor.close()
	db.close()

	if order_update:
		now = datetime.now()
		date = now.strftime('%y%m%d')
		title = ['bsc', 'command', 'remark']
		response = HttpResponse(content_type='text/csv')
		response['Content-Disposition'] = 'attachment; filename="nokia22_%s.csv"' % date
		writer = csv.writer(response)
		writer.writerow(title)
		writer.writerows(order_update)
		return response
	else:
		return HttpResponse("诺基亚2G-2G没有数据需要进行更新")


def nokia24_update(request):
	#数据库信息
	db = rp_support.get_db()
	cursor = db.cursor()

	"""诺基亚2-4指令"""
	order_add = []

	"""替换站指令"""
	# 读取替换计划中的信息
	sql_replaceplan = "select * from replace_plan where state = '替换站'"
	cursor.execute(sql_replaceplan)
	res_replaceplan = cursor.fetchall()
	if res_replaceplan:
		replaceplan = {}
		for tup in res_replaceplan:
			old_lac_ci = tup[3] + '_' + tup[4]
			new_lac_ci = tup[6] + '_' + tup[7]
			new_english_name = tup[8]
			new_bsc = tup[9]
			new_seg = tup[10]
			key = old_lac_ci
			replaceplan[key] = [new_lac_ci, new_bsc, new_seg, new_english_name]


		for key, value in replaceplan.items():
			old_lac_ci = key
			old_lac = key[:4]
			old_ci = key[5:]
			new_lac_ci = value[0]
			new_lac = value[0][:4]
			new_ci = value[0][5:]
			new_bsc = value[1]
			new_seg = value[2]

			#本站在替换计划中
			sql = "select * from two_four where lac='%s' and ci='%s'" % (old_lac, old_ci)
			cursor.execute(sql)
			res = cursor.fetchall()
			for tup in res:
				#bsc = tup[3]
				freq = tup[17]
				remark = 'replace cell'
				#增加指令
				if freq == '37900' or freq == '38098' or freq == '39946' or freq == '40144' or freq == '40936' or freq == '1252' or freq == '1275' or freq == '1302' or freq == '3683' or freq == '38103':
					add = 'ZEAN:SEG=%s::TAC=%s:FREQ=%s,LTECP=4,LTERUT=8,LTERLT=6,LTERXM=-124,LTEBCG=0,LTEPS=0,LTEMB=5;' % (new_seg, new_lac, freq)
				elif freq == '38400' or freq == '38404' or freq == '38494' or freq == '38500':
					add = 'ZEAN:SEG=%s::TAC=%s:FREQ=%s,LTECP=3,LTERUT=8,LTERLT=6,LTERXM=-124,LTEBCG=0,LTEPS=0,LTEMB=5;' % (new_seg, new_lac, freq)
				elif freq == '38544':
					add = 'ZEAN:SEG=%s::TAC=%s:FREQ=%s,LTECP=3,LTERUT=8,LTERLT=6,LTERXM=-124,LTEBCG=0,LTEPS=0,LTEMB=3;' % (new_seg, new_lac, freq)
				elif freq == '39148' or freq == '38950' or freq == '39292':
					add = 'ZEAN:SEG=%s::TAC=%s:FREQ=%s,LTECP=7,LTERUT=8,LTERLT=6,LTERXM=-124,LTEBCG=0,LTEPS=0,LTEMB=5;' % (new_seg, new_lac, freq)
				else:
					add = 'ZEAN:SEG=%s::TAC=%s:FREQ=%s,LTECP=3,LTERUT=8,LTERLT=6,LTERXM=-124,LTEBCG=0,LTEPS=0,LTEMB=5;' % (new_seg, new_lac, freq)
				order_add.append([new_bsc, add, remark])


	"""分裂站指令"""
	# 读取替换计划中的信息
	sql_replaceplan = "select * from replace_plan where state = '分裂站'"
	cursor.execute(sql_replaceplan)
	res_replaceplan = cursor.fetchall()
	if res_replaceplan:
		replaceplan = {}
		for tup in res_replaceplan:
			old_lac_ci = tup[3] + '_' + tup[4]
			new_lac_ci = tup[6] + '_' + tup[7]
			new_english_name = tup[8]
			new_bsc = tup[9]
			new_seg = tup[10]
			key = old_lac_ci
			replaceplan[key] = [new_lac_ci, new_bsc, new_seg, new_english_name]


		for key, value in replaceplan.items():
			old_lac_ci = key
			old_lac = key[:4]
			old_ci = key[5:]
			new_lac_ci = value[0]
			new_lac = value[0][:4]
			new_ci = value[0][5:]
			new_bsc = value[1]
			new_seg = value[2]

			#本站在替换计划中
			sql = "select * from two_four where lac='%s' and ci='%s'" % (old_lac, old_ci)
			cursor.execute(sql)
			res = cursor.fetchall()
			for tup in res:
				#bsc = tup[3]
				freq = tup[17]
				remark = 'New split cell'
				#增加指令
				if freq == '37900' or freq == '38098' or freq == '39946' or freq == '40144' or freq == '40936' or freq == '1252' or freq == '1275' or freq == '1302' or freq == '3683' or freq == '38103':
					add = 'ZEAN:SEG=%s::TAC=%s:FREQ=%s,LTECP=4,LTERUT=8,LTERLT=6,LTERXM=-124,LTEBCG=0,LTEPS=0,LTEMB=5;' % (new_seg, new_lac, freq)
				elif freq == '38400' or freq == '38404' or freq == '38494' or freq == '38500':
					add = 'ZEAN:SEG=%s::TAC=%s:FREQ=%s,LTECP=3,LTERUT=8,LTERLT=6,LTERXM=-124,LTEBCG=0,LTEPS=0,LTEMB=5;' % (new_seg, new_lac, freq)
				elif freq == '38544':
					add = 'ZEAN:SEG=%s::TAC=%s:FREQ=%s,LTECP=3,LTERUT=8,LTERLT=6,LTERXM=-124,LTEBCG=0,LTEPS=0,LTEMB=3;' % (new_seg, new_lac, freq)
				elif freq == '39148' or freq == '38950' or freq == '39292':
					add = 'ZEAN:SEG=%s::TAC=%s:FREQ=%s,LTECP=7,LTERUT=8,LTERLT=6,LTERXM=-124,LTEBCG=0,LTEPS=0,LTEMB=5;' % (new_seg, new_lac, freq)
				else:
					add = 'ZEAN:SEG=%s::TAC=%s:FREQ=%s,LTECP=3,LTERUT=8,LTERLT=6,LTERXM=-124,LTEBCG=0,LTEPS=0,LTEMB=5;' % (new_seg, new_lac, freq)
				order_add.append([new_bsc, add, remark])

	cursor.close()
	db.close()

	if order_add:
		#下载2-4替换站的指令
		now = datetime.now()
		date = now.strftime('%y%m%d')
		title = ['bsc', 'command', 'remark']
		response = HttpResponse(content_type='text/csv')
		response['Content-Disposition'] = 'attachment; filename="nokia24_%s.csv"' % date
		writer = csv.writer(response)
		writer.writerow(title)
		writer.writerows(order_add)
		return response
	else:
		return HttpResponse("诺基亚2G—4G没有数据需要进行更新")


def nokia32_update(request):
	#数据库信息
	db = rp_support.get_db()
	cursor = db.cursor()

	"""诺基亚3-2指令"""
	order1_del = []
	order2_del = []
	def1_order = []
	def2_order = []
	#读取替换计划中的信息
	"""替换站指令"""
	sql_replaceplan = "select * from replace_plan where state = '替换站'"
	cursor.execute(sql_replaceplan)
	res_replaceplan = cursor.fetchall()
	if res_replaceplan:
		replaceplan = {}
		for tup in res_replaceplan:
			old_lac_ci = tup[3] + '_' + tup[4]
			#old_english_name = tup[5]
			new_lac_ci = tup[6] + '_' + tup[7]
			new_bsc = tup[9]
			new_seg = tup[10]
			# new_freq = tup[13]
			key = old_lac_ci
			replaceplan[key] = [new_lac_ci, new_bsc, new_seg]

		#根据replaceplan中的信息读取two_two表中的相关信息，并生成列表
		for key, value in replaceplan.items():
			old_lac_ci = key
			old_lac = key[:4]
			old_ci = key[5:]
			new_lac_ci = value[0]
			new_lac = value[0][:4]
			new_ci = value[0][5:]
			new_bsc =value[1]
			new_seg =value[2]

			sql1 = "select * from three_two where supplier='诺西' and lac_two='%s' and ci_two='%s'" % (old_lac, old_ci)
			cursor.execute(sql1)
			res1 = cursor.fetchall()
			for tup in res1:
				rnc_three = tup[3]
				lac_three = tup[5]
				ci_three = tup[4]
				order1 = "RMV TGSMNCELL:CELLID=%s,GSMCELLID=%s;{%s}\n" % (ci_three, old_ci, rnc_three)
				def1 = "ADD TGSMNCELL:CELLID=%s,GSMCELLID=%s,CELLINDIVIDALOFFSET=0,TPENALTYHCSRESELECT=NOT_USED,TEMPOFFSET1=T03,NCELLTYPE=FALSE;{%s}\n" % (ci_three, new_ci, rnc_three)
				order1_del.append(order1)
				def1_order.append(def1)

			sql2 = "select * from three_out where lac='%s' and gsm_xqbs='%s'" % (old_lac, old_ci)
			cursor.execute(sql2)
			res2 = cursor.fetchall()
			for tup in res2:
				name = tup[1] #RNC
				gsm_xqbs = tup[3]
				lac = tup[8]
				ncc = tup[9]
				bcc = tup[10]
				rac = tup[11] #lyqm
				racc = tup[12] #lyqsm
				bcch = tup[14]
				order2 = "RMV TGSMCELL:GSMCELLID=%s;{%s}\n" % (gsm_xqbs, name)
				def2 = 'ADD TGSMCELL:GSMCELLID=%s,CI=%s,PLMNMCC="460",PLMNMNC="00",LAC=%s,NCC=%s,BCC=%s,RAC=%s,RACC=%s,BANDINDICATOR=DCS_1800_BAND_USED,BCCHARFCN=%s,GSMCELLTYPEIND=GPRS,NCMODE=NC_MODE_I,SUPPRIMFLAG=NOTSUPPORT,SUPPPSHOFLAG=NOTSUPPORT,USEOFHCS=NOT_USED,BSCID=1;{%s}\n' % (new_ci, new_ci, new_lac, ncc, bcc, rac, racc, bcch, name)
				order2_del.append(order2)
				def2_order.append(def2)

	"""倒回站指令"""
	sql_replaceplan = "select * from replace_plan where state = '倒回站'"
	cursor.execute(sql_replaceplan)
	res_replaceplan = cursor.fetchall()
	if res_replaceplan:
		replaceplan = {}
		for tup in res_replaceplan:
			old_lac_ci = tup[3] + '_' + tup[4]
			#old_english_name = tup[5]
			new_lac_ci = tup[6] + '_' + tup[7]
			new_bsc = tup[9]
			new_seg = tup[10]
			key = old_lac_ci
			replaceplan[key] = [new_lac_ci, new_bsc, new_seg]

		#根据replaceplan中的信息读取two_two表中的相关信息，并生成列表
		for key, value in replaceplan.items():
			old_lac_ci = key
			old_lac = key[:4]
			old_ci = key[5:]
			new_lac_ci = value[0]
			new_lac = value[0][:4]
			new_ci = value[0][5:]
			new_bsc =value[1]
			new_seg =value[2]

			sql1 = "select * from three_two where supplier='诺西' and lac_two='%s' and ci_two='%s'" % (new_lac, new_ci)
			cursor.execute(sql1)
			res1 = cursor.fetchall()
			for tup in res1:
				rnc_three = tup[3]
				lac_three = tup[5]
				ci_three = tup[4]
				order1 = "RMV TGSMNCELL:CELLID=%s,GSMCELLID=%s;{%s}\n" % (ci_three, new_ci, rnc_three)
				def1 = "ADD TGSMNCELL:CELLID=%s,GSMCELLID=%s,CELLINDIVIDALOFFSET=0,TPENALTYHCSRESELECT=NOT_USED,TEMPOFFSET1=T03,NCELLTYPE=FALSE;{%s}\n" % (ci_three, old_ci, rnc_three)
				order1_del.append(order1)
				def1_order.append(def1)

			sql2 = "select * from three_out where lac='%s' and gsm_xqbs='%s'" % (new_lac, new_ci)
			cursor.execute(sql2)
			res2 = cursor.fetchall()
			for tup in res2:
				name = tup[1] #RNC
				gsm_xqbs = tup[3]
				lac = tup[8]
				ncc = tup[9]
				bcc = tup[10]
				rac = tup[11] #lyqm
				racc = tup[12] #lyqsm
				bcch = tup[14]
				order2 = "RMV TGSMCELL:GSMCELLID=%s;{%s}\n" % (gsm_xqbs, name)
				def2 = 'ADD TGSMCELL:GSMCELLID=%s,CI=%s,PLMNMCC="460",PLMNMNC="00",LAC=%s,NCC=%s,BCC=%s,RAC=%s,RACC=%s,BANDINDICATOR=DCS_1800_BAND_USED,BCCHARFCN=%s,GSMCELLTYPEIND=GPRS,NCMODE=NC_MODE_I,SUPPRIMFLAG=NOTSUPPORT,SUPPPSHOFLAG=NOTSUPPORT,USEOFHCS=NOT_USED,BSCID=1;{%s}\n' % (old_ci, old_ci, old_lac, ncc, bcc, rac, racc, bcch, name)
				order2_del.append(order2)
				def2_order.append(def2)


	"""分裂站指令"""
	sql_replaceplan = "select * from replace_plan where state = '分裂站'"
	cursor.execute(sql_replaceplan)
	res_replaceplan = cursor.fetchall()
	if res_replaceplan:
		replaceplan = {}
		for tup in res_replaceplan:
			old_lac_ci = tup[3] + '_' + tup[4]
			#old_english_name = tup[5]
			new_lac_ci = tup[6] + '_' + tup[7]
			new_bsc = tup[9]
			new_seg = tup[10]
			new_freq = tup[13]
			new_ncc = tup[14]
			new_bcc = tup[15]
			key = old_lac_ci
			replaceplan[key] = [new_lac_ci, new_bsc, new_seg, new_freq, new_ncc, new_bcc]

		#根据replaceplan中的信息读取two_two表中的相关信息，并生成列表
		for key, value in replaceplan.items():
			old_lac_ci = key
			old_lac = key[:4]
			old_ci = key[5:]
			new_lac_ci = value[0]
			new_lac = value[0][:4]
			new_ci = value[0][5:]
			new_bsc = value[1]
			new_seg = value[2]
			new_freq = value[3]
			new_ncc = value[4]
			new_bcc = value[5]

			sql1 = "select * from three_two where supplier='诺西' and lac_two='%s' and ci_two='%s'" % (old_lac, old_ci)
			cursor.execute(sql1)
			res1 = cursor.fetchall()
			for tup in res1:
				rnc_three = tup[3]
				lac_three = tup[5]
				ci_three = tup[4]
				# order1 = "RMV TGSMNCELL:CELLID=%s,GSMCELLID=%s;{%s}\n" % (ci_three, old_ci, rnc_three)
				def1 = "ADD TGSMNCELL:CELLID=%s,GSMCELLID=%s,CELLINDIVIDALOFFSET=0,TPENALTYHCSRESELECT=NOT_USED,TEMPOFFSET1=T03,NCELLTYPE=FALSE;{%s}\n" % (ci_three, new_ci, rnc_three)
				# order1_del.append(order1)
				def1_order.append(def1)

			sql2 = "select * from three_out where lac='%s' and gsm_xqbs='%s'" % (old_lac, old_ci)
			cursor.execute(sql2)
			res2 = cursor.fetchall()
			for tup in res2:
				name = tup[1] #RNC
				gsm_xqbs = tup[3]
				lac = tup[8]
				ncc = tup[9]
				bcc = tup[10]
				rac = tup[11] #lyqm
				racc = tup[12] #lyqsm
				# bcch = tup[14]
				# order2 = "RMV TGSMCELL:GSMCELLID=%s;{%s}\n" % (gsm_xqbs, name)
				def2 = 'ADD TGSMCELL:GSMCELLID=%s,CI=%s,PLMNMCC="460",PLMNMNC="00",LAC=%s,NCC=%s,BCC=%s,RAC=%s,RACC=%s,BANDINDICATOR=DCS_1800_BAND_USED,BCCHARFCN=%s,GSMCELLTYPEIND=GPRS,NCMODE=NC_MODE_I,SUPPRIMFLAG=NOTSUPPORT,SUPPPSHOFLAG=NOTSUPPORT,USEOFHCS=NOT_USED,BSCID=1;{%s}\n' % (new_ci, new_ci, new_lac, new_ncc, new_bcc, rac, racc, new_freq, name)
				# order2_del.append(order2)
				def2_order.append(def2)

	cursor.close()
	db.close()

	if order1_del or order2_del or def2_order or def1_order:
		now = datetime.now()
		date = now.strftime('%y%m%d')
		response = HttpResponse(content_type='text/plain')
		response['Content-Disposition'] = 'attachment; filename="nokia32_%s.txt"' % date
		for line in order1_del:
			response.write(line)
		for line in order2_del:
			response.write(line)
		for line in def2_order:
			response.write(line)
		for line in def1_order:
			response.write(line)
		return response
	else:
		return HttpResponse("诺基亚3G-2G没有数据需要进行更新")

def nokia42_update(request):
	#数据库信息
	db = rp_support.get_db()
	cursor = db.cursor()

	"""诺基亚4-2指令"""
	order_update = []

	"""替换站指令"""
	#读取替换计划中的信息
	sql_replaceplan = "select * from replace_plan where state = '替换站'"
	cursor.execute(sql_replaceplan)
	res_replaceplan = cursor.fetchall()
	if res_replaceplan:
		replaceplan = {}
		for tup in res_replaceplan:
			old_lac_ci = tup[3] + '_' + tup[4]
			#old_english_name = tup[5]
			new_lac_ci = tup[6] + '_' + tup[7]
			new_bsc = tup[9]
			new_seg = tup[10]
			key = old_lac_ci
			replaceplan[key] = [new_lac_ci, new_bsc, new_seg]

		#根据replaceplan中的信息读取two_two表中的相关信息，并生成列表
		for key, value in replaceplan.items():
			old_lac_ci = key
			old_lac = key[:4]
			old_ci = key[5:]
			new_lac_ci = value[0]
			new_lac = value[0][:4]
			new_ci = value[0][5:]
			new_bsc =value[1]
			new_seg =value[2]

			sql1 = "select * from four_two where supplier='诺基亚' and lac='%s' and ci='%s'" % (old_lac, old_ci)
			cursor.execute(sql1)
			res1 = cursor.fetchall()
			for tup in res1:
				ecgi = tup[4]
				order = '<managedObject class="EXGCE" version="1.0" distName="PLMN-PLMN/EXCCG-1/EXGCE-%s" operation="update"><p name="cellIdentity">%s</p ><p name="lac">%s</p ><p name="name">460 00 %s %s</p ></managedObject>\n' % (ecgi, new_ci, new_lac, new_lac, new_ci)
				if order not in order_update:
					order_update.append(order)

	"""倒回站指令"""
	#读取替换计划中的信息
	sql_replaceplan = "select * from replace_plan where state = '倒回站'"
	cursor.execute(sql_replaceplan)
	res_replaceplan = cursor.fetchall()
	if res_replaceplan:
		replaceplan = {}
		for tup in res_replaceplan:
			old_lac_ci = tup[3] + '_' + tup[4]
			#old_english_name = tup[5]
			new_lac_ci = tup[6] + '_' + tup[7]
			new_bsc = tup[9]
			new_seg = tup[10]
			key = old_lac_ci
			replaceplan[key] = [new_lac_ci, new_bsc, new_seg]

		#根据replaceplan中的信息读取two_two表中的相关信息，并生成列表
		for key, value in replaceplan.items():
			old_lac_ci = key
			old_lac = key[:4]
			old_ci = key[5:]
			new_lac_ci = value[0]
			new_lac = value[0][:4]
			new_ci = value[0][5:]
			new_bsc =value[1]
			new_seg =value[2]

			sql1 = "select * from four_two where supplier='诺基亚' and lac='%s' and ci='%s'" % (new_lac, new_ci)
			cursor.execute(sql1)
			res1 = cursor.fetchall()
			for tup in res1:
				ecgi = tup[4]
				order = '<managedObject class="EXGCE" version="1.0" distName="PLMN-PLMN/EXCCG-1/EXGCE-%s" operation="update"><p name="cellIdentity">%s</p ><p name="name">460 00 %s %s</p ></managedObject>\n' % (ecgi, old_ci, old_lac, old_ci)
				if order not in order_update:
					order_update.append(order)


	"""分裂站指令"""
	#读取替换计划中的信息
	# ecgi_list = []
	# sql_ecgi = "select ecgi from four_two where supplier='诺基亚' group by ecgi"
	# cursor.execute(sql_ecgi)
	# res_ecgi = cursor.fetchall()
	# for tup in res_ecgi:
	# 	ecgi_list.append( tup[0] )

	sql_replaceplan = "select * from replace_plan where state = '分裂站'"
	cursor.execute(sql_replaceplan)
	res_replaceplan = cursor.fetchall()
	if res_replaceplan:
		for tup in res_replaceplan:
			old_lac = tup[3]
			old_ci = tup[4]
			# old_lac_ci = tup[3] + '_' + tup[4]
			new_lac = tup[6]
			new_ci = tup[7]
			# new_lac_ci = tup[6] + '_' + tup[7]
			new_bsc = tup[9]
			new_seg = tup[10]
			new_freq = tup[13]
			new_ncc = tup[14]
			new_bcc = tup[15]

			sql1 = "select enbid from four_two where supplier='诺基亚' and lac='%s' and ci='%s'" % (old_lac, old_ci)
			cursor.execute(sql1)
			res1 = cursor.fetchall()
			for tup in res1:
				enbid = tup[0]

				lnadjg_list = []
				sql3 = "select lnadjg_id from nokia_lnadjg where enbid='%s'" % enbid
				cursor.execute(sql3)
				res3 = cursor.fetchall()
				for tup3 in res3:
					lnadjg_list.append( tup3[0] )

				sql2 = "select * from nokia_lnadjg where enbid='%s'" % enbid
				cursor.execute(sql2)
				res2 = cursor.fetchall()
				for tup2 in res2:
					version = tup2[2]
					for i in range(1,200):
						if str(i) not in lnadjg_list:
							lnadjg = str(i)
							break
					order = '<managedObject class="LNADJG" version="%s" distName="PLMN-PLMN/MRBTS-%s/LNBTS-%s/LNADJG-%s" operation="create"><p name="mcc">460</p ><p name="mnc">00</p ><p name="arfcnValueGeran">%s</p ><p name="networkColourCode">%s</p ><p name="basestationColourCode">%s</p ><p name="gTargetLac">%s</p ><p name="gTargetCi">%s</p ><p name="gTargetRac">1</p ></managedObject>\n' % (version, enbid, enbid, lnadjg, new_freq, new_ncc, new_bcc, new_lac, new_ci)
					# if order not in order_update:
					order_update.append(order)



	cursor.close()
	db.close()

	if order_update:
		now = datetime.now()
		date = now.strftime('%y%m%d')
		response = HttpResponse(content_type='application/rss+xml')
		response['Content-Disposition'] = 'attachment; filename="nokia42_%s.xml"' % date

		first = '<?xml version="1.0" encoding="UTF-8"?>\n'
		second = "<!DOCTYPE raml SYSTEM 'raml20.dtd'>\n"
		third = '<raml version="2.0" xmlns="raml20.xsd">\n'
		fourth = '  <cmData type="plan" scope="all" name="New Plan (9999)" id="PlanConfiguration( 9999 )">\n'
		#order_update
		fifth = '  </cmData>\n'
		sixth = '</raml>\n'

		response.write(first)
		response.write(second)
		response.write(third)
		response.write(fourth)
		for line in order_update:
			response.write(line)
		response.write(fifth)
		response.write(sixth)

		return response
	else:
		return HttpResponse("诺基亚4G-2G没有数据需要进行更新")
