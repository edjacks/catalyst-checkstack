This program will ssh through a jumphost to a Cisco catalyst switchstack
and issue the commands necessary to see the actual counters for the
stackwise cabling.   It was written to easily check for stackwise errors
on these switch stacks.

The program sames the output from the command to a file that is named for
the switch and also includes a timestamp.  This will allow for an easy way
to diff the various files for a given switch to look for incrementing error
counts.
