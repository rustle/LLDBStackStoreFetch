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
	id block = ^(void) {
		// NSLog will cause some dispatch to happen, so printf can help bring down the noise level
		printf("test");
//		NSLog(@"test");
	};
	dispatch_async(dispatch_get_global_queue(DISPATCH_QUEUE_PRIORITY_HIGH, 0), block);
}

void foo(void)
{
	bar();
}

void blocks(void)
{
	foo();
}

NSOperationQueue *queue;

void bat()
{
	[[NSNotificationCenter defaultCenter] postNotificationName:@"Test" object:nil];
}

void baz()
{
	bat();
}

void notifications(void)
{
	queue = [NSOperationQueue new];
	
	[[NSNotificationCenter defaultCenter] addObserverForName:@"Test" object:nil queue:queue usingBlock:^(NSNotification *note) {
		
	}];
	
	baz();
}

int main(int argc, const char * argv[])
{
	@autoreleasepool {
		blocks();
		
		notifications();
		
		dispatch_main();
	}
    return 0;
}
