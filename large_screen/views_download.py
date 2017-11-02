# -*-coding:utf-8 -*-
from django.http import HttpResponse
from django.http import JsonResponse
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.forms.models import model_to_dict
# import pandas as pd
import datetime
import calendar
# import urllib.request
import json
# import pymysql
import psycopg2
import xlwt


db = psycopg2.connect(database='postgres', user='postgres', password='postgres', host='192.168.61.20', port='5433')
cursor = db.cursor()
# res tuple组成的list


def kpi_now_solved(request):
	"""index3： yellow-今天之前的告警数目； green-昨天之前所有出现的告警 并且 在昨天并未出现 的数目"""
	"""并根据enbid去重"""
	db = psycopg2.connect(database='postgres', user='postgres', password='postgres', host='192.168.61.20', port='5433')
	cursor = db.cursor()
	now = datetime.datetime.now()
	td = datetime.timedelta(days=1)
	yesterday = now - td
	now_0 = now.strftime('%Y-%m-%d')
	now_1 = yesterday.strftime('%Y-%m-%d')

	# 今天之前的不重复的告警enbid
	sql = "SELECT enb_id FROM kpi_ty.pd_to_boco WHERE alarm_pd='TRUE' and start_time<'%s' group by enb_id" % (now_0)
	cursor.execute(sql)
	res = cursor.fetchall()
	enbid_0 = len(res) # yellow-kpi

	# 今天之前累计解决的不重复的告警数
	# 存储昨天之前的告警enbid
	sql_1 = "SELECT enb_id FROM kpi_ty.pd_to_boco WHERE alarm_pd='TRUE' and start_time<'%s' group by enb_id" % (now_1)
	cursor.execute(sql_1)
	res_1 = cursor.fetchall()
	enbid_1 = [] # 存储昨天之前的告警enbid
	if res_1:
		for tup in res_1:
			enbid_1.append(tup[0])

	# 存储昨天的告警enbid
	sql_y = "SELECT enb_id FROM kpi_ty.pd_to_boco WHERE alarm_pd='TRUE' and start_time='%s' group by enb_id" % (now_1)
	cursor.execute(sql_y)
	res_y = cursor.fetchall()
	enbid_y = [] # 存储昨天的告警enbid
	if res_y:
		for tup in res_y:
			enbid_y.append(tup[0])

	# 今天之前（到昨天）累计解决的不重复的告警数
	solved = 0 # green-kpi
	for x in enbid_1:
		if x not in enbid_y:
			solved += 1
	result = {}
	result['num_kpi_before_today'] = enbid_0
	result['solved'] = solved

	return JsonResponse(result)


def kqi_now_solved(request):
	"""index3： yellow-今天之前的告警数目； green-昨天之前所有出现的告警 并且 在昨天并未出现 的数目"""
	"""并根据enbid去重"""
	result = {'num_kqi_before_today': '?', 'solved': '?'}
	return JsonResponse(result)


def hw_fault_now_solved(request):
	"""index3 硬件故障： yellow-今天之前的告警数目； green-昨天之前所有出现的告警 并且 在昨天并未出现 的数目"""
	"""并根据enbid去重"""
	db = psycopg2.connect(database='postgres', user='postgres', password='postgres', host='192.168.61.20', port='5433')
	cursor = db.cursor()

	now = datetime.datetime.now()
	td = datetime.timedelta(days=1)
	yesterday = now - td
	now_0 = now.strftime('%Y-%m-%d')
	now_1 = yesterday.strftime('%Y-%m-%d')

	# 今天之前的不重复的硬件故障告警bs_code
	sql = "SELECT bs_code FROM kpi_ty.kpi_ty_alarm where bs_code is not null and create_time<'%s' group by bs_code" % (now_0)
	print(sql)
	cursor.execute(sql)
	res = cursor.fetchall()
	bs_code_0 = len(res) # yellow-硬件故障

	# 今天之前累计解决的不重复的硬件故障告警数
	# 存储昨天之前的硬件故障告警bs_code
	sql_1 = "SELECT bs_code FROM kpi_ty.kpi_ty_alarm where bs_code is not null and create_time<'%s' group by bs_code" % (now_1)
	print(sql_1)
	cursor.execute(sql_1)
	res_1 = cursor.fetchall()
	bscode_1 = [] # 存储昨天之前的硬件故障告警bs_code
	if res_1:
		for tup in res_1:
			bscode_1.append(tup[0])

	# 存储昨天的硬件故障告警enbid
	sql_y = "SELECT bs_code FROM kpi_ty.kpi_ty_alarm where bs_code is not null and create_time='%s' group by bs_code" % (now_1)
	print(sql_y)
	cursor.execute(sql_y)
	res_y = cursor.fetchall()
	bscode_y = [] # 存储昨天的告警bs_code
	if res_y:
		for tup in res_y:
			bscode_y.append(tup[0])

	# 今天之前（到昨天）累计解决的不重复的告警数
	solved = 0 # green-硬件故障
	for x in bscode_1:
		if x not in bscode_y:
			solved += 1
	result = {}
	result['num_hw_before_today'] = bs_code_0
	result['solved'] = solved

	return JsonResponse(result)


def num_kpi(request):
	db = psycopg2.connect(database='postgres', user='postgres', password='postgres', host='192.168.61.20', port='5433')
	cursor = db.cursor()
	sql = "SELECT enb_id FROM kpi_ty.pd_to_boco WHERE alarm_pd='TRUE' group by enb_id"
	cursor.execute(sql)
	res = cursor.fetchall()
	nkdic = {'first_kpi': len(res)}
	return JsonResponse(nkdic)


def num_volume(request):
	# sql = 'SELECT kr_count FROM kpi_ty.kr_lte_pivot'
	db = psycopg2.connect(database='postgres', user='postgres', password='postgres', host='192.168.61.20', port='5433')
	cursor = db.cursor()
	sql = 'select enb_id from kpi_ty.kr_lte_pivot group by enb_id'
	cursor.execute(sql)
	res = cursor.fetchall()
	num = len(res)
	# for tup in res:
	# 	num += tup[0]
	nvdic = {'first_volume':num}
	return JsonResponse(nvdic)


def num_hardware(request):
	# sql = 'SELECT kr_count FROM kpi_ty.kr_lte_pivot'
	db = psycopg2.connect(database='postgres', user='postgres', password='postgres', host='192.168.61.20', port='5433')
	cursor = db.cursor()
	sql = 'SELECT bs_code FROM kpi_ty.kpi_ty_alarm where bs_code is not null group by bs_code'
	cursor.execute(sql)
	res = cursor.fetchall()
	num = len(res)
	# for tup in res:
	# 	num += tup[0]
	nhdic = {'first_hardware':num}
	return JsonResponse(nhdic)

def num_kqi(request):
	"""no data"""
	nkqidic = {'first_kqi':"?"}
	return JsonResponse(nkqidic)


def firstkpi(request):
	db = psycopg2.connect(database='postgres', user='postgres', password='postgres', host='192.168.61.20', port='5433')
	cursor = db.cursor()

	# 创建excel
	wb = xlwt.Workbook()
	ws = wb.add_sheet('KPI')
	# 写入列名
	title = ['开始时间', '告警内容', '小区名', '分区', '闭环时间', '是否解决']
	for i in range(len(title)):
		ws.write(0, i, title[i])

	# 写入数据
	sql = "SELECT start_time, alarm_type, z_cname, partition, close_time, alarm_boco FROM kpi_ty.pd_to_boco"
	cursor.execute(sql)
	res = cursor.fetchall()
	row = 1
	for tup in res:
		ws.write(row, 0, str(tup[0]))
		ws.write(row, 1, tup[1])
		ws.write(row, 2, tup[2])
		ws.write(row, 3, tup[3])
		ws.write(row, 4, tup[4])
		ws.write(row, 5, tup[5])
		row += 1

	# 保存及下载数据
	date = datetime.datetime.now()
	datestr = date.strftime('%y%m%d')
	response = HttpResponse(content_type='application/vnd.ms-excel')
	response['Content-Disposition'] = 'attachment; filename="KPI_%s.xls"' % (datestr)
	wb.save(response)
	return response


def firstvolume(request):
	db = psycopg2.connect(database='postgres', user='postgres', password='postgres', host='192.168.61.20', port='5433')
	cursor = db.cursor()

	# 创建excel
	wb = xlwt.Workbook()
	ws = wb.add_sheet('volume')
	# 写入列名
	title = ['sdate', 'enb_id', 'z_id', 'z_name', 'branches', 'area', 'vendor', 'abc', 'mis', 'z_type',
			'scene_zdn', 'scene_kbn', 'kr_count', 'kr_cell1', 'kr_cell2', 'kr_cell3',
			'kr_cell4', 'kr_cell5', 'kr_cell6', 'prb_cell1', 'prb_cell2', 'prb_cell3',
			'prb_cell4', 'prb_cell5', 'prb_cell6', 'gprs_cell1', 'gprs_cell2', 'gprs_cell3',
			'gprs_cell4', 'gprs_cell5', 'gprs_cell6', 'rrc_cell1', 'rrc_cell2', 'rrc_cell3',
			'rrc_cell4', 'rrc_cell5', 'rrc_cell6', 'cqi_cell1', 'cqi_cell2', 'cqi_cell3',
			'cqi_cell4', 'cqi_cell5', 'cqi_cell6', 'avg_prb_cell1', 'avg_prb_cell2',
			'avg_prb_cell3', 'avg_prb_cell4', 'avg_prb_cell5', 'avg_prb_cell6']
	for i in range(len(title)):
		ws.write(0, i, title[i])

	# 写入数据
	sql = 'SELECT * FROM kpi_ty.kr_lte_pivot'
	cursor.execute(sql)
	res = cursor.fetchall()
	row = 1
	for tup in res:
		for i in range(49):
			if i == 0:
				ws.write(row, 0, str(tup[0]))
			else:
				ws.write(row, i, tup[1])
		# ws.write(row, 0, str(tup[0]))
		# ws.write(row, 1, tup[1])
		# ws.write(row, 2, tup[2])
		# ws.write(row, 3, tup[3])
		# ws.write(row, 4, tup[4])
		# ws.write(row, 5, tup[5])
		# ws.write(row, 6, tup[6])
		# ws.write(row, 7, tup[7])
		# ws.write(row, 8, tup[8])
		# ws.write(row, 9, tup[9])
		# ws.write(row, 10, tup[10])
		# ws.write(row, 11, tup[11])
		# ws.write(row, 12, tup[12])
		# ws.write(row, 13, tup[13])
		# ws.write(row, 14, tup[14])
		# ws.write(row, 15, tup[15])
		# ws.write(row, 16, tup[16])
		# ws.write(row, 17, tup[17])
		# ws.write(row, 18, tup[18])
		# ws.write(row, 19, tup[19])
		# ws.write(row, 20, tup[20])
		# ws.write(row, 21, tup[21])
		# ws.write(row, 22, tup[22])
		# ws.write(row, 23, tup[23])
		# ws.write(row, 24, tup[24])
		# ws.write(row, 25, tup[25])
		# ws.write(row, 26, tup[26])
		# ws.write(row, 27, tup[27])
		# ws.write(row, 28, tup[28])
		# ws.write(row, 29, tup[29])
		# ws.write(row, 30, tup[30])
		# ws.write(row, 31, tup[31])
		# ws.write(row, 32, tup[32])
		# ws.write(row, 33, tup[33])
		# ws.write(row, 34, tup[34])
		# ws.write(row, 35, tup[35])
		# ws.write(row, 36, tup[36])
		# ws.write(row, 37, tup[37])
		# ws.write(row, 38, tup[38])
		# ws.write(row, 39, tup[39])
		# ws.write(row, 40, tup[40])
		# ws.write(row, 41, tup[41])
		# ws.write(row, 42, tup[42])
		# ws.write(row, 43, tup[43])
		# ws.write(row, 44, tup[44])
		# ws.write(row, 45, tup[45])
		# ws.write(row, 46, tup[46])
		# ws.write(row, 47, tup[47])
		# ws.write(row, 48, tup[48])
		row += 1

	# 保存及下载数据
	date = datetime.datetime.now()
	datestr = date.strftime('%y%m%d')
	response = HttpResponse(content_type='application/vnd.ms-excel')
	response['Content-Disposition'] = 'attachment; filename="kuorong_list_%s.xls"' % (datestr)
	wb.save(response)
	return response


def firsthardware(request):
	db = psycopg2.connect(database='postgres', user='postgres', password='postgres', host='192.168.61.20', port='5433')
	cursor = db.cursor()

	# 创建excel
	wb = xlwt.Workbook()
	ws = wb.add_sheet('hardware')
	# 写入列名
	title = ['alarm_id', 'alarm_title', 'alarm_text', 'alarm_time', 'alarm_level', 'alarm_status',
			'ne_type', 'ne_name', 'bs_code', 'clear_time', 'create_time']
	for i in range(len(title)):
		ws.write(0, i, title[i])

	# 写入数据
	sql = 'SELECT * FROM kpi_ty.kpi_ty_alarm'
	cursor.execute(sql)
	res = cursor.fetchall()
	row = 1
	for tup in res:
		ws.write(row, 0, tup[0])
		ws.write(row, 1, tup[1])
		ws.write(row, 2, tup[2])
		ws.write(row, 3, str(tup[3]))
		ws.write(row, 4, tup[4])
		ws.write(row, 5, tup[5])
		ws.write(row, 6, tup[6])
		ws.write(row, 7, tup[7])
		ws.write(row, 8, tup[8])
		ws.write(row, 9, tup[9])
		ws.write(row, 10, str(tup[10]))
		row += 1

	# 保存及下载数据
	date = datetime.datetime.now()
	datestr = date.strftime('%y%m%d')
	response = HttpResponse(content_type='application/vnd.ms-excel')
	response['Content-Disposition'] = 'attachment; filename="hardware_fault_list_%s.xls"' % (datestr)
	wb.save(response)
	return response
