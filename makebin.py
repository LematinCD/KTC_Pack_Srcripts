#!/usr/bin/env python
# -*- coding:UTF-8 -*-
import os
import re
import sys
import sqlite3
import shutil
import subprocess
import logging
import logging.handlers
import time
import json
import stat

project_path =''
module_path = ''
db_path = 'tvdatabase/Database/'
pq_path = 'pq_test'
tups = ('mode', 'type')
country_dict = {}
language_dict = {}
timezone_dict = {}
config_dict = {}

debug_info = []
error_dict = {}

log_path = "Log"
log = logging.getLogger(__name__)
def set_logging():
	abs_log_path = os.path.join(os.path.abspath("."),log_path)
	if not os.path.exists(abs_log_path):
		os.makedirs(abs_log_path)
		os.chmod(abs_log_path,stat.S_IRWXU)
	log.setLevel(logging.INFO)
	handler = logging.handlers.TimedRotatingFileHandler(os.path.join(abs_log_path,'makebin.log'),when='D',interval=1,backupCount=30)
	handler.setLevel(logging.INFO)
	formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
	handler.setFormatter(formatter)
	log.addHandler(handler)


#还原repo库
def code_restore():
	CMD = ['repo','forall','-c','git','checkout','.']
	try:
		out = subprocess.check_output(CMD, shell = False)
	except subprocess.CalledProcessError as err:
		log.error("Code Restore Fail!")
		error_dict['code_restore'] = 'fail'
		return
	else:
		log.info("Code Restore Succees")
		debug_info.append("Code Restore:Success")




def throws():
	raise RuntimeError('this is the error message')

def loadfile_config(file_name, tmp_dict):
	abs_file_path = os.path.join(os.path.abspath("."),file_name)
	try:
		f = open(abs_file_path, 'r')
	except IOError:
		log.error("Error: Open " + file_name + " fail!")
		error_dict[file_name] = 'fail'
		return
	else:
		log.info("Open " + file_name + " successfully!")
		for line in f.readlines():
			line = line.strip()
			if not len(line):
				continue
			tmp_dict[line.split(':')[0]] = line.split(':')[1]
	f.close()

def import_pq_data(filename):
	abs_pq_data_path = os.path.join(os.path.abspath("."),os.path.join(project_path,os.path.join(pq_path,config_dict['pq'])))
	final_db_path = os.path.join(project_path,os.path.join(module_path,db_path))
	import_count = 0
	try:
		r = open(os.path.join(abs_pq_data_path,filename),'r')
	except IOError:
		log.error("Error: Open "+ filename + " fail!")
		error_dict[filename] = 'none'
		return
	else:
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
				log.error("Error_LineNum:"+str(num)+"  value:"+value)
				error_dict[filename] = 'fail'
				return
			else:
				#log.info(value+'commit transacation')
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
		log.error("The Country doesn't exist'!")
		error_dict['country'] = 'none'
		return
	for key2 in sorted(language_dict.keys()):
		if str(language).lower() == key2.lower():
			language_key = key2
			break
	if language_key == "":
		log.error("The Language doesn't exist'!")
		error_dict['language'] = 'none'
		return
	abs_db_path=os.path.join(os.path.abspath("."),os.path.join(project_path,os.path.join(module_path,db_path)))
	conn = sqlite3.connect(os.path.join(abs_db_path, 'user_setting.db'))
	c = conn.cursor()
	log.info("Open user_setting.db successfully!")
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
		log.error("The timezone doesn't exist'!")
		error_dict['timezone'] = 'none'
		return
	abs_db_path=os.path.join(os.path.abspath("."),os.path.join(project_path,os.path.join(module_path,db_path)))
	conn = sqlite3.connect(os.path.join(abs_db_path, 'user_setting.db'))
	c = conn.cursor()
	log.info("Open user_setting.db successfully!")
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
		if file.find(panel)>-1 and file.find(board_type[0:3])>-1:
			tmp_file_name = file
			abs_src_path=os.path.join(os.path.abspath("."),os.path.join(project_path,panel_src_path))
			abs_dst_path=os.path.join(os.path.abspath("."),os.path.join(project_path,os.path.join(module_path,panel_dst_path)))
			CMD = ["cp", os.path.join(abs_src_path,file), abs_dst_path]
			try:
				out = subprocess.check_call(CMD, shell=False)
			except subprocess.CalledProcessError as err:
				log.error("set panel file copy error")
				error_dict['copy_panel_file'] = 'fail'
	if tmp_file_name == '':
		log.error("No panel file")
		error_dict['panel'] = 'none'
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
		for item in tmp_list:
			error_dict[item] = 'none'
		return

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
def set_build_prop(boardType,DDRSize,lcd_density,SDA):
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
			elif line.startswith('ro.product.serial'):
				w.write(re.sub(r'=(.*)',"=SDA"+SDA, line))
			else:
				w.write(line)
	debug_info.append("设置版型:OK")
	debug_info.append("设置内存大小:OK")
	debug_info.append("设置DPI:OK")

uart_path = "scripts"

def set_UARTOnOff(uart_status):
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
			error_dict['logo_dir'] = 'empty'
			return
		for filename in os.listdir(abs_Logo_src_path):
			fp =os.path.join(abs_Logo_src_path,filename)
			if os.path.isfile(fp):
	 			shutil.copyfile(os.path.join(abs_Logo_src_path,filename),os.path.join(abs_Logo_dst_path,'boot0.jpg'))
			else:
				error_dict['logo_file'] = 'none'
	debug_info.append("设置Logo:OK")



Animation_src_path = 'animation_tmp'
Animation_dst_path = 'system/media'
def set_animation(animation):
	abs_animation_src_path = os.path.join(os.path.abspath("."),Animation_src_path)
	abs_animation_dst_path = os.path.join(os.path.abspath("."),os.path.join(project_path,os.path.join(module_path,Animation_dst_path)))
	if animation == 'default':
		pass
	else:
		if not os.listdir(abs_animation_src_path):
			error_dict['animation_dir'] = 'empty'
			return
		for filename in os.listdir(abs_animation_src_path):
			fp =os.path.join(abs_animation_src_path,filename)
			if os.path.isfile(fp):
	 			shutil.copyfile(os. path.join(abs_animation_src_path,filename),os.path.join(abs_animation_dst_path,'bootanimation.zip'))
			else:
				error_dict['animation_file'] = 'none'
	debug_info.append("设置开机动画:OK")
		

def remove_Logo_Animation():
	abs_Logo_src_path = os.path.join(os.path.abspath("."),Logo_src_path)
	abs_animation_src_path = os.path.join(os.path.abspath("."),Animation_src_path)
	shutil.rmtree(abs_Logo_src_path)
	os.mkdir(abs_Logo_src_path)
	shutil.rmtree(abs_animation_src_path)
	os.mkdir(abs_animation_src_path)


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
			error_dict['apk'] = 'none'
			return
		for filename in os.listdir(abs_apk_src_path):
			apk_list.append(filename.strip(".apk"))
			fp = os.path.join(abs_apk_src_path,filename)
			if os.path.isfile(fp):
				if  not os.path.isdir(os.path.join(abs_apk_dst_path,filename.strip('.apk'))):
					 os.makedirs(os.path.join(abs_apk_dst_path,filename.strip('.apk')))
				shutil.copy(os.path.join(abs_apk_src_path,filename),os.path.join(abs_apk_dst_path,filename.strip('.apk')))
	debug_info.append("设置 APK:OK")



def print_info():
	if error_dict:
		error_dict['status'] = 'fail'
		print json.dumps(error_dict)
		sys.exit(1)
	else:
		pass

def final_print_info():
	if error_dict:
		error_dict['status'] = 'fail'
		print json.dumps(error_dict)
		sys.exit(1)
	else:
		tmp_dict = {'status':'success'}
		print json.dumps(tmp_dict)


def delete_APK():
	abs_apk_dst_path = os.path.join(os.path.abspath("."),os.path.join(project_path,os.path.join(module_path,apk_dst_path)))
	for filename in os.listdir(abs_apk_dst_path):
		if filename in apk_list:
			shutil.rmtree(os.path.join(abs_apk_dst_path,filename))




build_path = 'my_scripts'
MM_scripts_path = 'my_scripts/MM_scripts'
def copy_scripts():
	abs_scripts_src_path = os.path.join(os.path.abspath("."),'my_scripts')
	abs_build_dst_path = os.path.join(os.path.abspath("."),os.path.join(project_path,build_path))
	abs_MM_dst_path = os.path.join(os.path.abspath("."),os.path.join(project_path,MM_scripts_path))
	for file in os.listdir(abs_scripts_src_path):
		if file == 'build.sh':
			shutil.copy(os.path.join(abs_scripts_src_path,file),abs_build_dst_path)
		elif file == 'releaseimage.sh' or file == 'make_usb_upgrade.sh':
			shutil.copy(os.path.join(abs_scripts_src_path,file),abs_MM_dst_path)



make_usb_upgrade_file_path = 'my_scripts/MM_scripts'
def format_make(filename):
	abs_make_path = os.path.join(os.path.join(os.path.abspath("."),project_path),make_usb_upgrade_file_path)
	CMD = ["find", abs_make_path, "-name", "make_usb_upgrade_tmp.sh"]
	out = ''
	try:
		out = subprocess.check_output(CMD, shell=False)
	except subprocess.CalledProcessError as err:
		print "find error"
	if out == '':
		CMD = ["cp", os.path.join(abs_make_path, 'make_usb_upgrade.sh'),os.path.join(abs_make_path, 'make_usb_upgrade_tmp.sh')]
		try:
			out = subprocess.check_output(CMD, shell=False)
		except subprocess.CalledProcessError as err:
			print "cp error1"
	else:
		CMD = ["cp", os.path.join(abs_make_path, 'make_usb_upgrade_tmp.sh'),os.path.join(abs_make_path, 'make_usb_upgrade.sh')]
		try:
			out = subprocess.check_output(CMD, shell=False)
		except subprocess.CalledProcessError as err:
			print "cp error2"
	with open(os.path.join(abs_make_path,filename), 'r') as r:
		lines = r.readlines()
	with open(os.path.join(abs_make_path,filename), 'w') as w:
		flag = False
		my_tmp = ''
		for line in lines:
			for tup in tups:
				if re.match('^(\s*) select(\s*)' + tup + '(.*)', line): 
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
				w.write('tmp=' + "'" +'Y' + "'" + '\n')
				continue 
			if flag:
				w.write('#' + line)
			elif not flag:
				w.write(line)

origin_path = os.path.abspath('/home/ktcfwm')
def make_image():
	os.chdir(os.path.join(project_path,'my_scripts'))
	CMD = ['./build.sh '+config_dict['moduleType']+' 348_DVBT_8G']
	try:
		out = subprocess.check_call(CMD, shell=True)
	except subprocess.CalledProcessError as err:
		error_dict['make_image'] = 'fail'
	os.chdir(origin_path)


#if __name__=='__main__'	:


os.chdir('/home/ktcfwm')
start_time = time.time()

#code_restore()
set_logging()
loadfile_config('swinfo.txt', config_dict)
set_project_module_path(config_dict['project'],config_dict['moduleType'])

copy_scripts()
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
set_build_prop(config_dict['boardType'],config_dict['DDRSize'],config_dict['lcd_density'],config_dict['SDA'])
set_Logo(config_dict['logo'])
set_animation(config_dict['animation'])
set_UARTOnOff(config_dict['UARTOnOff'])
format_make('make_usb_upgrade.sh')
print_info()
make_image()
final_print_info()
delete_APK()
remove_Logo_Animation()
end_time = time.time()
print "\033[1;35m****************打包完成*****************\033[0m"
for item in debug_info:
	print "\033[1;35m       %s" % item
print "\033[1;35m总共耗时:%s秒\033[0m" % str(end_time-start_time)
print "\033[1;35m*****************************************\033[0m"

