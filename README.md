# haproxy-postgresql

Use this to determine who's the master server in a postgresql cluster setup.  this sends a `select pg_is_in_recovery()` command to the psql servers to see if it is in standby more or not.  haproxy will only mark masters as up.  The standby node is in backup mode, so haproxy will not try to write to it unless the master node is down AND the standby node is promoted to a master

You need to setup a trust connection between haproxy and postgresql.  In this example there are 2 pgbouncers in between haproxy and postgresql.  This means you need to install the postgresql nodes at a different port (here 6432).  Trust connection suggestions will be shown when you run the script.

calculates byte length so the tcp package is well constructed, when changing length of username, you need to adjust.  

This is tested in conjunction with repmgrd, pgbouncer, keepalived/haproxy architected setup, but without a witness server.

The latest version will block all connections when it detects more or less than a single master server.  You do not want to write your data in just any server.  In the case you have 2 disconnected masters servers (meaning 2 servers that aren't standby/slaves) they both will pass this check.  Hence a built-in ACL will prevent writing to any servers, which as a DBA is what you want.  It's better to block this than to accept , also this way you don't show bias towards a node when using the backup directive for example for your second node.  It's not a good idea when a former master comes back after a failure, it will be the primary candidate to write to, but in such cases, your standby server should already be promoted and the old primary should not be written to anymore without resyncing it with the freshly promoted standby. 

### Screenshot
![alt text][haproxy1]


## Prepare

 - setup a cluster first (atleast the master)
 - use repmgr to create a managed cluster
 - use pgbouncer in front of the DB in production setups, point haproxy to the bouncer but check directly on the pg servers

## generate a config

```
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
```

 - edit config.py, set vars

 - run it :
    ./create_haproxy_check.py standby mystandby 

 - alternatively, you can also test the redirect config :
    ./create_haproxy_check.py redirect myredirect 

There are 2 templates now, standby will make haproxy mark slaves as bad candidates.  the redirect template will allow you to filter out a rogue client to redirect it towards the correct master server while letting legitimate connections (monitoring, admin etc) pass based on ip address ACL's

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
    local   replication   repmgr                           trust
    host    replication   repmgr      127.0.0.1/32         trust
    host    replication   repmgr      192.168.1.144/32     trust
    host    replication   repmgr      192.168.1.145/32     trust
    local   repmgr        repmgr                           trust
    host    repmgr        repmgr      127.0.0.1/32         trust
    host    repmgr        repmgr      192.168.1.144/32     trust
    host    repmgr        repmgr      192.168.1.145/32     trust


## suggestions
 - pull requests/ comments welcome here on github

##

[haproxy1]: https://github.com/gplv2/haproxy-postgresql/raw/master/screenshots/hastats.png "Stats example of normal DB situation"

