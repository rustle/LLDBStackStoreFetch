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
import lldbutil
from optparse import OptionParser

def parse_command(command):
	parser = OptionParser()
	parser.add_option("-k", "--key", action="store", type="string", dest="key")
	parser.add_option("-a", "--argument", action="store", type="string", dest="argument")
	(options, args) = parser.parse_args(shlex.split(command))
	return options

def key_for_options(options):
	if options.key:
		return options.key
	elif options.argument:
		# This is a pretty crappy way to resolve the $arg into a memory address, 
		# hopefully I can find a better
		# way to do this
		argument = str(options.argument)
		result = lldb.thread.GetFrameAtIndex(0).EvaluateExpression(argument)
		key = str(result.GetObjectDescription())
		# Not sure why I need to do this filtering
		# My python isn't great
		if key == "<nil>":
			key = None
		if key == "None":
			key = None
		if key:
			print "Key {k} for {a}".format(k=key,a=options.argument)
		else:
			print "Unable to get a key for {a}".format(a=options.argument)
		return key
	else:
		return None

stack_hash_map = None

def SetStackHashMap(key, value):
	global stack_hash_map
	if stack_hash_map == None:
		stack_hash_map = dict()
	stack_hash_map[key] = value

def GetStackHashMap(key):
	global stack_hash_map
	if stack_hash_map == None:
		stack_hash_map = dict()
	return stack_hash_map[key]

def store_stack(debugger, command, result, dict):
	print "Store"
	options = parse_command(command)
	key = key_for_options(options)
	if key:
		SetStackHashMap(key, lldbutil.print_stacktrace(lldb.thread, True))

def print_stack(debugger, command, result, dict):
	print "Print"
	options = parse_command(command)
	key = key_for_options(options)
	if key:
		if key in stack_hash_map:
			originating_stack = stack_hash_map[key]
			current_stack = lldbutil.print_stacktrace(lldb.thread, True)
			appended_stack = "Reconstructed stack trace for " + key + "\n" + str(current_stack) + str(originating_stack)
			print appended_stack

def append_stack(debugger, command, result, dict):
	options = parse_command(command)
	key = key_for_options(options)
	if key:
		current_stack = lldbutil.print_stacktrace(lldb.thread, True)
		if key in stack_hash_map:
			originating_stack = stack_hash_map[key]
			appended_stack = str(current_stack) + str(originating_stack)
			SetStackHashMap(key, appended_stack)
		else:
			SetStackHashMap(key, current_stack)

def set_dispatch_breakpoints(debugger, command, result, dict):
	bp = lldb.target.BreakpointCreateByName('dispatch_async')
	debugger.HandleCommand("breakpoint command add -s python {id} -o 'lldb.debugger.HandleCommand(\"store_stack -a $arg2\"); lldb.process.Continue()'".format(id=bp.GetID()))
	bp = lldb.target.BreakpointCreateByName('_dispatch_call_block_and_release')
#	debugger.HandleCommand("breakpoint command add -s python {id} -o 'lldb.debugger.HandleCommand(\"print_stack -a $arg1\"); lldb.process.Continue()'".format(id=bp.GetID()))

def __lldb_init_module(debugger, dict):
	# This initializer is being run from LLDB in the embedded command interpreter
	# Add any commands contained in this module to LLDB
	debugger.HandleCommand('command script add -f stack_store_fetch.store_stack store_stack')
	debugger.HandleCommand('command script add -f stack_store_fetch.append_stack append_stack')
	debugger.HandleCommand('command script add -f stack_store_fetch.print_stack print_stack')
	debugger.HandleCommand('command script add -f stack_store_fetch.set_dispatch_breakpoints set_dispatch_breakpoints')
	print 'Stack trace store fetch commands installed'
