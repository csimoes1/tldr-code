# Testing Summary

We are trying to test tldr against large open source projects.  A good test size we are currently working with is around 10M-100M total file size.
tldr works fine on larger code bases such as the react project (1G+ in size), but analyzing test cases of this size takes a long time and is not practical for testing purposes.
Below is a list of projects we are considering for testing.  We are looking for projects that are around 10M-100M in size, but we are also considering smaller projects that are well known and have a good number of functions.

To get the size of a repo on local disk: du -s ./* | grep -v '/\.' | awk '{sum+=$1} END {print sum/1024 " MB"}'

## Projects considered:
### Javascript:
- React - too large (1G)
- create-react-app - smaller (36M)

### Typescript:
- vscode - too large (1.2G)

### Java:
- spring-framework - too large (337M)
- junit5 - smaller (766M)
- OpenPDF - smaller (87M)

### Python:
- fastapi (62M)

### C++:
- whisper.cpp (53M)

### C:
- redis (41M)

### C#:
- PowerShell - (154M)

### Swift:
- iine (36M) (tested by ChatGPT(A-) and Claude(B+) - Objective C files are poorly covered, swift files covered well)


## Testing with LLMs
Below are prompts we have fed into Grok, GhatGPT, Gemeni and Claude to test the effectiveness of tldr on these projects.
We have also performed manual inspection of the output files to see how well tldr captures function signatures from these projects.
We have found differing results from the different models, with some models performing better than others.
Currently Claud eis our favorite model for this task, but we are still testing and evaluating the results.

## PROMPTS: 

Please grade me on how well the attached file captures the functions contained in the popular open source project found here:
https://github.com/LibrePDF/OpenPDF
Please grade me just on the capturing of function signatures for this project.

Please grade me on how well the attached file captures the functions contained in the popular open source project found here:
https://github.com/facebook/create-react-app
Please grade me just on the capturing of function signatures for this project.

Please grade me on how well the attached file captures the functions contained in the popular open source project found here:
https://github.com/vitejs/vite
Please grade me just on the capturing of function signatures for this project.

Please grade me on how well the attached file captures the functions contained in the popular open source project found here:
https://github.com/fastapi/fastapi
Please grade me just on the capturing of function signatures for this project.

## Prompts for Claude Code to test on our local file system:
Please grade me on how well the file OpenPDF.tldr.json captures the functions contained in the open source project found in this
  directory.  Please grade me just on the capturing of function signatures from this project.

Please grade me on how well the file create-react-app.tldr captures the functions contained in the open source project found in this
  directory.  Please grade me just on the capturing of function signatures from this project.

Please grade me on how well the file vite.tldr captures the functions contained in the open source project found in this directory.
Please grade me just on the capturing of function signatures from this project.

Please grade me on how well the file fastapi.tldr.json captures the functions contained in the open source project found in this directory.
Please grade me just on the capturing of function signatures from this project.

Please grade me on how well the file whisper.cpp.tldr.json captures the functions contained in the open source project found in this directory.
Please grade me just on the capturing of function signatures from this project.