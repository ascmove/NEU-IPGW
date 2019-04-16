# Documentation

Python脚本实现东北大学网关认证、IP变更邮件提醒、远程上线下线操作，适合部署在实验室内网服务器。

## Configuration

在服务器上检出项目代码，建议检出到/usr/local目录下；重命名配置文件为config.ini，修改文件内基本信息、修改各个脚本内与路径相关信息。

## Usage

* 网关认证

    > python /usr/local/neu/ipgw.py

* 网关下线

    > python /usr/local/neu/ipgw.py disconnect

* IP变动提醒及启动提示

    > python /usr/local/neu/ip.py

## License

[MIT](http://opensource.org/licenses/MIT)

