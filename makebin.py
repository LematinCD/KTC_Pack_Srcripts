#!/usr/bin/env python
# -*- coding:UTF-8 -*-
import os
import re
import sys
import sqlite3
import shutil
import subprocess
import logging
import time

project_path =''
module_path = ''
db_path = 'tvdatabase/Database/'
pq_path = 'pq_test'
tups = ('mode', 'type')
logging.basicConfig(level=logging.INFO)
log = logging.getLogger('db_log')
country_dict = {}
language_dict = {}
timezone_dict = {}
config_dict = {}
debug_info = []
#还原repo库
def code_restore():
	CMD = ['repo','forall','-c','git','checkout','.']
	try:
		out = subprocess.check_output(CMD, shell = False)
	except subprocess.CalledProcessError as err:
		print "Code Restore Error!"
	debug_info.append("文件还原:OK")


def throws():
	raise RuntimeError('this is the error message')

def loadfile_config(file_name, tmp_dict):
    try:
        f = open(file_name, 'r')
    except IOError:
        print "Error: Open " + file_name + " fail!"
    else:
        print "Open " + file_name + " successfully!"
        for line in f.readlines():
            line = line.strip()
            if not len(line):
                continue
            tmp_dict[line.split(':')[0]] = line.split(':')[1]
        f.close()

def import_pq_data(filename):
	abs_pq_data_path = os.path.join(os.path.abspath("."),os.path.join(project_path,os.path.join(pq_path,config_dict['pq'])))
	global db_path
	final_db_path = os.path.join(project_path,os.path.join(module_path,db_path))
	import_count = 0
	with open(os.path.join(abs_pq_data_path,filename),'r') as r:
		lines = r.readlines()
		conn = sqlite3.connect(os.path.join(final_db_path,'factory.db'))
		c = conn.cursor()
		for (num,value) in enumerate(lines):
			if re.match('UPDATE(\s*)tbl_(.*);(\s*)$',value):
				import_count = import_count + 1
				try:
					c.execute(value)
				except:
					conn.rollback()
					log.error('Rolling back transaction')
					print "Error_LineNum:"+str(num)+"  value:"+value
					raise
				else:
					log.info(value+'commit transacation')
		 			conn.commit()
		conn.close()

	debug_info.append("导入 "+filename+ " 数据:OK")
	debug_info.append("导入:"+str(import_count)+" 条")


def set_project_module_path(project,module_type):
	global project_path
	global module_path
	project_path = project
	module_path = module_type


def set_country_language(country, language):
	country_key = ""
	language_key = ""
	for key1 in sorted(country_dict.keys()):
		if str(country).lower() == key1.lower():
			country_key = key1
			break
	if country_key == "":
		print "The Country doesn't exist'!"
		return
	for key2 in sorted(language_dict.keys()):
		if str(language).lower() == key2.lower():
			language_key = key2
			break
	if language_key == "":
		print "The Language doesn't exist'!"
		return
	abs_db_path=os.path.join(os.path.abspath("."),os.path.join(project_path,os.path.join(module_path,db_path)))
	conn = sqlite3.connect(os.path.join(abs_db_path, 'user_setting.db'))
	c = conn.cursor()
	print "Open user_setting.db successfully!"
	sql = "UPDATE tbl_SystemSetting set Country = ?,Language = ?"
	c.execute(sql, (country_dict[country_key], language_dict[language_key]))
	conn.commit()
	conn.close()
	debug_info.append("设置国家: OK")
	debug_info.append("设置语言: OK")

def set_timezone(timezone):
	timezone_key = ""
	for key in sorted(timezone_dict.keys()):
		if str(timezone).lower() == key.lower():
			timezone_key = key
			break
	if timezone_key == "":
		print "The timezone doesn't exist'!"
		return
	abs_db_path=os.path.join(os.path.abspath("."),os.path.join(project_path,os.path.join(module_path,db_path)))
	conn = sqlite3.connect(os.path.join(abs_db_path, 'user_setting.db'))
	c = conn.cursor()
	print "Open user_setting.db successfully!"
	sql = "UPDATE tbl_TimeSetting set eTimeZoneInfo = ?"
	c.execute(sql, (timezone_dict[timezone_key],))
	conn.commit()
	conn.close()

panel_cus_path = 'tvconfig/config/model'
panel_dst_path = 'tvconfig/config/panel'
panel_src_path = 'panel_test'
def set_panel(panel,board_type):
	panel = panel.strip(".ini")
	file_list = os.listdir(os.path.join(project_path,panel_src_path))
	tmp_file_name = ''
	for file in file_list:
		if file.find(panel)>-1 and file.find(board_type)>-1:
			tmp_file_name = file
			abs_src_path=os.path.join(os.path.abspath("."),os.path.join(project_path,panel_src_path))
			abs_dst_path=os.path.join(os.path.abspath("."),os.path.join(project_path,os.path.join(module_path,panel_dst_path)))
			CMD = ["cp", os.path.join(abs_src_path,file), abs_dst_path]
			try:
				out = subprocess.check_call(CMD, shell=False)
			except subprocess.CalledProcessError as err:
				print "cp Error"
	if tmp_file_name == '':
		print "No panel file!!!"
		return
	final_panel_path = os.path.join(project_path,os.path.join(module_path,panel_cus_path))
	with open(os.path.join(final_panel_path,'Customer_1.ini'), 'r') as r:
		lines = r.readlines()
	with open(os.path.join(final_panel_path ,'Customer_1.ini'), 'w') as w:
		for line in lines:
			if line.startswith('m_pPanelName'):
				w.write(re.sub(r'panel/(.*?).ini',"panel/"+tmp_file_name, line))
			elif line.startswith('Manufacturer_Name'):
				if config_dict['EDID_manufacturer'] != 'default':
					w.write(re.sub(r'=(\s*)"(\w*)"','= "'+config_dict['EDID_manufacturer']+'"', line))
				else:
					w.write(line)
			elif line.startswith('Product_Code'):
				if config_dict['EDID_produceCode'] != 'default':
					w.write(re.sub(r'=(\s*)(\w*)',"= "+config_dict['EDID_produceCode'], line))
				else:
					w.write(line)
			elif line.startswith('Monitor_Name'):
				if config_dict['EDID_productName'] != "default":
					w.write(re.sub(r'=(\s*)"(.*)"','= "'+config_dict['EDID_productName']+'"', line))
				else:
					w.write(line)
			else:
				w.write(line)
	r.close()
	w.close()
	debug_info.append("设置Panel:OK")


PQ_dst_path = 'tvconfig/config/pq/'
DLC_dst_path = 'tvconfig/config/DLC/'
color_dst_path = 'tvconfig/config/ColorMatrix/'
PQ_src_path = 'pq_test'
exists_file = []
def search_file(path,files):
	for filename in os.listdir(path):
		fp =os.path.join(path,filename)
		for file in files:
			if os.path.isfile(fp) and file == filename:
				exists_file.append(file)
		 		break

def PQ_test(pq):
	abs_src_path = os.path.join(project_path,os.path.join(pq_path,pq))
	find_file = ["Main.bin","Main_Text.bin","DLC.ini","ColorMatrix.ini","ColorTemp.txt","nonlinear.txt"]
	search_file(abs_src_path,find_file)
	tmp_list = []  
	tmp_list = list(set(find_file).difference(set(exists_file)))
	if tmp_list:	
		with open("pq_not_exists.txt",'w') as w:
			for item in tmp_list:
				w.write(item+'\n')
		sys.exit(1)
	

def set_PQ(pq):
	abs_src_path=os.path.join(os.path.abspath("."),os.path.join(project_path,os.path.join(PQ_src_path,pq)))
	abs_dst_path=os.path.join(os.path.abspath("."),os.path.join(project_path,os.path.join(module_path,PQ_dst_path)))
	abs_dlc_dst_path=os.path.join(os.path.abspath("."),os.path.join(project_path,os.path.join(module_path,DLC_dst_path)))
	abs_color_dst_path=os.path.join(os.path.abspath("."),os.path.join(project_path,os.path.join(module_path,color_dst_path)))
	file_list = os.listdir(abs_src_path)
	for file in file_list:
		if file == "Main.bin" or file == "Main_Text.bin":
			shutil.copy(os.path.join(abs_src_path,file),abs_dst_path)
		elif file == "DLC.ini":
			shutil.copy(os.path.join(abs_src_path,file),abs_dlc_dst_path)
		elif file == "ColorMatrix.ini":
			shutil.copy(os.path.join(abs_src_path,file),abs_color_dst_path)
		else:
			continue
	debug_info.append("设置 PQ:OK")

build_prop_path = 'system'
def set_build_prop(boardType,DDRSize,lcd_density):
	final_build_prop_path = os.path.join(project_path,os.path.join(module_path,build_prop_path))
	with open(os.path.join(final_build_prop_path,'build.prop'), 'r') as r:
		lines = r.readlines()
	with open(os.path.join(final_build_prop_path ,'build.prop'), 'w') as w:
		for line in lines:
			if line.startswith('ktc.board.type='):
				w.write(re.sub(r'=(.*)',"="+boardType, line))
			elif line.startswith('ktc.board.memory='):
				w.write(re.sub(r'=(.*)',"="+DDRSize, line))
			elif line.startswith('ro.sf.lcd_density='):
				w.write(re.sub(r'=(.*)',"="+lcd_density, line))
			else:
				w.write(line)
	debug_info.append("设置版型:OK")
	debug_info.append("设置内存大小:OK")
	debug_info.append("设置DPI:OK")

uart_path = "scripts"

def set_UARTOnOff(uart_status):
	print uart_status
	abs_uart_path = os.path.join(os.path.abspath("."),os.path.join(project_path,os.path.join(module_path,os.path.join(uart_path,'set_config'))))
	with open(abs_uart_path, 'r') as r:
		lines = r.readlines()
	with open(abs_uart_path, 'w') as w:
		for line in lines:
			if line.startswith('setenv UARTOnOff'):
				w.write(re.sub(r'setenv UARTOnOff (.*)','setenv UARTOnOff '+uart_status,line))
			else:
				w.write(line)



Logo_src_path = 'logo_tmp'
Logo_dst_path = 'tvconfig'
def set_Logo(logo_set):
	abs_Logo_src_path = os.path.join(os.path.abspath("."),Logo_src_path)
	abs_Logo_dst_path = os.path.join(os.path.abspath("."),os.path.join(project_path,os.path.join(module_path,Logo_dst_path)))
	if logo_set == 'default':
		pass
	else:
		if not os.listdir(abs_Logo_src_path):
			print "dir empty"
			sys.exit(1)
		for filename in os.listdir(abs_Logo_src_path):
			fp =os.path.join(abs_Logo_src_path,filename)
			if os.path.isfile(fp) and logo_set == filename:
	 			shutil.copyfile(os.path.join(abs_Logo_src_path,logo_set),os.path.join(abs_Logo_dst_path,'boot0.jpg'))
				print "exists!!!"
			else:
				print "Logo file not exists!!!"
		shutil.rmtree(abs_Logo_src_path)
		os.mkdir(abs_Logo_src_path)
	debug_info.append("设置Logo:OK")


Animation_src_path = 'animation_tmp'
Animation_dst_path = 'system/bin'
def set_animation(animation):
	abs_animation_src_path = os.path.join(os.path.abspath("."),Animation_src_path)
	abs_animation_dst_path = os.path.join(os.path.abspath("."),os.path.join(project_path,os.path.join(module_path,Animation_dst_path)))
	if animation == 'default':
		pass
	else:
		if not os.listdir(abs_animation_src_path):
			print "animation dir empty!"
			sys.exit(1)
		for filename in os.listdir(abs_animation_src_path):
			fp =os.path.join(abs_animation_src_path,filename)
			if os.path.isfile(fp) and animation == filename:
	 			shutil.copyfile(os.path.join(abs_animation_src_path,animation),os.path.join(abs_animation_dst_path,'bootanimation'))
				print "exists!!!"
			else:
				print "not exists!!!"
		shutil.rmtree(abs_animation_src_path)
		os.mkdir(abs_animation_src_path)
	debug_info.append("设置开机动画:OK")
		

# def set_SDA(sdanum):


apk_dst_path = 'system/app'
apk_src_path = 'apklist_tmp'
apk_list = []

def set_apk(apk):
	abs_apk_src_path = os.path.join(os.path.abspath("."),apk_src_path)
	abs_apk_dst_path = os.path.join(os.path.abspath("."),os.path.join(project_path,os.path.join(module_path,apk_dst_path)))
	if apk == 'default':
		pass
	else:
		if not os.listdir(abs_apk_src_path):
			print "apk dir empty!"
			sys.exit(1)
		for filename in os.listdir(abs_apk_src_path):
			apk_list.append(filename.strip(".apk"))
			fp = os.path.join(abs_apk_src_path,filename)
			if os.path.isfile(fp):
				if not os.path.isdir(os.path.join(abs_apk_dst_path,filename.strip('.apk'))):
					os.makedirs(os.path.join(abs_apk_dst_path,filename.strip('.apk')))
				shutil.copy(os.path.join(abs_apk_src_path,filename),os.path.join(abs_apk_dst_path,filename.strip('.apk')))
	debug_info.append("设置 APK:OK")


def delete_APK():
	abs_apk_dst_path = os.path.join(os.path.abspath("."),os.path.join(project_path,os.path.join(module_path,apk_dst_path)))
	for filename in os.listdir(abs_apk_dst_path):
		if filename in apk_list:
			shutil.rmtree(os.path.join(abs_apk_dst_path,filename))

make_usb_upgrade_file_path = 'my_scripts/MM_scripts'
def format_make(filename):
	abs_path = os.path.join(os.path.join(os.path.abspath("."),project_path),make_usb_upgrade_file_path)
	CMD = ["find", abs_path, "-name", "make_usb_upgrade_tmp.sh"]
	out = ''
	try:
		out = subprocess.check_output(CMD, shell=False)
	except subprocess.CalledProcessError as err:
		print "find error"
	if out == '':
		CMD = ["cp", os.path.join(abs_path, 'make_usb_upgrade.sh'),os.path.join(abs_path, 'make_usb_upgrade_tmp.sh')]
		try:
			out = subprocess.check_output(CMD, shell=False)
		except subprocess.CalledProcessError as err:
			print "cp error1"
	else:
		CMD = ["cp", os.path.join(abs_path, 'make_usb_upgrade_tmp.sh'),os.path.join(abs_path, 'make_usb_upgrade.sh')]
		try:
			out = subprocess.check_output(CMD, shell=False)
		except subprocess.CalledProcessError as err:
			print "cp error2"
	with open(os.path.join(abs_path,filename), 'r') as r:
		lines = r.readlines()
	with open(os.path.join(abs_path,filename), 'w') as w:
		flag = False
		my_tmp = ''
		for line in lines:
			for tup in tups:
				if re.match('^(\s*)select(\s*)' + tup + '(.*)', line): 
					my_tmp = tup
			if re.match('^(\s*)select(.*)', line) or re.match('^(\s*)break;(.*)', line):
				flag = True
			elif re.match('^(\s*)fi(.*)', line) and (flag == True):
				flag = False
				w.write('#' + line)
				w.write('\t' + my_tmp + '=' + "'" + config_dict[my_tmp] + "'")
				continue 
			elif re.match('^(\s*)done(.*)', line) and (flag == True):
				flag = False
				w.write('#' + line)
				continue
			elif re.match('(\s*)read(\s*)-p(\s*)"Full Upgrade(.*)', line):
				w.write('# ' + line)
				w.write('tmp=' + "'" + config_dict['tmp'] + "'" + '\n')
				continue
			if flag:
				w.write('#' + line)
			elif not flag:
				w.write(line)
origin_path = os.path.abspath(os.curdir)
def make_image():
	os.chdir(os.path.join(project_path,'my_scripts'))
	CMD = ['./build.sh '+config_dict['moduleType']]
	try:
		out = subprocess.check_call(CMD, shell=True)
	except subprocess.CalledProcessError as err:
		print "make images error!"
	os.chdir(origin_path)


# if __name__=='__main__'	:


start_time = time.time()

code_restore()
loadfile_config('swinfo.txt', config_dict)
set_project_module_path(config_dict['project'],config_dict['moduleType'])

loadfile_config('country.txt', country_dict)
loadfile_config('language.txt', language_dict)
loadfile_config('timezone.txt', timezone_dict)
import_pq_data('ColorTemp.txt')
import_pq_data('nonlinear.txt')
set_panel(config_dict['panel'],config_dict['boardType'])
set_apk(config_dict['apkList'])
PQ_test(config_dict['pq'])
set_PQ(config_dict['pq'])
set_country_language(config_dict['country'], config_dict['language'])
set_timezone(config_dict['timezone'])
set_build_prop(config_dict['boardType'],config_dict['DDRSize'],config_dict['lcd_density'])
set_Logo(config_dict['logo'])
set_animation(config_dict['animation'])
set_UARTOnOff(config_dict['UARTOnOff'])

format_make('make_usb_upgrade.sh')
make_image()
delete_APK()
end_time = time.time()
print "\033[1;35m****************打包完成*****************\033[0m"
for item in debug_info:
	print "\033[1;35m       %s" % item
print "\033[1;35m总共耗时:%s秒\033[0m" % str(end_time-start_time)
print "\033[1;35m*****************************************\033[0m"

