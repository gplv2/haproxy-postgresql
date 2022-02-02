#! /usr/bin/env python3
import config
import os, errno
import sys
from io import StringIO
#from pprint import pprint

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

def new_haproxy_conf(props, slavelist):
    project = props["<%= @bn.project %>"]
    new_conf = "%s/%s/haproxy-%s.cnf" % (BASEDIR, project, project)
    print("Creating %s" % new_conf, file=sys.stderr)

    if(slavelist):
        print("Config.py has multiple slave definitions, using -multi template instead : template/%s-multi.template" % sys.argv[1], file=sys.stderr)
        if os.path.isfile("template/%s-multi.template" % sys.argv[1]):
            print("Looking for partial template for slave entries: template/%s-partial.template" % sys.argv[1], file=sys.stderr)
            if os.path.isfile("template/%s-partial.template" % sys.argv[1]):
                #load partial template in variable (expect this to be a one liner)
                with open("template/%s-partial.template" % sys.argv[1], 'r') as templatefile:
                    slavetemplate = templatefile.read().rstrip()

                slaves = StringIO()
                #pprint(locals())
                for name,dsn in slavelist.items():
                    format_dictionary = {'name': name, 'dsn': dsn, 'checkport': props["<%= @bn.checkport %>"] }
                    print("    " + slavetemplate.format(**format_dictionary), file=slaves)

                props["<%= @SLAVELIST %>"] = slaves.getvalue()
                replace("template/%s-multi.template" % sys.argv[1], props, new_conf)
            else:
                print("Partial template does not exist : template/%s-partial.template" % sys.argv[1], file=sys.stderr)
                sys.exit(0)
        else:
            print("Template does not exist : template/%s-multi.template" % sys.argv[1], file=sys.stderr)
            sys.exit(0)
    else:
        if os.path.isfile("template/%s.template" % sys.argv[1]):
            replace("template/%s.template" % sys.argv[1], props, new_conf)
        else:
            print("Template does not exist : template/%s.template" % sys.argv[1], file=sys.stderr)
            sys.exit(0)

def add_hba_checkuser(props,extras):
    print('')
    #print("Add the following lines to pg_hba.conf:", file=sys.stderr)
    print("### master/slaves are only a concept at start, any database node can later have a different role")
    print("### this is just to give some clear pointers to the ones using this")
    print("### special loadbalancer account in trust")
    print("")
    print("## vip / haproxy check user")
    print("host    template1             %s             %s/32        trust" % (props["<%= @bn.checkuser %>"], props["<%= @bn.vipip %>"]))
    print("# master")
    print("host    template1             %s             %s/32        trust" % (props["<%= @bn.checkuser %>"], props["<%= @bn.masterdsn %>"].split(':')[0]))
    print("# slaves")
    if(extras['checkuser'] == "#"):
        print("host    template1             %s             %s/32        trust" % (props["<%= @bn.checkuser %>"], props["<%= @bn.standbydsn %>"].split(':')[0]))

    if(extras):
        print(extras['checkuser'])

def add_hba_repmgr(props,extras):
    #print("Add the following lines to pg_hba.conf:", file=sys.stderr)
    print("### replication user")
    print("local   replication   repmgr                            trust")
    print("host    replication   repmgr      127.0.0.1/32          trust")
    print("# master")
    print("host    replication   repmgr      %s/32     trust" % props["<%= @bn.masterdsn %>"].split(':')[0])
    print("# slaves")
    if(extras['repmgr'] == "#"):
        print("host    replication   repmgr      %s/32     trust" % props["<%= @bn.standbydsn %>"].split(':')[0])

    if(extras):
        print(extras['repl'])
    print('')

    print("### repmgr user")
    print("local   repmgr        repmgr                            trust")
    print("host    repmgr        repmgr      127.0.0.1/32          trust")
    print("# master")
    print("host    repmgr        repmgr      %s/32     trust" % props["<%= @bn.masterdsn %>"].split(':')[0])
    print("# slaves")
    if(extras['repl'] == "#"):
        print("host    repmgr        repmgr      %s/32     trust" % props["<%= @bn.standbydsn %>"].split(':')[0])

    if(extras):
        print(extras['repmgr'])
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

    multiple_slaves = False
    extras = { "repl": "#", "repmgr": "#" , "checkuser": "#" }

    #print("D %s" % d)
    #print("H %s" % hex(d).split('x')[-1])

    # clean up when receiving a cidr block from config (\ escaped or not)
    if vipip.find('/'):
        vipip = vipip.split('/')[0].strip('\\')

    # the props
    props = {
        "<%= @bn.template %>": sys.argv[1],
        "<%= @bn.project %>": sys.argv[2],
        "<%= @bn.mastername %>": mastername,
        "<%= @bn.standbyname %>": standbyname,
        "<%= @bn.masterdsn %>": masterdsn,
        "<%= @bn.masterip %>": masterdsn.split(':')[0],
        "<%= @bn.standbydsn %>": standbydsn,
        "<%= @bn.checkuserhex %>": checkuser.encode("utf-8").hex() + "00",
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

    if standbyname.find(";")!=-1:
        print("Found multiple slave names.", file=sys.stderr)
        names = standbyname.split(";")
        multiple_slaves = True
        for name in names:
            #print(name)
    else:
        print("No multiple standy servers found.", file=sys.stderr)

    if standbydsn.find(";")!=-1:
        print("Found multiple slave dsn.", file=sys.stderr)
        dsns = standbydsn.split(";")
        multiple_slaves = True
        for ip in dsns:
            #print(ip)
    else:
        print("No multiple standy ips found.", file=sys.stderr)

    slavelist = False
    if multiple_slaves == True:
        if len(dsns) != len(names):
            print("dsn and names do not have the same number of entries", file=sys.stderr)
            sys.exit(0)
        slavelist = dict(zip(names,dsns))
        hba_repl = StringIO()
        hba_repmgr = StringIO()
        hba_extra_checkuser = StringIO()

        for dsn in dsns:
            print("host    replication   repmgr      %s/32     trust" % dsn.split(':')[0], file=hba_repl)
            print("host    repmgr        repmgr      %s/32     trust" % dsn.split(':')[0], file=hba_repmgr)
            print("host    template1             %s             %s/32        trust" % (props["<%= @bn.checkuser %>"], dsn.split(':')[0]), file=hba_extra_checkuser)
        #hba_repl.seek(0)
        #hba_repmgr.seek(0)
        #hba_extra_checkuser.seek(0)
        extras['repl'] = hba_repl.getvalue()
        extras['repmgr'] = hba_repmgr.getvalue()
        extras['checkuser'] = hba_extra_checkuser.getvalue()

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

    new_haproxy_conf(props, slavelist)
    add_hba_checkuser(props, extras)
    add_hba_repmgr(props, extras)

    print("Done!", file=sys.stderr)

if __name__ == '__main__':
    main()
