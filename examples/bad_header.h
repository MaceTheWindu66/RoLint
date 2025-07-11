// Missing include guard!

#include <stdio.h>

int global_flag = 0;       // ❌ object definition
char buffer[256];          // ❌ object definition
static int counter = 1;    // ❌ static object definition

void do_work();            // ✅ function declaration is okay
