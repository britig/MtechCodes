'''
Created on 13 Jun 2018

@author: raouf_z
'''
import os
import telnetlib
import re
import configparser
from enum import Enum
import time
import csv

import paramiko, sys, time, threading
import ClosedLoopDictionary
import ACSAutomation


hostname = "192.168.0.112"
password = "Mapping2018"
command = 'bash -l -c "bash .bashrc && echo $PATH"'

username = "jorge"
port = 22


'''
SimStatus >= 0 : The ID of the maneuveur currently running
SimStatus < 0  : Simulation is not running, details below
'''
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
        cmd = msg + '\r\n'
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
        return (msg, status)
    
    
    '''
    CMMonitor :: getSimStatus
    
    getSimStatus returns a null positive value if a simulation is
    currently running, and a negative value if no simulation currently running.
    '''            
    def getSimStatus(self):
        self.write('SimStatus')
        rt = self.read()
        #print (rt)
        if (rt[0] == b'not_idle'):
            return 0
        else:
            return int(str(rt[0], 'ascii'))
    
    
    '''
    CMMonitor :: getCollisionCount
    
    getCollisionCount reads the DVA from the collision sensor, 
    correspondig to the number of objects hit by the vehicle
    '''    
    def getCollisionCount(self):
        self.write('DVARead Sensor.Collision.Vhcl.Fr1.Count')
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
    CMMonitor :: getSimStatus
    
    getSimStatus starts the carmaker simulation.
    ''' 
    def startSim(self):
            self.write("StartSim")
            cmm.tn.read_some()
    
    
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
        self.write(cmd)
        
    '''
    CMMonitor :: waitForSimEnd
    
    Block until the Carmaker simulation is not finish. 
    '''
    def waitForSimEnd(self):
        while (self.getSimStatus() >= -1):
            time.sleep(0.1)
    
    '''
    CMMonitor :: waitForSimReady
    
    Block until the simulation is not started or in preparation.
    '''        
    def waitForSimReady(self):
        while (self.getSimStatus() < 0):
            time.sleep(0.1)
    
    
if __name__ == '__main__':
    cmc = CMConfig('config.ini')
    
    # Get the list of the files avilable in path specified
    # by config.ini
    l = os.listdir(cmc.getFolderPath())
    
    # New empty list for the testrun files
    testRunList = list()
    
    # Omit filnames starting by '.' as they are not test run files.
    # Each testrun filenames should follow this convention SituationX_[description]   
    for f in l:
        if f[0] != '.' :
            testRunList.append(f)
    
    #print(cmc)
    cmm = CMMonitor("localhost", 16660)
    
    # Working thread for RVIZ
    RVIZRemoteShellControl = ACSAutomation.ACSRemoteControlSSH('192.168.0.112', 'jorge', 'Mapping2018')
    
    # Working thread for rostopic /remote_start_destination advertising
    WaypRemoteShellControl = ACSAutomation.ACSRemoteControlSSH('192.168.0.112', 'jorge', 'Mapping2018')
    
    # Working thread for CommsSerialArduino.launch
    CommRemoteShellControl = ACSAutomation.ACSRemoteControlSSH('192.168.0.112', 'jorge', 'Mapping2018')
    
    # Working thread for rostopic pub /start_message std_msgs/String "data: 'start'" command
    StrtRemoteShellControl = ACSAutomation.ACSRemoteControlSSH('192.168.0.112', 'jorge', 'Mapping2018')
    
    # Working thread for resetting /acs_to_pod :
    # rostopic pub /acs_to_pod CommsArduinoSerialCAN/AcsToPod 
    #     "{StateRequest: 0, 
    #       Throttle: 0, 
    #       Velocity: 0, 
    #       SteeringPercent: 0,
    #       BrakeOff: false}"
    StopRemoteShellControl = ACSAutomation.ACSRemoteControlSSH('192.168.0.112', 'jorge', 'Mapping2018')
    
    # Start each remote shells as individual working thread
    RVIZRemoteShellControl.start()
    WaypRemoteShellControl.start()
    CommRemoteShellControl.start()
    StrtRemoteShellControl.start()
    StopRemoteShellControl.start()   
    
    # Prepare CSV file for the simulation result
    with open('result.csv', 'w', newline='') as csvfile:
        spamwriter = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        spamwriter.writerow(['Test Name', 'End Status', 'End Distance', 'End Time', 'Number of objects hit'])
        
        # For each testrun file in the data/testrun directory
        for t in testRunList:
            
            print ('Starting test ' + t)
            
            # Reset the /acs_to_pod parameters
            StopRemoteShellControl.writeCmd('~/code/WMG/scripts/stop_pod.bash\n')
            time.sleep(5)
            StopRemoteShellControl.sendSIGINT()
            
            # Load&start Carmaker testrun
            cmm.LoadTestRun(t)
            cmm.startSim()
            cmm.read()
            
            time.sleep(1)
            
            # Wait until the testrun is in preparation in Carmaker
            cmm.waitForSimReady()
            
            # Subscribe to the quantity
            cmm.write("QuantSubscribe Sensor.Collision.Vhcl.Fr1.Count")
            cmm.read()

            # Get RVIZ launch file Sx.launch corresponding to the testrun
            #RVIZLaunchFile = ClosedLoopDictionary.ClosedLoopData[t.split('_')[0]][0];
            RVIZLaunchFile = ClosedLoopDictionary.ClosedLoopData[re.split('-|_',t)[0]][0];
            
            # Get the bash file Sx.bash corresponfing to the actual testrun
            #BashScript = ClosedLoopDictionary.ClosedLoopData[t.split('_')[0]][1];
            BashScript = ClosedLoopDictionary.ClosedLoopData[re.split('-|_',t)[0]][1];
            
            time.sleep(1)
            
            # Launch RVIZ
            RVIZRemoteShellControl.writeCmd("roslaunch " + RVIZLaunchFile + "\n")
            time.sleep(10)
            
            # Set start/and destination
            WaypRemoteShellControl.writeCmd(BashScript + "\n")
            time.sleep(1)
            
            # Start CommsArdiunoSerial
            CommRemoteShellControl.writeCmd('roslaunch ~/code/WMG/launchers/CommsArduinoSerialCAN.launch\n')
            
            time.sleep(1)
            
            # Start the navigation
            StrtRemoteShellControl.writeCmd('~/code/WMG/scripts/start.bash\n')
            
            # Wait until the end of the simulation
            cmm.waitForSimEnd()
            
            # Close the programs
            RVIZRemoteShellControl.sendSIGINT()
            WaypRemoteShellControl.sendSIGINT()
            CommRemoteShellControl.sendSIGINT()
            StrtRemoteShellControl.sendSIGINT()
            
            # Get the status of the last finished simulation from Carmaker
            endstatus = cmm.getEndStatus()
            time.sleep(0.1)
            
            # Get the last traveled distance in Carmaker
            enddist = cmm.getEndDist()
            time.sleep(0.1)  
            
            # Get the duration of the Carmaker simulation
            endtime = cmm.getEndTime()
            time.sleep(0.1)
            
            # How much object hit
            collisionCount = cmm.getCollisionCount()
            
            # Write the result in the CSV file
            spamwriter.writerow([t,  str(endstatus[0], 'ascii'), str(enddist[0], 'ascii'), str(endtime[0], 'ascii'), str(collisionCount[0], 'ascii')])
            
    RVIZRemoteShellControl.stopLoop()
    WaypRemoteShellControl.stopLoop()
    CommRemoteShellControl.stopLoop()
    StrtRemoteShellControl.stopLoop()
    StopRemoteShellControl.stopLoop()

    #list = cmm.testRunListActiveProject()
    #cmm.LoadTestRun(list[1])