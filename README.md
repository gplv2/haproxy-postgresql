# haproxy-postgresql

Use this to determine who's the master server in a postgresql cluster setup

The standby node is in backup mode, so haproxy will not try to write to it unless the master node is down AND the standby node is promoted to a master

you need to setup a trust connection between haproxy and postgresql.  In this example there are 2 pgbouncers in between haproxy and postgresql.  This means you need to install the postgresql nodes at a different port (here 6432)

This is tested in conjunction with repmgrd, pgbouncer, keepalived/haproxy architected setup, but without a witness server.

### Screenshot
![alt text][haproxy1]


## Prepare

 - setup a cluster first (atleast the master)
 - use repmgr to create a managed cluster
 - use pgbouncer in front of the DB in production setups, point haproxy to the bouncer but check directly on the pg servers

## generate a config

 - edit config.py, set vars


    HA_MASTER_NAME = "node1"
    HA_MASTER_DSN = "192.168.1.144:5432"
    HA_STANDBY_NAME = "node2"
    HA_STANDBY_DSN = "192.168.1.145:5432"
    HA_VIP_IP = "192.168.1.141"
    HA_CHECK_USER = "pgcheck"
    HA_CHECK_PORT = "6432"
    HA_LISTEN_PORT = "5432"
    HA_STATS_USER = "hapsql"
    HA_STATS_PASSWORD = "snowball1"


 - run it :
    ./create_haproxy_check.py mytest 

## the results

    Creating haproxy project mytest
    Creating configs/mytest/haproxy-mytest.cnf

## check the pg_hba suggestions and implement these for passwordless checks

### pg_hba user check additions (for balancer access to db)

    Add the following lines to pg_hba.conf:
    # special loadbalancer account in trust
    host    template1             pgcheck             192.168.1.141/32        trust
    host    template1             pgcheck             192.168.1.144/32        trust
    host    template1             pgcheck             192.168.1.145/32        trust


### pg_hba repmgr additions

    Add the following lines to pg_hba.conf:
    # repmgr account
    local   replication   repmgr                            trust
    host    replication   repmgr      127.0.0.1/32          trust
    host    replication   repmgr      192.168.1.144/32     trust
    host    replication   repmgr      192.168.1.145/32     trust
    local   repmgr        repmgr                            trust
    host    repmgr        repmgr      127.0.0.1/32          trust
    host    repmgr        repmgr      192.168.1.144/32     trust
    host    repmgr        repmgr      192.168.1.145/32     trust


## suggestions
 - welcome here

##

[haproxy1]: https://github.com/gplv2/haproxy-postgresql/raw/master/screenshots/hastats.png "Stats example of normal DB situation"

