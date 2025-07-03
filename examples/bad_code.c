#include <stdio.h>
#include <string.h>

char global_buf[100];

void test() {
    char buf[100];
    gets(buf);                     // 🚨 banned: gets
    strcpy(global_buf, buf);      // 🚨 banned: strcpy
    sprintf(buf, "Hello %s", buf); // 🚨 banned: sprintf

    int x = 5;
    printf("%d\n", x++);          // 🚨 side effect in function arg

    int temp = 42;                // 🚨 defined at global scope, used only here
    return;
    temp += 1;                    // 🚨 dead code
}

int main() {
    test();
    return 0;
}
