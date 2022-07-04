import re #Library of regular expressions for working with text.
import os #Library for working with the Windows operating system.
import sys #System Functions Library is cross-platform.
# Remove the grid at the beginning to connect the folder with the necessary libraries in the same directory as the script
# sys.path.append(os.path.join(sys.path[0], './resourses/'))
import ipaddress #Library for working with ip addresses.
import time # to stop the program.
import telnetlib #Library for remote telnet connections.



class ZteC320():

	def __init__(self):

		self.zte_log_file = open('zte_c320_log.txt', 'a', newline='')
		self.zte_unregistered_onts = {}
		self.zte_profile_line = 'Internet' # CHANGE ME
		self.zte_profile_remote = 'Internet_pon' # CHANGE ME
		self.zte_opt_82_profile = 'PF82-1' # CHANGE ME

		print ('\nProgram for auto-registration ONU for gpon zte c320\n')

	def info(self):

		for gpon_port in self.zte_unregistered_onts:
			print ('\nOn port gpon_olt_'+gpon_port+' serial numbers were found: '+', '.join(self.zte_unregistered_onts[gpon_port]['serials']))


	def zte_ip_validation(self):

		try:
			self.ip = ipaddress.ip_address(self.ip.strip()) #Type conversion
		except ValueError:
			input('Incorrect format of ip address record')
			return False

		if self.ip.is_private:

			if self.ip in ipaddress.IPv4Network('10.0.0.0/22'): # CHANGE ME
				print('You made it and entered the ip correctly, wait, checking availability...')
				return self.ip
			else:
				input('This is the wrong control subnet, our company uses a different')
				return False
		else:
			input ('White ip is entered, subnet management can only be gray.')
			return False

	def zte_c320_ping(self):

		response = os.system('ping '+str(self.ip)+'. -n 1') #Pinging the switch.
		if response == 0:
			print ('\n\nGPON - '+str(self.ip)+' is available, starting authentication...\n'); time.sleep(1)
			return True
		else:
			print ('\n\nGPON - '+str(self.ip)+' does not respond to icmp requests.\n'); time.sleep(1)
			return False

	def zte_telnet_authentication(self):

		self.__login = input('\nEnter login: ')
		self.__password = input('\nEnter pass: ')

		self.zte_cli_in = telnetlib.Telnet(str(self.ip), 23, 2); time.sleep(.1) #Telnet to our gpon.
		self.zte_cli_out = self.zte_cli_in.read_until(b'Username:', timeout=3) #Waiting for username invitation
		self.zte_log_file.write(self.zte_cli_out.decode('ascii')) #Let's start writing the log.

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

		self.zte_uncfg_onts = re.findall('gpon-onu_(\d\/\d\/\d)\:(\d)\s+(\w+)', self.zte_cli_out.decode('ascii')) #\d - any digit

		if self.zte_uncfg_onts:

			for string in self.zte_uncfg_onts:

				current_gepon_port = string[0]
				current_onu_number = string[1]
				current_onu_serial = string[2]

				#retrieve the value of the gpon port key, at this point it definitely does not exist yet, so the dictionary is created 
				#And if there is one, already in the next iteration, it just brings itself back. 
				self.zte_unregistered_onts.setdefault(current_gepon_port, {'serials' : [], 'busy_onts_id' : [], 'vlan' : None})
				self.zte_unregistered_onts[current_gepon_port]['serials'].append(current_onu_serial)
				i += 1

			print ('\nThe total number of unregistered onts: '+str(i)+'\n')
			return True

		else:
			print ('There are currently no unregistered onts on gpon '+str(self.ip)+'\n')
			input ('\nPress enter to exit')
			return False


	def zte_check_profiles(self):

		self.zte_cli_in.write(b'show running-config | include onu-profile\n'); time.sleep(2)
		self.zte_cli_out = self.zte_cli_in.read_very_eager(); time.sleep(1)
		self.zte_log_file.write(self.zte_cli_out.decode('ascii'))
		zte_check_profile_line = re.findall('onu-profile gpon line (\w+)', self.zte_cli_out.decode('ascii'))
		zte_check_profile_remote = re.findall('onu-profile gpon remote (\w+)', self.zte_cli_out.decode('ascii'))

		if self.zte_profile_line in zte_check_profile_line:
			print ('\nFound the correct line profile = Internet\n')
		else:
			print('\nError! Profile line of the gpon '+str(self.ip)+' = '+self.zte_profile_line+' was not found!')
			return False

		if zte_check_profile_remote:
			count_remote = 0 # Just counter
			for remote_profile in zte_check_profile_remote:
				count_remote += 1
				print ('For pon-'+str(count_remote)+' gpon '+str(self.ip)+ ' profile '+remote_profile); time.sleep(.3)


		else:
			print ('\nError! No remote profiles '+self.zte_profile_remote+'were found in gpon '+str(self.ip))
			return False

		profile_counter = (8 - count_remote)
		if profile_counter != 0:
			print ('\nError! Not enough ('+count_remote+') remote profiles were found in gpon '+str(self.ip))
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
				print ('\nFor the pon port '+key+' based on the profile '+self.zte_profile_remote+key[-1]+' vlan will be: '+zte_check_vlan_on_remote_profile[0]+'\n')
		
				self.zte_unregistered_onts[key]['vlan'] = zte_check_vlan_on_remote_profile[0]

				return True

			else:
				print('Error on the procedure for defining the option 82 and the vlans\n')



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

				print ('Busy id of onts on port gpon-olt_'+key+': '+', '.join(self.zte_unregistered_onts[key]['busy_onts_id']))
				return True

			else:
				print ('There are no registered onts on port gpon-olt_'+key+'.')
				return True


	def zte_auto_add_onts(self):

		self.zte_successful_ont_counter = 0

		self.zte_cli_in.write(b'configure terminal\n'); time.sleep(1)
		self.zte_cli_out = self.zte_cli_in.read_very_eager(); time.sleep(1)
		self.zte_log_file.write(self.zte_cli_out.decode('ascii'))

		for gpon_port in self.zte_unregistered_onts.keys(): #For each gpon port

			i = 1 #Initialize a variable to select the registration index.

			for current_onu_serial in self.zte_unregistered_onts[gpon_port]['serials']: #For each serial 

				for i in range(i, 129): #There can be a total of 1-128 occupied onu.

					if str(i) not in self.zte_unregistered_onts[gpon_port]['busy_onts_id']: #And if the index is free

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

						print ('Successfully registered onu with serial number '+current_onu_serial+ ' on port gpon-onu_'+gpon_port+' using the index: '+str(i)+'\n')
						i += 1 # Increase the following index for the given gpon port by 1
						self.zte_successful_ont_counter += 1 #For the counter how many onu were registered.
						break #Close the loop and go to the loop above for the next serial.



					else:
						print ('onu index '+str(i)+' for port '+gpon_port+' is busy, I will take the next one')
						i += 1
						continue #Don't exit the loop, but start the next iteration until you get to an unoccupied index in the range of 1-128


gpon = ZteC320()

gpon.ip = input('Enter the ip address of the GPON:')
# Drawing steps
if gpon.ip:
	if gpon.zte_ip_validation():
		print ('\nThe engineer was able to enter the ip address, successful completion of the first procedure.\n')
		if gpon.zte_c320_ping():
			print ('\nThe accessibility check is successful.\n')
			if gpon.zte_telnet_authentication():
				print ('\nAuthorization successful.\n')
				if gpon.zte_vendor_validation():
					print ('\nCorrespondence of the equipment vendor to the script: successful.\n')
					if gpon.zte_show_onu_uncfg():
						print ('\nThe procedure of checking for unregistered names has been successfully completed, and the dictionary of auto-registration parameters has been formed.\n')
						if gpon.zte_check_profiles():
							print ('\nThe procedure to check whether profiles '+gpon.zte_profile_line+' and '+gpon.zte_profile_remote+' match the script - passed successfully.\n')
							if gpon.zte_check_free_onu_id():
								print ('\nThe indexes occupancy check is successfully completed. The dictionary of occupied indexes is formed.\n')
								if gpon.zte_check_option_82_and_vlans():
									print('\nVlans from remote profiles were successfully added to the dictionary, the option 82 formatting profile was found.')
									gpon.info()
									print ('\nI am starting the auto-registration process, wait for it...\n')
									gpon.zte_auto_add_onts()
									gpon.zte_log_file.close()
									input ('\n Successfully registered '+str(gpon.zte_successful_ont_counter)+' onu, no errors detected\n' ) #self поменял на gpon.