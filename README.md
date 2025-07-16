# RoLint Compliance Checker And Linter

RoLint is designed to be a robust and strict linter for robotics / embedded systems. It was originally developed for the Humanoid Robot Project at Worcester Polytechnic Institute.
This Linter is designed with MIRSA-C, MIRSA-C++, PEP8, and The Power Of 10 Standards in mind. Below is how to install and use RoLint, as well as an overview of the rules for the linter.

## Installation of RoLint

(NOT CURRENTLY ACCURATE. WILL BE IN FUTURE) RoLint is registtered on PyPi, and you can install it with  

 > **pip install rolint**

This will install the RoLint linter.
Additionally, you can install by cloning this github onto your computer.

## How to Use RoLint

RoLint is extremely simple to use. There are 2 "commands" of RoLint:

> rolint check [OPTIONS] path/to/code.c  <-- To be used on specific files  
> rolint directory/  <--- To run on a project directory as a whole.

### Options for Specific File Linting

When linting a specific file, options must be defined. These options define the language and output.

> #### Options:
> 
> > --lang c | cpp | python  
> > --output text | json  
>
> #### Examples:
> >
> > rolint check --lang c --output text main.c  

## Overview of Rules

There are a lot of rules spanning over the 3 separate languages used for the original project that ROLINT was created for. These rules are primarily
based on MIRSA C/C++, The Power of 10, and PEP8 Standards.

### C Rules  
1. Certain unsafe standard library functions are banned to ensure safe memory operations. The current list is:
> gets, printf, fprintf, sprintf, vsprintf, strcpy, strncpy, strcat, strncat, scanf, sscanf, fscanf, strtok, atoi, atol, atof, atoll, setjmp, longjmp, malloc, calloc, free, realloc  
2. Only one variable can be declared per line.
3. Variables must be initialized when declared.
> int x; **<-- NOT ALLOWED**  
> int x = 5; **<-- ALLOWED**
4. Variables MUST be used if declared.
5. No global variables
6. Side effects are not permitted inside function calls
> EXAMPLE: printf(x++) **<-- NOT ALLOWED**  
7. No function-like macro definitions.
8. No implicit conversions in variable declarations or assignments
> int x = 3.14 **<-- NOT ALLOWED**
9. No narrowing casts
> Casting floats to ints, ints to shorts, etc.
10. No casting between pointer and arithmetic types
11. No recursion.
12. No break/continue statements in a switch statement (unless in a for loop).
13. Switch statements must have a default case.
14. No goto calls or unchecked jumps.
15. Header files must be guarded with an #ifndef statement.
16. Object definitions in header files are not permitted.

### Python Rules  
1. Code must follow PEP8 standards (flake8 used for PEP8 compliance checking).
2. All variables must be declared with static type hints.
  > x : int = 5
3. All functions must have a return annotation.  
> def func() -> int:
4. All function parameters must have static type hints.
> def func(x:int) -> int:
5. Certain inherently unsafe python functions (with regards to external code execution) are banned. The current list is:
> eval, exec, pickles
6. Threads used from python threading module must be joined.
7. Subprocesses must have a termination, wait, or communicate call to prevent zombie processes.




