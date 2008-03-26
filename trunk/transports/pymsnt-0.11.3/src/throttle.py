# Copyright 2006 James Bunton <james@delx.cjb.net> 
# Licensed for distribution under the GPL version 2, check COPYING for details


from twisted.internet import task

class Throttler:
	def __init__(self, consumer, speed):
		self.consumer = consumer

		self.buffer = ""
		self.speed = speed # Bytes/second
		self.canClose = False

		self.loopTask = task.LoopingCall(self.loopFunc)
		self.loopTask.start(1.0)
	
	def write(self, data):
		if not self.consumer:
			raise ValueError, "I/O operation on closed 'file'"
		self.buffer += data
	
	def close(self):
		self.canClose = True
	
	def error(self):
		self.consumer.error()
		self.consumer = None
		self.buffer = None
		self.loopTask.stop()
	
	def loopFunc(self):
		if self.canClose and len(self.buffer) == 0:
			self.consumer.close()
			self.consumer = None
			self.loopTask.stop()

		else:
			chunk, self.buffer = self.buffer[:self.speed], self.buffer[self.speed:]
			self.consumer.write(chunk)



