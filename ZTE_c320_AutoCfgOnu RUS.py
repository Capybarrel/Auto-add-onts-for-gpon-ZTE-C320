import re #Библиотека регулярных выражений для работы с текстом.
import os #Библиотека для работы с операционной системой Windows.
import sys #Библиотека системных функций кросплатформенная.
# Убрать решетку в начале чтобы подключить папку с необходимыми библиотеками в той же директории что скрипт
# sys.path.append(os.path.join(sys.path[0], './resourses/'))
import ipaddress #Библиотека для работы с ip адресами.
import time #Слипы для остановки программы.
import telnetlib #Библиотека для удаленного подключения по протоколу telnet.




class ZteC320():

	def __init__(self):

		self.zte_log_file = open('zte_c320_log.txt', 'a', newline='')
		self.zte_unregistered_onts = {}
		self.zte_profile_line = 'Internet' # ПОМЕНЯЙ МЕНЯ
		self.zte_profile_remote = 'Internet_pon' # ПОМЕНЯЙ МЕНЯ
		self.zte_opt_82_profile = 'PF82-1' # ПОМЕНЯЙ МЕНЯ

		print ('\nProgram for auto-registration ONU for gpon zte c320\n' +\
			'If you see a wrong symbols in CMD, you do not have correct russian fonts for it.\n')

	def info(self):

		for gpon_port in self.zte_unregistered_onts:
			print ('\nНа gpon_olt_'+gpon_port+' найдены серийники: '+', '.join(self.zte_unregistered_onts[gpon_port]['serials']))


	def zte_ip_validation(self):

		try:
			self.ip = ipaddress.ip_address(self.ip.strip()) #Преобразование типа
		except ValueError:
			input('Не верный формат ip адреса')
			return False

		if self.ip.is_private:

			if self.ip in ipaddress.IPv4Network('10.0.0.0/22'): # ПОМЕНЯЙ МЕНЯ
				print('Ты справился и ввёл ip верно, ожидай, проверяю доступность...')
				return self.ip
			else:
				input('Это не подсеть управления gpon-ами')
				return False
		else:
			input ('Введён белый ip, влан управления может быть только серым.')
			return False

	def zte_c320_ping(self):

		response = os.system('ping '+str(self.ip)+'. -n 1') #Пингуем коммутатор.
		if response == 0:
			print ('\n\nGPON - '+str(self.ip)+' доступен, начинаю аутентификацию...\n'); time.sleep(1)
			return True
		else:
			print ('\n\nGPON - '+str(self.ip)+' не доступен!\n'); time.sleep(1)
			return False

	def zte_telnet_authentication(self):

		self.__login = input('\nВведите логин: ')
		self.__password = input('\nВведите пароль: ')

		self.zte_cli_in = telnetlib.Telnet(str(self.ip), 23, 2); time.sleep(.1) #Телнетимся к нашему gpon.
		self.zte_cli_out = self.zte_cli_in.read_until(b'Username:', timeout=3) #Ждём приглашения username
		self.zte_log_file.write(self.zte_cli_out.decode('ascii')) #Начинаем писать лог.

		if self.zte_cli_out:
			self.zte_cli_in.write(self.__login.encode('ascii')+b'\n'); time.sleep(.5)
			self.zte_cli_out = self.zte_cli_in.read_until(b'Password:', timeout=3)
			self.zte_log_file.write(self.zte_cli_out.decode('ascii'))

			if self.zte_cli_out:
				self.zte_cli_in.write(self.__password.encode('ascii')+b'\n'); time.sleep(.5)
				self.zte_cli_out = self.zte_cli_in.read_until(b'#' or '>', timeout=3)
				self.zte_log_file.write(self.zte_cli_out.decode('ascii'))

				return True


	def zte_vendor_validation(self):

		self.zte_cli_in.write(b'show shelf\n'); time.sleep(.3)
		self.zte_cli_out = self.zte_cli_in.read_until(b'C320_SHELF', timeout=3)
		self.zte_log_file.write(self.zte_cli_out.decode('ascii'))
		if self.zte_cli_out:
			return True

	def zte_show_onu_uncfg(self):

		i = 0
		self.zte_cli_in.write(b'show gpon onu uncfg\n'); time.sleep(2)
		self.zte_cli_out = self.zte_cli_in.read_very_eager(); time.sleep(1)
		self.zte_log_file.write(self.zte_cli_out.decode('ascii'))

		self.zte_uncfg_onts = re.findall('gpon-onu_(\d\/\d\/\d)\:(\d)\s+(\w+)', self.zte_cli_out.decode('ascii')) #\d - любая цифра.

		if self.zte_uncfg_onts:

			for string in self.zte_uncfg_onts:

				current_gepon_port = string[0]
				current_onu_number = string[1]
				current_onu_serial = string[2]

				#Возвращаем значение ключа порта gpon, на этом моменте его еще точно нет, поэтому создаём словарь 
				#А если он есть, уже в следующей итерации, то он просто сам себя возвращает.
				self.zte_unregistered_onts.setdefault(current_gepon_port, {'serials' : [], 'busy_onts_id' : [], 'vlan' : None})
				self.zte_unregistered_onts[current_gepon_port]['serials'].append(current_onu_serial)
				i += 1

			print ('\nВсего незарегестрированных ону: '+str(i)+'\n')
			return True

		else:
			print ('В данный момент на gpon '+str(self.ip)+' нет незарегестрированных ону\n')
			input ('\nНажмите Enter чтобы выйти')
			return False


	def zte_check_profiles(self):

		self.zte_cli_in.write(b'show running-config | include onu-profile\n'); time.sleep(2)
		self.zte_cli_out = self.zte_cli_in.read_very_eager(); time.sleep(1)
		self.zte_log_file.write(self.zte_cli_out.decode('ascii'))
		zte_check_profile_line = re.findall('onu-profile gpon line (\w+)', self.zte_cli_out.decode('ascii'))
		zte_check_profile_remote = re.findall('onu-profile gpon remote (\w+)', self.zte_cli_out.decode('ascii'))

		if self.zte_profile_line in zte_check_profile_line:
			print ('\nНайден корректный профайл line = Internet\n')
		else:
			print('\nОшибка! Профайл line gpon-а '+str(self.ip)+' = '+self.zte_profile_line+' не найден!')
			return False

		if zte_check_profile_remote:
			count_remote = 0 # Просто счётчик.
			for remote_profile in zte_check_profile_remote:
				count_remote += 1
				print ('Для pon-'+str(count_remote)+' gpon-а '+str(self.ip)+ ' профайл '+remote_profile); time.sleep(.3)


		else:
			print ('\nОшибка! Не найдено ни одного remote профайла '+self.zte_profile_remote+' gpon-а '+str(self.ip))
			return False

		profile_counter = (8 - count_remote)
		if profile_counter != 0:
			print ('\nОшибка! Не хватает '+count_remote+' remote профайлов gpon-а '+str(self.ip))
			return False
		else:
			return True

	def zte_check_option_82_and_vlans(self):

		for key in self.zte_unregistered_onts.keys():

			self.zte_cli_in.write(b'   show pon onu-profile gpon remote '+(self.zte_profile_remote+key[-1]).encode('ascii')+b' cfg\n'); time.sleep(1)
			self.zte_cli_out = self.zte_cli_in.read_very_eager(); time.sleep(1)
			self.zte_log_file.write(self.zte_cli_out.decode('ascii'))
			zte_check_vlan_on_remote_profile = re.findall('vlan port eth_0/1 mode hybrid def-vlan (\d+)', self.zte_cli_out.decode('ascii'))

			if zte_check_vlan_on_remote_profile:
				print ('\nДля pon порта '+key+' по профайлу '+self.zte_profile_remote+key[-1]+' влан будет: '+zte_check_vlan_on_remote_profile[0]+'\n')
		
				self.zte_unregistered_onts[key]['vlan'] = zte_check_vlan_on_remote_profile[0]

				return True

			else:
				print('Ошибка на процедуре определения опции 82 и вланов\n')



	def zte_check_free_onu_id(self):

		for key in self.zte_unregistered_onts.keys():

			self.zte_cli_in.write(b'   show running-config interface gpon-olt_'+key.encode('ascii')+b' | include type\n'); time.sleep(2)

			i=0
			while i < 3:
				self.zte_cli_in.write(b'   \n')
				time.sleep(.3)
				i+=1

			self.zte_cli_out = self.zte_cli_in.read_very_eager(); time.sleep(1)
			self.zte_log_file.write(self.zte_cli_out.decode('ascii'))

			onts = re.findall('onu (\d+) type (\S+) sn (\w+)', self.zte_cli_out.decode('ascii'))

			if onts:

				for string in onts:

					current_onu_id = string[0]
					current_onu_type = string[1]
					current_onu_serial = string[2]

					self.zte_unregistered_onts[key]['busy_onts_id'].append(current_onu_id)

				print ('Занятые id онушек на порту gpon-olt_'+key+': '+', '.join(self.zte_unregistered_onts[key]['busy_onts_id']))
				return True

			else:
				print ('На порту gpon-olt_'+key+' нет зарегестрированных ону.')
				return True


	def zte_auto_add_onts(self):

		self.zte_successful_ont_counter = 0

		self.zte_cli_in.write(b'configure terminal\n'); time.sleep(1)
		self.zte_cli_out = self.zte_cli_in.read_very_eager(); time.sleep(1)
		self.zte_log_file.write(self.zte_cli_out.decode('ascii'))

		for gpon_port in self.zte_unregistered_onts.keys(): #Для каждого gpon порта

			i = 1 #Инициализируем переменную, для выбора индекса регистрации ону.

			for current_onu_serial in self.zte_unregistered_onts[gpon_port]['serials']: #Для каждого серийника 

				for i in range(i, 129): #Всего может быть 1-128 занятых ону.

					if str(i) not in self.zte_unregistered_onts[gpon_port]['busy_onts_id']: #И если индекс ону свободен

						self.zte_cli_in.write(b'interface gpon-olt_'+gpon_port.encode('ascii')+b'\n'); time.sleep(1)
						self.zte_cli_out = self.zte_cli_in.read_very_eager(); time.sleep(1)
						self.zte_log_file.write(self.zte_cli_out.decode('ascii'))
						
						self.zte_cli_in.write(b'onu '+str(i).encode('ascii')+b' type ZTE-F601 sn '+current_onu_serial.encode('ascii')+b'\n'); time.sleep(1)
						self.zte_cli_out = self.zte_cli_in.read_until(b'Successful', timeout=3)
						self.zte_log_file.write(self.zte_cli_out.decode('ascii'))

						self.zte_cli_in.write(b'onu '+str(i).encode('ascii')+b' profile line '+self.zte_profile_line.encode('ascii')+\
							b' remote '+self.zte_profile_remote.encode('ascii')+gpon_port[-1].encode('ascii')+b'\n'); time.sleep(1)
						self.zte_cli_out = self.zte_cli_in.read_until(b'Successful', timeout=7)
						self.zte_log_file.write(self.zte_cli_out.decode('ascii'))

						self.zte_cli_in.write(b'exit\n'); time.sleep(.3)
						self.zte_cli_out = self.zte_cli_in.read_very_eager(); time.sleep(.3)
						self.zte_log_file.write(self.zte_cli_out.decode('ascii'))

						self.zte_cli_in.write(b'interface gpon-onu_'+gpon_port.encode('ascii')+b':'+str(i).encode('ascii')+b'\n'); time.sleep(.3)
						self.zte_cli_out = self.zte_cli_in.read_until(b'config-if', timeout=3)
						self.zte_log_file.write(self.zte_cli_out.decode('ascii'))

						self.zte_cli_in.write(b'ip dhcp snooping enable vport 1\n'); time.sleep(.3)
						self.zte_cli_out = self.zte_cli_in.read_very_eager(); time.sleep(.3)
						self.zte_log_file.write(self.zte_cli_out.decode('ascii'))

						self.zte_cli_in.write(b'port-identification format '+self.zte_opt_82_profile.encode('ascii')+b' vport 1\n'); time.sleep(.3)
						self.zte_cli_out = self.zte_cli_in.read_very_eager(); time.sleep(.3)
						self.zte_log_file.write(self.zte_cli_out.decode('ascii'))

						self.zte_cli_in.write(b'dhcpv4-l2-relay-agent enable vport 1\n'); time.sleep(.3)
						self.zte_cli_out = self.zte_cli_in.read_very_eager(); time.sleep(.3)
						self.zte_log_file.write(self.zte_cli_out.decode('ascii'))

						self.zte_cli_in.write(b'service-port 1 vport 1 user-vlan '+self.zte_unregistered_onts[gpon_port]['vlan'].encode('ascii')+\
							b' vlan '+self.zte_unregistered_onts[gpon_port]['vlan'].encode('ascii')+b'\n'); time.sleep(.3)
						self.zte_cli_out = self.zte_cli_in.read_very_eager(); time.sleep(.3)
						self.zte_log_file.write(self.zte_cli_out.decode('ascii'))

						self.zte_cli_in.write(b'exit\n'); time.sleep(.3)
						self.zte_cli_out = self.zte_cli_in.read_very_eager(); time.sleep(.3)
						self.zte_log_file.write(self.zte_cli_out.decode('ascii'))

						print ('Успешно зарегестрированна ону '+current_onu_serial+ ' на порту gpon-onu_'+gpon_port+' под индексом: '+str(i)+'\n')
						i += 1 #Увеличить следующий индекс для данного gpon порта на 1
						self.zte_successful_ont_counter += 1 #Для счетчика сколько ону было зарегестрированно.
						break #Завершить цикл и перейти к циклу выше для следующего серийника.



					else:
						print ('Индекс ону '+str(i)+' для порта '+gpon_port+' занят, беру следующий')
						i += 1
						continue #Не выходим из цикла а начинаем следующую итерацию, пока не попадём на не занятый индекс в диапазоне 1-128.


gpon = ZteC320()

gpon.ip = input('Введите ip адрес GPON:')
#Рисуем лесенку
if gpon.ip:
	if gpon.zte_ip_validation():
		print ('\nИнженер смог ввести ip адрес, успешное завершение первой процедуры.\n')
		if gpon.zte_c320_ping():
			print ('\nПроверка доступности выполнена успешно.\n')
			if gpon.zte_telnet_authentication():
				print ('\nАвторизация выполнена успешно.\n')
				if gpon.zte_vendor_validation():
					print ('\nСоответствие вендора оборудования - скрипту: успешно.\n')
					if gpon.zte_show_onu_uncfg():
						print ('\nПроцедура проверки начичия незарегестрированных ону успешно завершена, сформирован словарь параметров авторегистрации.\n')
						if gpon.zte_check_profiles():
							print ('\nПроцедура проверки соответствия профайлов '+gpon.zte_profile_line+' и '+gpon.zte_profile_remote+' скрипту - успешно пройдена.\n')
							if gpon.zte_check_free_onu_id():
								print ('\nПроверка занятости индексов ону успешно произведена. Сформирован словарь занятых индексов.\n')
								if gpon.zte_check_option_82_and_vlans():
									print('\nВланы из remote профайлов успешно добавлены в словарь, профайл форматирования опции 82 найден.')
									gpon.info()
									print ('\nНачинаю процесс автореистрации ону, ожидайте...\n')
									gpon.zte_auto_add_onts()
									gpon.zte_log_file.close()
									input ('\n Успешно зарегестрированны '+str(gpon.zte_successful_ont_counter)+' ону, ошибок не обнаружено\n' ) #self поменял на gpon.