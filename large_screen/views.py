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
import csv

def timeall():
	"""生成最近3天的一个时间序列，每段时间间隔2小时"""
	now = datetime.datetime.now()
	td = datetime.timedelta(days=3)
	delt = datetime.timedelta(hours=2)
	time_1 = now - td
	time_1 = datetime.datetime(time_1.year,time_1.month,time_1.day,0,0,0)
	time_all = []
	for i in range(36):
		time_2 = time_1.strftime('%Y-%m-%d %H:%M:%S')
		time_all.append(time_2)
		time_1 += delt
	return time_all

def sevendates():
	"""生成最近7天的时间序列"""
	lastFriday = datetime.date.today()
	oneday = datetime.timedelta(days=1)
	sevendays = datetime.timedelta(days=7)
	while lastFriday.weekday() != calendar.FRIDAY:
		lastFriday -= oneday
	s7cycles = []
	for i in range(7):
		s7cycles.append(lastFriday.strftime('%Y-%m-%d'))
		lastFriday -= sevendays
	return s7cycles


# 导入postgres数据库
db = psycopg2.connect(database='postgres', user='postgres', password='postgres', host='192.168.61.20', port='5433')
cursor = db.cursor()
# res tuple组成的list

time_all = timeall()
s7cycles = sevendates()

def index(request):
	return render(request, 'index.html')

def other(request):
	"""return the 3rd html"""
	return render(request, 'index3.html')

def fourth_html(request):
	"""return the 4th html"""
	return render(request, 'index4.html')

def map(request):
	return render(request, 'map/map1.html')

def shange(request):
	return render(request, 'map/map2.html')

def three_map(request):
	return render(request, 'map/map3.html')

def four_map_v(request):
	return render(request, 'map/map4.html')


def dubiao_all_rate(request):
	"""整体对标领先率"""
	db = psycopg2.connect(database='postgres', user='postgres', password='postgres', host='192.168.61.20', port='5433')
	cursor = db.cursor()
	# 统计最近一个时间的对标情况
	sql = "SELECT duibiao, count(duibiao) FROM ui.duibiao_490 WHERE sdate in (SELECT max(sdate) FROM ui.duibiao_490) group by duibiao"
	cursor.execute(sql)
	res = cursor.fetchall()
	dic = {"lingxian": 0, "xiangdang": 0, "luohou": 0, "all": 0, "lingxian_rate": 0}
	if res:
		for tup in res:
			if tup[0] == '领先':
				dic['lingxian'] += tup[1]
			elif tup[0] == '相当':
				dic['xiangdang'] += tup[1]
			elif tup[0] == '落后':
				dic['luohou'] += tup[1]
	dic['all'] = dic['lingxian'] + dic['xiangdang'] + dic['luohou']
	if dic['all']:
		dic['lingxian_rate'] = 100 * dic['lingxian'] / dic['all']
	dic['num_of_duibiao'] = str(dic['lingxian']) + '/' + str(dic['all'])
	return JsonResponse(dic)


def gprs_dl_all(request):
	"""最近的忙时的流量"""
	# 获取最近的忙时 busy_time
	db = psycopg2.connect(database='postgres', user='postgres', password='postgres', host='192.168.61.20', port='5433')
	cursor = db.cursor()
	sql_busy = "select max(start_time) from kpi_ty.kpi_ty_lte"
	cursor.execute(sql_busy)
	res_busy = cursor.fetchall()
	date = str(res_busy[0][0]).split()[0]
	hour = int(str(res_busy[0][0]).split()[1].split(':')[0])
	if hour >= 20:
		busy_time = date + ' 20:00:00'
	elif hour >= 10:
		busy_time = date + ' 10:00:00'
	else:
		date1 = datetime.datetime.strptime(date, "%Y-%m-%d")
		td = datetime.timedelta(days=1)
		oneday_before = (date1 - td).strftime("%Y-%m-%d")
		busy_time = oneday_before + ' 20:00:00'

	# 获取忙时 busy_time的流量
	sql = "SELECT start_time, gprs_dl FROM kpi_ty.kpi_ty_lte where start_time='%s'" % (busy_time)
	print(sql)
	cursor.execute(sql)
	res = cursor.fetchall()
	total_gprs_dl = 0.0
	for tup in res:
		total_gprs_dl += float(tup[1])
	dic = {}
	dic['gprs'] = int(total_gprs_dl)
	return JsonResponse(dic)


def seven_rate(request):
	"""七大场景达标率"""
	db = psycopg2.connect(database='postgres', user='postgres', password='postgres', host='192.168.61.20', port='5433')
	cursor = db.cursor()

	# 找到场景分类和达标数目、总数目
	sql = 'SELECT sdate, key_scene_name, "覆盖良好栅格", "不需解决低采样栅格" FROM osm.lte_scene_shanghai where sdate in (select max(sdate) from osm.lte_scene_shanghai)'
	cursor.execute(sql)
	res = cursor.fetchall()
	eight = {} # {'高铁':[ok, all]}
	for tup in res:
		scene_name = tup[1]
		rate = tup[2] + tup[3]
		try:
			sqla = "SELECT cj_name, cj_type FROM ui.cell_scene_lte where cj_name='%s' limit 1" % (scene_name)
			cursor.execute(sqla)
			resa = cursor.fetchall()
			scene_a = resa[0][1]
			if scene_a not in eight:
				if rate > 0.9:
					eight[scene_a] = [1, 1]
				else:
					eight[scene_a] = [0, 1]
			else:
				if rate > 0.9:
					eight[scene_a][0] += 1
				eight[scene_a][1] += 1
		except:
			pass

	# eight = {'交通枢纽类': [1, 6], '高铁': [1, 6], '地铁': [1, 6], '商业类': [10, 45], '文体类': [14, 34], '教育类': [9, 48], '医疗类': [10, 18], '政府机关类': [1, 2]}
	# 统计三高一地和整体的达标数目和总数目
	listall = [0, 0]
	three_one = [0, 0]
	for k,v in eight.items():
		listall[0] += v[0]
		listall[1] += v[1]
		if k in ('高铁', '高架', '高速', '地铁'):
			three_one[0] += v[0]
			three_one[1] += v[1]

	eight['三高一地'] = three_one
	try:
		eight.pop('高铁')
	except:
		pass
	try:
		eight.pop('高架')
	except:
		pass
	try:
		eight.pop('高速')
	except:
		pass
	try:
		eight.pop('地铁')
	except:
		pass
	# print(eight)
	eight['整体'] = listall
	# 输出格式转换
	eightlist = []
	for k,v in eight.items():
		dic = {}
		if v[1] == 0:
			dic['name'] = k
			dic['rate'] = 0
		else:
			dic['name'] = k
			dic['rate'] = round(100 * v[0] / v[1], 2)
		eightlist.append(dic)
	eightlist[-1]['num_of_dabian'] = str(listall[0]) + '/' + str(listall[1]) # add num of zhengti dabiaolv
	seven_dict = {'aa': eightlist}
	# print(seven_dict)
	cursor.close()
	db.close()

	# seven_dict = {'aa':[{'rate':98,'name':'三高一地'}, {'rate':95,'name':'交通枢纽类'}, {'rate':99,'name':'医疗类'},
	# 	{'rate':100,'name':'商业类'}, {'rate':90,'name':'政府机关类'}, {'rate':80,'name':'教育类'}, {'rate':85,'name':'文体类'}]}
	return JsonResponse(seven_dict)


def six_cycles(request):
	"""统计重点场景的达标率"""
	db = psycopg2.connect(database='postgres', user='postgres', password='postgres', host='192.168.61.20', port='5433')
	cursor = db.cursor()
	date_list = []
	sql_date = "SELECT sdate FROM osm.lte_scene_shanghai group by sdate order by sdate"
	cursor.execute(sql_date)
	res_date = cursor.fetchall()
	for tup in res_date:
		date_list.append(str(tup[0]).split()[0])

	if len(date_list) >= 6:
		# sql = '''SELECT sdate, key_scene_name, "覆盖良好栅格", "不需解决低采样栅格" FROM osm.lte_scene_shanghai where sdate in ('%s', '%s', '%s', '%s', '%s', '%s') order by sdate''' % (s7cycles[-2],s7cycles[-3],s7cycles[-4],s7cycles[-5],s7cycles[-6],s7cycles[-7])
		sql = '''SELECT sdate, key_scene_name, "覆盖良好栅格", "不需解决低采样栅格" FROM osm.lte_scene_shanghai where sdate in ('%s', '%s', '%s', '%s', '%s', '%s') order by sdate''' % (date_list[-6],date_list[-5],date_list[-4],date_list[-3],date_list[-2],date_list[-1])
		cursor.execute(sql)
		res = cursor.fetchall()
		zd = []
		timelist = []
		countok = 0
		countnotok = 0
		for tup in res:
			dateflag = tup[0]
			if dateflag not in timelist:
				if countok != 0:
					rate1 = round(100 * countok / (countok + countnotok), 2)
					dic = {'time':date1, 'ratezd':rate1}
					zd.append(dic)
				timelist.append(dateflag)
				date1 = str(dateflag).split()[0]
				countok = 0
				countnotok = 0
				if tup[2]+tup[3] > 0.9:
					countok += 1
				else:
					countnotok += 1
			else:
				if tup[2]+tup[3] > 0.9:
					countok += 1
				else:
					countnotok += 1
		rate1 = round(100 * countok / (countok + countnotok), 2)
		dic = {'time':str(dateflag).split()[0], 'ratezd':rate1}
		zd.append(dic)

		# 统计口碑场景的达标率
		# sqla = '''SELECT sdate, key_scene_name, koubei_scene, "覆盖良好栅格", "不需解决低采样栅格" FROM osm.lte_scene_shanghai where sdate in ('%s', '%s', '%s', '%s', '%s', '%s') and koubei_scene=1 order by sdate''' % (s7cycles[-2],s7cycles[-3],s7cycles[-4],s7cycles[-5],s7cycles[-6],s7cycles[-7])
		sqla = '''SELECT sdate, key_scene_name, koubei_scene, "覆盖良好栅格", "不需解决低采样栅格" FROM osm.lte_scene_shanghai where sdate in ('%s', '%s', '%s', '%s', '%s', '%s') and koubei_scene=1 order by sdate''' % (date_list[-6],date_list[-5],date_list[-4],date_list[-3],date_list[-2],date_list[-1])
		cursor.execute(sqla)
		resa = cursor.fetchall()
		koubei = []
		timelist2 = []
		countok = 0
		countnotok = 0
		for tup in resa:
			dateflag = tup[0]
			if dateflag not in timelist2:
				if countok != 0:
					rate2 = round(100 * countok / (countok + countnotok), 2)
					dic2 = {'time':date2, 'ratekb':rate2}
					koubei.append(dic2)
				timelist2.append(dateflag)
				date2 = str(dateflag).split()[0]
				countok = 0
				countnotok = 0
				if tup[3]+tup[4] > 0.9:
					countok += 1
				else:
					countnotok += 1
			else:
				if tup[3]+tup[4] > 0.9:
					countok += 1
				else:
					countnotok += 1
		rate2 = round(100 * countok / (countok + countnotok), 2)
		dic2 = {'time':str(dateflag).split()[0], 'ratekb':rate2}
		koubei.append(dic2)

		# 合并重点场景和口碑场景的达标率
		result = []
		length = len(zd)
		for i in range(length):
			d = {}
			if zd[i]['time'] == koubei[i]['time']:
				d['time'] = zd[i]['time']
				d['ratezd'] = zd[i]['ratezd']
				d['ratekb'] = koubei[i]['ratekb']
				result.append(d)

	six_dict = {'six_c':result}
	cursor.close()
	db.close()

	# six_dict = {'six_c':[{'ratezd':100, 'ratekb':90, 'time':'周期一'}, {'ratezd':100, 'ratekb':90, 'time':'周期二'}, {'ratezd':100, 'ratekb':90, 'time':'周期三'}]}
	return JsonResponse(six_dict)


def name_of_scene(request):
	"""统计场景名称以及对应的位置信息和对标率, 并按照达标与否进行分类"""
	db = psycopg2.connect(database='postgres', user='postgres', password='postgres', host='192.168.61.20', port='5433')
	cursor = db.cursor()

	# sql = "select scene_name from ui.cell_scene_lte group by scene_name"
	# sql = 'SELECT sdate, key_scene_name,  x_lon, y_lat, "覆盖良好栅格", "不需解决低采样栅格"  FROM osm.lte_scene_shanghai where sdate in (select max(sdate) from osm.lte_scene_shanghai)'
	sql = 'SELECT a.sdate, a.key_scene_name,  a.x_lon, a.y_lat, "覆盖良好栅格", "不需解决低采样栅格", b.duibiao FROM osm.lte_scene_shanghai a left join ui.duibiao_490 b on a.key_scene_name=b.scene_name where a.sdate in (select max(sdate) from osm.lte_scene_shanghai)'
	# print(sql)
	cursor.execute(sql)
	res = cursor.fetchall()
	db.commit()
	name_list = [] #去重
	worse = []
	better = []
	count = 1
	for tup in res:
		s_name = tup[1]
		if s_name not in name_list:
			name_list.append(s_name)
			rate = int(100 * ( tup[4] + tup[5] ))
			dic = {}
			if rate < 90: #不达标:
				dic['id'] = str(count)
				dic['text'] = tup[1]
				dic['lon'] = tup[2]
				dic['lat'] = tup[3]
				dic['rate'] = str(rate) + '%'
				dic['duibiao'] = tup[6]
				if dic not in worse:
					worse.append(dic)
					count += 1
			else:
				dic['id'] = str(count)
				dic['text'] = tup[1]
				dic['lon'] = tup[2]
				dic['lat'] = tup[3]
				dic['rate'] = str(rate) + '%'
				dic['duibiao'] = tup[6]
				if dic not in better:
					better.append(dic)
					count += 1

	name_dict = {}
	name_dict['better'] = better
	name_dict['worse'] = worse
	# print(dl)
	# cursor.close()
	# db.close()
	return JsonResponse(name_dict)


def important_4GKPI(request):
	"""重点场景4G-KPI接通率和掉话率，时间序列 2小时*36 """
	db = psycopg2.connect(database='postgres', user='postgres', password='postgres', host='192.168.61.20', port='5433')
	cursor = db.cursor()

	sql = ("select start_time, sum(rrc_num) as sum_rrc_num, sum(rrc_den) as sum_rrc_den, sum(erab_num) as sum_erab_num, "
		"sum(erab_den) as sum_erab_den, sum(drop_num) as sum_drop_num, sum(drop_den) as sum_drop_den, sum(gprs_mb) as sum_gprs_mb "
		"from kpi_ty.kpi_ty_lte where start_time in ('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s') group by start_time order by start_time"
		) % (time_all[0],time_all[1],time_all[2],time_all[3],time_all[4],time_all[5],time_all[6],time_all[7],time_all[8],time_all[9],time_all[10],time_all[11],time_all[12],time_all[13],time_all[14],time_all[15],time_all[16],time_all[17],time_all[18],time_all[19],time_all[20],time_all[21],time_all[22],time_all[23],time_all[24],time_all[25],time_all[26],time_all[27],time_all[28],time_all[29],time_all[30],time_all[31],time_all[32],time_all[33],time_all[34],time_all[35])
	cursor.execute(sql)
	res = cursor.fetchall()
	im_4GKPI_list = []
	for tup in res:
		dic = {}
		dic['time'] = str(tup[0]).split()[1]
		dic['receive_rate'] = round(100 * tup[1] * tup[3] / tup[2] / tup[4], 2)
		dic['drop_rate'] = round(100 * tup[5] / tup[6], 2)
		dic['ll'] = tup[7]
		im_4GKPI_list.append(dic)
	mi = 100 # minimum of receive_rate
	for item in im_4GKPI_list:
		rd = float(item['receive_rate'])
		if rd < mi:
			mi = rd
	im_4GKPI_list[0]['min_receive_rate'] = round(mi - 0.05, 1)
	important_4GKPI_dict = {'im_4g': im_4GKPI_list}
	# print(time_all)
	# print(res)
	# important_4GKPI_dict = {'important_4GKPI_dict':[{'time':'8:00',"receive_rate":99.94,"drop_rate":0.23,"ll":100},
	# 		{'time':'4:00',"receive_rate":90.94,"drop_rate":0.9,"ll":110}, {'time':'0:00',"receive_rate":95.94,"drop_rate":1.23,"ll":120},
	# 		{'time':'8:00',"receive_rate":97.94,"drop_rate":0.23,"ll":100}, {'time':'4:00',"receive_rate":96.94,"drop_rate":0.83,"ll":140},
	# 		{'time':'0:00',"receive_rate":89.94,"drop_rate":1.23,"ll":150}, {'time':'8:00',"receive_rate":92.94,"drop_rate":0.73,"ll":100},
	# 		{'time':'4:00',"receive_rate":93.94,"drop_rate":0.53,"ll":105}, {'time':'0:00',"receive_rate":97.94,"drop_rate":0.63,"ll":90}]}
	return JsonResponse(important_4GKPI_dict)


def index2(request):
	"""获取场景名称 并定义为全局变量"""
	global name_special_scene
	name = request.GET['name']
	# name_special_scene = '华夏高架'
	name_special_scene = name
	# print(name_special_scene)
	# request.session['name'] = name
	# print(name)
	return render(request, 'index2.html', {"name":name})


def problem_sg(request):
	"""统计良好栅格和不良栅格的位置信息、基站信息"""
	db = psycopg2.connect(database='postgres', user='postgres', password='postgres', host='192.168.61.20', port='5433')
	cursor = db.cursor()
	name_scene = name_special_scene
	sql = "SELECT x_50, y_50, grid_properties FROM osm.tdlte_mro_locate_tmr_g where key_scene_name='%s' and sdate in (select max(sdate) from osm.tdlte_mro_locate_tmr_g)" % (name_scene)
	cursor.execute(sql)
	res = cursor.fetchall()
	better = []
	worse = []
	for tup in res:
		if tup[2] == '不良栅格':
			worse.append([ float(tup[0])+0.012, float(tup[1])+0.005 ])
		else:
			better.append([ float(tup[0])+0.012, float(tup[1])+0.005 ])

	# 场景名称附近基站位置信息
	sql_enbid = "SELECT z_name, longitude, latitude, enb FROM ui.cell_scene_lte where cj_name='%s'" % (name_scene)
	cursor.execute(sql_enbid)
	res_enbid = cursor.fetchall()
	enbid = {} # {enbid: [z-name, lon, lat]}
	jz_name = []
	if res_enbid:
		for tup in res_enbid:
			if tup[0] not in jz_name:
				jz_name.append(tup[0])
				key = tup[3]
				enbid[key] = []
				enbid[key].append(tup[0])
				enbid[key].append(tup[1])
				enbid[key].append(tup[2])

	# 判断所有基站是否有告警以及告警类型
	kpi = []
	volume = []
	neither_alarm = []
	both_alarm = []
	kpi_alarm = []
	volume_alarm = []

	# KPI告警
	sqlkpi = "SELECT enb_id FROM kpi_ty.pd_to_boco where start_time in (select max(start_time) from kpi_ty.pd_to_boco) group by enb_id"
	cursor.execute(sqlkpi)
	reskpi = cursor.fetchall()
	if reskpi:
		for tup in reskpi:
			kpienbid = tup[0]
			if kpienbid in enbid:
				kpi.append(kpienbid)

	# 扩容告警
	sqlvol = "SELECT enb_id FROM kpi_ty.kr_lte_pivot where sdate in (select max(sdate) from kpi_ty.kr_lte_pivot) group by enb_id"
	cursor.execute(sqlvol)
	resvol = cursor.fetchall()
	if resvol:
		for tup in resvol:
			v_enbid = tup[0]
			if v_enbid in enbid:
				volume.append(v_enbid)

	for key, value in enbid.items():
		dic = {}
		dic['zname'] = value[0]
		dic['enbid'] = key
		dic['lon'] = value[1]
		dic['lat'] = value[2]
		# dic['alarm_type'] = 'KPI'
		if key in kpi and key in volume:
			dic['alarm_type'] = 'KPI and Volume'
			both_alarm.append(dic)
		elif key in kpi and key not in volume:
			dic['alarm_type'] = 'KPI'
			kpi_alarm.append(dic)
		elif key in volume and key not in kpi:
			dic['alarm_type'] = 'Volume'
			volume_alarm.append(dic)
		else:
			dic['alarm_type'] = 'No alarm'
			neither_alarm.append(dic)
	# data = {'both':both_alarm, 'kpi':kpi_alarm, 'volume':volume_alarm, 'neither':neither_alarm}

	# data1-良好栅格； data2-不良栅格； both-kpi和volume都告警； neither-都不告警
	data = {'data1':better, 'data2':worse, 'both':both_alarm, 'kpi':kpi_alarm, 'volume':volume_alarm, 'neither':neither_alarm}
	# print(data)
	cursor.close()
	db.close()

	# print(data['data2'])
	return JsonResponse(data)


def cell_ok(request):
	"""具体场景最近6周 场景栅格比例"""
	name_scene = name_special_scene
	db = psycopg2.connect(database='postgres', user='postgres', password='postgres', host='192.168.61.20', port='5433')
	cursor = db.cursor()

	date_list = []
	sql_date = "SELECT sdate FROM osm.tdlte_mro_locate_tmr_g group by sdate order by sdate"
	cursor.execute(sql_date)
	res_date = cursor.fetchall()
	for tup in res_date:
		date_list.append(str(tup[0]).split()[0])

	# sql = "SELECT sdate, key_scene_name, grid_properties FROM osm.tdlte_mro_locate_tmr_g where key_scene_name='%s' and sdate in ('%s', '%s', '%s', '%s', '%s', '%s', '%s') order by sdate" % (name_scene,s7cycles[-1],s7cycles[-2],s7cycles[-3],s7cycles[-4],s7cycles[-5],s7cycles[-6],s7cycles[-7])
	sql = "SELECT sdate, key_scene_name, grid_properties FROM osm.tdlte_mro_locate_tmr_g where key_scene_name='%s' and sdate in ('%s', '%s', '%s', '%s', '%s', '%s') order by sdate" % (name_scene,date_list[-6],date_list[-5],date_list[-4],date_list[-3],date_list[-2],date_list[-1])
	cursor.execute(sql)
	res = cursor.fetchall()
	ok = []
	timelist = []
	countok = 0
	countnotok = 0
	for tup in res:
		dateflag = tup[0]
		if dateflag not in timelist:
			if countok != 0:
				rate1 = round(100 * countok / (countok + countnotok), 2)
				rate2 = round(100 - rate1, 2)
				dic = {'time':date1, 'rateok':rate1, 'ratenotok':rate2}
				ok.append(dic)
			timelist.append(dateflag)
			date1 = str(dateflag).split()[0]
			countok = 0
			countnotok = 0
			if tup[2] in ('良好栅格', '不需解决低采样栅格'):
				countok += 1
			else:
				countnotok += 1
		else:
			if tup[2] in ('良好栅格', '不需解决低采样栅格'):
				countok += 1
			else:
				countnotok += 1
	rate1 = round(100 * countok / (countok + countnotok), 2)
	rate2 = round(100 - rate1, 2)
	dic = {'time':date1, 'rateok':rate1, 'ratenotok':rate2}
	ok.append(dic)
	cell_ok_dict = {'cellok':ok}

	# cell_ok_dict = {"场景名称":{"week":'First',"良好栅格总计":null,"问题栅格总计":null}}
	return JsonResponse(cell_ok_dict)


def num_busy(request):
	"""统计主控小区的忙时流量"""
	# index2 左下表格 主控小区
	name_scene = name_special_scene
	# name_scene = '虹桥商务区核心区'

	db = psycopg2.connect(database='postgres', user='postgres', password='postgres', host='192.168.61.20', port='5433')
	cursor = db.cursor()

	time_now = datetime.datetime.now()
	td = datetime.timedelta(days=1)
	yesterday = (time_now - td).strftime('%Y-%m-%d')
	# today = time_now.strftime('%Y-%m-%d')
	# hour = time_now.strftime('%H')
	busy_am = yesterday + ' 10:00:00'
	busy_pm = yesterday + ' 20:00:00'

	sql_am = '''SELECT a.scene_name, a.oid, b.gprs_dl, b.start_time FROM ui.cell_scene_lte_jt a left join kpi_ty.kpi_ty_lte b on "substring"(b.oid::text, "position"(b.oid::text, '.'::text) + 1) = a.oid WHERE b.start_time='%s' and a.scene_name='%s' ''' % (busy_am, name_scene)
	# print(sql_am)
	cursor.execute(sql_am)
	res_am = cursor.fetchall()
	ap_gprs_dl = {}
	for tup in res_am:
		oid = tup[1]
		gprs_dl = tup[2]
		if oid in ap_gprs_dl:
			ap_gprs_dl[oid][0] += gprs_dl
		else:
			gprs_dl_list = [gprs_dl, 0]
			ap_gprs_dl[oid] = gprs_dl_list

	sql_pm = '''SELECT a.scene_name, a.oid, b.gprs_dl, b.start_time FROM ui.cell_scene_lte_jt a left join kpi_ty.kpi_ty_lte b on "substring"(b.oid::text, "position"(b.oid::text, '.'::text) + 1) = a.oid WHERE b.start_time='%s' and a.scene_name='%s' ''' % (busy_pm, name_scene)
	# print(sql_am)
	cursor.execute(sql_pm)
	res_pm = cursor.fetchall()
	for tup in res_pm:
		oid = tup[1]
		gprs_dl = tup[2]
		if oid in ap_gprs_dl:
			ap_gprs_dl[oid][1] += gprs_dl
		else:
			gprs_dl_list = [0, gprs_dl]
			ap_gprs_dl[oid] = gprs_dl_list
	nb_list = []
	for k,v in ap_gprs_dl.items():
		dic = {}
		dic['name'] = name_scene
		dic['oid'] = k
		dic['am'] = round(v[0], 1)
		dic['pm'] = round(v[1], 1)
		nb_list.append(dic)
	numbusy = {'nb': nb_list}
	# numbusy = {'nb': [{'name':'1', 'oid':'2', 'am':'3', 'pm':'4'}, {'name':'1', 'oid':'2', 'am':'3', 'pm':'4'}, {'name':'1', 'oid':'2', 'am':'3', 'pm':'4'}]}
	return JsonResponse(numbusy)


def special_4GKPI(request):
	"""具体场景4G-KPI接通率和掉话率"""
	# name_scene = '外环高架' #需要获取前端的具体场景名称
	name_scene = name_special_scene
	db = psycopg2.connect(database='postgres', user='postgres', password='postgres', host='192.168.61.20', port='5433')
	cursor = db.cursor()

	# 增加ci这一列，用replace
	sql = ('''select b.start_time, sum(b.rrc_num) as sum_rrc_num, sum(b.rrc_den) as sum_rrc_den, sum(b.erab_num) as sum_erab_num, sum(b.erab_den) as sum_erab_den, sum(b.drop_num) as sum_drop_num, sum(b.drop_den) as sum_drop_den, sum(prb_num) as sum_prb_num, sum(prb_den) as sum_prb_den from ui.cell_scene_lte a left join kpi_ty.kpi_ty_lte b on "substring"(b.oid,"position"(b.oid,'.')+1) = a.oid where a.cj_name='%s' and '''
		"b.start_time in ('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s') group by start_time order by start_time"
		) % (name_scene,time_all[0],time_all[1],time_all[2],time_all[3],time_all[4],time_all[5],time_all[6],time_all[7],time_all[8],time_all[9],time_all[10],time_all[11],time_all[12],time_all[13],time_all[14],time_all[15],time_all[16],time_all[17],time_all[18],time_all[19],time_all[20],time_all[21],time_all[22],time_all[23],time_all[24],time_all[25],time_all[26],time_all[27],time_all[28],time_all[29],time_all[30],time_all[31],time_all[32],time_all[33],time_all[34],time_all[35])
	cursor.execute(sql)
	res = cursor.fetchall()
	sp_4G_list = []
	for tup in res:
		if tup[0] is not None:
			dic = {}
			dic['time'] = str(tup[0]).split()[1]
			dic['receive_rate'] = round(100 * tup[1] * tup[3] / tup[2] / tup[4], 2)
			dic['drop_rate'] = round(100 * tup[5] / tup[6], 2)
			dic['prb_ratio'] = round(100 * tup[7] / tup[8], 2)
			sp_4G_list.append(dic)
			#print(tup)
	mi = 100 # minimum of receive_rate
	for item in sp_4G_list:
		rd = float(item['receive_rate'])
		if rd < mi:
			mi = rd
	sp_4G_list[0]['min_receive_rate'] = round(mi - 0.05, 1)
	special4G_dict = {'sp_4g': sp_4G_list}
	# print(special4G_dict)

	# special4G_dict = {"sp_4g": [{"time": "12:00", "receive_rate": "99.79", "drop_rate": "0.28", "prb_ratio": 8.31},
	# 							{"time": "14:00", "receive_rate": "95", "drop_rate": "0.2", "prb_ratio": 10},
	# 							{"time": "16:00", "receive_rate": "90", "drop_rate": "0.18", "prb_ratio": 9},
	# 							{"time": "18:00", "receive_rate": "99.79", "drop_rate": "0.2", "prb_ratio": 11},
	# 							{"time": "20:00", "receive_rate": "97", "drop_rate": "0.08", "prb_ratio": 9}]}
	return JsonResponse(special4G_dict)


def sp_gj_info(request):
	"""统计具体场景的告警信息"""
	# index2 右中表格 告警详单
	name_scene = name_special_scene
	# name_scene = '外环高架'

	db = psycopg2.connect(database='postgres', user='postgres', password='postgres', host='192.168.61.20', port='5433')
	cursor = db.cursor()
	result = []

	sql_kpi = "SELECT a.cj_name, a.z_name, a.oid, b.boco_id, b.start_time, b.oid, b.alarm_type, b.alarm_values FROM ui.cell_scene_lte a, kpi_ty.pd_to_boco b where a.oid=b.oid and a.cj_name='%s'" % (name_scene)
	cursor.execute(sql_kpi)
	res_kpi = cursor.fetchall()
	if res_kpi:
		for tup in res_kpi:
			dic = {}
			dic['id'] = str(tup[3]) # 工单流水号
			dic['name'] = tup[1] # 问题小区
			dic['alarm_type'] = tup[6] # 告警类型
			dic['alarm_value'] = round(tup[7], 1) # 触发指标
			dic['start_time'] = str(tup[4]).split()[0] # 首次触发
			result.append(dic)

	sql_volume = "SELECT a.cj_name, a.z_name, a.enb, b.sdate, b.enb_id, b.mis, b.prb_cell1, b.prb_cell2, b.prb_cell3, b.prb_cell4, b.prb_cell5, b.prb_cell6 FROM ui.cell_scene_lte a, kpi_ty.kr_lte_pivot b where a.enb=b.enb_id and a.cj_name='%s'" % (name_scene)
	cursor.execute(sql_volume)
	res_v = cursor.fetchall()
	quchong = []
	if res_v:
		for tup in res_v:
			z_name = tup[1]
			sdate = str(tup[3])
			flag = z_name + sdate
			if flag not in quchong:
				quchong.append(flag)
				dic = {}
				dic['id'] = '' # 工单流水号
				dic['name'] = z_name # 问题小区
				dic['alarm_type'] = tup[5] # 告警类型
				if tup[6]:
					dic['alarm_value'] = round(tup[6], 1) # 触发指标
				elif tup[7]:
					dic['alarm_value'] = round(tup[7], 1) # 触发指标
				elif tup[8]:
					dic['alarm_value'] = round(tup[8], 1) # 触发指标
				elif tup[9]:
					dic['alarm_value'] = round(tup[9], 1) # 触发指标
				elif tup[10]:
					dic['alarm_value'] = round(tup[10], 1) # 触发指标
				elif tup[11]:
					dic['alarm_value'] = round(tup[11], 1) # 触发指标
				else:
					dic['alarm_value'] = 0.0
				dic['start_time'] = sdate # 首次触发
				result.append(dic)
	gj_info = {'gj': result}
	return JsonResponse(gj_info)


def download_sp_gj(request):
	"""具体场景的告警信息的下载接口"""
	# index2 右中表格 告警详单 - 导出详单
	name_scene = name_special_scene
	# name_scene = '外环高架'

	db = psycopg2.connect(database='postgres', user='postgres', password='postgres', host='192.168.61.20', port='5433')
	cursor = db.cursor()
	result = []
	# 创建excel
	wb = xlwt.Workbook()

	sql_kpi = "SELECT a.cj_name, a.z_name, b.* FROM ui.cell_scene_lte a, kpi_ty.pd_to_boco b where a.oid=b.oid and a.cj_name='%s'" % (name_scene)
	# sql_kpi = "SELECT a.cj_name, a.z_name, a.oid, b.boco_id, b.start_time, b.oid, b.alarm_type, b.alarm_values FROM ui.cell_scene_lte a, kpi_ty.pd_to_boco b where a.oid=b.oid and a.cj_name='%s'" % (name_scene)
	cursor.execute(sql_kpi)
	res_kpi = cursor.fetchall()
	title_kpi = ['cj_name', 'z_name', 'boco_id', 'start_time', 's_hour', 'net_type', 'alarm_type', 'alarm_values',
				'enb_id', 'z_id', 'oid', 'z_cname', 'ci', 'partition', 'alarm_close', 'alarm_pd',
				'pd_time', 'close_time', 'alarm_boco', 'remark']
	ws_kpi = wb.add_sheet('kpi')
	for i in range(len(title_kpi)):
		ws_kpi.write(0, i, title_kpi[i])
	if res_kpi:
		row = 1
		for tup in res_kpi:
			ws_kpi.write(row, 0, tup[0])
			ws_kpi.write(row, 1, tup[1])
			ws_kpi.write(row, 2, tup[2])
			ws_kpi.write(row, 3, str(tup[3]))
			ws_kpi.write(row, 4, tup[4])
			ws_kpi.write(row, 5, tup[5])
			ws_kpi.write(row, 6, tup[6])
			ws_kpi.write(row, 7, tup[7])
			ws_kpi.write(row, 8, tup[8])
			ws_kpi.write(row, 9, tup[9])
			ws_kpi.write(row, 10, tup[10])
			ws_kpi.write(row, 11, tup[11])
			ws_kpi.write(row, 12, tup[12])
			ws_kpi.write(row, 13, tup[13])
			ws_kpi.write(row, 14, tup[14])
			ws_kpi.write(row, 15, tup[15])
			ws_kpi.write(row, 16, str(tup[16]))
			ws_kpi.write(row, 17, str(tup[17]))
			ws_kpi.write(row, 18, tup[18])
			ws_kpi.write(row, 19, tup[19])
			row += 1

	# sql_volume = "SELECT a.cj_name, a.z_name, a.enb, b.sdate, b.enb_id, b.mis, b.prb_cell1, b.prb_cell2, b.prb_cell3, b.prb_cell4, b.prb_cell5, b.prb_cell6 FROM ui.cell_scene_lte a, kpi_ty.kr_lte_pivot b where a.enb=b.enb_id and a.cj_name='%s'" % (name_scene)
	sql_volume = "SELECT b.*, a.cj_name FROM ui.cell_scene_lte a, kpi_ty.kr_lte_pivot b where a.enb=b.enb_id and a.cj_name='%s'" % (name_scene)
	cursor.execute(sql_volume)
	res_v = cursor.fetchall()
	title_v = ['sdate', 'enb_id', 'z_id', 'z_name', 'branches', 'area', 'vendor', 'abc', 'mis', 'z_type',
			'scene_zdn', 'scene_kbn', 'kr_count', 'kr_cell1', 'kr_cell2', 'kr_cell3',
			'kr_cell4', 'kr_cell5', 'kr_cell6', 'prb_cell1', 'prb_cell2', 'prb_cell3',
			'prb_cell4', 'prb_cell5', 'prb_cell6', 'gprs_cell1', 'gprs_cell2', 'gprs_cell3',
			'gprs_cell4', 'gprs_cell5', 'gprs_cell6', 'rrc_cell1', 'rrc_cell2', 'rrc_cell3',
			'rrc_cell4', 'rrc_cell5', 'rrc_cell6', 'cqi_cell1', 'cqi_cell2', 'cqi_cell3',
			'cqi_cell4', 'cqi_cell5', 'cqi_cell6', 'avg_prb_cell1', 'avg_prb_cell2',
			'avg_prb_cell3', 'avg_prb_cell4', 'avg_prb_cell5', 'avg_prb_cell6', 'cj_name']
	ws_v = wb.add_sheet('volume')
	for i in range(len(title_v)):
		ws_v.write(0, i, title_v[i])
	if res_v:
		row = 1
		for tup in res_v:
			for i in range(50):
				if i == 0:
					ws_v.write(row, 0, str(tup[0]))
				else:
					ws_v.write(row, i, tup[i])
			row += 1
			# ws_v.write(row, 0, str(tup[0]))
			# ws_v.write(row, 1, tup[1])
			# ws_v.write(row, 2, tup[2])
			# ws_v.write(row, 3, tup[3])
			# ws_v.write(row, 4, tup[4])
			# ws_v.write(row, 5, tup[5])
			# ws_v.write(row, 6, tup[6])
			# ws_v.write(row, 7, tup[7])
			# ws_v.write(row, 8, tup[8])
			# ws_v.write(row, 9, tup[9])
			# ws_v.write(row, 10, tup[10])
			# ws_v.write(row, 11, tup[11])
			# ws_v.write(row, 12, tup[12])
			# ws_v.write(row, 13, tup[13])
			# ws_v.write(row, 14, tup[14])
			# ws_v.write(row, 15, tup[15])
			# ws_v.write(row, 16, tup[16])
			# ws_v.write(row, 17, tup[17])
			# ws_v.write(row, 18, tup[18])
			# ws_v.write(row, 19, tup[19])
			# ws_v.write(row, 20, tup[20])
			# ws_v.write(row, 21, tup[21])
			# ws_v.write(row, 22, tup[22])
			# ws_v.write(row, 23, tup[23])
			# ws_v.write(row, 24, tup[24])
			# ws_v.write(row, 25, tup[25])
			# ws_v.write(row, 26, tup[26])
			# ws_v.write(row, 27, tup[27])
			# ws_v.write(row, 28, tup[28])
			# ws_v.write(row, 29, tup[29])
			# ws_v.write(row, 30, tup[30])
			# ws_v.write(row, 31, tup[31])
			# ws_v.write(row, 32, tup[32])
			# ws_v.write(row, 33, tup[33])
			# ws_v.write(row, 34, tup[34])
			# ws_v.write(row, 35, tup[35])
			# ws_v.write(row, 36, tup[36])
			# ws_v.write(row, 37, tup[37])
			# ws_v.write(row, 38, tup[38])
			# ws_v.write(row, 39, tup[39])
			# ws_v.write(row, 40, tup[40])
			# ws_v.write(row, 41, tup[41])
			# ws_v.write(row, 42, tup[42])
			# ws_v.write(row, 43, tup[43])
			# ws_v.write(row, 44, tup[44])
			# ws_v.write(row, 45, tup[45])
			# ws_v.write(row, 46, tup[46])
			# ws_v.write(row, 47, tup[47])
			# ws_v.write(row, 48, tup[48])
			# ws_v.write(row, 49, tup[49])
			# row += 1

	# 保存及下载数据
	date = datetime.datetime.now()
	datestr = date.strftime('%y%m%d')
	response = HttpResponse(content_type='application/vnd.ms-excel')
	response['Content-Disposition'] = 'attachment; filename="cj_gaojiang_info_%s.xls"' % (datestr)
	wb.save(response)
	return response


def kpi_enbid(request):
	"""KPI告警的基站位置信息"""
	db = psycopg2.connect(database='postgres', user='postgres', password='postgres', host='192.168.61.20', port='5433')
	cursor = db.cursor()
	sql = "SELECT a.enb_id, a.z_cname, b.longitude, b.latitude, b.enb FROM kpi_ty.pd_to_boco a left join ui.cell_scene_lte b on a.enb_id=b.enb where a.start_time in (select max(start_time) from kpi_ty.pd_to_boco) and a.alarm_pd='TRUE'"
	# sql = "SELECT a.enb_id, a.z_cname, b.longitude, b.latitude, b.enb FROM kpi_ty.pd_to_boco a left join ui.cell_scene_lte b on a.enb_id=b.enb where a.start_time in ('2017-10-10') and a.alarm_pd='TRUE'"
	cursor.execute(sql)
	res = cursor.fetchall()
	result = []
	if res:
		for tup in res:
			dic = {}
			dic['name'] = tup[1]
			dic['lon'] = tup[2]
			dic['lat'] = tup[3]
			if dic not in result:
				result.append(dic)
	kpi_enb_dic = {'ked': result}
	return JsonResponse(kpi_enb_dic)


def st_from(request):
	"""返回一个默认周期，前10天到前2天"""
	now = datetime.datetime.now()
	td2 = datetime.timedelta(days=2)
	td10= datetime.timedelta(days=10)

	time_1 = now - td2
	date_to = time_1.strftime('%Y-%m-%d')
	time_2 = now - td10
	date_from = time_2.strftime('%Y-%m-%d')

	ft = {'ft':[{'from':date_from, 'to':date_to}]}
	return JsonResponse(ft)


def gj_monitor_mid(request):
	"""统计告警工单的具体信息"""
	# index3 告警工单监控右中表格 默认前10天到前2天
	db = psycopg2.connect(database='postgres', user='postgres', password='postgres', host='192.168.61.20', port='5433')
	cursor = db.cursor()

	# 时间序列依据前端的返回值来改写
	date_from = request.GET['starttime']
	date_to = request.GET['endtime']

	if date_from == '1':
		now = datetime.datetime.now()
		td2 = datetime.timedelta(days=2)
		td10= datetime.timedelta(days=10)

		time_1 = now - td2
		date_to = time_1.strftime('%Y-%m-%d')
		time_2 = now - td10
		date_from = time_2.strftime('%Y-%m-%d')

	global date3_from, date3_to
	date3_from = date_from
	date3_to = date_to

	# 搜索具体信息写入告警工单
	row_name = {'east': '东区', 'west': '西区', 'south': '南区', 'north': '北区', 'special': '专项', 'total': '总计'}

	kpi = {'east': 0, 'west': 0, 'south': 0, 'north': 0, 'special': 0, 'total': 0}
	sql_kpi = "SELECT partition FROM kpi_ty.pd_to_boco WHERE alarm_pd='TRUE' and start_time>'%s' and start_time<'%s'" % (date_from, date_to)
	cursor.execute(sql_kpi)
	res_kpi = cursor.fetchall()
	if res_kpi:
		for tup in res_kpi:
			par = tup[0]
			kpi['total'] += 1
			if par == '东区':
				kpi['east'] += 1
			elif par == '西区':
				kpi['west'] += 1
			elif par == '南区':
				kpi['south'] += 1
			elif par == '北区':
				kpi['north'] += 1
			else:
				kpi['special'] += 1

	kqi = {'east': 0, 'west': 0, 'south': 0, 'north': 0, 'special': 0, 'total': 0}

	hardware_fault = {'east': 0, 'west': 0, 'south': 0, 'north': 0, 'special': 0, 'total': 0}
	sql_hf = "SELECT a.bs_code, b.z_id, b.partition FROM kpi_ty.kpi_ty_alarm a, ui.cell_scene_lte b where a.bs_code=b.z_id and create_time>'%s' and create_time<'%s'" % (date_from, date_to)
	cursor.execute(sql_hf)
	res_hf = cursor.fetchall()
	# print(len(res_hf))
	if res_hf:
		for tup in res_hf:
			par = tup[2]
			hardware_fault['total'] += 1
			if par == '东区':
				hardware_fault['east'] += 1
			elif par == '西区':
				hardware_fault['west'] += 1
			elif par == '南区':
				hardware_fault['south'] += 1
			elif par == '北区':
				hardware_fault['north'] += 1
			else:
				hardware_fault['special'] += 1


	volume = {'east': 0, 'west': 0, 'south': 0, 'north': 0, 'special': 0, 'total': 0}
	sql_v = "SELECT a.sdate, a.enb_id, b.enb, b.partition FROM kpi_ty.kr_lte_pivot a, ui.cell_scene_lte b WHERE a.enb_id = b.enb and a.sdate>'%s' and a.sdate<'%s'" % (date_from, date_to)
	# sql_v = "SELECT a.sdate, a.enb_id, b.enb, b.partition FROM kpi_ty.kr_lte_pivot a, ui.cell_scene_lte b WHERE a.enb_id = b.enb and a.sdate>'%s' and a.sdate<'%s'" % (date_from, date_to)
	cursor.execute(sql_v)
	res_v = cursor.fetchall()
	if res_v:
		for tup in res_v:
			par = tup[3]
			volume['total'] += 1
			if par == '东区':
				volume['east'] += 1
			elif par == '西区':
				volume['west'] += 1
			elif par == '南区':
				volume['south'] += 1
			elif par == '北区':
				volume['north'] += 1
			else:
				volume['special'] += 1

	actual_row = ['east', 'west', 'south', 'north', 'special', 'total'] # 累计数
	result = [{},{},{},{},{},{}]
	i = 0
	for item in actual_row:
		result[i]['row_name'] = row_name[item]
		result[i]['kpi'] = kpi[item]
		result[i]['kqi'] = kqi[item]
		result[i]['hardware_fault'] = hardware_fault[item]
		result[i]['volume'] = volume[item]
		i += 1
	# result = []
	# result.append(row_name)
	# result.append(kpi)
	# result.append(kqi)
	# result.append(hardware_fault)
	# result.append(volume)
	gj_monitor_dict = {'gmd': result}
	return JsonResponse(gj_monitor_dict)


def download_gj_monitor(request):
	"""提供告警工单详情的下载接口"""
	# index3 告警工单监控右中表格下载
	db = psycopg2.connect(database='postgres', user='postgres', password='postgres', host='192.168.61.20', port='5433')
	cursor = db.cursor()

	# date_from = '2017-10-01'
	# date_to = '2017-10-16'
	# row_name = {'east': '东区', 'west': '西区', 'south': '南区', 'north': '北区', 'special': '专项', 'total': '总计'}

	# 创建excel
	wb = xlwt.Workbook()

	# kpi = {'east': 0, 'west': 0, 'south': 0, 'north': 0, 'special': 0, 'total': 0}
	sql_kpi = "SELECT * FROM kpi_ty.pd_to_boco WHERE alarm_pd='TRUE' and start_time>'%s' and start_time<'%s'" % (date3_from, date3_to)
	cursor.execute(sql_kpi)
	res_kpi = cursor.fetchall()
	title_kpi = ['boco_id', 'start_time', 's_hour', 'net_type', 'alarm_type', 'alarm_values',
				'enb_id', 'z_id', 'oid', 'z_cname', 'ci', 'partition', 'alarm_close', 'alarm_pd',
				'pd_time', 'close_time', 'alarm_boco', 'remark']
	ws_kpi = wb.add_sheet('kpi')
	for i in range(len(title_kpi)):
		ws_kpi.write(0, i, title_kpi[i])
	if res_kpi:
		row = 1
		for tup in res_kpi:
			ws_kpi.write(row, 0, tup[0])
			ws_kpi.write(row, 1, str(tup[1]))
			ws_kpi.write(row, 2, tup[2])
			ws_kpi.write(row, 3, tup[3])
			ws_kpi.write(row, 4, tup[4])
			ws_kpi.write(row, 5, tup[5])
			ws_kpi.write(row, 6, tup[6])
			ws_kpi.write(row, 7, tup[7])
			ws_kpi.write(row, 8, tup[8])
			ws_kpi.write(row, 9, tup[9])
			ws_kpi.write(row, 10, tup[10])
			ws_kpi.write(row, 11, tup[11])
			ws_kpi.write(row, 12, tup[12])
			ws_kpi.write(row, 13, tup[13])
			ws_kpi.write(row, 14, str(tup[14]))
			ws_kpi.write(row, 15, str(tup[15]))
			ws_kpi.write(row, 16, tup[16])
			ws_kpi.write(row, 17, tup[17])
			row += 1

	# hardware_fault = {'east': 0, 'west': 0, 'south': 0, 'north': 0, 'special': 0, 'total': 0}
	sql_hf = "SELECT a.*, b.partition FROM kpi_ty.kpi_ty_alarm a, ui.cell_scene_lte b where a.bs_code=b.z_id and create_time>'%s' and create_time<'%s'" % (date3_from, date3_to)
	cursor.execute(sql_hf)
	res_hf = cursor.fetchall()
	title_hf = ['alarm_id', 'alarm_title', 'alarm_text', 'alarm_time', 'alarm_level', 'alarm_status', 'ne_type', 'ne_name', 'bs_code', 'clear_time', 'create_time', 'partition']
	ws_hf = wb.add_sheet('hardware_fault')
	for i in range(len(title_hf)):
		ws_hf.write(0, i, title_hf[i])
	if res_hf:
		row = 1
		for tup in res_hf:
			ws_hf.write(row, 0, tup[0])
			ws_hf.write(row, 1, tup[1])
			ws_hf.write(row, 2, tup[2])
			ws_hf.write(row, 3, str(tup[3]))
			ws_hf.write(row, 4, tup[4])
			ws_hf.write(row, 5, tup[5])
			ws_hf.write(row, 6, tup[6])
			ws_hf.write(row, 7, tup[7])
			ws_hf.write(row, 8, tup[8])
			ws_hf.write(row, 9, str(tup[9]))
			ws_hf.write(row, 10, str(tup[10]))
			ws_hf.write(row, 11, tup[11])
			row += 1

	# volume = {'east': 0, 'west': 0, 'south': 0, 'north': 0, 'special': 0, 'total': 0}
	sql_v = "SELECT a.*, b.partition FROM kpi_ty.kr_lte_pivot a, ui.cell_scene_lte b WHERE a.enb_id = b.enb and a.sdate>'%s' and a.sdate<'%s'" % (date3_from, date3_to)
	cursor.execute(sql_v)
	res_v = cursor.fetchall()
	title_v = ['sdate', 'enb_id', 'z_id', 'z_name', 'branches', 'area', 'vendor', 'abc', 'mis', 'z_type',
			'scene_zdn', 'scene_kbn', 'kr_count', 'kr_cell1', 'kr_cell2', 'kr_cell3',
			'kr_cell4', 'kr_cell5', 'kr_cell6', 'prb_cell1', 'prb_cell2', 'prb_cell3',
			'prb_cell4', 'prb_cell5', 'prb_cell6', 'gprs_cell1', 'gprs_cell2', 'gprs_cell3',
			'gprs_cell4', 'gprs_cell5', 'gprs_cell6', 'rrc_cell1', 'rrc_cell2', 'rrc_cell3',
			'rrc_cell4', 'rrc_cell5', 'rrc_cell6', 'cqi_cell1', 'cqi_cell2', 'cqi_cell3',
			'cqi_cell4', 'cqi_cell5', 'cqi_cell6', 'avg_prb_cell1', 'avg_prb_cell2',
			'avg_prb_cell3', 'avg_prb_cell4', 'avg_prb_cell5', 'avg_prb_cell6', 'partition']
	ws_v = wb.add_sheet('volume')
	for i in range(len(title_v)):
		ws_v.write(0, i, title_v[i])
	if res_v:
		row = 1
		for tup in res_v:
			for i in range(50):
				if i == 0:
					ws_v.write(row, 0, str(tup[0]))
				else:
					ws_v.write(row, i, tup[i])
			row += 1
			# ws_v.write(row, 0, str(tup[0]))
			# ws_v.write(row, 1, tup[1])
			# ws_v.write(row, 2, tup[2])
			# ws_v.write(row, 3, tup[3])
			# ws_v.write(row, 4, tup[4])
			# ws_v.write(row, 5, tup[5])
			# ws_v.write(row, 6, tup[6])
			# ws_v.write(row, 7, tup[7])
			# ws_v.write(row, 8, tup[8])
			# ws_v.write(row, 9, tup[9])
			# ws_v.write(row, 10, tup[10])
			# ws_v.write(row, 11, tup[11])
			# ws_v.write(row, 12, tup[12])
			# ws_v.write(row, 13, tup[13])
			# ws_v.write(row, 14, tup[14])
			# ws_v.write(row, 15, tup[15])
			# ws_v.write(row, 16, tup[16])
			# ws_v.write(row, 17, tup[17])
			# ws_v.write(row, 18, tup[18])
			# ws_v.write(row, 19, tup[19])
			# ws_v.write(row, 20, tup[20])
			# ws_v.write(row, 21, tup[21])
			# ws_v.write(row, 22, tup[22])
			# ws_v.write(row, 23, tup[23])
			# ws_v.write(row, 24, tup[24])
			# ws_v.write(row, 25, tup[25])
			# ws_v.write(row, 26, tup[26])
			# ws_v.write(row, 27, tup[27])
			# ws_v.write(row, 28, tup[28])
			# ws_v.write(row, 29, tup[29])
			# ws_v.write(row, 30, tup[30])
			# ws_v.write(row, 31, tup[31])
			# ws_v.write(row, 32, tup[32])
			# ws_v.write(row, 33, tup[33])
			# ws_v.write(row, 34, tup[34])
			# ws_v.write(row, 35, tup[35])
			# ws_v.write(row, 36, tup[36])
			# ws_v.write(row, 37, tup[37])
			# ws_v.write(row, 38, tup[38])
			# ws_v.write(row, 39, tup[39])
			# ws_v.write(row, 40, tup[40])
			# ws_v.write(row, 41, tup[41])
			# ws_v.write(row, 42, tup[42])
			# ws_v.write(row, 43, tup[43])
			# ws_v.write(row, 44, tup[44])
			# ws_v.write(row, 45, tup[45])
			# ws_v.write(row, 46, tup[46])
			# ws_v.write(row, 47, tup[47])
			# ws_v.write(row, 48, tup[48])
			# ws_v.write(row, 49, tup[49])
			# row += 1

	# 保存及下载数据
	# date = datetime.datetime.now()
	# datestr = date.strftime('%y%m%d')
	datestr = date3_from.split('-')[2] + "_" + date3_to.split('-')[2]
	response = HttpResponse(content_type='application/vnd.ms-excel')
	response['Content-Disposition'] = 'attachment; filename="gaojiang_info_%s.xls"' % (datestr)
	wb.save(response)
	return response

def kpi_alarm_info(request):
	"""根据前端返回的工单号寻找具体告警信息"""
	db = psycopg2.connect(database='postgres', user='postgres', password='postgres', host='192.168.61.20', port='5433')
	cursor = db.cursor()
	global booc_id
	boco_id = request.GET['xiaoqu'] # 告警单号
	# boco_id = '106' # 告警单号
	booc_id = boco_id
	result = []
	if boco_id:
		td = datetime.timedelta(days=1)
		sql_boco = "select boco_id, start_time, alarm_type, alarm_values, oid FROM kpi_ty.pd_to_boco where alarm_pd='TRUE' and boco_id='%s'" % (boco_id)
		cursor.execute(sql_boco)
		res_boco = cursor.fetchall()
		for tup in res_boco:
			kpi_alerm = {}
			kpi_alerm['boco_id'] = tup[0]
			kpi_alerm['start_time'] = str(tup[1])
			kpi_alerm['name'] = 'KPI'
			kpi_alerm['alarm_type'] = tup[2]
			kpi_alerm['alarm_values'] = tup[3]
			kpi_alerm['oid'] = tup[4]
			# 最新时间减1天
			sql_time = "select max(start_time) from kpi_ty.pd_to_boco"
			cursor.execute(sql_time)
			latest_time = str(cursor.fetchall()[0][0]-td).split()[0]
			# 判断是否解决 ，上面的时间里有无相同的oid
			sql_oid = "select * from kpi_ty.pd_to_boco where oid='%s' and start_time='%s'" % (kpi_alerm['oid'], latest_time)
			cursor.execute(sql_oid)
			res_oid = cursor.fetchall()
			if res_oid:
				kpi_alerm['fix_or_not'] = '未解决'
			else:
				kpi_alerm['fix_or_not'] = '已解决'
			result.append(kpi_alerm)
	kpi_alerm_dict = {'kad': result}
	return JsonResponse(kpi_alerm_dict)


def download_kpi_alarm(request):
	"""下载告警信息"""
	db = psycopg2.connect(database='postgres', user='postgres', password='postgres', host='192.168.61.20', port='5433')
	cursor = db.cursor()
	# 创建excel
	wb = xlwt.Workbook()
	ws = wb.add_sheet('bocoid')
	# 写入列名
	title = ['boco_id', 'start_time', 's_hour', 'net_type', 'alarm_type', 'alarm_values',
			'enb_id', 'z_id', 'oid', 'z_cname', 'ci', 'partition', 'alarm_close', 'alarm_pd',
			'pd_time', 'close_time', 'alarm_boco', 'remark']
	for i in range(len(title)):
		ws.write(0, i, title[i])

	result = []
	# td = datetime.timedelta(days=1)
	sql_boco = "select * FROM kpi_ty.pd_to_boco where alarm_pd='TRUE' and boco_id='%s'" % (booc_id)
	cursor.execute(sql_boco)
	res_boco = cursor.fetchall()
	if res_boco:
		row = 1
		for tup in res_boco:
			ws.write(row, 0, tup[0])
			ws.write(row, 1, str(tup[1]))
			ws.write(row, 2, tup[2])
			ws.write(row, 3, tup[3])
			ws.write(row, 4, tup[4])
			ws.write(row, 5, tup[5])
			ws.write(row, 6, tup[6])
			ws.write(row, 7, tup[7])
			ws.write(row, 8, tup[8])
			ws.write(row, 9, tup[9])
			ws.write(row, 10, tup[10])
			ws.write(row, 11, tup[11])
			ws.write(row, 12, tup[12])
			ws.write(row, 13, tup[13])
			ws.write(row, 14, str(tup[14]))
			ws.write(row, 15, str(tup[15]))
			ws.write(row, 16, tup[16])
			ws.write(row, 17, tup[17])
			row += 1

	# 保存及下载数据
	# date = datetime.datetime.now()
	# datestr = date.strftime('%y%m%d')
	# datestr = date_from.split('-')[2] + "_" + date_to.split('-')[2]
	response = HttpResponse(content_type='application/vnd.ms-excel')
	response['Content-Disposition'] = 'attachment; filename="KPI_alarm_info_%s.xls"' % (booc_id)
	wb.save(response)
	return response


def volume_enbid(request):
	"""扩容告警基站信息，包括名称和位置"""
	db = psycopg2.connect(database='postgres', user='postgres', password='postgres', host='192.168.61.20', port='5433')
	cursor = db.cursor()
	sql = "SELECT a.enb_id, a.z_name, b.longitude, b.latitude, b.enb FROM kpi_ty.kr_lte_pivot a left join ui.cell_scene_lte b on a.enb_id=b.enb where a.sdate in (select max(sdate) from kpi_ty.kr_lte_pivot)"
	cursor.execute(sql)
	res = cursor.fetchall()
	result = []
	if res:
		for tup in res:
			if tup[2]:
				dic = {}
				dic['name'] = tup[1]
				dic['lon'] = tup[2]
				dic['lat'] = tup[3]
				if dic not in result:
					result.append(dic)
	volume_enb_dic = {'ved': result}
	return JsonResponse(volume_enb_dic)


def datechoose(request):
	"""返回一个默认选择日期"""
	# 默认时间向前推一天
	now = datetime.datetime.now()
	td = datetime.timedelta(days=1)

	time_1 = now - td
	date_ch = time_1.strftime('%Y-%m-%d')

	dc = {'dc':[{'from':date_ch}]}
	return JsonResponse(dc)

def volume_alert_info(request):
	"""容量预警监控信息"""
	# index4 容量预警监控右上表格 默认时间向前推一天
	db = psycopg2.connect(database='postgres', user='postgres', password='postgres', host='192.168.61.20', port='5433')
	cursor = db.cursor()
	# date_choose = '2017-10-17'
	date_choose = request.GET['starttime']

	if date_choose == '1':
		now = datetime.datetime.now()
		td = datetime.timedelta(days=1)

		time_1 = now - td
		date_choose = time_1.strftime('%Y-%m-%d')

	global date4_choose
	date4_choose = date_choose

	time_from = date4_choose + ' 10:00:00'
	time_to = date4_choose + ' 20:00:00'

	row_name = {'east': '东区', 'west': '西区', 'south': '南区', 'north': '北区', 'special': '专项', 'total': '总计'}

	volume_now = {'east': 0, 'west': 0, 'south': 0, 'north': 0, 'special': 0, 'total': 0} # 预警小区数
	sql_vn = "select a.sdate, a.enb_id, a.kr_count, b.enb, b.partition FROM kpi_ty.kr_lte_pivot a, ui.cell_scene_lte b where a.sdate in (select max(sdate) from kpi_ty.kr_lte_pivot) and a.enb_id=b.enb"
	cursor.execute(sql_vn)
	res_vn = cursor.fetchall()
	if res_vn:
		enb_id_list = [] # drop dulplicates
		for tup in res_vn:
			enb_id = tup[1]
			par = tup[4]
			if enb_id not in enb_id_list:
				enb_id_list.append(enb_id)
				volume_now['total'] += 1
				if par == '东区':
					volume_now['east'] += 1
				elif par == '西区':
					volume_now['west'] += 1
				elif par == '南区':
					volume_now['south'] += 1
				elif par == '北区':
					volume_now['north'] += 1
				elif par == '专项':
					volume_now['special'] += 1

	volume_all = {'east': 0, 'west': 0, 'south': 0, 'north': 0, 'special': 0, 'total': 0} # 累计数
	sql_va = "select a.sdate, a.enb_id, a.kr_count, b.enb, b.partition FROM kpi_ty.kr_lte_pivot a, ui.cell_scene_lte b where a.enb_id=b.enb"
	cursor.execute(sql_va)
	res_va = cursor.fetchall()
	if res_va:
		enb_id_list = [] # drop dulplicates
		for tup in res_va:
			enb_id = tup[1]
			par = tup[4]
			if enb_id not in enb_id_list:
				enb_id_list.append(enb_id)
				volume_all['total'] += 1
				if par == '东区':
					volume_all['east'] += 1
				elif par == '西区':
					volume_all['west'] += 1
				elif par == '南区':
					volume_all['south'] += 1
				elif par == '北区':
					volume_all['north'] += 1
				elif par == '专项':
					volume_all['special'] += 1

	solved_num = {'east': 0, 'west': 0, 'south': 0, 'north': 0, 'special': 0, 'total': 0} # 解决数
	solved_rate = {} # 解决率
	for k in solved_num.keys():
		solved_num[k] += (volume_all[k] - volume_now[k])
		solved_rate[k] = round((100 * solved_num[k] / volume_all[k]), 1)

	prb_rate = {} # prb ratio
	sql_prb = '''select a.partition, sum(b.prb_num) as sum_prb_num, sum(b.prb_den) as sum_prb_den from ui.cell_scene_lte a left join kpi_ty.kpi_ty_lte b on "substring"(b.oid,"position"(b.oid,'.')+1) = a.oid where b.start_time in ('%s', '%s') group by a.partition''' % (time_from, time_to)
	cursor.execute(sql_prb)
	res_prb = cursor.fetchall()
	prb_num_all = 0
	prb_den_all = 0
	if res_prb:
		for tup in res_prb:
			par = tup[0]
			prb_num = tup[1]
			prb_den = tup[2]
			if par == '东区':
				prb_rate['east'] = round(100 * prb_num / prb_den, 1)
			elif par == '西区':
				prb_rate['west'] = round(100 * prb_num / prb_den, 1)
			elif par == '南区':
				prb_rate['south'] = round(100 * prb_num / prb_den, 1)
			elif par == '北区':
				prb_rate['north'] = round(100 * prb_num / prb_den, 1)
			elif par == '专项':
				prb_rate['special'] = round(100 * prb_num / prb_den, 1)
			prb_num_all += prb_num
			prb_den_all += prb_den
		prb_rate['total'] = round(100 * prb_num_all / prb_den_all, 1)

	actual_row = ['east', 'west', 'south', 'north', 'special', 'total'] # 累计数
	result = [{},{},{},{},{},{}]
	i = 0
	for item in actual_row:
		result[i]['row_name'] = row_name[item]
		result[i]['volume_now'] = volume_now[item]
		result[i]['volume_all'] = volume_all[item]
		result[i]['solved_num'] = solved_num[item]
		result[i]['solved_rate'] = solved_rate[item]
		result[i]['prb_rate'] = prb_rate[item]
		i += 1
	# result.append(row_name)
	# result.append(volume_now)
	# result.append(volume_all)
	# result.append(solved_num)
	# result.append(solved_rate)
	# result.append(prb_rate)
	volume_alert_info_dict = {'vai': result}
	return JsonResponse(volume_alert_info_dict)


def download_volume_alert(request):
	"""提供扩容信息下载接口"""
	# index4 容量预警监控右上表格下载
	db = psycopg2.connect(database='postgres', user='postgres', password='postgres', host='192.168.61.20', port='5433')
	cursor = db.cursor()
	date_choose = date4_choose
	time_from = date_choose + ' 10:00:00'
	time_to = date_choose + ' 20:00:00'

	# 创建excel
	wb = xlwt.Workbook()
	ws_v = wb.add_sheet('volume')
	# 写入列名
	title_v = ['sdate', 'enb_id', 'z_id', 'z_name', 'branches', 'area', 'vendor', 'abc', 'mis', 'z_type',
			'scene_zdn', 'scene_kbn', 'kr_count', 'kr_cell1', 'kr_cell2', 'kr_cell3',
			'kr_cell4', 'kr_cell5', 'kr_cell6', 'prb_cell1', 'prb_cell2', 'prb_cell3',
			'prb_cell4', 'prb_cell5', 'prb_cell6', 'gprs_cell1', 'gprs_cell2', 'gprs_cell3',
			'gprs_cell4', 'gprs_cell5', 'gprs_cell6', 'rrc_cell1', 'rrc_cell2', 'rrc_cell3',
			'rrc_cell4', 'rrc_cell5', 'rrc_cell6', 'cqi_cell1', 'cqi_cell2', 'cqi_cell3',
			'cqi_cell4', 'cqi_cell5', 'cqi_cell6', 'avg_prb_cell1', 'avg_prb_cell2',
			'avg_prb_cell3', 'avg_prb_cell4', 'avg_prb_cell5', 'avg_prb_cell6', 'partition']
	for i in range(len(title_v)):
		ws_v.write(0, i, title_v[i])

	sql = "select a.*, b.partition FROM kpi_ty.kr_lte_pivot a, ui.cell_scene_lte b where a.sdate='%s' and a.enb_id=b.enb" % (date_choose)
	cursor.execute(sql)
	res_v = cursor.fetchall()
	if res_v:
		row = 1
		for tup in res_v:
			for i in range(50):
				if i == 0:
					ws_v.write(row, 0, str(tup[0]))
				else:
					ws_v.write(row, i, tup[i])
			row += 1
			# ws_v.write(row, 0, str(tup[0]))
			# ws_v.write(row, 1, tup[1])
			# ws_v.write(row, 2, tup[2])
			# ws_v.write(row, 3, tup[3])
			# ws_v.write(row, 4, tup[4])
			# ws_v.write(row, 5, tup[5])
			# ws_v.write(row, 6, tup[6])
			# ws_v.write(row, 7, tup[7])
			# ws_v.write(row, 8, tup[8])
			# ws_v.write(row, 9, tup[9])
			# ws_v.write(row, 10, tup[10])
			# ws_v.write(row, 11, tup[11])
			# ws_v.write(row, 12, tup[12])
			# ws_v.write(row, 13, tup[13])
			# ws_v.write(row, 14, tup[14])
			# ws_v.write(row, 15, tup[15])
			# ws_v.write(row, 16, tup[16])
			# ws_v.write(row, 17, tup[17])
			# ws_v.write(row, 18, tup[18])
			# ws_v.write(row, 19, tup[19])
			# ws_v.write(row, 20, tup[20])
			# ws_v.write(row, 21, tup[21])
			# ws_v.write(row, 22, tup[22])
			# ws_v.write(row, 23, tup[23])
			# ws_v.write(row, 24, tup[24])
			# ws_v.write(row, 25, tup[25])
			# ws_v.write(row, 26, tup[26])
			# ws_v.write(row, 27, tup[27])
			# ws_v.write(row, 28, tup[28])
			# ws_v.write(row, 29, tup[29])
			# ws_v.write(row, 30, tup[30])
			# ws_v.write(row, 31, tup[31])
			# ws_v.write(row, 32, tup[32])
			# ws_v.write(row, 33, tup[33])
			# ws_v.write(row, 34, tup[34])
			# ws_v.write(row, 35, tup[35])
			# ws_v.write(row, 36, tup[36])
			# ws_v.write(row, 37, tup[37])
			# ws_v.write(row, 38, tup[38])
			# ws_v.write(row, 39, tup[39])
			# ws_v.write(row, 40, tup[40])
			# ws_v.write(row, 41, tup[41])
			# ws_v.write(row, 42, tup[42])
			# ws_v.write(row, 43, tup[43])
			# ws_v.write(row, 44, tup[44])
			# ws_v.write(row, 45, tup[45])
			# ws_v.write(row, 46, tup[46])
			# ws_v.write(row, 47, tup[47])
			# ws_v.write(row, 48, tup[48])
			# ws_v.write(row, 49, tup[49])
			# row += 1


	# 保存及下载数据
	date = datetime.datetime.now()
	datestr = date.strftime('%y%m%d')
	# datestr = date_from.split('-')[2] + "_" + date_to.split('-')[2]
	response = HttpResponse(content_type='application/vnd.ms-excel')
	response['Content-Disposition'] = 'attachment; filename="volume_info_%s.xls"' % (datestr)
	wb.save(response)
	return response


def prb_num_distribution(request):
	"""选择日期上忙时对应的prb利用率的分布情况 - 小区数目"""
	db = psycopg2.connect(database='postgres', user='postgres', password='postgres', host='192.168.61.20', port='5433')
	cursor = db.cursor()

	date_choose = request.GET['starttime']

	if date_choose == '1':
		now = datetime.datetime.now()
		td = datetime.timedelta(days=1)

		time_1 = now - td
		date_choose = time_1.strftime('%Y-%m-%d')

	date1 = date_choose + ' 10:00:00'
	date2 = date_choose + ' 20:00:00'
	result = [{'rate':'10%', 'num':0}, {'rate':'20%', 'num':0}, {'rate':'30%', 'num':0}, {'rate':'40%', 'num':0}, {'rate':'50%', 'num':0},
			{'rate':'60%', 'num':0}, {'rate':'70%', 'num':0}, {'rate':'80%', 'num':0}, {'rate':'90%', 'num':0}, {'rate':'100%', 'num':0}]

	sql = "SELECT oid, sum(prb_num) as sum_prb_num, sum(prb_den) as sum_prb_den FROM kpi_ty.kpi_ty_lte where start_time in ('%s', '%s') group by oid" % (date1, date2)
	cursor.execute(sql)
	res = cursor.fetchall()
	for tup in res:
		if not tup[2]:
			prb_ratio = 0
		else:
			prb_ratio = round(100 * tup[1] / tup[2], 1)
		if prb_ratio < 10:
			result[0]['num'] += 1
		elif prb_ratio < 20:
			result[1]['num'] += 1
		elif prb_ratio < 30:
			result[2]['num'] += 1
		elif prb_ratio < 40:
			result[3]['num'] += 1
		elif prb_ratio < 50:
			result[4]['num'] += 1
		elif prb_ratio < 60:
			result[5]['num'] += 1
		elif prb_ratio < 70:
			result[6]['num'] += 1
		elif prb_ratio < 80:
			result[7]['num'] += 1
		elif prb_ratio < 90:
			result[8]['num'] += 1
		else:
			result[9]['num'] += 1
	pnd = {'pnd': result}
	return JsonResponse(pnd)


def volume_7days(request):
	"""返回7天内的容量预警信息"""
	# index4 容量预警监控左下柱状图
	db = psycopg2.connect(database='postgres', user='postgres', password='postgres', host='192.168.61.20', port='5433')
	cursor = db.cursor()

	# date_choose = date4_choose
	date_choose = request.GET['starttime']

	if date_choose == '1':
		now = datetime.datetime.now()
		td = datetime.timedelta(days=1)

		time_1 = now - td
		date_choose = time_1.strftime('%Y-%m-%d')

	time_1 = datetime.datetime.strptime(date_choose, "%Y-%m-%d")
	td = datetime.timedelta(days=1)
	m_d = []
	enbid = []
	for i in range(8):
		time_2 = time_1.strftime("%Y-%m-%d")
		month_day = time_1.strftime("%m-%d")
		time_1 = time_1 - td

		sql_vn = "select a.enb_id FROM kpi_ty.kr_lte_pivot a, ui.cell_scene_lte b where a.sdate='%s' and a.enb_id=b.enb group by a.enb_id" % (time_2)
		cursor.execute(sql_vn)
		res_vn = cursor.fetchall()
		a = []
		for tup in res_vn:
			a.append(tup[0])

		m_d.append(month_day)
		enbid.append(a)
	result = []
	for i in range(2,9):
		dic = {}
		dic['time'] = m_d[-i]
		dic['volume'] = len(enbid[-i])
		solved = 0
		for item in enbid[-i+1]:
			if item not in enbid[-i]:
				solved += 1
		dic['solved'] = solved
		result.append(dic)
	vs = {'vs': result}
	return JsonResponse(vs)

def bingtu(request):
	"""七大场景在所选时间的忙时的prb利用率"""
	# bt = {'bt': [{'value':335, 'name':'直接'}, {'value':310, 'name':'邮件营销'}, {'value':234, 'name':'联盟广告'}, {'value':135, 'name':'视频广告'}, {'value':1548, 'name':'搜索引擎'}]}
	db = psycopg2.connect(database='postgres', user='postgres', password='postgres', host='192.168.61.20', port='5433')
	cursor = db.cursor()

	date_choose = request.GET['starttime']

	if date_choose == '1':
		now = datetime.datetime.now()
		td = datetime.timedelta(days=1)

		time_1 = now - td
		date_choose = time_1.strftime('%Y-%m-%d')

	date1 = date_choose + ' 10:00:00'
	date2 = date_choose + ' 20:00:00'
	sql = '''select a.cj_type, sum(b.prb_num) as sum_prb_num, sum(b.prb_den) as sum_prb_den FROM ui.cell_scene_lte a left join kpi_ty.kpi_ty_lte b on "substring"(b.oid,"position"(b.oid,'.')+1) = a.oid where b.start_time in ('%s', '%s') group by a.cj_type''' % (date1, date2)
	cursor.execute(sql)
	res = cursor.fetchall()
	three_one = {'name':'三高一地', 'prb_num':0, 'prb_den':0}
	result = []
	for tup in res:
		if tup[0] in ('高铁','高架','高速','地铁'):
			three_one['prb_num'] += tup[1]
			three_one['prb_den'] += tup[2]
		else:
			dic = {}
			dic['name'] = tup[0]
			dic['value'] = round(100 * tup[1] / tup[2], 1)
			result.append(dic)

	three_one['value'] = round(100 * three_one['prb_num'] / three_one['prb_den'], 1)
	result.append(three_one)
	bs = {'bs': result}
	return JsonResponse(bs)

# def special_3GKPI(request):
# 	"""具体场景3G-KPI接通率和掉话率"""
# 	# name_scene = '外环高架' #需要获取前端的具体场景名称
# 	name_scene = name_special_scene
# 	# name = request.GET['du']
# 	# print(name_special_scene + '123')
# 	sql = ("select b.start_time, sum(b.amr) as sum_amr, sum(b.gprs_mb) as sum_gprs_mb, sum(b.rrc_num) as sum_rrc_num, "
# 		"sum(b.rrc_den) as sum_rrc_den, sum(b.rab_num) as sum_rab_num, sum(b.rab_den) as sum_rab_den, sum(b.drop_num) as sum_drop_num, "
# 		"sum(b.drop_den) as sum_drop_den "
# 		"from ui.cell_scene_umts a left join kpi_ty.kpi_ty_umts b on a.oid=b.oid where a.scene_name='%s' and b.start_time in "
# 		"('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s',"
# 		"'%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s') group by start_time order by start_time"
# 		) % (name_scene,time_all[0],time_all[1],time_all[2],time_all[3],time_all[4],time_all[5],time_all[6],time_all[7],time_all[8],time_all[9],
# 		time_all[10],time_all[11],time_all[12],time_all[13],time_all[14],time_all[15],time_all[16],time_all[17],time_all[18],time_all[19],
# 		time_all[20],time_all[21],time_all[22],time_all[23],time_all[24],time_all[25],time_all[26],time_all[27],time_all[28],time_all[29],
# 		time_all[30],time_all[31],time_all[32],time_all[33],time_all[34],time_all[35])
# 	cursor.execute(sql)
# 	res = cursor.fetchall()
# 	sp_3G_list = []
# 	for tup in res:
# 		if tup[0] is not None:
# 			dic = {}
# 			dic['time'] = str(tup[0]).split()[1]
# 			dic['amr'] = tup[1] #hua wu liang
# 			dic['gprs_mb'] = tup[2] #liu liang
# 			dic['receive_rate'] = round(100 * tup[3] * tup[5] / tup[4] / tup[6], 2) #tong hua lv
# 			if tup[8] == 0:
# 				dic['drop_rate'] = 0
# 			else:
# 				dic['drop_rate'] = round(100 * tup[7] / tup[8], 2) #diao xian lv
# 			sp_3G_list.append(dic)
# 	special3G_dict = {'sp_3g': sp_3G_list}
# 	# print(special3G_dict)
#
# 	# special3G_dict = {"sp_3g": [{"time": "15:00", "amr": 64.1093, "gprs_mb": 5589.995499999998, "receive_rate": 99.48, "drop_rate": 0.1},
# 	# 							{"time": "16:00", "amr": 80, "gprs_mb": 6000, "receive_rate": 90, "drop_rate": 0.2},
# 	# 							{"time": "17:00", "amr": 60, "gprs_mb": 7000, "receive_rate": 95, "drop_rate": 0.15},
# 	# 							{"time": "18:00", "amr": 70, "gprs_mb": 5000, "receive_rate": 96, "drop_rate": 0.1},
# 	# 							{"time": "19:00", "amr": 40, "gprs_mb": 4000, "receive_rate": 97, "drop_rate": 0.25}]}
# 	return JsonResponse(special3G_dict)
