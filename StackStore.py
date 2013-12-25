#!/usr/bin/python
# 
#  Created by Doug Russell on 6/14/12.
#  Copyright (c) 2012 Doug Russell. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# 

import lldb
import commands
import shlex
from optparse import OptionParser

#TODO add type to indicate local var vs argument var

def RSTLAppendValue(name, value, string):
	if len(string) > 1:
		string += ","
	string += "'{name}': '{value}'".format(name=name, value=value)
	return string

class RSTLCapturedVariable(object):
	# A captured local var or function argument from a stack frame
	_name = None
	_value = None
	_dereference = None
	_string_description = None
	_summary = None
	_is_pointer = False
	def __init__(self, variable):
		name = variable.name
		if name:
			self.name = name
		value = variable.value
		if value:
			self.value = value
		summary = variable.summary
		if summary:
			self.summary = summary
		else:
			if variable.type.is_pointer:
				self.is_pointer = True
				deref = variable.deref;
				self.dereference = RSTLCapturedVariable(deref)
			else:
				self.string_description = str(variable)
	@property
	def name(self):
		return self._name
	@name.setter
	def name(self, value):
		self._name = value
	@property
	def value(self):
		return self._value
	@value.setter
	def value(self, value):
		self._value = value
	@property
	def dereference(self):
		return self._dereference
	@dereference.setter
	def dereference(self, value):
		self._dereference = value
	@property
	def string_description(self):
		return self._string_description
	@string_description.setter
	def string_description(self, value):
		self._string_description = value
	@property
	def summary(self):
		return self._summary
	@summary.setter
	def summary(self, value):
		self._summary = value
	@property
	def is_pointer(self):
		return self._is_pointer
	@is_pointer.setter
	def is_pointer(self, value):
		self._is_pointer = value
	def __repr__(self):
		rep = "{"
		if self.name:
			rep = RSTLAppendValue('name', self.name, rep)
		if self.value:
			rep = RSTLAppendValue('value', self.value, rep)
		if self.is_pointer:
			rep = RSTLAppendValue('is_pointer', self.is_pointer, rep)
		if self.dereference:
			rep = RSTLAppendValue('dereference', self.dereference, rep)
		if self.string_description:
			rep = RSTLAppendValue('string_description', self.string_description.replace("\n", ""), rep)
		if self.summary:
			rep = RSTLAppendValue('summary', self.summary, rep)
		rep += "}"
		return rep

class RSTLStackFrame(object):
	# An individual stack frame in a stack trace
	_function_name = None
	_is_inline = False
	_variables = None
	def __init__(self, frame):
		self.variables = list()
		function_info = self.GetFunctionInfoForFrame(frame)
		self.function_name = function_info[0]
		self.is_inline = function_info[1]
		if frame.line_entry.IsValid():
			variables = frame.GetVariables(True, True, False, True)
			for variable in variables:
				name = variable.name
				if name:
					self.AddVariable(RSTLCapturedVariable(variable));
	@property
	def function_name(self):
		return self._function_name
	@function_name.setter
	def function_name(self, value):
		self._function_name = value
	@property
	def is_inline(self):
		return self._is_inline
	@is_inline.setter
	def is_inline(self, value):
		self._is_inline = value
	def AddVariable(self, value):
		if value:
			self.variables.append(value)
	def GetFunctionInfoForFrame(self, frame):
		inline_block = frame.GetBlock().GetContainingInlinedBlock()
		if (inline_block.IsValid()):
			return (inline_block.GetInlinedName(), True)
		else:
			function_name = frame.GetFunction().GetName()
			if not function_name:
				function_name = frame.GetSymbol().GetName()
			return (function_name, False)
	def __repr__(self):
		rep = "{"
		if self.function_name:
			rep += "\n	'function_name': '%s'" % self.function_name
		if self.is_inline:
			rep += "\n	'is_inline': '%s'" % self.is_inline
		if self.variables:
			rep += "\n	["
			for variable in self.variables:
				rep += "\n		%s" % variable
			rep += "\n	]"
		rep += "\n}"
		return rep


#######
# LLDB State Getters
#######

def GetSelectedThread(debugger):
	thread = debugger.GetSelectedTarget().process.GetSelectedThread()
	return thread

def GetSelectedTarget(debugger):
	target = debugger.GetSelectedTarget()
	return target

def GetSelectedFrame(debugger):
	frame = debugger.GetSelectedTarget().process.GetSelectedThread().frames[0]
	return frame

#######
# Input parsing
#######

def ParseCommands(command):
	parser = OptionParser()
	parser.add_option("-k", "--key", action="store", type="string", dest="key")
	parser.add_option("-a", "--argument", action="store", type="string", dest="argument")
	parser.add_option('-b', "--block", default=False, action='store_true', dest="block")
	(options, args) = parser.parse_args(shlex.split(command))
	return options

def KeyForOptions(options, debugger):
	key = None
	if options.key:
		key = options.key
	elif options.block:
		frame = GetSelectedFrame(debugger)
		block = GetSelectedFrame(debugger).EvaluateExpression(options.argument)
		debugger.HandleCommand('expr struct $BlockLiteral {void *isa; int flags; int reserved; void (*invoke)(void *, ...);};')
		blockCast = frame.EvaluateExpression("($BlockLiteral *)%d" % block.GetValueAsUnsigned())
		invoke = blockCast.GetChildMemberWithName("invoke")
		key = "%d" % invoke.GetValueAsUnsigned()
	elif options.argument:
		# Fix this to check the SBValues type and probably use GetValueAsUnsigned for pointers
		argument = str(options.argument)
		result = GetSelectedThread(debugger).GetFrameAtIndex(0).EvaluateExpression(argument)
		key = str(result.GetObjectDescription())
	# Filter for non object sbvalues returning none or and empty object descriptions returning nil
	if key == "<nil>":
		key = None
	if key == "None":
		key = None
	if key == None:
		print "Unable to get a key for {a}".format(a=options.argument)
	return key

#######
# Storage
#######

stack_hash_map = None

def GetStackHashMap():
	global stack_hash_map
	if stack_hash_map == None:
		stack_hash_map = dict()
	return stack_hash_map

#######
# Stack Trace
#######

def CaptureStackTrace(thread):
	frame_depth = thread.GetNumFrames()
	trace = list()
	for frame_index in range(frame_depth):
		trace.append(RSTLStackFrame(thread.GetFrameAtIndex(frame_index)))
	return trace

def PrintTraceForKey(key):
	if key:
		stack_map = GetStackHashMap()
		if key in stack_map:
			trace_list = stack_map[key]
			for trace in trace_list:
				for frame in trace:
					print frame

#######
# Public API
#######

def AppendStack(debugger, command, result, dict):
	options = ParseCommands(command)
	key = KeyForOptions(options, debugger)
	if key:
		current_stack = CaptureStackTrace(GetSelectedThread(debugger))
		stack_map = GetStackHashMap()
		trace_list = None
		if key in stack_map:
			trace_list = stack_map[key]
		if trace_list == None:
			trace_list = list()
			stack_map[key] = trace_list
		trace_list.append(current_stack)
		print "Stored trace for " + key
	return False

def PrintOriginatingStack(debugger, command, result, dict):
	frame = GetSelectedFrame(debugger)
	address = frame.GetFunction().GetStartAddress().GetLoadAddress(GetSelectedTarget(debugger))
	key = "%d" % address
	PrintTraceForKey(key)
	return False

def PrintStack(debugger, command, result, dict):
	options = ParseCommands(command)
	key = KeyForOptions(options, debugger)
	PrintTraceForKey(key)
	return False

def PrintAllStoredStacks(debugger, command, result, dict):
	stack_map = GetStackHashMap()
	print stack_map
	return False

def SetDispatchBreakpoints(debugger, command, result, dict):
	bp = GetSelectedTarget(debugger).BreakpointCreateByName('dispatch_async')
	debugger.HandleCommand("breakpoint command add -s python {id} -o 'lldb.debugger.HandleCommand(\"append_stack -b -a $arg2\"); return False;'".format(id=bp.GetID()))
	print "Setup dispatch breakpoints"
	return False

def __lldb_init_module(debugger, dict):
	# This initializer is being run from LLDB in the embedded command interpreter
	# Add any commands contained in this module to LLDB
	debugger.HandleCommand('command script add -f StackStore.AppendStack append_stack')
	debugger.HandleCommand('command script add -f StackStore.PrintOriginatingStack print_originating_stack')
	debugger.HandleCommand('command script add -f StackStore.PrintAllStoredStacks print_stored_stacks')
	debugger.HandleCommand('command script add -f StackStore.PrintStack print_stack')
	debugger.HandleCommand('command script add -f StackStore.SetDispatchBreakpoints set_dispatch_breakpoints')
