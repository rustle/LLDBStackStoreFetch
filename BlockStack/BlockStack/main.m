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
	__block id block = ^(void) {
		printf("%p\n", block);
	};
	printf("%p\n", block);
	dispatch_async(dispatch_get_global_queue(DISPATCH_QUEUE_PRIORITY_HIGH, 0), block);
}

void foo(void)
{
	bar();
}

int main(int argc, const char * argv[])
{
	@autoreleasepool {
		foo();
		
		dispatch_main();
	}
    return 0;
}
