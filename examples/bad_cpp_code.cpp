#include <iostream>
#include <cstdlib>

using namespace std;

#define BUFFER_SIZE 256
#define SQUARE(x) x * x

int global_var;

class MotorController : public MotorBase {
public:
    MotorController() {
        speed = 0;
    }

    ~MotorController() {
        delete[] buffer;  // ❌ dynamic memory
    }

    void setSpeed(int s) {
        if (s > 100)
            speed = 100; // ❌ no braces
        else
            speed = s;
    }

    void unsafeFunction(int* ptr) {
        //rolint: ignore
        *ptr = rand(); // ❌ unsafe random, possible null deref
    }

    void loopWithGoto() {
        int i = 0;
    start:
        if (i < 10) {
            cout << "i: " << i << endl;
            i++;
            goto start; // ❌ forbidden control flow
        }
    }

    void recursive(int n) {
        if (n == 0) return;
        recursive(n - 1); // ❌ recursion
    }

    void badSwitch(int val) {
        switch (val) {
        case 1:
            cout << "One" << endl;
            // ❌ missing break (fallthrough)
        case 2:
            cout << "Two" << endl;
            continue;
        default:
            return;
        }
    }

    void start() {
        buffer = new char[BUFFER_SIZE]; // ❌ heap allocation
        int x = 5;
        int result = SQUARE(x + 1);  // ❌ macro side effect
        cout << "Result: " << result << endl;
    }

private:
    int speed;
    char* buffer;
};
