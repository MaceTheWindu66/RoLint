#include <stdio.h>
#include <string.h>

char global_buf[100];

void test() {
    
    int a;
    int b = 0;
    int c = 0, d = 5;

    char buf[100];
    gets(buf);                     // 🚨 banned: gets
    strcpy(global_buf, buf);      // 🚨 banned: strcpy
    sprintf(buf, "Hello %s", buf); // 🚨 banned: sprintf
    
    int x = 5;
    printf("%d\n", x++);          // 🚨 side effect in function arg

    int temp = 42;                // 🚨 defined at global scope, used only here

    if (x == 3){
        goto error;
    }

    error:
        return;
}


int main() {
    test();
    return 0;
}
