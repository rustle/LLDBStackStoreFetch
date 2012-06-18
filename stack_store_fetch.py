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

def key_for_command(command):
	parser = OptionParser()
	parser.add_option("-k", "--key", action="store", type="string", dest="key")
	parser.add_option("-a", "--argument", action="store", type="string", dest="argument")
	(options, args) = parser.parse_args(shlex.split(command))
	if options.key:
		return options.key
	elif options.argument:
		# This is a pretty crappy way to resolve the $arg into a memory address, 
		# hopefully I can find a better
		# way to do this
		return lldb.thread.GetFrameAtIndex(0).EvaluateExpression(str(options.argument)).GetObjectDescription()
	else:
		return False

stack_hash_map = None

def store_stack_for_object(stack, object):
	global stack_hash_map
	if stack_hash_map == None:
		stack_hash_map = dict()
	stack_hash_map[object] = stack

def store_stack(debugger, command, result, dict):
	key = key_for_command(command)
	if key:
		store_stack_for_object(lldbutil.print_stacktrace(lldb.thread, True), key)

def fetch_stack(debugger, command, result, dict):
	key = key_for_command(command)
	if key:
		if key in stack_hash_map:
			originating_stack = stack_hash_map[key]
			current_stack = lldbutil.print_stacktrace(lldb.thread, True)
			appended_stack = "Reconstructed stack trace for " + key + "\n" + str(current_stack) + str(originating_stack)
			return appended_stack

def print_stack(debugger, command, result, dict):
	stack_trace = fetch_stack(debugger, command, result, dict)
	print stack_trace

def append_stack(debugger, command, result, dict):
	key = key_for_command(command)
	if key:
		current_stack = lldbutil.print_stacktrace(lldb.thread, True)
		if key in stack_hash_map:
			originating_stack = stack_hash_map[key]
			appended_stack = str(current_stack) + str(originating_stack)
			store_stack_for_object(appended_stack, key)
			return appended_stack
		else:
			store_stack_for_object(current_stack, key)
			return current_stack

if __name__ == '__main__':
	# Create a new debugger instance in your module if your module 
	# can be run from the command line. When we run a script from
	# the command line, we won't have any debugger object in
	# lldb.debugger, so we can just create it if it will be needed
	lldb.debugger = lldb.SBDebugger.Create()
elif lldb.debugger:
	# Module is being run inside the LLDB interpreter
	target = lldb.debugger.GetSelectedTarget()
	# set symbolic breakpoint on "dispatch_async"
#	dispatch_async_bp = target.BreakpointCreateByName("dispatch_async", "")
	# attach debugger command "store_stack -a $arg2"
#	dispatch_async_bp.SetCallback()
	# set symbolic breakpoint on "_dispatch_call_block_and_release"
#	dispatch_call_and_release_bp = target.BreakpointCreateByName("_dispatch_call_block_and_release", "")
	# attach debugger command "fetch_stack -a $arg1"
#	dispatch_async_bp.SetCallback()

def __lldb_init_module(debugger, dict):
	# This initializer is being run from LLDB in the embedded command interpreter
	# Add any commands contained in this module to LLDB
	debugger.HandleCommand('command script add -f stack_store_fetch.store_stack store_stack')
	debugger.HandleCommand('command script add -f stack_store_fetch.fetch_stack fetch_stack')
	debugger.HandleCommand('command script add -f stack_store_fetch.append_stack append_stack')
	debugger.HandleCommand('command script add -f stack_store_fetch.print_stack print_stack')
	print '"BTStoreFetch" commands installed'
