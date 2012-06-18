//
//  main.m
//  BlockStack
//
//  Created by Doug Russell on 6/14/12.
//  Copyright (c) 2012 __MyCompanyName__. All rights reserved.
//

#import <Foundation/Foundation.h>

void bar(void)
{
	dispatch_async(dispatch_get_global_queue(DISPATCH_QUEUE_PRIORITY_HIGH, 0), ^(void) {
		
	});
}

void foo(void)
{
	bar();
}

int main(int argc, const char * argv[])
{
	@autoreleasepool {
		foo();
		
		// dead lock on purpose too let the async call finish
		dispatch_sync(dispatch_get_main_queue(), ^(void) {
			
		});
	}
    return 0;
}

