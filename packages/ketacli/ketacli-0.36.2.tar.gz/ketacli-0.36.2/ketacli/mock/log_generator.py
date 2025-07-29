import time
import random


class LogGenerator:
    """日志生成器类，用于生成不同类型的日志模板
    
    这个类抽象了不同日志类型的生成逻辑，支持多种日志类型，包括：
    - nginx: Nginx访问日志
    - java: Java应用日志
    - linux: Linux系统日志
    - apache: Apache访问日志
    - mysql: MySQL数据库日志
    - windows: Windows事件日志
    - mongodb: MongoDB数据库日志
    
    每种日志类型都支持两种渲染模式：
    - render=True: 使用Jinja2模板引擎渲染，支持动态内容
    - render=False: 使用f-strings直接生成，性能更好
    
    使用示例：
    ```python
    generator = LogGenerator()
    nginx_log = generator.generate_log("nginx", render=True)
    java_log = generator.generate_log("java", render=False)
    ```
    """
    
    def __init__(self):
        """初始化日志生成器"""
        
        # 初始化日志类型映射
        self._log_generators = {
            "nginx": self._generate_nginx_log,
            "java": self._generate_java_log,
            "linux": self._generate_linux_log,
            "apache": self._generate_apache_log,
            "mysql": self._generate_mysql_log,
            "windows": self._generate_windows_log,
            "mongodb": self._generate_mongodb_log,
        }
    
    def get_supported_log_types(self):
        """获取支持的日志类型列表
        
        Returns:
            list: 支持的日志类型列表
        """
        return list(self._log_generators.keys())
    
    def generate_log(self, log_type="nginx", render=False):
        """生成指定类型的日志
        
        Args:
            log_type (str): 日志类型，支持 "nginx", "java", "linux", "apache", "mysql", "windows", "mongodb"
            render (bool): 是否使用Jinja2渲染，True使用模板渲染，False使用f-strings
            
        Returns:
            str: 生成的日志JSON字符串
        
        Raises:
            ValueError: 如果指定的日志类型不支持
        """
        if log_type not in self._log_generators:
            raise ValueError(f"不支持的日志类型: {log_type}，支持的类型: {', '.join(self.get_supported_log_types())}")
        
        # 调用对应的日志生成函数
        return self._log_generators[log_type](render)
    
    def _generate_nginx_log(self, render):
        """生成Nginx访问日志
        
        Args:
            render (bool): 是否使用Jinja2渲染
            
        Returns:
            str: 生成的Nginx日志JSON字符串
        """
        if render:
            data = (
                '{"raw":"{{ random.choice([\"192.168.1.1\", \"192.168.1.2\", \"192.168.1.3\", \"192.168.1.4\", \"192.168.1.5\"]) }} - - '
                '[{{ time.strftime(\"%d/%b/%Y:%H:%M:%S +0000\", time.localtime()) }}] '
                '\\\"{{ random.choice([\"GET\", \"POST\", \"PUT\"]) }} {{ random.choice([\"/\", \"/index.html\", \"/api/v1/users\", \"/login\", \"/static/css/main.css\"]) }} HTTP/1.1\\\" '
                '{{ random.choice([\"200\", \"201\", \"301\", \"302\", \"304\", \"400\", \"404\", \"500\"]) }} '
                '{{ random.randint(100, 10000) }} '
                '\\\"{{ random.choice([\"http://example.com\", \"http://referer.com\", \"-\"]) }}\\\" '
                '\\\"Mozilla/5.0 ({{ random.choice([\"Windows NT 10.0\", \"Macintosh\", \"Linux x86_64\", \"iPhone; CPU iPhone OS 14_0\"]) }}) '
                '{{ random.choice([\"Chrome/90.0.4430.212\", \"Safari/537.36\", \"Firefox/88.0\", \"Edge/91.0.864.48\"]) }}\\\"",' 
                '"host":"{{ random.choice([\"web-server-01\", \"web-server-02\", \"web-server-03\", \"web-server-04\", \"web-server-05\"]) }}"'
                '}'
            )
        else:
            # 使用双引号而不是单引号，确保生成有效的JSON
            data = (
                '{"raw": "' + random.choice(["192.168.1.1", "192.168.1.2", "192.168.1.3", "192.168.1.4", "192.168.1.5"]) + ' - - '
                + '[' + time.strftime("%d/%b/%Y:%H:%M:%S +0000", time.localtime()) + '] "' + random.choice(["GET", "POST", "PUT", "DELETE"]) + ' ' + random.choice(["/", "/index.html", "/api/v1/users", "/login", "/static/css/main.css"]) + ' '
                + 'HTTP/1.1" ' + random.choice(["200", "201", "301", "302", "304", "400", "404", "500"]) + ' ' + str(random.randint(100, 10000))
                + ' "-" "Mozilla/5.0 (' + random.choice(["Windows NT 10.0", "Macintosh", "Linux x86_64", "iPhone; CPU iPhone OS 14_0"]) + ') '
                + random.choice(["Chrome/90.0.4430.212", "Safari/537.36", "Firefox/88.0", "Edge/91.0.864.48"]) + '"", '
                + '"host": "' + random.choice(["web-server-01", "web-server-02", "web-server-03", "web-server-04", "web-server-05"]) + '"}'
            )
        return data
    
    def _generate_java_log(self, render):
        """生成Java应用日志
        
        Args:
            render (bool): 是否使用Jinja2渲染
            
        Returns:
            str: 生成的Java日志JSON字符串
        """
        if render:
            data = (
                '{"raw":"{{ time.strftime(\"%Y-%m-%d %H:%M:%S,%f\"[:-3], time.localtime()) }} '
                '[{{ random.choice([\"main\", \"http-nio-8080-exec-1\", \"pool-1-thread-1\", \"AsyncTask-1\", \"RMI TCP Connection\"]) }}] '
                '{{ random.choice([\"INFO\", \"DEBUG\", \"WARN\", \"ERROR\", \"TRACE\"]) }} '
                '{{ random.choice([\"com.example.Controller\", \"org.springframework.web.servlet.DispatcherServlet\", \"com.example.service.UserService\", \"com.example.repository.UserRepository\", \"org.hibernate.SQL\"]) }} - '
                '{{ faker.sentence() }}",' 
                '"host":"{{ random.choice([\"app-server-01\", \"app-server-02\", \"app-server-03\", \"app-server-04\", \"app-server-05\"]) }}",'
                '"level":"{{ random.choice([\"INFO\", \"DEBUG\", \"WARN\", \"ERROR\", \"TRACE\"]) }}",'
                '"thread":"{{ random.choice([\"main\", \"http-nio-8080-exec-1\", \"pool-1-thread-1\", \"AsyncTask-1\", \"RMI TCP Connection\"]) }}",'
                '"class":"{{ random.choice([\"com.example.Controller\", \"org.springframework.web.servlet.DispatcherServlet\", \"com.example.service.UserService\", \"com.example.repository.UserRepository\", \"org.hibernate.SQL\"]) }}"'
                '}'
            )
            
        else:
            log_levels = ["INFO", "DEBUG", "WARN", "ERROR", "TRACE"]
            threads = ["main", "http-nio-8080-exec-1", "pool-1-thread-1", "AsyncTask-1", "RMI TCP Connection"]
            classes = ["com.example.Controller", "org.springframework.web.servlet.DispatcherServlet", 
                      "com.example.service.UserService", "com.example.repository.UserRepository", "org.hibernate.SQL"]
            hosts = ["app-server-01", "app-server-02", "app-server-03", "app-server-04", "app-server-05"]
            
            level = random.choice(log_levels)
            thread = random.choice(threads)
            class_name = random.choice(classes)
            host = random.choice(hosts)
            message = f"Processing request ID {random.randint(10000, 99999)} for user {random.choice(['user1', 'admin', 'guest', 'customer'])}"
            
            # 使用双引号而不是单引号，确保生成有效的JSON
            data = (
                '{"raw": "' + time.strftime("%Y-%m-%d %H:%M:%S,%f"[:-3], time.localtime()) + ' '
                + '[' + thread + '] ' + level + ' ' + class_name + ' - ' + message + '", '
                + '"host": "' + host + '", '
                + '"level": "' + level + '", '
                + '"thread": "' + thread + '", '
                + '"class": "' + class_name + '"}'
            )
        return data
    
    def _generate_linux_log(self, render):
        """生成Linux系统日志
        
        Args:
            render (bool): 是否使用Jinja2渲染
            
        Returns:
            str: 生成的Linux日志JSON字符串
        """
        if render:
            data = (
                '{"raw":"{{ time.strftime(\"%b %d %H:%M:%S\", time.localtime()) }} '
                '{{ random.choice([\"localhost\", \"server1\", \"server2\", \"server3\", \"server4\"]) }} '
                '{{ random.choice([\"sshd\", \"systemd\", \"kernel\", \"cron\", \"nginx\", \"apache2\", \"mysql\"]) }}'
                '[{{ random.randint(1000, 9999) }}]: '
                '{{ faker.sentence() }}",' 
                '"host":"{{ random.choice([\"localhost\", \"server1\", \"server2\", \"server3\", \"server4\"]) }}",'
                '"program":"{{ random.choice([\"sshd\", \"systemd\", \"kernel\", \"cron\", \"nginx\", \"apache2\", \"mysql\"]) }}",'
                '"pid":{{ random.randint(1000, 9999) }}'
                '}'
            )
            
        else:
            hosts = ["localhost", "server1", "server2", "server3", "server4"]
            programs = ["sshd", "systemd", "kernel", "cron", "nginx", "apache2", "mysql"]
            
            host = random.choice(hosts)
            program = random.choice(programs)
            pid = random.randint(1000, 9999)
            messages = [
                f"User {random.choice(['root', 'admin', 'user1', 'guest'])} logged in from {random.choice(['192.168.1.1', '10.0.0.1', '172.16.0.1'])}",
                f"Started {random.choice(['Service', 'Process', 'Task'])} {random.randint(100, 999)}",
                f"Connection from {random.choice(['192.168.1.1', '10.0.0.1', '172.16.0.1'])} port {random.randint(1000, 65535)}",
                f"Failed password for {random.choice(['root', 'admin', 'user1', 'guest'])} from {random.choice(['192.168.1.1', '10.0.0.1', '172.16.0.1'])}",
                f"Out of memory: Kill process {random.randint(1000, 9999)}"
            ]
            message = random.choice(messages)
            
            # 使用双引号而不是单引号，确保生成有效的JSON
            data = (
                '{"raw": "' + time.strftime("%b %d %H:%M:%S", time.localtime()) + ' '
                + host + ' ' + program + '[' + str(pid) + ']: ' + message + '", '
                + '"host": "' + host + '", '
                + '"program": "' + program + '", '
                + '"pid": ' + str(pid) + '}'
            )
        return data
    
    def _generate_apache_log(self, render):
        """生成Apache访问日志
        
        Args:
            render (bool): 是否使用Jinja2渲染
            
        Returns:
            str: 生成的Apache日志JSON字符串
        """
        if render:
            data = (
                '{"raw":"{{ random.choice([\"192.168.1.1\", \"192.168.1.2\", \"192.168.1.3\", \"192.168.1.4\", \"192.168.1.5\"]) }} - {{ random.choice([\"user1\", \"admin\", \"-\"]) }} '
                '[{{ time.strftime(\"%d/%b/%Y:%H:%M:%S %z\", time.localtime()) }}] '
                '\\\"{{ random.choice([\"GET\", \"POST\", \"PUT\", \"DELETE\"]) }} {{ random.choice([\"/\", \"/index.php\", \"/wp-admin\", \"/images/logo.png\", \"/api/data\"]) }} HTTP/{{ random.choice([\"1.0\", \"1.1\", \"2.0\"]) }}\\\" '
                '{{ random.choice([\"200\", \"201\", \"301\", \"302\", \"304\", \"400\", \"403\", \"404\", \"500\", \"503\"]) }} '
                '{{ random.randint(100, 50000) }} '
                '\\\"{{ random.choice([\"http://example.com/page\", \"http://google.com/search?q=example\", \"https://www.bing.com/search?q=example\", \"-\"]) }}\\\" '
                '\\\"{{ random.choice([\"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36\", \"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15\", \"Mozilla/5.0 (X11; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0\"]) }}\\\"",' 
                '"host":"{{ random.choice([\"apache-server-01\", \"apache-server-02\", \"apache-server-03\", \"apache-server-04\", \"apache-server-05\"]) }}",'
                '"method":"{{ random.choice([\"GET\", \"POST\", \"PUT\", \"DELETE\"]) }}",'
                '"status":{{ random.choice([\"200\", \"201\", \"301\", \"302\", \"304\", \"400\", \"403\", \"404\", \"500\", \"503\"]) }},'
                '"bytes":{{ random.randint(100, 50000) }},'
                '"referer":"{{ random.choice([\"http://example.com/page\", \"http://google.com/search?q=example\", \"https://www.bing.com/search?q=example\", \"-\"]) }}"'
                '}'
            )
            
        else:
            ips = ["192.168.1.1", "192.168.1.2", "192.168.1.3", "192.168.1.4", "192.168.1.5"]
            users = ["user1", "admin", "-"]
            methods = ["GET", "POST", "PUT", "DELETE"]
            paths = ["/", "/index.php", "/wp-admin", "/images/logo.png", "/api/data"]
            http_versions = ["1.0", "1.1", "2.0"]
            statuses = ["200", "201", "301", "302", "304", "400", "403", "404", "500", "503"]
            referers = ["http://example.com/page", "http://google.com/search?q=example", "https://www.bing.com/search?q=example", "-"]
            user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
                "Mozilla/5.0 (X11; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0"
            ]
            hosts = ["apache-server-01", "apache-server-02", "apache-server-03", "apache-server-04", "apache-server-05"]
            
            ip = random.choice(ips)
            user = random.choice(users)
            method = random.choice(methods)
            path = random.choice(paths)
            http_version = random.choice(http_versions)
            status = random.choice(statuses)
            bytes_sent = random.randint(100, 50000)
            referer = random.choice(referers)
            user_agent = random.choice(user_agents)
            host = random.choice(hosts)
            
            # 使用双引号而不是单引号，确保生成有效的JSON
            data = (
                '{"raw": "' + ip + ' - ' + user + ' '
                + '[' + time.strftime("%d/%b/%Y:%H:%M:%S %z", time.localtime()) + '] "' + method + ' ' + path + ' HTTP/' + http_version + '" '
                + status + ' ' + str(bytes_sent) + ' "' + referer + '" "' + user_agent + '"", '
                + '"host": "' + host + '", '
                + '"method": "' + method + '", '
                + '"status": ' + status + ', '
                + '"bytes": ' + str(bytes_sent) + ', '
                + '"referer": "' + referer + '"}'
            )
        return data
    
    def _generate_mysql_log(self, render):
        """生成MySQL数据库日志
        
        Args:
            render (bool): 是否使用Jinja2渲染
            
        Returns:
            str: 生成的MySQL日志JSON字符串
        """
        if render:
            data = (
                '{"raw":"{{ time.strftime(\"%Y-%m-%d %H:%M:%S\", time.localtime()) }} '
                '{{ random.randint(1, 999999) }} '
                '[{{ random.choice([\"Note\", \"Warning\", \"Error\", \"System\"]) }}] '
                '{{ random.choice([\"[Server] Shutdown complete\", \"[InnoDB] Database was not shut down normally!\", \"[Server] /usr/sbin/mysqld: ready for connections.\", \"[Warning] IP address could not be resolved\", \"[Note] Event Scheduler: Loaded 0 events\", \"[System] [MY-010931] [Server] /usr/sbin/mysqld: ready for connections.\", \"[Warning] Aborted connection\", \"[Note] [MY-010311] [Server] Server initialized for online backups\", \"[ERROR] [MY-013183] [InnoDB] Assertion failure\", \"[Note] [MY-010051] [Server] Event Scheduler: scheduler thread started with id\"]) }}",' 
                '"host":"{{ random.choice([\"mysql-server-01\", \"mysql-server-02\", \"mysql-server-03\", \"mysql-server-04\", \"mysql-server-05\"]) }}",'
                '"thread_id":{{ random.randint(1, 999999) }},'
                '"level":"{{ random.choice([\"Note\", \"Warning\", \"Error\", \"System\"]) }}",'
                '"component":"{{ random.choice([\"Server\", \"InnoDB\", \"Connection\", \"System\", \"Warning\"]) }}"'
                '}'
            )
            
        else:
            thread_ids = [random.randint(1, 999999) for _ in range(5)]
            levels = ["Note", "Warning", "Error", "System"]
            components = ["Server", "InnoDB", "Connection", "System", "Warning"]
            messages = [
                "[Server] Shutdown complete",
                "[InnoDB] Database was not shut down normally!",
                "[Server] /usr/sbin/mysqld: ready for connections.",
                "[Warning] IP address could not be resolved",
                "[Note] Event Scheduler: Loaded 0 events",
                "[System] [MY-010931] [Server] /usr/sbin/mysqld: ready for connections.",
                "[Warning] Aborted connection",
                "[Note] [MY-010311] [Server] Server initialized for online backups",
                "[ERROR] [MY-013183] [InnoDB] Assertion failure",
                "[Note] [MY-010051] [Server] Event Scheduler: scheduler thread started with id"
            ]
            hosts = ["mysql-server-01", "mysql-server-02", "mysql-server-03", "mysql-server-04", "mysql-server-05"]
            
            thread_id = random.choice(thread_ids)
            level = random.choice(levels)
            message = random.choice(messages)
            host = random.choice(hosts)
            component = random.choice(components)
            
            # 使用双引号而不是单引号，确保生成有效的JSON
            data = (
                '{"raw": "' + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + ' '
                + str(thread_id) + ' [' + level + '] ' + message + '", '
                + '"host": "' + host + '", '
                + '"thread_id": ' + str(thread_id) + ', '
                + '"level": "' + level + '", '
                + '"component": "' + component + '"}'
            )
        return data
    
    def _generate_windows_log(self, render):
        """生成Windows事件日志
        
        Args:
            render (bool): 是否使用Jinja2渲染
            
        Returns:
            str: 生成的Windows事件日志JSON字符串
        """
        if render:
            data = (
                '{"raw":"{{ time.strftime(\"%Y-%m-%d %H:%M:%S\", time.localtime()) }} '
                '{{ random.choice([\"Information\", \"Warning\", \"Error\", \"Critical\", \"Verbose\"]) }} '
                '{{ random.choice([\"System\", \"Application\", \"Security\", \"Setup\", \"Windows PowerShell\"]) }} '
                '{{ random.choice([\"Service Control Manager\", \"Microsoft-Windows-Security-Auditing\", \"Microsoft-Windows-Kernel-General\", \"Microsoft-Windows-Winlogon\", \"Microsoft-Windows-GroupPolicy\"]) }} '
                '{{ random.randint(1000, 9999) }} '
                '{{ random.choice([\"The service entered the running state.\", \"Windows is shutting down.\", \"A user logged on to this computer.\", \"The Group Policy settings for the computer were processed successfully.\", \"The Windows Firewall service entered the running state.\", \"The Windows Update service failed to start.\", \"The system has resumed from sleep.\", \"A service was installed in the system.\", \"The system time has changed.\", \"The Windows Firewall has detected an unauthorized application attempting to access the network.\"]) }}",' 
                '"host":"{{ random.choice([\"win-server-01\", \"win-server-02\", \"win-server-03\", \"win-server-04\", \"win-server-05\"]) }}",'
                '"level":"{{ random.choice([\"Information\", \"Warning\", \"Error\", \"Critical\", \"Verbose\"]) }}",'
                '"log":"{{ random.choice([\"System\", \"Application\", \"Security\", \"Setup\", \"Windows PowerShell\"]) }}",'
                '"source":"{{ random.choice([\"Service Control Manager\", \"Microsoft-Windows-Security-Auditing\", \"Microsoft-Windows-Kernel-General\", \"Microsoft-Windows-Winlogon\", \"Microsoft-Windows-GroupPolicy\"]) }}",'
                '"event_id":{{ random.randint(1000, 9999) }}'
                '}'
            )
            
        else:
            levels = ["Information", "Warning", "Error", "Critical", "Verbose"]
            logs = ["System", "Application", "Security", "Setup", "Windows PowerShell"]
            sources = ["Service Control Manager", "Microsoft-Windows-Security-Auditing", "Microsoft-Windows-Kernel-General", 
                      "Microsoft-Windows-Winlogon", "Microsoft-Windows-GroupPolicy"]
            event_ids = [random.randint(1000, 9999) for _ in range(5)]
            messages = [
                "The service entered the running state.",
                "Windows is shutting down.",
                "A user logged on to this computer.",
                "The Group Policy settings for the computer were processed successfully.",
                "The Windows Firewall service entered the running state.",
                "The Windows Update service failed to start.",
                "The system has resumed from sleep.",
                "A service was installed in the system.",
                "The system time has changed.",
                "The Windows Firewall has detected an unauthorized application attempting to access the network."
            ]
            hosts = ["win-server-01", "win-server-02", "win-server-03", "win-server-04", "win-server-05"]
            
            level = random.choice(levels)
            log = random.choice(logs)
            source = random.choice(sources)
            event_id = random.choice(event_ids)
            message = random.choice(messages)
            host = random.choice(hosts)
            
            # 使用双引号而不是单引号，确保生成有效的JSON
            data = (
                '{"raw": "' + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + ' '
                + level + ' ' + log + ' ' + source + ' ' + str(event_id) + ' ' + message + '", '
                + '"host": "' + host + '", '
                + '"level": "' + level + '", '
                + '"log": "' + log + '", '
                + '"source": "' + source + '", '
                + '"event_id": ' + str(event_id) + '}'
            )
        return data
    
    def _generate_mongodb_log(self, render):
        """生成MongoDB数据库日志
        
        Args:
            render (bool): 是否使用Jinja2渲染
            
        Returns:
            str: 生成的MongoDB日志JSON字符串
        """
        if render:
            data = (
                '{"raw":"{{ time.strftime(\"%Y-%m-%dT%H:%M:%S.%f\"[:-3], time.localtime()) }}+00:00 '
                '{{ random.choice([\"I\", \"W\", \"E\", \"F\", \"D\"]) }} '
                '{{ random.choice([\"NETWORK\", \"COMMAND\", \"STORAGE\", \"QUERY\", \"CONTROL\", \"SHARDING\", \"REPL\"]) }} '
                '[{{ random.choice([\"conn123\", \"conn456\", \"conn789\", \"conn101112\", \"conn131415\"]) }}] '
                '{{ random.choice([\"connection accepted from 127.0.0.1:63712 #1\", \"received client metadata from 127.0.0.1:63712 conn1: { driver: { name: \\\"nodejs\\\", version: \\\"4.0.0\\\" }, os: { type: \\\"Linux\\\", name: \\\"linux\\\", architecture: \\\"x64\\\", version: \\\"5.4.0-42-generic\\\" }, platform: \\\"Node.js v14.15.1, LE\\\" }\", \"Interrupted operation as its client disconnected\", \"Index build: done building index on ns admin.system.version properties: { v: 2, key: { version: 1 }, name: \\\"version_1\\\", ns: \\\"admin.system.version\\\" } using method: Hybrid\", \"Shutting down the WiredTiger storage engine\", \"Replica set config is invalid or does not include us\", \"Applied op: command { createIndexes: \\\"users\\\", v: 2, key: { email: 1 }, name: \\\"email_1\\\", background: true, ns: \\\"myapp.users\\\" }\", \"Slow query: { find: \\\"users\\\", filter: { status: \\\"active\\\" }, sort: { createdAt: -1 }, limit: 100, $db: \\\"myapp\\\" } keysExamined:0 docsExamined:10000 hasSortStage:1 cursorExhausted:1 numYields:78 nreturned:100 queryHash:D03C6C92 planCacheKey:D03C6C92 reslen:16408 locks:{ Global: { acquireCount: { r: 158 } }, Database: { acquireCount: { r: 79 } }, Collection: { acquireCount: { r: 79 } } } storage:{ data: { bytesRead: 339968, timeReadingMicros: 1513 } } protocol:op_msg 200ms\"]) }}",' 
                '"host":"{{ random.choice([\"mongodb-server-01\", \"mongodb-server-02\", \"mongodb-server-03\", \"mongodb-server-04\", \"mongodb-server-05\"]) }}",'
                '"severity":"{{ random.choice([\"I\", \"W\", \"E\", \"F\", \"D\"]) }}",'
                '"component":"{{ random.choice([\"NETWORK\", \"COMMAND\", \"STORAGE\", \"QUERY\", \"CONTROL\", \"SHARDING\", \"REPL\"]) }}",'
                '"context":"{{ random.choice([\"conn123\", \"conn456\", \"conn789\", \"conn101112\", \"conn131415\"]) }}"'
                '}'
            )
            
        else:
            severities = ["I", "W", "E", "F", "D"]  # Info, Warning, Error, Fatal, Debug
            components = ["NETWORK", "COMMAND", "STORAGE", "QUERY", "CONTROL", "SHARDING", "REPL"]
            contexts = ["conn123", "conn456", "conn789", "conn101112", "conn131415"]
            messages = [
                "connection accepted from 127.0.0.1:63712 #1",
                "received client metadata from 127.0.0.1:63712 conn1: { driver: { name: \"nodejs\", version: \"4.0.0\" }, os: { type: \"Linux\", name: \"linux\", architecture: \"x64\", version: \"5.4.0-42-generic\" }, platform: \"Node.js v14.15.1, LE\" }",
                "Interrupted operation as its client disconnected",
                "Index build: done building index on ns admin.system.version properties: { v: 2, key: { version: 1 }, name: \"version_1\", ns: \"admin.system.version\" } using method: Hybrid",
                "Shutting down the WiredTiger storage engine",
                "Replica set config is invalid or does not include us",
                "Applied op: command { createIndexes: \"users\", v: 2, key: { email: 1 }, name: \"email_1\", background: true, ns: \"myapp.users\" }",
                "Slow query: { find: \"users\", filter: { status: \"active\" }, sort: { createdAt: -1 }, limit: 100, $db: \"myapp\" } keysExamined:0 docsExamined:10000 hasSortStage:1 cursorExhausted:1 numYields:78 nreturned:100 queryHash:D03C6C92 planCacheKey:D03C6C92 reslen:16408 locks:{ Global: { acquireCount: { r: 158 } }, Database: { acquireCount: { r: 79 } }, Collection: { acquireCount: { r: 79 } } } storage:{ data: { bytesRead: 339968, timeReadingMicros: 1513 } } protocol:op_msg 200ms"
            ]
            hosts = ["mongodb-server-01", "mongodb-server-02", "mongodb-server-03", "mongodb-server-04", "mongodb-server-05"]
            
            severity = random.choice(severities)
            component = random.choice(components)
            context = random.choice(contexts)
            message = random.choice(messages)
            host = random.choice(hosts)
            
            # 使用双引号而不是单引号，确保生成有效的JSON
            data = (
                '{"raw": "' + time.strftime("%Y-%m-%dT%H:%M:%S.%f"[:-3], time.localtime()) + '+00:00 '
                + severity + ' ' + component + ' [' + context + '] ' + message + '", '
                + '"host": "' + host + '", '
                + '"severity": "' + severity + '", '
                + '"component": "' + component + '", '
                + '"context": "' + context + '"}'
            )
        return data