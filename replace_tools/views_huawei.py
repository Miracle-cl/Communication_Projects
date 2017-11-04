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


def huawei22_update(request):
	db = rp_support.get_db()
	cursor = db.cursor()

	"""huawei2-2 指令"""
	order_update = []

	"""替换站指令"""
	#读取替换计划中的信息
	sql_replaceplan = "select * from replace_plan where state = '替换站'"
	cursor.execute(sql_replaceplan)
	res_replaceplan = cursor.fetchall()
	if res_replaceplan:
		# replaceplan = {}
		for tup in res_replaceplan:
			old_lac = tup[3]
			old_ci = tup[4]
			new_lac = tup[6]
			new_ci = tup[7]
			# old_lac_ci = tup[3] + '_' + tup[4]
			# #old_english_name = tup[5]
			# new_lac_ci = tup[6] + '_' + tup[7]
			new_bsc = tup[9]
			new_seg = tup[10]

			#针对目标站为替换站
			#使用前提：原站的数据已更新，即数据库更新过
			sql2 = "select * from two_two where supplier='华为' and alac='%s' and aci='%s'" % (old_lac, old_ci)
			cursor.execute(sql2)
			res2 = cursor.fetchall()
			if res2:
				for tup in res2:
					bsc = tup[5]
					remark = '-'
					sql3 = "select seg, nbcellname from hw_gext2gcell where bsc='%s' and lac='%s' and ci='%s'" % (bsc, old_lac, old_ci)
					cursor.execute(sql3)
					res = cursor.fetchall()
					# print(res)

					if res:
						ext2gcellid = res[0][0]
						ext2gcellname = res[0][1]
						update3 = 'MOD GEXT2GCELL: IDTYPE=BYID, EXT2GCELLID=%s, BSCN2GCELLNAME="%s", LAC=%s, CI=%s;' % (ext2gcellid, ext2gcellname, new_lac, new_ci)
						# update3 = 'MOD GEXT2GCELL: EXT2GCELLID=%s, LAC=%s, CI=%s;' % (cell_index, new_lac, new_ci)
						order_update.append([bsc, update3, remark])


	"""倒回站指令"""
	#读取替换计划中的信息
	sql_replaceplan = "select * from replace_plan where state = '倒回站'"
	cursor.execute(sql_replaceplan)
	res_replaceplan = cursor.fetchall()
	if res_replaceplan:
		# replaceplan = {}
		for tup in res_replaceplan:
			old_lac = tup[3]
			old_ci = tup[4]
			new_lac = tup[6]
			new_ci = tup[7]
			new_bsc = tup[9]
			new_seg = tup[10]

			#针对目标站为替换站
			#使用前提：原站的数据已更新，即数据库更新过
			sql2 = "select * from two_two where supplier='华为' and alac='%s' and aci='%s'" % (new_lac, new_ci)
			cursor.execute(sql2)
			res2 = cursor.fetchall()
			if res2:
				for tup in res2:
					bsc = tup[5]
					remark = '-'
					sql3 = "select seg, nbcellname from hw_gext2gcell where bsc='%s' and lac='%s' and ci='%s'" % (bsc, new_lac, new_ci)
					cursor.execute(sql3)
					res = cursor.fetchall()
					if res[0]:
						ext2gcellid = res[0][0]
						ext2gcellname = res[0][1]
						update3 = 'MOD GEXT2GCELL: EXT2GCELLID=%s, EXT2GCELLNAME="%s", LAC=%s, CI=%s;' % (ext2gcellid, ext2gcellname, old_lac, old_ci)
						# update3 = 'MOD GEXT2GCELL: EXT2GCELLID=%d, LAC=%s, CI=%s;' % (cell_index, old_lac, old_ci)
						order_update.append([bsc, update3, remark])


	"""分裂站指令"""
	sql_replaceplan = "select * from replace_plan where state = '分裂站'"
	cursor.execute(sql_replaceplan)
	res_replaceplan = cursor.fetchall()
	if res_replaceplan:
		for tup in res_replaceplan:
			old_lac = tup[3]
			old_ci = tup[4]
			new_lac = tup[6]
			new_ci = tup[7]
			new_bsc = tup[9]
			new_seg = tup[10]
			new_freq = tup[13]
			new_ncc = tup[14]
			new_bcc = tup[15]


			#newci_16 = hex(int(new_ci)).upper()[2:]
			if int(new_freq) < 125:
				ext2gcellname = 'EXT_G' + new_ci
			else:
				ext2gcellname = 'EXT_D' + new_ci

			#针对目标站为替换站
			#使用前提：原站的数据已更新，即数据库更新过
			sql2 = "select * from two_two where supplier='华为' and alac='%s' and aci='%s'" % (old_lac, old_ci)
			cursor.execute(sql2)
			res2 = cursor.fetchall()
			if res2:
				for tup in res2:
					bsc = tup[5]
					lac = tup[12]
					ci = tup[13]
					remark = '-'
					#sql3 = "select seg from hw_gext2gcell where bsc='%s'" % (bsc)
					#cursor.execute(sql3)
					#seglist = []
					#res3 = cursor.fetchall()
					# 读取同一个bsc下的所有索引号，然后从1-20000之间找到一个未使用的作为新索引
					#for segtup in res3:
					#	seglist.append( segtup[0] )
					#for i in range(1, 20000):
					#	if str(i) not in seglist:
					#		ext2gcellid = str(i)
					#		break
					#ext2gcellname = ext2gcellname + bsc[3:5] + newci_16

					#sql4 = "select cell_name from hwswap_list where newbsc='%s' and newlac='%s' and newci='%s'" % (bsc, lac, ci)
					#cursor.execute(sql4)
					#res4 = cursor.fetchall()
					#if res4:
					#	new_cell_name = res4[0][0]
					#else:
					#	new_cell_name = ''

					update3 = 'ADD GEXT2GCELL:EXT2GCELLNAME="%s", MCC="460", MNC="00", LAC=%s, CI=%s, BCCH=%s, NCC=%s, BCC=%s;' % (ext2gcellname, new_lac, new_ci, new_freq, new_ncc, new_bcc)
					#update3 = 'ADD GEXT2GCELL: EXT2GCELLID=%s, EXT2GCELLNAME="%s", MCC="460", MNC="00", LAC=%s, CI=%s, BCCH=%s, NCC=%s, BCC=%s, LAYER=3;' % (ext2gcellid, ext2gcellname, new_lac, new_ci, new_freq, new_ncc, new_bcc)
					if [bsc, update3, remark] not in order_update:
						order_update.append([bsc, update3, remark])
					update3 = 'ADD G2GNCELL:IDTYPE=BYCGI, SRCMCC="460", SRCMNC="00", SRCLAC=%s, SRCCI=%s, NBRMCC="460", NBRMNC="00", NBRLAC=%s, NBRCI=%s, NCELLTYPE=HANDOVERNCELL, SRCHOCTRLSWITCH=HOALGORITHM1;' % (lac, ci, new_lac, new_ci)
					#update3 = 'ADD G2GNCELL: IDTYPE=BYNAME, SRC2GNCELLNAME="%s", NBR2GNCELLNAME="%s", NCELLTYPE=HANDOVERNCELL, SRCHOCTRLSWITCH=HOALGORITHM1;' % (new_cell_name, ext2gcellname)
					order_update.append([bsc, update3, remark])



	cursor.close()
	db.close()

	if order_update:
		now = datetime.now()
		date = now.strftime('%y%m%d')
		title = ['bsc', 'command', 'remark']
		response = HttpResponse(content_type='text/csv')
		response['Content-Disposition'] = 'attachment; filename="huawei22_%s.csv"' % date
		writer = csv.writer(response)
		writer.writerow(title)
		writer.writerows(order_update)
		return response
	else:
		return HttpResponse("华为2G-2G没有数据需要进行更新")


def huawei32_update(request):
	#数据库信息
	db = rp_support.get_db()
	cursor = db.cursor()

	"""华为3-2指令"""
	order1_del = []
	order2_del = []
	def1_order = []
	def2_order = []

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

			sql1 = "select * from three_two where supplier='华为' and lac_two='%s' and ci_two='%s'" % (old_lac, old_ci)
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

			sql1 = "select * from three_two where supplier='华为' and lac_two='%s' and ci_two='%s'" % (new_lac, new_ci)
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

			sql1 = "select * from three_two where supplier='华为' and lac_two='%s' and ci_two='%s'" % (old_lac, old_ci)
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
				# ncc = tup[9]
				# bcc = tup[10]
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
		response['Content-Disposition'] = 'attachment; filename="huawei32_%s.txt"' % date
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
		return HttpResponse("华为3G-2G没有数据需要进行更新")


def huawei42_update(request):
	#数据库信息
	db = rp_support.get_db()
	cursor = db.cursor()

	"""华为4-2指令"""
	order1_del = []
	order2_del = []
	def1_order = []
	def2_order = []

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
			new_cellname = tup[11]
			key = old_lac_ci
			replaceplan[key] = [new_lac_ci, new_cellname]

		#根据replaceplan中的信息读取two_two表中的相关信息，并生成列表
		for key, value in replaceplan.items():
			old_lac_ci = key
			old_lac = key[:4]
			old_ci = key[5:]
			new_lac_ci = value[0]
			new_lac = value[0][:4]
			new_ci = value[0][5:]
			new_cellname = value[1]

			sql1 = "select * from four_two where supplier='华为' and lac='%s' and ci='%s'" % (old_lac, old_ci)
			cursor.execute(sql1)
			res1 = cursor.fetchall()
			for tup in res1:
				name = tup[5]
				lte_xqbs = tup[6]
				lac = tup[10]
				ci = tup[11]
				blindhopriority = tup[19]
				english_name_four = tup[7]
				gsm_xqmc = tup[16]
				remark = '-'
				order1 = 'RMV GERANNCELL:LOCALCELLID=%s,MCC="460",MNC="00",LAC=%s,GERANCELLID=%s;{%s}\n' % (lte_xqbs, lac, ci, name)
				def1 = 'ADD GERANNCELL:LOCALCELLID=%s,MCC="460",MNC="00",LAC=%s,GERANCELLID=%s,BLINDHOPRIORITY=%s,LOCALCELLNAME="%s",NEIGHBOURCELLNAME="%s";{%s}\n' % (lte_xqbs, new_lac, new_ci, blindhopriority, english_name_four, new_cellname, name)
				order1_del.append(order1)
				def1_order.append(def1)

			sql2 = "select * from four_out where lac='%s' and ci='%s'" % (old_lac, old_ci)
			cursor.execute(sql2)
			res2 = cursor.fetchall()
			for tup in res2:
				name = tup[1] #RNC
				ci = tup[4]
				lac = tup[5]
				bcch = tup[10]
				ncc = tup[11]
				bcc = tup[12]
				cell_name = tup[14]
				remark = '-'
				order2 = 'RMV GERANEXTERNALCELL:MCC="460",MNC="00",GERANCELLID=%s,LAC=%s;{%s}\n' % (ci, lac, name)
				def2 = 'ADD GERANEXTERNALCELL:MCC="460",MNC="00",GERANCELLID=%s,LAC=%s,RACCFGIND=NOT_CFG,BANDINDICATOR=GSM_dcs1800,GERANARFCN=%s,NETWORKCOLOURCODE=%s,BASESTATIONCOLOURCODE=%s,CELLNAME="%s";{%s}\n' % (new_ci, new_lac, bcch, ncc, bcc, new_cellname, name)
				order2_del.append(order2)
				def2_order.append(def2)


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
			new_cellname = tup[11]
			key = old_lac_ci
			replaceplan[key] = [new_lac_ci, new_cellname]

		#根据replaceplan中的信息读取two_two表中的相关信息，并生成列表
		for key, value in replaceplan.items():
			old_lac_ci = key
			old_lac = key[:4]
			old_ci = key[5:]
			new_lac_ci = value[0]
			new_lac = value[0][:4]
			new_ci = value[0][5:]
			new_cellname = value[1]

			sql1 = "select * from four_two where supplier='华为' and lac='%s' and ci='%s'" % (new_lac, new_ci)
			cursor.execute(sql1)
			res1 = cursor.fetchall()
			for tup in res1:
				name = tup[5]
				lte_xqbs = tup[6]
				lac = tup[10]
				ci = tup[11]
				blindhopriority = tup[19]
				english_name_four = tup[7]
				gsm_xqmc = tup[16]
				remark = '-'
				order1 = 'RMV GERANNCELL:LOCALCELLID=%s,MCC="460",MNC="00",LAC=%s,GERANCELLID=%s;{%s}\n' % (lte_xqbs, lac, ci, name)
				def1 = 'ADD GERANNCELL:LOCALCELLID=%s,MCC="460",MNC="00",LAC=%s,GERANCELLID=%s,BLINDHOPRIORITY=%s,LOCALCELLNAME="%s",NEIGHBOURCELLNAME="%s";{%s}\n' % (lte_xqbs, old_lac, old_ci, blindhopriority, english_name_four, new_cellname, name)
				order1_del.append(order1)
				def1_order.append(def1)

			sql2 = "select * from four_out where lac='%s' and ci='%s'" % (new_lac, new_ci)
			cursor.execute(sql2)
			res2 = cursor.fetchall()
			for tup in res2:
				name = tup[1] #RNC
				ci = tup[4]
				lac = tup[5]
				bcch = tup[10]
				ncc = tup[11]
				bcc = tup[12]
				cell_name = tup[14]
				remark = '-'
				order2 = 'RMV GERANEXTERNALCELL:MCC="460",MNC="00",GERANCELLID=%s,LAC=%s;{%s}\n' % (ci, lac, name)
				def2 = 'ADD GERANEXTERNALCELL:MCC="460",MNC="00",GERANCELLID=%s,LAC=%s,RACCFGIND=NOT_CFG,BANDINDICATOR=GSM_dcs1800,GERANARFCN=%s,NETWORKCOLOURCODE=%s,BASESTATIONCOLOURCODE=%s,CELLNAME="%s";{%s}\n' % (old_ci, old_lac, bcch, ncc, bcc, new_cellname, name)
				order2_del.append(order2)
				def2_order.append(def2)


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
			new_cellname = tup[11]
			new_freq = tup[13]
			new_ncc = tup[14]
			new_bcc = tup[15]

			key = old_lac_ci
			replaceplan[key] = [new_lac_ci, new_cellname, new_freq, new_ncc, new_bcc]

		#根据replaceplan中的信息读取two_two表中的相关信息，并生成列表
		for key, value in replaceplan.items():
			old_lac_ci = key
			old_lac = key[:4]
			old_ci = key[5:]
			new_lac_ci = value[0]
			new_lac = value[0][:4]
			new_ci = value[0][5:]
			new_cellname = value[1]
			new_freq = value[2]
			new_ncc = value[3]
			new_bcc = value[4]

			sql1 = "select * from four_two where supplier='华为' and lac='%s' and ci='%s'" % (old_lac, old_ci)
			cursor.execute(sql1)
			res1 = cursor.fetchall()
			for tup in res1:
				name = tup[5]
				lte_xqbs = tup[6]
				lac = tup[10]
				ci = tup[11]
				blindhopriority = tup[19]
				english_name_four = tup[7]
				gsm_xqmc = tup[16]
				remark = '-'
				# order1 = 'RMV GERANNCELL:LOCALCELLID=%s,MCC="460",MNC="00",LAC=%s,GERANCELLID=%s;{%s}\n' % (lte_xqbs, lac, ci, name)
				def1 = 'ADD GERANNCELL:LOCALCELLID=%s,MCC="460",MNC="00",LAC=%s,GERANCELLID=%s,BLINDHOPRIORITY=%s,LOCALCELLNAME="%s",NEIGHBOURCELLNAME="%s";{%s}\n' % (new_ci, new_lac, new_ci, blindhopriority, english_name_four, new_cellname, name)
				# order1_del.append(order1)
				def1_order.append(def1)

			sql2 = "select * from four_out where lac='%s' and ci='%s'" % (old_lac, old_ci)
			cursor.execute(sql2)
			res2 = cursor.fetchall()
			for tup in res2:
				name = tup[1]
				ci = tup[4]
				lac = tup[5]
				# bcch = tup[10]
				# ncc = tup[11]
				# bcc = tup[12]
				cell_name = tup[14]
				remark = '-'
				# order2 = 'RMV GERANEXTERNALCELL:MCC="460",MNC="00",GERANCELLID=%s,LAC=%s;{%s}\n' % (ci, lac, name)
				def2 = 'ADD GERANEXTERNALCELL:MCC="460",MNC="00",GERANCELLID=%s,LAC=%s,RACCFGIND=NOT_CFG,BANDINDICATOR=GSM_dcs1800,GERANARFCN=%s,NETWORKCOLOURCODE=%s,BASESTATIONCOLOURCODE=%s,CELLNAME="%s";{%s}\n' % (new_ci, new_lac, new_freq, new_ncc, new_bcc, new_cellname, name)
				# order2_del.append(order2)
				def2_order.append(def2)

	cursor.close()
	db.close()

	if order1_del or order2_del or def2_order or def1_order:
		now = datetime.now()
		date = now.strftime('%y%m%d')
		#title = ['command','remark']
		response = HttpResponse(content_type='text/plain')
		response['Content-Disposition'] = 'attachment; filename="huawei42_%s.txt"' % date
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
		return HttpResponse("华为4G-2G没有数据需要进行更新")
