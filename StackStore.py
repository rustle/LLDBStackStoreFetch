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
		# This is a pretty crappy way to resolve the $arg into a memory address, 
		# hopefully I can find a better
		# way to do this
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

def DictionaryForSBValue(variable):
	dictionary = dict()
	value = variable.value
	if value:
		dictionary["value"] = value
	summary = variable.summary
	if summary == None:
		if variable.type.is_pointer:
			dictionary["deref"] = DictionaryForSBValue(variable.deref)
		else:
			dictionary["string_description"] = str(variable)
	else:
		dictionary["summary"] = summary
	return dictionary

def GetFunctionNameForFrame(frame):
	inline_block = frame.GetBlock().GetContainingInlinedBlock()
	if (inline_block.IsValid()):
		return (inline_block.GetInlinedName(), True)
	else:
		function_name = frame.GetFunction().GetName()
		if not function_name:
			function_name = frame.GetSymbol().GetName()
		return (function_name, False)

#TODO: This needs a helper function to handle maximum depth and already visited pointers for deref
def CaptureStackTrace(thread):
	frame_depth = thread.GetNumFrames()
	trace = list()
	for frame_index in range(frame_depth):
		frame = thread.GetFrameAtIndex(frame_index)
		frame_dictionary = dict()
		function = GetFunctionNameForFrame(frame)
		frame_dictionary["frame"] = function[0]
		frame_dictionary["is_inline"] = function[1]
		if frame.line_entry.IsValid():
			variables = frame.GetVariables(True, True, False, True)
			for variable in variables:
				name = variable.name
				if name:
					frame_dictionary[variable.name] = DictionaryForSBValue(variable)
		trace.append(frame_dictionary)
	return trace

#######
# Public API
#######

def AppendStack(debugger, command, result, dict):
	options = ParseCommands(command)
	key = KeyForOptions(options, debugger)
	if key:
		current_stack = CaptureStackTrace(GetSelectedThread(debugger))
		stack_map = GetStackHashMap()
		stack_list = None
		if key in stack_hash_map:
			stack_list = stack_hash_map[key]
		if stack_list == None:
			stack_list = list()
			stack_hash_map[key] = stack_list
		stack_list.append(current_stack)
		print "Stored trace for " + key
	return False

def PrintOriginatingStack(debugger, command, result, dict):
	frame = GetSelectedFrame(debugger)
	address = frame.GetFunction().GetStartAddress().GetLoadAddress(GetSelectedTarget(debugger))
	stack_map = GetStackHashMap()
	key = "%d" % address
	trace_list = stack_map[key]
	for trace in trace_list:
		for frame in trace:
			print frame
	return False

def PrintAllStoredStacks(debugger, command, result, dict):
	stack_map = GetStackHashMap()
	print stack_map
	return False

def SetDispatchBreakpoints(debugger, command, result, dict):
	bp = GetSelectedTarget(debugger).BreakpointCreateByName('dispatch_async')
	debugger.HandleCommand("breakpoint command add -s python {id} -o 'lldb.debugger.HandleCommand(\"append_stack -b -a $arg2\"); return False;'".format(id=bp.GetID()))
	print "Setup dispatch breakpoints"

def __lldb_init_module(debugger, dict):
	# This initializer is being run from LLDB in the embedded command interpreter
	# Add any commands contained in this module to LLDB
	debugger.HandleCommand('command script add -f StackStore.AppendStack append_stack')
	debugger.HandleCommand('command script add -f StackStore.PrintOriginatingStack print_originating_stack')
	debugger.HandleCommand('command script add -f StackStore.PrintAllStoredStacks print_stored_stacks')
	debugger.HandleCommand('command script add -f StackStore.SetDispatchBreakpoints set_dispatch_breakpoints')
