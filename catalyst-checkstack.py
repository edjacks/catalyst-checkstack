#! /usr/bin/env python
"""
This program will ssh through a jumphost to a Cisco catalyst switchstack
and issue the commands necessary to see the actual counters for the
stackwise cabling.   It was written to easily check for stackwise errors
on these switch stacks.

The program sames the output from the command to a file that is named for
the switch and also includes a timestamp.  This will allow for an easy way
to diff the various files for a given switch to look for incrementing error
counts.
"""


import getpass
import pexpect
import sys
import re
import platform
import datetime

prompt = '#'

jumphost = 'somehost.somewhere.com'

def get_credentials():
    print('\nGathering usernames and passwords for network access.')
    i_user = raw_input('Enter username for {} [user]: '.format(jumphost))
    if i_user == '':
        i_user = 'user'

    la_user_temp = 'la-' + i_user

    i_pass = getpass.getpass('Enter password for {}: '.format(jumphost))

    la_user = raw_input('Enter LA username [' + la_user_temp + ']: ')
    if la_user == '':
        la_user = la_user_temp

    la_pass = getpass.getpass('Enter LA password: ')

    return i_user, i_pass, la_user, la_pass



def open_jumphost(iuser, ipass):
    print('\nOpening connection to {}.'.format(jumphost))
    c = pexpect.spawn('ssh ' + iuser + '@' + jumphost, timeout=300)
    # uncomment the next line if you want to debug.. NOTE: passwords will be shown
    c.logfile = sys.stdout
    c.expect('assword')
    c.sendline(ipass)
    c.expect('\$')
    c.sendline('HISTCONTROL=ignoreboth; export HISTCONTROL; set | grep -i histcon')
    c.expect('\$')

    return c



def ping_check(host):
    m = re.match('.*cygwin.*', platform.system(), re.IGNORECASE)
    if m:

        p = pexpect.spawn('ping -n 1 -w 2000 ' + host)
        for line in p.readlines():
            m = re.match('.*Packets.*Sent.*Received = ([0-9]).*', line)
            if m:
                p.close()
                if m.group(1) == '0':
                    return False
                else:
                    return True

        p.close()
        return False

    else:
        print('\n\n')
        print(sys.argv[0] + ' running on unknown system type.  Cannot issue correct PING statement.')
        print('\n\n')

        return False




def login_to_switch(host,c,lu,lp):
    print('\nLogging into switch ' + host)
    c.sendline(' ssh ' + lu + '@' + host)
    c.expect('assword')
    c.sendline(lp)
    c.expect('#')
    c.sendline('term len 0')
    c.expect('#')



def get_prompt(c):
    c.sendline('')
    c.expect('#')
    prompt = c.before.splitlines()[-1] + '#'

    return prompt


def get_switch_members(c):
    print('\nGathering switch stack members')
    prompt = get_prompt(c)
    c.sendline('show switch')
    c.expect(prompt)
    switches = []
    for line in c.before.splitlines():
        m = re.match('.([0-9]) .*(ctive|tandby|ember).*$', line)
        if m:
            switches.append(m.group(1))

    return switches



def save_switch_output(host, c):
    prompt = get_prompt(c)

    hostfile = host + '.output'

    with open(hostfile, 'a') as output:
        output.write('\n\n\n\n')
        output.write('=======================================\n')
        output.flush()

        c.sendline('show clock')
        c.expect(prompt)
        output.write(c.before)
        output.flush()

        c.sendline('show switch')
        c.expect(prompt)
        output.write(c.before)
        output.flush()

        c.sendline('show switch stack-ports')
        c.expect(prompt)
        output.write(c.before)
        output.flush()

        c.sendline('show switch stack-ports summ')
        c.expect(prompt)
        output.write(c.before)
        output.flush()

        switches = get_switch_members(c)

        for switch in switches:
            c.sendline('show platform port-asic 0 read register SifRacRwCrcErrorCnt switch ' + switch)
            c.expect(prompt)
            output.write(c.before)

            now = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
            stackfile = host + '_' + switch + '_' + now
            with open(stackfile, 'w') as stack:
                stack.write(c.before)
                stack.flush()

            output.flush()


    c.sendline('exit')
    c.expect(']\$')




def check_argv(args):
    if len(args) == 2:
        return True
    else:
        print '\n\n----------------------------'
        print args[0] + ' called incorrectly.  Please run ' + args[0]
        print 'with a single argument that is the file with the hostnames\n'
        print 'that you wish to check for stack-port errors\n\n'
        return False



if __name__ == '__main__':
    if not check_argv(sys.argv):
        sys.exit()


    iu, ip, lu, lp = get_credentials()
    c = open_jumphost(iu, ip)

    with open(sys.argv[1], 'r') as file:
        for line in file.readlines():
            if len(line.split()) == 2:
                host = line.split()[1]
                print('trying host: ' + host + '\n')

                if ping_check(host):
                    login_to_switch(host, c, lu, lp)
                    save_switch_output(host, c)

                else:
                    print('\n\nCould not ping ' + host + '\n')



