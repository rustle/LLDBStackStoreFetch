#Setup

Add .lldbinit, stack_store_fetch.py, lldbutil.py to ~/

Restart Xcode (I had to restart my machine for .lldbinit)

Add a symbolic breakpoint for dispatch_async with action:

store_stack -a $arg2

Add a symbolic breakpoint for _dispatch_call_block_and_release with action:

print_stack -a $arg1

Then run the app and see the reconstructed stack trace

#Things that don't work

* Setting symbolic breakpoints works from the script, but I can't suss out the syntax for callbacks or how to autocontinue after the callback
* There is a set_dispatch_breakpoints function now, but if you use that instead of making the breakpoints manually, it never reaches the second breakpoint and doesn't resolve expressions correctly

#Future plans

* verbosity settings to be able to get more detailed info from stack traces

#PSA

If you make any changes to the script and you're running an unreleased build of a popular lldb using ide, you'll need to restart it after each change.