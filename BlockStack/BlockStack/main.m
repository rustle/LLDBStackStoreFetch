//
//  main.m
//  BlockStack
//
//  Created by Doug Russell on 6/14/12.
//  Copyright (c) 2012 __MyCompanyName__. All rights reserved.
//

#import <Foundation/Foundation.h>

NS_INLINE void bar(NSString *string)
{
	id block = ^(void) {
		// NSLog will cause some dispatch to happen, so printf can help bring down the noise level
		printf("test\n");
	};
	dispatch_async(dispatch_get_global_queue(DISPATCH_QUEUE_PRIORITY_HIGH, 0), block);
}

static void foo(void)
{
	struct aStruct { int i; };
	struct aStruct aLocalStruct = { 0 };
	struct aStruct * aLocalStructRef = &aLocalStruct;
	char * test = "testing";
	NSString *foo = @"bar";
	NSString *__strong*baz = &foo;
	int scalar = 10;
	bar(foo);
}

static void blocks(void)
{
	foo();
}

int main(int argc, const char * argv[])
{
	@autoreleasepool {
		blocks();
		
		dispatch_main();
	}
    return 0;
}
