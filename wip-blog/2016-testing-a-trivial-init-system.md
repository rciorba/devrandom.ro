This is the first in a series on using docker with pytest to test
otherwise hard to test things.

Docker, Zombies and PID 1
=========================

So I once wrote an init system for docker containers. Since no program
should be without tests, docker to the rescue.

Testing 
