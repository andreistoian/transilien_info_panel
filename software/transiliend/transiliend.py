import os
import os.path
import sys
import glob
import time
import threading
import thread
import urllib2
import json
import base64
from math import floor
import xml.etree.ElementTree as ET
from datetime import datetime
from datetime import timedelta
import mysql.connector
import traceback
import serial
import serial.tools.list_ports

API_username = ""
API_password = ""

IDFM_API_KEY = os.environ.get('IDFM_API_KEY', None)

assert IDFM_API_KEY is not None 

TT_DIR = 'tt/'

REFRESH_PERIOD = 10

MINS_ST_DENIS_NORD = 8
MIN_TIME_TO_STATION = 1


# ['MonitoredVehicleJourney']['DestinationRef']
def make_stop(id):
	return 'STIF:StopPoint:Q:' + id + ':'

GARES_PARIS = { 
	'C': [
		'41251', # St Quentien
		'41217', # Versailles Chateau
		'473919', '473911', '473921', '473926', '473920', '412842', '473909', '473906', '473905', '473903',  #Pontoise
		'41075', '472491', '470910', '411487', '471885', # Invalides
		'471233', '471077', '471976', '472718', '472582', '472323', '472865', # Austerlitz
	],
	'D': [
		'411439', #Gare de Creil'
		'411420', #  Orry-la-Ville Coye la Foret
		'472711', '470637', '472411', '411369', '471680', '472548', '470904', '411370', '471426', # Stade De France
		'470983', '470949', '470954', '470903', '470898', '470891', '470890', '470759', '470752', 
		'470737', '470689', '470683', '470664', '470646', '470864', '470869', '470877', '470842', 
		'470846', '470809', '470812', '470799', '470762', '470774', '470773', '41396', # Gare de lyon
		'470637', '470605', '472927', '472932', '472902', '472915', '472887', '472892', '472867', '472878',
		'472845', '472848', '472828', '472837', '472982', '472997', '472940', '41251', '411475', '411500', '411451'
		'411427', '420316', '41357', '41239', '41385', '41145', '41160', '41141', '41365', '41254',  # Gare du nord
		'41097', '470760', '470629', '472930', '472908', '472918', '472882' # Villiers le bel
	]
}

GARES_BANLIEUE = { 
	'C': [
		'41316', #"Gare de Saint-Martin d'Etampes", 
		'41324', #"Gare de Dourdan" 
		'471121', '471238', '471217', '471229', '471085', '471095', '471043', #Bretigny
	], 
	'D': [
		'41336' #'Gare de Corbeil Essonnes'
	] 
}

GARES_IGNORE = list(map(make_stop, [
	'411484', # Malsherbes
	'41361', #Melun
]))

GARES_LISTS = [
	list(map(make_stop, GARES_PARIS['C'])), 
	list(map(make_stop, GARES_PARIS['D'])),
	list(map(make_stop, GARES_BANLIEUE['C'])), 
	list(map(make_stop, GARES_BANLIEUE['D']))
]

NUM_LISTS = 4 #len(GARES_LISTS)

NAME_GARE_JUVISY = "JUVISY"
NAME_GARE_MASSY = "MASSY PALAISEAU"
NAME_GARE_EVRY = "EVRY COURCOURONNES - Centre"
NAME_GARE_AUSTERLITZ = "PARIS AUSTERLITZ"
NAME_GARE_LYON = "PARIS GARE DE LYON"

NAME_GARE_ROUTES_1 = [[NAME_GARE_JUVISY, NAME_GARE_MASSY], [NAME_GARE_JUVISY, NAME_GARE_EVRY], [NAME_GARE_JUVISY, NAME_GARE_AUSTERLITZ], [NAME_GARE_JUVISY, NAME_GARE_LYON]]

MISSION_FILTERS = [[]]*NUM_LISTS

#//TIMECODE: HHMM
#//FORMAT: CURTIME:TIMECODE-{TRAINNAME:CHAR-ARRIVE:TIMECODE-STATUS:CHAR[01234RS]-VOIE:CHARx2}x4
DATA1 = "1350D1359002H1410005D1411202H1415S00"
DATA2 = "1450D1459002H1515005D1521202H1525S00"

LISTEN_SLEEP = 0.2
UPDATE_SLEEP = 60

device = None
block_refresh = False
update_number = 0
listen_thread = None
refresh_thread = None

device_lock = threading.Lock()
train_list_lock = threading.Lock()
refresh_event = threading.Event()
internet_refresh_event = threading.Event()

rt_train_lists = [[]]*NUM_LISTS
rt_train_list_time = datetime.now()

db_train_lists = [[]]*NUM_LISTS
db_train_list_time = datetime.now()

prev_timetable_date = datetime.now()

#times_src = 0 #0 for real-time times thread, 1 for db times thread
toggle_interm_display = 0
destination_id = 0
time_offset = 0

db_info = {'user': 'root', 'database': 'transilien', 'password': 'tqbfjotld'}
#cnx_pool = mysql.connector.connect(**db_info)

def bths(bytes):
	return " ".join("{:02x}".format(ord(c)) for c in bytes)

def find_transilien_device():
	if not os.path.exists('/dev/serial'):
#		print "no serial devices"
		return None
#	for path_device in glob.glob('/dev/serial/by-id/*CDC_RS-232*'):
#		print "got device " + path_device
#		fdev = os.open(path_device, os.O_RDWR | os.O_NONBLOCK);
#		return fdev

	devices = serial.tools.list_ports.comports()	
	
	for dev_path in devices:
		if not dev_path[2].find('04d8'):
			continue
		fdev = None
		try:
			fdev = serial.Serial(dev_path[0], 9600, timeout=0)
		except:
			pass
		if fdev:
			return fdev
	return None
	
def read_command_from_device(device, block):
	global device_lock
	if block:
		print("Not implemented: blocking read from device")
		sys.exit(-1)
		
	with device_lock:
		if device == None:
			return ""
			
		readBytes = 0		
		try:
			#readBytes = os.read(device, 1)
			readBytes = device.read()
		#except OSError as err:
		except serial.SerialException as err:
#			if err.errno == 11:
#				pass
#			else:
				traceback.print_exc()
				#os.close(device)
				device.close()
				device = None
				raise
		if not block and len(readBytes) == 0:
	#		print "No bytes read"
			return ""
		#	print "Got 1 byte, waiting for " + str(ord(readBytes[0]))
		commandLength = ord(readBytes[0])
#		print "read " + str(len(readBytes)) + " cmd len: " + str(commandLength) + ": " + bths(readBytes)
		while len(readBytes) < 1 + commandLength:
			try: 
				#readBytes = readBytes + os.read(device, 1)
				readBytes = readBytes + device.read(commandLength - (len(readBytes) - 1))
			except serial.SerialException as err:
#				if err.errno == 11:
#					pass
#				else:
					traceback.print_exc()
					#os.close(device)
					device = None
					raise
										
		#print "Finished reading " + str(ord(readBytes[0])) + " bytes, message is " + bths(readBytes)
		return readBytes

def transilien_listen_thread():
	stop_listen = False
	global destination_id
	global device
#	global times_src
	global block_refresh
	global toggle_interm_display
	global time_offset
	
	print("device listen thread start")
	while not stop_listen:
		try:
	#		print "Listen acquire"
			readBytes = read_command_from_device(device, False)
			if len(readBytes) > 0:				
				if ord(readBytes[1]) == 0x30:
					print("request times: " + bths(readBytes))
					if ord(readBytes[2]) == 0:
						print("Schedule: reset to real-time")
#						times_src = 0 #set to Internet real time schedule
						time_offset = 0
						refresh_event.set()
						internet_refresh_event.set()
					else:
#						times_src = times_src + 1 #set to db schedule
						time_offset = ord(readBytes[2])
						refresh_event.set()
				elif ord(readBytes[1]) == 0x50:
					toggle_interm_display = ord(readBytes[2])
					print("display toggle" + str(toggle_interm_display))
					time_offset = 0
					refresh_event.set()
				elif ord(readBytes[1]) == 0x40:
					print("direction switch")
					destination_id = ord(readBytes[2])
					block_refresh = True
#					times_src = 0
					internet_refresh_event.set()
				elif ord(readBytes[1]) == 0xA0:
					#print("Cmd ok: " + bths(readBytes))
					pass
				else:
					print("Error input: " + bths(readBytes))
	#			else:
	#				print "No incoming data"
		except:
			stop_listen = True				
			traceback.print_exc()
			print("Stopped listening")
			return
		time.sleep(LISTEN_SLEEP)

#listen_lock = threading.Lock()

def transilien_parse_xml(xml_data, nmax, mission_filter):
	train_list = []
	root = ET.fromstring(xml_data)
	if root is not None:
		if len(root) < nmax:
			train_list_xml = root
		else:
			train_list_xml = root[0:nmax]

		for train in train_list_xml:
			train_info = {}
			train_info['etat'] = ''
			train_info['corresp'] = 0
			for train_prop in train:
				if train_prop.tag == 'date':
					train_info['time'] = datetime.strptime(train_prop.text, '%d/%m/%Y %H:%M')
					train_info['mode'] = train_prop.attrib['mode']
				elif train_prop.tag == 'miss':
					train_info['miss'] = train_prop.text
				elif train_prop.tag == 'num':
					train_info['num'] = train_prop.text
				elif train_prop.tag == 'etat':
					train_info['etat'] = train_prop.text.strip()

			if len(mission_filter) > 0:
				try:
					mission_filter.index(train_info['miss'])
				except ValueError as err: #if not found				
					continue
					
			cnx = mysql.connector.connect(**db_info)
			cursor = cnx.cursor(buffered=True)
			mission_name = train_info['miss']
			if len(mission_name) > 4:
				mission_name = mission_name[0:4]
			result = cursor.callproc("query_train_id", (train_info['num'],mission_name,0))			
#			print str(result) + " " + train_info['etat'] + " " + str(train_info['time'])
			if result == None:
#				print('Cannot find train ' + train_info['num'])
#				print 'Cannot find train ' + train_info['num']
				train_info['id'] = '-'
			else:
				#allres = cursor.fetchall()
				if len(result) == 0 or result[2] == None:
					print('Cannot find train ' + train_info['num'])
					train_info['id'] = '-'
				else:
					train_info['id'] = result[2].encode()
			cursor.close()
#				cnx.close()
			train_list.append(train_info)	
	return train_list
			
def transilien_get_current_trains(nmax):	
	global db_info
	train_lists = [[]]*NUM_LISTS
	for k in range(NUM_LISTS):
	
		url = 'http://api.transilien.com/gare/' + ID_GARE_ROUTES_1[k][0] + '/depart/' + ID_GARE_ROUTES_1[k][1]
			
#		print url

		req = urllib2.Request(url)
		base64string = base64.encodestring('%s:%s' % (API_username, API_password))[:-1]
		authheader =  "Basic %s" % base64string
		req.add_header("Authorization", authheader)
		req.add_header("Accept", "application/vnd.sncf.transilien.od.depart+xml;vers=1.0")
	
		the_page = None
		try:
			response = urllib2.urlopen(req)
			the_page = response.read()
#			print the_page
		except IOError as err:
			print("Transilien API GET error")
			traceback.print_exc()
			return []
		
		try:
			train_lists[k] = transilien_parse_xml(the_page, 1e10, MISSION_FILTERS[k])
		except:
			print("XML Error for document\n: " + the_page)
			traceback.print_exc()
			return []			
					
	return train_lists


def datetime_from_utc_to_local(utc_datetime):
    now_timestamp = time.time()
    offset = datetime.fromtimestamp(now_timestamp) - datetime.utcfromtimestamp(now_timestamp)
    return utc_datetime + offset

def idfm_get_current_trains(maxtrains):

	url = "https://prim.iledefrance-mobilites.fr/marketplace/stop-monitoring?MonitoringRef=STIF:StopPoint:Q:41309:"
	req = urllib2.Request(url)

	all_line_id = {'STIF:Line::C01727:' : 'C', 'STIF:Line::C01728:': 'D' }
	arrival_statuses = { 'delayed': 'ret', 'onTime': 'T', 'cancelled': 'supp', 'early': 'T'}

	req.add_header("apikey", IDFM_API_KEY)
	req.add_header('Pragma', 'no-cache')
	req.add_header('Cache-Control', 'no-cache')

	the_page = None
	try:
		response = urllib2.urlopen(req)
		the_page = response.read()
	except IOError as err:
		print("Transilien API GET error")

	data = json.loads(the_page)

	train_list = [[] for _ in range(NUM_LISTS)]
	trains_data = data['Siri']['ServiceDelivery']['StopMonitoringDelivery'][0]['MonitoredStopVisit']
	for record in trains_data:

		try:
			line_id = record['MonitoredVehicleJourney']['LineRef']['value']
			arrival_status = record['MonitoredVehicleJourney']['MonitoredCall']['ArrivalStatus']
		except Exception as err:
			print("API returned format error: \n\n" + str(err) + "\n\n" + str(record))

		try:
			str_departure_time = record['MonitoredVehicleJourney']['MonitoredCall']['ExpectedDepartureTime']
			dest_ref = record['MonitoredVehicleJourney']['DestinationRef']['value'].decode('utf-8')
			dest_name = record['MonitoredVehicleJourney']['DestinationName'][0]['value'].decode('utf-8')
		except:
			# No departure = train is at end of the line
			continue

		idx_list_record = -1
		for idx_list, dest_list in enumerate(GARES_LISTS):
			if dest_ref in dest_list:
				idx_list_record = idx_list
				break

		if dest_ref in GARES_IGNORE:
			continue

		if idx_list_record == -1:
			print("Unknown train found: " + str(record))
			continue

		if idx_list_record >= len(train_list):
			print("ERROR Trying to insert to train list " + str(idx_list_record))
			continue

		train_info = {}
		train_info['id'] = all_line_id.get(line_id, '-')
		train_info['miss'] = 0
		train_info['time'] = datetime_from_utc_to_local(datetime.strptime(str_departure_time[0:-5], '%Y-%m-%dT%H:%M:%S'))
		train_info['mode'] = 0
		train_info['num'] = 0 #str_departure_time
		train_info['dest_name'] = dest_name
		train_info['etat'] = arrival_statuses.get(arrival_status, 'supp')
		train_info['corresp'] = 0

		train_list[idx_list_record].append(train_info)

	return train_list

def merge_combined_train_lists(c_list_1, c_list_2, display_datetime):
	train_list = c_list_1 + c_list_2
	train_list = [ti for ti in train_list if ti['time'] > display_datetime + timedelta(seconds=MIN_TIME_TO_STATION*60)]
	train_list = sorted(train_list, key=lambda train_info: train_info['time'])
	return train_list
	
def combine_rt_and_tt_train_lists(isFirstLeg, display_datetime, rt_train_list, db_train_list):
	train_list = []
	cur_date = datetime.now()
	
	if len(db_train_list) == 0:
		train_list = rt_train_list
	else:	
		mintime = datetime.now() + timedelta(seconds=10*3600)
		maxtime = datetime.now() + timedelta(seconds=-10*3600)
		for ti in rt_train_list:
			if ti['time'] < mintime:
				mintime = ti['time']
			elif ti['time'] > maxtime:
				maxtime = ti['time']
		#print "min: " + str(mintime) + " -- max: " + str(maxtime)
		rt_found = [0]*len(rt_train_list)
		for train_info in db_train_list:
			rt_info = None
			td = train_info['time'] - cur_date
#			if (abs(td.total_seconds()) < 180 and cur_date > train_info['time'])  or (train_info['time'] :
			for (k, ti2) in enumerate(rt_train_list):
				td_rt = train_info['time'] - ti2['time']					
				if ti2['miss'] == train_info['miss'] and abs(td_rt.total_seconds()) < 5*60:
					rt_info = ti2
					rt_found[k] = 1
			if not rt_info == None:
				train_list.append(rt_info)
			elif not len(rt_train_list) == 0 and (train_info['time'] < mintime or train_info['time'] > maxtime): #not isFirstLeg or (
				train_list.append(train_info)
		
		for k in range(len(rt_found)):
			if rt_found[k] == 0:
				train_list.append(rt_train_list[k])
				
#		print rt_found
#		print rt_train_list
		
	train_list = [ti for ti in train_list if ti['time'] > display_datetime + timedelta(seconds=MIN_TIME_TO_STATION*60)]
	train_list = sorted(train_list, key=lambda train_info: train_info['time'])
				
	return train_list
	
def chain_train_lists(train_list1, train_list2):
	train_list = []
	train_list2_valid = []
	ntrains = 2;
	for nt1 in range(len(train_list2)):
		t_depart_needed = train_list2[nt1]['time'] + timedelta(minutes=-MINS_ST_DENIS_NORD)
		#print "To get to train at " + str(train_list2[nt1]['time']) + " at " + NAME_GARE_ITERM + " must depart at " + str(t_depart_needed) + " from " + NAME_GARE_DEPART
		trains_before = [ti for ti in train_list1 if ti['time'] < t_depart_needed]
		if len(trains_before) == 0:
			continue
		best_trains = sorted(trains_before, key=lambda ti: ti['time'], reverse=True)
		#print best_trains
		if len(best_trains) > ntrains:
			best_trains = best_trains[0:ntrains]
		#print best_trains			
		for best_train in best_trains:
			best_train_exists = [ti for ti in train_list if ti['time']==best_train['time'] and ti['miss'] == ti['miss']]			
			if len(best_train_exists) == 0:
				train_list.append(best_train)
				tnew = dict(train_list2[nt1])
				td = train_list2[nt1]['time'] - best_train['time'] + timedelta(minutes=-MINS_ST_DENIS_NORD)
				tnew['corresp'] = int(floor(td.total_seconds() / 60))
#				print str(best_train['time']) + " - " + str(MINS_ST_DENIS_NORD) + " mins - " + str(train_list2[nt1]['time']) + " => corresp is " + str(tnew['corresp']) + " mins"
				train_list2_valid.append(tnew)

	indices = sorted(range(len(train_list)), key=lambda k: train_list[k]['time'])
	train_list =  map(train_list.__getitem__, indices) #[]
	train_list2_valid = map(train_list2_valid.__getitem__, indices)
	#train_list = sorted(train_list, key=lambda train_info: train_info['time'])		
	#print train_list
	return (train_list, train_list2_valid)
	
def display_refresh_thread_func():	
	global refresh_event
	global rt_train_lists
	global db_train_lists
	global device
	global block_refresh
	global rt_train_list_time
	global db_train_list_time
	global toggle_interm_display
	global time_offset

	TIME_OFFSET_MINUTES = 15

	nmax = 4
	
	print("display refresh thread start")
	while True:
		wait_result = refresh_event.wait(REFRESH_PERIOD)
			
		#print "Refresh event wait result: " + str(wait_result)
		
		if block_refresh and wait_result:
			refresh_event.clear()
			print(datetime.now().strftime("%H:%M:%S") +" : Refresh blocked for regular refresh")
			continue
			
		#//FORMAT: CURTIME:TIMECODE-{TRAINNAME:CHAR-ARRIVE:TIMECODE-STATUS:CHAR[01234RS]-FLAGS:CHARx2}x4
	#	"1350D1359002H1410005D1411202H1415S00"
	#	"2109O2119000O2121000O2127000O2129000"
					
		with train_list_lock:
			train_lists_combined = [[]]*NUM_LISTS
			#print rt_train_lists
			#print db_train_lists
			cur_display_datetime = datetime.now()
			if time_offset > 0:
				cur_display_datetime = cur_display_datetime + timedelta(minutes = time_offset*TIME_OFFSET_MINUTES)
			for tl in range(NUM_LISTS):
				try:
					train_lists_combined[tl] = combine_rt_and_tt_train_lists(tl == 0, cur_display_datetime, rt_train_lists[tl], db_train_lists[tl])
				except:
					print("Error running combine_rt_and_tt_train_lists: tl=[0.." + str(len(range(len(ID_GARE_ROUTES_1)))-1) + "]")
					print("train_lists_combined: len=" + str(len(train_lists_combined)))
					print("rt_train_lists: len=" + str(len(rt_train_lists)))
					print("db_train_lists: len=" + str(len(db_train_lists)))
					traceback.print_exc(file=sys.stdout)
				
			if toggle_interm_display == 1:
#				print "Intermediary times"

				if destination_id == 0:
					train_list = merge_combined_train_lists(rt_train_lists[0], rt_train_lists[1], cur_display_datetime)
				else:
					#res = rt_train_lists[2] #chain_train_lists(train_lists_combined[0], train_lists_combined[1])
					#train_list = res[1]
					train_list = rt_train_lists[2]
			else:
				if destination_id == 0:
#					print("Direct times to work")
					train_list = merge_combined_train_lists(train_lists_combined[0], train_lists_combined[1], cur_display_datetime)
				else:
#					print("Times to Paris")
					#res =  chain_train_lists(train_lists_combined[0], train_lists_combined[1])
					# train_list = res[0]
					train_list = merge_combined_train_lists(train_lists_combined[2], train_lists_combined[3], cur_display_datetime)
				
			train_list_time = cur_display_datetime
							
			if len(train_list) > nmax:
				train_list = train_list[0:nmax]		
				
#			print "train list time is : " + str(train_list_time)
			device_string = '{0:02d}'.format(train_list_time.hour) + '{0:02d}'.format(train_list_time.minute)
			for train in train_list:
				device_string = device_string + train['id'] + '{0:02d}'.format(train['time'].hour) + '{0:02d}'.format(train['time'].minute)
				if train['etat'].lower().startswith('supp'):
					device_string = device_string + 'S'
				elif train['etat'].lower().startswith('ret'):
					device_string = device_string + 'R'
				elif train['etat'] == 'T':
					device_string = device_string + 'T'	#scheduled time
				else:
					device_string = device_string + '0';
					
				if destination_id == 1:
					if train['corresp'] > 9:
						device_string = device_string + "Z"
					else:
						device_string = device_string + str(train['corresp'])
				else:
					device_string = device_string + "-"
					
				device_string = device_string + "0"
				
			for k in range(0, 4-len(train_list)):
				device_string = device_string + "-----" + "0" + "00"

		#print datetime.now().strftime("%H:%M:%S") + " Send string: " + device_string

		header = [0, 0x20];
		serialData = bytearray(header + list(device_string.encode('ascii', 'ignore')))
		with device_lock:
			try:
				#os.write(device, serialData)
				device.write(serialData)
			except:
				print("Lost connection while writing to device")
				#os.close(device)
				device.close()
				device = None
				return
		refresh_event.clear()

def internet_times_thread_func():
	global refresh_event
	global update_number
	global rt_train_lists
	global destination_id
	global block_refresh
	global rt_train_list_time
	
	internet_refresh_event.set()
	while True:
		internet_refresh_event.wait(timeout=UPDATE_SLEEP)	
		start_dest_id = destination_id
		train_lists_new = idfm_get_current_trains(4)
		with train_list_lock: 
			rt_train_list_time = datetime.now()
#			print "set train list time to : " + str(train_list_time)
			rt_train_lists = train_lists_new
		
		if destination_id == start_dest_id:
			refresh_event.set();
			internet_refresh_event.clear()
		
		block_refresh = False
#		print datetime.now().strftime("%H:%M:%S") + " reset block refresh"				
		update_number = update_number + 1
	
def db_times_thread_func(): #time_offset, times_src_order):
	global refresh_event
	global destination_id
	global db_info
#	global times_src
	global db_train_lists
	global db_train_list_time
	
	while True:
		cur_date = datetime.now()
		cur_date = cur_date.replace(hour=5, minute=0, second=0, microsecond=0)
		new_train_lists = [[]]*NUM_LISTS
		for k in range(NUM_LISTS):
			new_train_lists[k] = get_and_cache_tt_two_stations(cur_date, NAME_GARE_ROUTES_1[0][k], NAME_GARE_ROUTES_1[1][k])
		with train_list_lock:
			db_train_lists = new_train_lists
			#db_train_lists

		time.sleep(3600)
	
def get_and_cache_tt_two_stations(cur_date, station1, station2):
	global prev_timetable_date
	tt_file = cur_date.strftime("%Y%m%d") + "_" + station1 + "_" + station2 + ".txt"
	if not os.path.exists(TT_DIR):
		os.makedirs(TT_DIR)
	tt_path = os.path.join(TT_DIR, tt_file)
	train_list = []
	if not os.path.isfile(tt_path):		
		#print "Refreshing timetable for routes between " + station1 + " and " + station2
		
		#try:
		cnx = mysql.connector.connect(**db_info)	
		cursor = cnx.cursor()
		cursor.callproc("train_times_for_day_2stations", (cur_date.strftime('%Y-%m-%d %H:%M:%S'),station1,station2))
		fp = open(tt_path, 'wt')
		day_start = datetime.now()
		day_start = day_start.replace(hour=0, minute=0, second=0, microsecond=0)
		for result in cursor.stored_results():
			rows = result.fetchall()			
			for row in rows:
				train_info = {}
				train_info['id'] = row[0]
				train_info['miss'] = row[1]
				train_info['time'] = day_start + row[2]
#				print train_info['time']
				train_info['mode'] = ''
				train_info['num'] = ''
				train_info['etat'] = 'T'
				train_info['corresp'] = 0
				train_list.append(train_info)
				fp.write(str(train_info['id']) + "," + str(train_info['miss']) + "," + train_info['time'].strftime('%Y-%m-%d %H:%M:%S') + "," + train_info['etat'] + "," + train_info['mode'] + "," + str(train_info['num']) + "," + train_info['etat'] + "\n")
		fp.close()
		prev_timetable_date = cur_date
		#except:
		#	return []
			
	else: #read from cache
		for line in open(tt_path):
			row = line.split(',')
			train_info = {}
			train_info['id'] = row[0]
			train_info['miss'] = row[1]
			train_info['time'] = datetime.strptime(row[2], '%Y-%m-%d %H:%M:%S')
			train_info['mode'] = row[4]
			train_info['num'] = row[5]
			train_info['etat'] = row[6].strip()
			train_info['corresp'] = 0
			train_list.append(train_info)			
			
	return train_list
#--- main program ----
		
internet_thread = thread.start_new_thread(internet_times_thread_func, tuple([]))		
#db_thread = thread.start_new_thread(db_times_thread_func, tuple([]))

while True:
	if device == None:
		device = find_transilien_device()
		print("device : " + str(device))
		if device:
			try:
				data = read_command_from_device(device, False)
				while len(data) > 0:
					data = read_command_from_device(device, False)
			except:
				print("Error while flushing serial data")
				continue
			listen_thread = thread.start_new_thread(transilien_listen_thread, tuple([]))
			#header = [0, 0x20];
			#initData = bytearray(header + list('INIT00000000000000000000000000000000'))
			#with device_lock:
			#	os.write(device, initData)
			refresh_thread = thread.start_new_thread(display_refresh_thread_func, tuple([]))
	if device == None:
		print("No device")
		
	time.sleep(1)
	
