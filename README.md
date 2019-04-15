# Winpath ASTM check

This script is designed to check ASTM files in a Winpath interface
to look for mis-formatted messages. 
Recently we have received clinical details with embedded LF characters 
(typed on an Apple Mac and not accounted for in the clients data format).
This causes the Winpath interface to stall and backlog.
This script moves the files to an error folder to prevent them causing a backlog.