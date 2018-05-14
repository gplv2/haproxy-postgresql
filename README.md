# haproxy-postgresql

Use this to determine who's the master server in a postgresql cluster setup

The standby node is in backup mode, so haproxy will not try to write to it unless the master node is down AND the standby node is promoted to a master

you need to setup a trust connection between haproxy and postgresql.  In this example there are 2 pgbouncers in between haproxy and postgresql.  This means you need to install the postgresql nodes at a different port (here 6432)

This is tested in conjunction with repmgrd, pgbouncer, keepalived/haproxy architected setup, but without a witness server.


