# RoLint Compliance Checker And Linter

<p align="center">
 <img width="300" height="500" alt="Rolint_Logo" src="https://github.com/user-attachments/assets/318bd375-e821-4a63-91ef-9e9a4cf12fde" />
</p>


RoLint is designed to be a robust and strict linter for robotics / embedded systems. It was originally developed for the Humanoid Robot Project at Worcester Polytechnic Institute.
This Linter is designed with MISRA-C, MISRA-C++, PEP8, and The Power Of 10 Standards in mind. Below is how to install and use RoLint, as well as an overview of the rules for the linter.

## UPDATE 0.1.9:  

### Changes to RoLint for the 0.1.9 update:  
> Bug Fixes:  
> > Raised minimum python version to 3.12
> > Fixed rolint: ignore bug where it would ignore the comment instead of the intended line itself.
> > Fixed versioning issue in pyproject.toml, leading to some issues with versioning and causing traceback issues.  
> > Structs no longer have false positive issue with implicit casting.  

> Features:  
> > Flags: Ignores / Overrides are now flagged and appear in stdout.  
> > JSON: Updated JSON output to support flags.  
> > Stdout: Cleaned up STDOUT, made it easy to discern between flags and violations.  

### Roadmap / Future Features:  
> Using Rich formatting for clean output to console
> rolint: extern flag to tell rolint an extern var doesn't need initialization here

## Installation of RoLint

RoLint is registtered on PyPi, and you can install it with  

 > **pip install rolint**

This will install the RoLint linter.
Additionally, you can install by cloning the github for the project at https://github.com/MaceTheWindu66/RoLint

## How to Use RoLint


> rolint check [OPTIONS] [PATH] <-- Runs the linter on file[s] in specified path.  
> rolint set-config [OPTIONS] <-- Changes configuration as specified in options.  
> rolint show-config <-- Shows current configuration.  

For C/C++, RoLint is to be ran on an uncompiled C/C++ file. RoLint is not built to run off of C/C++ binaries, however their text files. RoLint should be used in conjunction with a compiler for most effective results. The rules for common compilers and this linter have overlap, but cover slightly different areas. 

### Options for Check Command

When linting a specific file using the check command, options must be defined. These options define the language and output. 

> #### Options:
> 
> > --lang c | cpp | python  <-- Specifies language    
> > --output | json <-- Changes output format   
> > --output-path -p | [PATH] <-- Overrides output path if output specified.   
>  
> #### Examples:
> >
> > rolint check --output json -p results.json main.c  

## Ignore/Override Features

RoLint comes with an override feature built in for all 3 languages.  
> " rolint: ignore" <-- Ignores the next line  
> " rolint: ignore-block" <-- Ignores a code block

For example, RoLint will ignore a for loop, and all of the code inside of the for loop, if rolint: ignore-block is commented immediately before the loop.  

### C/C++:  
> "// rolint: ignore"  
> "// rolint: ignore-block"  
### Python:  
> "# rolint: ignore"  
> "# rolint: ignore-block"  

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

### C++ Rules
1. Unsafe standard library functions are banned, similar to C. Here is a list of the banned functions for C++:  
> malloc, calloc, realloc, free,
        printf, sprintf, scanf, gets, fgets,
        rand, srand, time, clock, gettimeofday,
        system, fork, exec, exit,
        va_start, va_arg, va_end,
        cin, cout, cerr, delete, new
2. Switch statements cannot have implicit fallthroughs (use break or [[fallthrough]])
3. Switch statements must have default statements
4. No continue statements
5. No uncontrolled jump statements, including goto
6. No function like macros

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




