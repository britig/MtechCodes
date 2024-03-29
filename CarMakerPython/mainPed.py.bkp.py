'''
Created on 06 March 2019

@author: briti_g
'''
import os
import telnetlib
import re
import configparser
from enum import Enum
import time
import csv
import numpy as np

import GPy
import GPyOpt
#from numpy.random import seed

'''import paramiko, sys, time, threading-
import ClosedLoopDictionary
import ACSAutomation
SimStatus >= 0 : The ID of the maneuveur currently running
SimStatus < 0  : Simulation is not running, details below
'''

euclidDist = 99999

class SimStatus(Enum):
	PREPROCESSING = -1
	IDLE = -2
	POSTPROCESSING = -3
	MODEL_CHECK = -4
	DRIVER_ADAPTION = -5
	FATAL_ERROR = -6
	WAITING_FOR_LICENSE = -7
	PAUSED = -8
	STARTING_APPLICATION = -10
	SIMULINK_INITIALIZATION = -11
	
class ReturnStatus(Enum):
	ERROR = -1
	OK = 1
	
class CMConfig:
	def __init__(self, config_path):
		self.cp = configparser.ConfigParser()
		self.cp.read(config_path)
	
	# Get the library path for testrun files according config.ini   
	def getFolderPath(self):
		return self.cp['Carmaker TestRun']['folderpath']

	# Get telnet configuration of carmaker form config.ini
	def getTelnetConfig(self):
		host = self.cp['telnet']['host']
		port = self.cp['telnet']['port']
		return (host,port)    

class CMMonitor:
	def __init__(self, host, port):
		self.tn = telnetlib.Telnet(host, port)
		print('tn value------')
		print(self.check_alive(self.tn))
	
	def check_alive(self, telnet_object):
		try:
			if telnet_object.sock:
				telnet_object.sock.send(telnetlib.IAC + telnetlib.NOP)
				telnet_object.sock.send(telnetlib.IAC + telnetlib.NOP)
				telnet_object.sock.send(telnetlib.IAC + telnetlib.NOP)
			return True
		except:
			pass 
	'''
	CMMonitor :: write
	@msg: the message (i.e a command) to send to Carmaker
	
	write send the command specified by msg to Carmaker GUI
	trough telnet protocol.
	
	NOTE: Sending multiple command without allowing a delay between each
	will result in an undetermined behaviour. ALWAYS wait a delay when sending
	multiple command imn a row.
	'''    
	def write(self, msg):
		cmd = msg + '\n'
		self.tn.write(cmd.encode('ascii'))
		#self.tn.read_some()
	
	'''
	CMMonitor :: read
	
	read reads the result of the last executed command.
	
	Returns a tuple which contains the message from Carmaker as
	first element and ReturnStatus.ERROR as second element
	if the command as not been correctly executed or ReturnStatus.OK instead
	
	'''
	def read(self):
		#tnout = self.tn.read_until('\r\n'.encode('ascii'), 10)
		tnout = self.tn.read_some()
		#print(tnout)
		status = ReturnStatus.OK if (tnout[0] == b'O'[0]) else ReturnStatus.ERROR
		msg = tnout.split(b'\r')[0][1:]
		#print('READ :: ' + str(msg) + str(status))
		return (msg, status)
	
	
	'''
	CMMonitor :: getSimStatus
	
	getSimStatus returns a null positive value if a simulation is
	currently running, and a negative value if no simulation currently running.
	'''            
	def getSimStatus(self):
		self.write('SimStatus')
		rt = self.read()
		#print ("Hello ......."+str(rt))
		if (rt[0] == b'not_idle'):
			return 0
		else:
			return int(float(str(rt[0], 'ascii'))) if (rt[0] != b'') else -1
	
	
	'''
	CMMonitor :: getCollisionCount
	
	getCollisionCount reads the DVA from the collision sensor, 
	correspondig to the number of objects hit by the vehicle
	'''    
	def getCollisionCount(self):
		self.write('DVARead Sensor.Collision.Vhcl.Fr1.Count')
		return self.read()


	'''
	CMMonitor :: getSlipAngleFL
	
	getSlipAngleFL reads the DVA from the slip of the front wheel, 
	correspondig to the number of objects hit by the vehicle
	'''    
	def getSlipAngleRL(self):
		self.write('DVARead Car.SlipAngleRL')
		return self.read()

	def getVhclX(self):
		self.write('DVARead Vhcl.Fr1.x')
		return self.read()

	def getVhclY(self):
		self.write('DVARead Vhcl.Fr1.y')
		return self.read()


	def getPedX(self):
		self.write('DVARead Traffic.Ped.tx')
		return self.read()

	def getPedY(self):
		self.write('DVARead Traffic.Ped.ty')
		return self.read()
	
	'''
	CMMonitor :: getEndStatus
	
	While a simulation is running, the command returns an empty string.
	In all other cases one of the following string values is returned:
		- completed – The simulation ran until the end.
		- aborted – The simulation was stopped prematurely.
		- failed – The simulation ended with an error.
		- unknown – No simulation was run yet.
	'''    
	def getEndStatus(self):
		self.write('SimInfo endstatus')
		return self.read()
	
	'''
	CMMonitor :: getEndDist
	
	Returns the driven distance as transmitted at the end of the TestRun.
	'''
	def getEndDist(self):
		self.write('SimInfo enddist')
		return self.read()
	
	'''
	CMMonitor :: getEndTime
	
	Returns the simulated time as transmitted at the end of the TestRun.
	'''
	def getEndTime(self):
		self.write('SimInfo endtime')
		return self.read()

	'''
	CMMonitor :: sendParameterValue
	
	sends the parameter value before TestRun.
	'''
	def sendParameterValue(self, speed, pedPos,pedSpeed ):
		#self.write('handle -set Road.Link.0.Bump.0.Param 141.064,0,155.087,0,-3.415,100,1,-1,12,3.5')
		self.write('IFileModify TestRun "DrivMan.Init.Velocity" "' + str(speed) +'"')
		self.read()
		self.write('IFileModify TestRun "DrivMan.0.LongDyn" "Driver 1 0 ' + str(speed) +'"')
		self.read()
		self.write('IFileModify TestRun "Traffic.0.Man.0.LongDyn" "v ' + str(round(pedSpeed,1)) +'"')
		self.read()
		self.write('IFileFlush')
		self.read()
		self.write('IFileModifyTxt TestRun "Traffic.0.Man.1.PathST" { {0 -4.8 0 0 0 ' + str(round(pedSpeed,1))+'} {' + str(round(pedPos,1)) +' 4 0 0 1 '+str(round(pedSpeed,1))+'} }')
		self.read()
		self.write('IFileFlush')
		#self.read()
		#self.write('IFileModify TestRun "VehicleLoad.0.mass" 500')
		#self.write('handle -set IsRunning 1')
		print('After writing param')
		return self.read()
	
	'''
	CMMonitor :: getSimStatus
	
	getSimStatus starts the carmaker simulation.
	''' 
	def startSim(self):
		self.write("StartSim")
		print("Start Sim")
		tnout2 = self.tn.read_some()
		print('After Start Sim')
	
	
	'''
	CMMonitor :: testRunListActiveProject
	
	testRunListActiveProject returns the list of the testruns
	files currently in the working project.
	'''     
	def testRunListActiveProject(self):
		self.write("glob ./Data/TestRun/*")
		
		tnout = self.read()
		
		tnout = tnout[0]
		
		tlist = list()
		
		for path in tnout.split(b' '):
			pathStr = str(path, 'ascii')
			pathStr = re.sub(r'^./Data/TestRun/', '', pathStr)
			tlist.append(pathStr)
		
		
			
		return tlist
	
	'''
	CMMonitor :: LoadTestRun
	
	@fpath : A string which contains the path with the TestRun library 
	folder in the filesystem.
	
	Loads testrun testName in the fpath folder library. If fpath is empty
	Carmaker will look for the testName file in the default folder
	for the current project (i.e ProjectFolder/Data/TestRun)
	'''    
	def LoadTestRun(self, testName, fpath=""):
		cmd = "LoadTestRun " + fpath + testName
		print(cmd)
		self.write(cmd)
		
	'''
	CMMonitor :: waitForSimEnd
	
	Block until the Carmaker simulation is not finish. 
	'''
	def waitForSimEnd(self):
		global euclidDist
		while (self.getSimStatus() >= -1):
			print("I am in loop.....")
			time.sleep(0.1)
			vehicleX = float(self.getVhclX()[0])
			vehicleY = float(self.getVhclY()[0])
			pedX = float(self.getPedX()[0])
			pedY = float(self.getPedY()[0])
			#dist = ((vehicleX - pedX)**2 + (vehicleY - pedY)**2)**0.5
			#print('dist==', str(dist))
			dist = 999999
			#print('dif------------'+str(int(vehicleY - pedY)))
			if(int((vehicleY - pedY)) == 0):
				dist = pedX - vehicleX
				print('vehicleX------'+str(vehicleX))
				print('pedX------'+str(pedX))
				print('dist-------', str(dist))
			if(dist<euclidDist):
				euclidDist = dist
			
		print('euclidDist======='+str(euclidDist))
			#print('---------slip angle FL'+str(slipAngleFL, 'ascii')+'---------slip angle RL'+str(slipAngleRL, 'ascii'))
	
	'''
	CMMonitor :: waitForSimReady
	
	Block until the simulation is not started or in preparation.
	'''        
	def waitForSimReady(self):
		while (self.getSimStatus() < 0):
			time.sleep(0.1)


def loadScenarioandSimulate(speed,pedPos,pedSpeed):
	global euclidDist
	cmm = CMMonitor("localhost", 16660)
	euclidDist = 99999
	
	# Prepare CSV file for the simulation result
	with open('result.csv', 'w', newline='') as csvfile:
		spamwriter = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
		spamwriter.writerow(['Test Name', 'End Status', 'End Distance', 'End Time', 'Number of objects hit'])
		
			
		print ('Starting test Maneuveur')
			
		# Load&start Carmaker testrun
		cmm.write('')
		cmm.read()
		cmm.LoadTestRun('PedestrianCrossing','C:\\\\CM_Projects\\\\CarMaker\\\\Data\\\\TestRun\\\\My_TestRuns\\\\')
		cmm.sendParameterValue(speed,pedPos,pedSpeed)
		print('After setting param values')		

		print('start sim')
		#print(cmm.getSimStatus())
		cmm.startSim()
		#print('sim started')
		print(cmm.getSimStatus())
		cmm.read()
		print('sim read')
			
		time.sleep(1)
			
		# Wait until the testrun is in preparation in Carmaker
		cmm.waitForSimReady()
			
		# Subscribe to the quantity
		cmm.write("QuantSubscribe Sensor.Collision.Vhcl.Fr1.Count")
		cmm.read()

		# Subscribe to the vehicle pos
		cmm.write("QuantSubscribe Vhcl.Fr1.x")
		cmm.read()

		# Subscribe to the ped pos
		cmm.write("QuantSubscribe Traffic.Ped.tx")
		cmm.read()

		cmm.write("QuantSubscribe Traffic.Ped.ty")
		cmm.read()

		cmm.write("QuantSubscribe Vhcl.Fr1.y")
		cmm.read()

		# Wait until the end of the simulation
		cmm.waitForSimEnd()
			
		# Get the status of the last finished simulation from Carmaker
		endstatus = cmm.getEndStatus()
		print('------endstatus value-----'+str(endstatus[0], 'ascii'))
		time.sleep(0.1)
			
		# Get the last traveled distance in Carmaker
		enddist = cmm.getEndDist()
		print('------enddist value-----'+str(enddist[0], 'ascii'))
		time.sleep(0.1)
			
		# Get the duration of the Carmaker simulation
		endtime = cmm.getEndTime()
		print('------endtime value-----'+str(endtime[0], 'ascii'))
		time.sleep(0.1)
		
			
		# How much object hit
		collisionCount = cmm.getCollisionCount()
		print('------collisionCount value-----'+str(collisionCount[0], 'ascii'))
			
		# Write the result in the CSV file
		spamwriter.writerow(["test 1", str(endstatus[0], 'ascii'), str(enddist[0], 'ascii'), str(endtime[0], 'ascii'), str(collisionCount[0], 'ascii')])


def bayes_opt(bounds):
	speed = bounds[0][0]
	pedPos = bounds[0][1]
	pedSpeed = bounds[0][2]
	print('chosen param values---'+str(speed)+'=='+str(pedPos)+'=='+str(pedSpeed))
	#Replace the file with new friction value

	loadScenarioandSimulate(speed,pedPos,pedSpeed)
	#print('slipAngleFLMax-------'+str(slipAngleFLMax)+'slipAngleRLMax--------'+str(slipAngleRLMax)+'Function value '+str(slipAngleFLMax - slipAngleRLMax))
	return euclidDist
	
if __name__ == '__main__':
	#loadScenarioandSimulate()
	np.random.seed(123)
	#Domain of uncertainity five sensor values
	bounds = [{'name': 'speed', 'type': 'continuous', 'domain': (40,60)},
			  {'name': 'pedPos', 'type': 'continuous', 'domain': (0,10)},
			  {'name': 'pedSpeed', 'type': 'continuous', 'domain': (15,20)}]
	#Budget number of evaluations of f
	max_iter = 60
	# Creates GPyOpt object with the model and acquisition fucntion
	myProblem = GPyOpt.methods.BayesianOptimization(bayes_opt,     # function to optimize
												model_type = 'GP',
												domain=bounds,  # box-constraints of the problem
												acquisition_type='EI',
												exact_feval = True) # Selects the Expected improvement
	max_time = 60     # time budget 
	myProblem.run_optimization(max_iter, max_time)
	print('Optimal parameter value'+str(myProblem.x_opt))
	print('Optimal function value'+str(myProblem.fx_opt))