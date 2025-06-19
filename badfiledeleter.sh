#!/bin/sh
# Palo Alto has deemed these files bad, delete them to avoid it stopping
# container image downloads
find / -type f -name "git-web--browse" -exec rm -vf {} \;
find / -type f -name "pre-receive.sample" -exec rm -vf {} \;
find / -type f -name "t64-arm.exe" -exec rm -vf {} \;
find / -type f -name "t32.exe" -exec rm -vf {} \;
find / -type f -name "t64.exe" -exec rm -vf {} \;
find / -type f -name "w32.exe" -exec rm -vf {} \;
find / -type f -name "w64.exe" -exec rm -vf {} \;
find / -type f -name "w64-arm.exe" -exec rm -vf {} \;
