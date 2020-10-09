#! /usr/bin/env python3

import config
import os, errno
import stat
import string
import sys

BASEDIR = "configs"

APPLICATION_PATH = "."

def utf8len(s):
    return len(s.encode('utf-8'))

def help_exit(exit_status):
    if exit_status != 0:
        print("Error: Wrong arguments in call", file=sys.stderr)
    help_msg = """Usage:

    %s <templatename> <project>

    Options:
        templatename    name of a template in the template dir
        project         project name
    """ % sys.argv[0]
    print(help_msg, file=sys.stderr)
    os.system('ls -altr template/*')
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
    print("Creating %s" % new_conf, file=sys.stderr)

    if os.path.isfile("template/%s.template" % sys.argv[1]):
        replace("template/%s.template" % sys.argv[1], props, new_conf)
    else:
        print("Template does not exist : template/%s.template" % sys.argv[1], file=sys.stderr)
        sys.exit(0)

def add_hba_checkuser(props):
    print('')
    #print("Add the following lines to pg_hba.conf:", file=sys.stderr)
    print("# special loadbalancer account in trust")
    print("host    template1             %s             %s/32        trust" % (props["<%= @bn.checkuser %>"], props["<%= @bn.vipip %>"]))
    print("host    template1             %s             %s/32        trust" % (props["<%= @bn.checkuser %>"], props["<%= @bn.masterdsn %>"].split(':')[0]))
    print("host    template1             %s             %s/32        trust" % (props["<%= @bn.checkuser %>"], props["<%= @bn.standbydsn %>"].split(':')[0]))
    print('')

def add_hba_repmgr(props):
    print('')
    #print("Add the following lines to pg_hba.conf:", file=sys.stderr)
    print("# repmgr account")
    print("local   replication   repmgr                            trust")
    print("host    replication   repmgr      127.0.0.1/32          trust")
    print("host    replication   repmgr      %s/32     trust" % props["<%= @bn.masterdsn %>"].split(':')[0])
    print("host    replication   repmgr      %s/32     trust" % props["<%= @bn.standbydsn %>"].split(':')[0])
    
    print("local   repmgr        repmgr                            trust")
    print("host    repmgr        repmgr      127.0.0.1/32          trust")
    print("host    repmgr        repmgr      %s/32     trust" % props["<%= @bn.masterdsn %>"].split(':')[0])
    print("host    repmgr        repmgr      %s/32     trust" % props["<%= @bn.standbydsn %>"].split(':')[0])
    print('')

def main():
    args = len(sys.argv)
    if args == 2:
        if sys.argv[1] == "help":
            help_exit(0)
        else:
            help_exit(1)
    if args != 3:
        help_exit(1)

    mastername = config.HA_MASTER_NAME
    masterdsn = config.HA_MASTER_DSN
    standbyname = config.HA_STANDBY_NAME
    standbydsn = config.HA_STANDBY_DSN
    checkport = config.HA_CHECK_PORT
    checkuser = config.HA_CHECK_USER
    listenport = config.HA_LISTEN_PORT
    statsuser = config.HA_STATS_USER
    statspassword = config.HA_STATS_PASSWORD
    vipip = config.HA_VIP_IP

    d = utf8len(checkuser) + 33 + 1;
    #print("D %s" % d)
    #print("H %s" % hex(d).split('x')[-1])

    # the props
    props = {
        "<%= @bn.template %>": sys.argv[1],
        "<%= @bn.project %>": sys.argv[2],
        "<%= @bn.mastername %>": mastername,
        "<%= @bn.standbyname %>": standbyname,
        "<%= @bn.masterdsn %>": masterdsn,
        "<%= @bn.masterip %>": masterdsn.split(':')[0],
        "<%= @bn.standbydsn %>": standbydsn,
        "<%= @bn.checkport %>": checkport,
        "<%= @bn.stats_user %>": statsuser,
        "<%= @bn.stats_password %>": statspassword,
        "<%= @bn.checkuser %>": checkuser,
        "<%= @bn.listenport %>": listenport,
        "<%= @bn.checkuserlen %>": str(utf8len(checkuser)+1),
        "<%= @bn.totalsize %>": str(d),
        "<%= @bn.vipip %>": vipip,
        "<%= @bn.totalbytes %>": str(hex(d).split('x')[-1]),
        "<%= @bn.path %>": APPLICATION_PATH
    }

    project = props["<%= @bn.project %>"]
    directory = ('%s/%s' % (BASEDIR, project))

    if not os.path.isfile("template/%s.template" % sys.argv[1]):
        print("Template does not exist : %s" % sys.argv[1], file=sys.stderr)
        sys.exit(0)

    try:
        print("Creating haproxy project %s" % (project), file=sys.stderr)
        os.makedirs(directory)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise

    new_haproxy_conf(props)
    add_hba_checkuser(props)
    add_hba_repmgr(props)

    print("Done!", file=sys.stderr)

if __name__ == '__main__':
    main()
