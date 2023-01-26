# Zahapa
This python script functions as a haproxy-agent to report the status of the zabbix-server service.
The problem is that zabbix-server does not respond to connections when in standby mode and because of that will often mistakenly be marked as "down".
This behaviour is not necessarily incorrect, but it could cause delays when performing failover and if haproxy is monitored with zabbix it can cause false alerts on the status of the zabbix-server.

# Goals
- Monitor the status of zabbix-server when using the native HA-failover mechanism.

# configuration

## database permissions
Create a user with the correct permissions with the following commmands in mysql
```
create user 'username'@'localhost' identified by 'verysecurepassword';
grant select (name, status) on ha_node to 'username'@'localhost';
```

## systemd init configuration
```
cp /opt/zahapa/scripts/zahapa.service /usr/lib/systemd/system/zahapa.service
chmod 644 /usr/lib/systemd/system/zahapa.service
```


## config file
Default configuration file location: /opt/zahapa/config.yml

Required options:  
db_user:  
db_password:  

optional:
db_name: <'zabbix'>  
db_host: # Default is 'localhost'  
db_port: # Default is 3306  
port: # default is 5555  
bind: # default is 0.0.0.0 (all interfaces)  
zbx_node_name: # default is to get the hostname from environment variables.  

# future
- Add more checks for errors while running
- make variable collection more automatic 
- improve the readme.md file
- extend the agent-checks to other zabbix functions (possibly proxies when they obtain native HA)
- add compatibility for postgresql