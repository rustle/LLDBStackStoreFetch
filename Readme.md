#What's it do?

This is a way to store stack frames, including their local variables using LLDBs python interface, with a goal to make sowing together stack traces across queues easy. Very much a work in progress, but pretty cool as is.

#Setup

Add .lldbinit, StackStore.py to ~/LLDB

Check out the BlockStack project and it's breakpoints.

#Notes

This has only been tested on Xcode 5. If you're making changes to StackStore.py, you usually don't need to restart Xcode, but once in awhile you do, cause bugs.