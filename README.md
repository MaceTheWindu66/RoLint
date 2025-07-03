# RoLint Compliance Checker And Linter

RoLint is designed to be a robust and strict linter for robotics / embedded systems. It was originally developed for the Humanoid Robot Project at Worcester Polytechnic Institute.
This Linter is designed with MIRSA-C, MIRSA-C++, PEP8, and The Power Of 10 Standards in mind. Below is how to install and use RoLint, as well as an overview of the rules for the linter.

## Installation of RoLint

(NOT CURRENTLY ACCURATE. WILL BE IN FUTURE) RoLint is registtered on PyPi, and you can install it with  

 > **pip install rolint**

This will install the RoLint linter.

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




