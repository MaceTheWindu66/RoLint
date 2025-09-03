#include <stdio.h>
#include <string.h>

char global_buf[100];
#define MAX_SIZE 100;
#define SQUARE(x) ((x)*(x))


void test() {

    int a;
    int b = 0;
    int c = 0, d = 5;
    int e = 3.14;
    short s = 1;

    struct MSG;
    
    b = s;


    
    char buf[100];
    gets(buf);                     // 🚨 banned: gets
    // rolint: ignore
    strcpy(global_buf, buf);      // 🚨 banned: strcpy
    sprintf(buf, "Hello %s", buf); // 🚨 banned: sprintf

    b = 4.2;
    int x = 5;
    printf("%d\n", x++);          // 🚨 side effect in function arg

    x = (short)b;

    int temp = 42;                

    test();

    // rolint: ignore-block
    switch (x) {
    case 1:
        printf("One\n");  // No break here!
    case 2:
        printf("Two\n");
        break;
    case 3:
        printf("Three\n");
        // fallthrough  //
    case 4:
        printf("Four\n");
        break;
}


    return;
    temp += 1;                    // 🚨 dead code
}

int main() {
    test();
    return 0;
}
