sshm
====
[![Build Status](https://travis-ci.org/rolobio/sshm.png?branch=master)](https://travis-ci.org/rolobio/sshm)

SSH Multiple. SSH into multiple machines and execute a single command.

### Examples
Get a count of processes on each server:

     sshm example1.com,example2.com,example3.com,mail[01-05].example.com,host[01-25].org "ps aux | wc -l"

Check if postfix is running on mail servers:

     sshm mail[01-03].example.com "postfix status"

Verify which servers are accepting SSH connections:

     sshm example[1-5].com "exit"

Copy a file to several servers (may not work for larger files):

     cat some_file | sshm example[1-5].com "cat > some_file"

