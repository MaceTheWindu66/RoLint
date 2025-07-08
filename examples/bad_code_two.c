#include <stdio.h>
#include <string.h>

const char global_buf[100];
extern char lol[10];

void test() {
    
    int a;
    int b = 0;
    int c = 0, d = 5;
    int arr[10];

    char buf[100];
    gets(buf);                     // 🚨 banned: gets
    strcpy(global_buf, buf);      // 🚨 banned: strcpy
    sprintf(buf, "Hello %s", buf); // 🚨 banned: sprintf
    
    int x = 5;
    printf("%d\n", toupper(x));          // 🚨 side effect in function arg that is known to be pure. False positive test ( i know you cant do toupper on an int its just a test)

    int temp = 42;                // 🚨 defined at global scope, used only here

    

    switch(x){
        case 1:
            break;
        case 2:
            continue;
    }

    for(int i = 0; i < 10; i++){
        switch(arr[i]) {
            case 1: break;
        }
    }


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
