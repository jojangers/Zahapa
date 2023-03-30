# Zahapa
Zahapa is a simple Python web service that returns the status of the Zabbix server in a HA setup to HAProxy so that HAProxy can route traffic to the correct Zabbix server. It periodically queries the HA status from a MySQL database and provides a simple web endpoint to check the current HA status.

# Table of contents

1. [Goals](#goals)
2. [Installation](#installation)
3. [Configuration](#configuration)
  3.1 [HAproxy configuration](#HAproxy-configuration)
  3.2 [Database config](#database-config)
    3.2.1 [MySQL](#mysql)
    3.2.2 [postgreSQL](#postgresql)
  3.3 [Configure Zahapa](#configure-zahapa)
4. [Usage](#usage)
  4.1 [Starting zahapa](#starting-zahapa)
  4.2 [testing endpoint](#test-the-zahapa-endpoint)
5. [License](#license)
6. [Contributing](#contributing)
7. [Future](#future)

# Goals
- Monitor the status of zabbix-server when using the native HA-failover mechanism.
- Make it easy for haproxy to only forward traffic to the currently active zabbix server

# Installation

NOTE: i have not uploaded the package to pip yet, so this is still work in progress.
Zahapa can be installed using pip: 
```shell
pip install zahapa
```

# Configuration

## HAproxy configuration

To configure haproxy to use Zahapa, you will need to use the `agent-check` option in haproxy's server configuration. Here is an example haproxy configuration:

```properties
listen zabbix_server_cluster
    bind *:10051
    balance roundrobin
    mode tcp
    option tcplog
    option tcpka
    server zabbix-01.yourdomain.com zabbix-01.yourdomain.com:10051 agent-check agent-addr 10.13.14.10 agent-port 65530 agent-inter 10s
    server zabbix-02.yourdomain.com zabbix-02.yourdomain.com:10051 backup agent-check agent-addr 10.13.14.11 agent-port 65530 agent-inter 10s
```

## Database config
in order for Zahapa to query the HA status of the zabbix server it needs to have access to the database.

### MySQL
Create a user with the correct permissions on mysql.
replace 'localhost' with the hostname or ip of the host running zahapa.
```sql
create user 'username'@'localhost' identified by 'verysecurepassword';
grant select (name, status) on ha_node to 'username'@'localhost';
```

### PostgreSQL
WIP (postgresql is not supported yet.)

## Configure Zahapa

Zahapa responds to HTTP requests on the root URL with a response corresponding to the current HA status of the Zabbix server. To use Zahapa, you will need to configure the following variables in the `config.yml` file:

```yaml
name of database
db_name: "zabbix"

hostname of the server hosting the database.
db_host: "localhost"

port to use when connecting to database
db_port: "3306"

username for accessing database.
db_user: "zahapa"

password for accessing the database.
db_password: 'verysecurepassword'

port to receive haproxy-agent checks on.
port: 65530

IP address for the agent-check to bind to.
bind: '192.168.0.1'

The zabbix server node name. This is used for looking up the node status in the database.
zbx_node_name: "zabbix.yourdomain.com"

Interval for database monitor to fetch HA status
monitor_interval: 5
```

An example of the config is contained in the repository as `example_config.yml`.

# Usage

## starting zahapa
start zahapa:
```shell
systemctl start zahapa
```

## Test the Zahapa endpoint
The Zahapa endpoint can be tested by sending a GET request to the root URL, e.g. http://zahapa.example.com:65530/. The response will be one of the following values:

ready up: The Zabbix server is ready and can receive connections.
up maint: The Zabbix server is in standby mode and cannot receive connections, but is up.
down: The Zabbix server is not available.
That's it! Zahapa is now set up and ready to use.

# License

Zahapa is released under the MIT License. See `LICENSE` for details.

# Contributing
If you find any issues or would like to contribute, feel free to open an issue or a pull request on the Zahapa GitHub repository.


# future
- Add more checks for errors while running
- make variable collection more automatic 
- improve the readme.md file
- add compatibility for postgresql