#Setup

Add .lldbinit, stack_store_fetch.py, lldbutil.py to ~/

Restart Xcode (I had to restart my machine for .lldbinit)

Option 1:

Add a symbolic breakpoint for dispatch_async with action:

store_stack -a $arg2

Add a symbolic breakpoint for _dispatch_call_block_and_release with action:

print_stack -a $arg1

Then run the app and see the reconstructed stack trace

Option 2:

Add a auto-continuing breakpoint as early in your app as possible (probably main) and set it's debug command to set_dispatch_breakpoints

This will cause the app to stop on _dispatch_call_block_and_release where you can fetch the trace using 

print_stack -a $arg1

#Things that don't work

* Setting symbolic breakpoints works from the script and there is a set_dispatch_breakpoints function now, but the second breakpoint is commented out because it doesn't behave correctly (the debug command is executed, but expressions are corrupted and the actual breakpoint never hits)

#Future plans

* verbosity settings to be able to get more detailed info from stack traces

#PSA

If you make any changes to the script and you're running an unreleased build of a popular lldb using ide, you'll need to restart it after each change.