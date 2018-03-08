# Multipath TCP Application Proxy

This is the Senior Design Project for CS179I at University of Califonia, Riverside.

## Contributers
* Henry Doan - [hdoan002@ucr.edu](mailto:hdoan002@ucr.edu)
* Han Sung Bae - [hbae003@ucr.edu](mailto:hbae003@ucr.edu)
* Michael Tran - [mtran049@ucr.edu](mailto:mtran049@ucr.edu)

## Running the program
1. Open two terminals.
2. Run `python PythonProxy.py` on terminal 1.
3. On terminal 2 run `curl --proxy localhost:8080 http://i.imgur.com/z4d4kWk.jpg`
   Add the `-I` flag to get only the header.
