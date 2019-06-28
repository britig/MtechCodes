# import threading
# import time
#
# j = 0
#
# def loop1_10():
#     global j
#     for i in range(1, 11):
#         time.sleep(1)
#         print(i)
#         print(j)
#         j = j + 1
#
#
# threading.Thread(target=loop1_10).start()
# threading.Thread(target=loop1_10).start()

import _thread
import time

# Define a function for the thread
def print_time( threadName, delay):
   count = 0
   while count < 5:
      time.sleep(delay)
      count += 1
      print("%s: %s" % ( threadName, time.ctime(time.time())))

# Create two threads as follows
try:
   _thread.start_new_thread( print_time, ("Thread-1", 2, ) )
   _thread.start_new_thread( print_time, ("Thread-2", 4, ) )
except:
   print("Error: unable to start thread")

while 1:
   pass
