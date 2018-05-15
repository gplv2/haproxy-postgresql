#! /usr/bin/env python

import config
import os
import stat
import string
import sys

BASEDIR = "configs"

# APPLICATION_PATH = "/srv/bosanova/9.5"
APPLICATION_PATH = "."

def help_exit(exit_status):
    if exit_status is not 0:
        print("Error: Wrong arguments in call")
    help_msg = """Usage:

    %s <project> <master>:<port> <standby>:<port>

    Options:
        project     project name
        masterdsn   host:port where postgresql will be running for initial master
        standbydsn  host:port where postgresql will be running for initial standby
        username    username for tcp-check
        checkport   port to use for check ( eg: 6432 )
    """ % sys.argv[0]
    print(help_msg)
    sys.exit(exit_status)

def replace(source_name, props, output_name):
    output = open(output_name, 'w')
    source = open(source_name, 'r')
    for line in source:
        newline = line
        for prop in props:
            newline = newline.replace(prop, props[prop])
        output.write(newline)
    output.close()
    source.close()

def new_haproxy_conf(props):
    project = props["<%= @bn.project %>"]
    new_conf = "%s/%s/haproxy-%s.cnf" % (BASEDIR, project, project)
    print("Creating %s" % new_conf)
    replace("template/haproxy.template", props, new_conf)

def main():
    args = len(sys.argv)
    if args is 2:
        if sys.argv[1] == "help":
            help_exit(0)
        else:
            help_exit(1)
    if args is not 3:
        help_exit(1)

    mastername = config.BN_MASTER_NAME
    masterdsn = config.BN_MASTER_DSN
    standbyname = config.BN_STANDBY_NAME
    standbydsn = config.BN_STANDBY_DSN
    checkport = config.BN_CHECK_PORT
    checkuser = config.BN_CHECK_USER
    listenport = config.BN_LISTEN_PORT
    statsuser = config.BN_STATS_USER
    statspassword = config.BN_STATS_PASSWORD

    # the props
    props = {
        "<%= @bn.project %>": sys.argv[1],
        "<%= @bn.port %>": sys.argv[2],
        "<%= @bn.mastername %>": mastername,
        "<%= @bn.standbyname %>": standbyname,
        "<%= @bn.masterdsn %>": masterdsn,
        "<%= @bn.standbydsn %>": standbydsn,
        "<%= @bn.checkport %>": checkport,
        "<%= @bn.stats_user %>": statsuser,
        "<%= @bn.stats_password %>": statspassword,
        "<%= @bn.checkuser %>": checkuser,
        "<%= @bn.path %>": APPLICATION_PATH
    }

    project = props["<%= @bn.project %>"]
    os.mkdir('%s/%s' % (BASEDIR, project))
    print("Creating haproxy project %s" % (project))
    new_haproxy_conf(props)

print("Done!")

if __name__ == '__main__':
    main()
