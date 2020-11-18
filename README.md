# IOTA Private
> Author: 大白菜

## 1. Introduction
1. 本手册用于指导如何部署IOTA私链，并说明如何使用IOTA。
2. 本手册根据[官方教程](https://docs.iota.org/docs/compass/0.1/how-to-guides/set-up-a-private-tangle)修改，并对教程中大量没有提及的坑做了补充说明。
3. 本文档后续会提供英文版。
4. 请大家随手给个星，非常感谢。

## 2. The components
1. IRI — IOTA Reference Implementation — software
2. A custom snapshot file — genesis
3. The Coordinator (COO)
4. The scripts in docs/private_tangle

### 2.1 Environment and base tools
1. [CentOS-8.2.2004-x86_64](http://ftp.sjtu.edu.cn/centos/8.2.2004/isos/x86_64/CentOS-8.2.2004-x86_64-dvd1.iso)
2. Docker 18.09.7
3. [bazel-0.29](https://github.com/bazelbuild/bazel/releases/download/0.29.0/bazel-0.29.0-installer-linux-x86_64.sh)

## 3. Install
### 3.1 CentOS8安装
1. 使用pallels安装CentOS8-iso镜像文件，最好为其分配2核(推荐4核)4G内存(注意勾选安装前设定来设置)，40G以上硬盘空间
2. 在setting中打开无线网卡开关
3. 设置root密码
```
sudo passwd root
su - root
```
4. 设置允许root用户通过ssh登录，并配置使用20002端口
- 安装openssh，用于在Mac上远程登录
```
yum install -y openssh-server
```
- 设置端口和允许root登录
```
vim /etc/ssh/sshd_config
# 修改13行
Port 20002
# 修改32行
PermitRootLogin yes
# wq保存退出
```
- 查看与修改当前SElinux允许的ssh端口
```
# 查看
semanage port -l | grep ssh
# 增加
semanage port -a -t ssh_port_t -p tcp 20002
# 如果要修改
semanage port -m -t ssh_port_t -p tcp 20002
```
- 关闭防火墙
```
systemctl stop firewalld
systemctl disable firewalld
```
- 重启sshd服务
```
systemctl restart sshd.service
```
**后续步骤均建议通过远程连接工具(例如SecureCRT)在Mac主机上来完成**
5. 安装依赖包
```
yum -y install telnet wget net-tools vim git curl jq pkg-config zip unzip python3 gcc-c++ patch java-11
```
- 设置python3环境
```
sudo ln -s /usr/bin/python3 /usr/bin/python
```
6. 关闭selinux
```
setenforce 0
sed -i "s/^SELINUX\=enforcing/SELINUX\=disabled/g" /etc/selinux/config
```
7. 安装jq
```
# 安装EPEL源
yum install -y epel-release
# 安装jq
yum install -y jq
```
8. 设置环境变量路径
```
vim /etc/profile
# 修改如下部分(增加/root/bin和/usr/local/sbin)
# Path manipulation
if [ "$EUID" = "0" ]; then
    pathmunge /usr/sbin
    pathmunge /usr/bin
    pathmunge /root/bin
    pathmunge /usr/local/sbin
else
    pathmunge /usr/local/sbin after
    pathmunge /usr/sbin afteri
    pathmunge /usr/bin after
    pathmunge /root/bin after
fi
# 设置生效
source /etc/profile
```

### 3.2 设置使用主机代理
参考《vm&proxy.md》设置。

### 3.3 安装bazel
- 安装bazel-0.29
**坑1：必须使用0.29以上的版本，否则会出现maven_jar构建错误问题**
```
cd /home
# 该步骤下载较慢，也可以使用迅雷下载
wget https://github.com/bazelbuild/bazel/releases/download/0.29.0/bazel-0.29.0-installer-linux-x86_64.sh
chmod +x bazel-0.29.0-installer-linux-x86_64.sh
./bazel-0.29.0-installer-linux-x86_64.sh --user
```
- 测试
```
bazel version
```
- 卸载bazel(如果安装有问题)
```
rm -rf ~/.bazel
rm -rf ~/bin
rm -rf /usr/bin/bazel
rm -rf /usr/local/lib/bazel
```

### 3.3 安装docker
1. 卸载之前安装版本
```
yum remove docker docker-engine docker.io containerd runc
```
2. 安装docker
```
# 境外
curl -fsSL https://get.docker.com | bash -s docker --mirror Aliyun
# 国内
curl -sSL https://get.daocloud.io/docker | sh
```
3. 设置使用国内镜像源加快下载速度
```
mkdir -p /etc/docker/
vim /etc/docker/daemon.json
# 增加如下内容
{
    "registry-mirrors": ["http://hub-mirror.c.163.com"]
}
# 重启docker服务
systemctl restart docker.service
# 设置开机自启动
systemctl enable docker.service
```
4. docker登录(请在dockerhub提前注册)
```
docker login
# 输入用户名密码
```
### 3.4 下载Compass
- git获取项目
```
cd /home
git clone https://github.com/iotaledger/compass.git
```

### 3.5 构建layers_calculator
1. 修改bazel构建文件
```
cd compass
vim WORKSPACE
```
- 将container_pull修改为如下内容
**坑2：必须修改container_pull，原配置会出现pull失败**
```
container_pull(
    name = "java_base",
    registry = "index.docker.io",
    repository = "anjia0532/distroless.java",
    tag = "latest"
)
```

2. 设置git
```
# 设置缓冲区
git config --global http.postBuffer 24288000
```

3. 修改repositories.bzl文件
**坑3：必须修改server_urls，否则会出现连接超时下载失败**
- 此时先执行一遍
```
bazel run //docker:layers_calculator
# 应该会有类似external/io_grpc_grpc_java的Connection refused错误
```
- 修改io_grpc_grpc_java配置
```
# 因为是使用root安装的，这里的home目录为/root
# 这里的7f1c2cd185de4bf31fb382c563058a5e可能是其他一串奇怪的字符
cd /root/.cache/bazel/_bazel_root/7f1c2cd185de4bf31fb382c563058a5e/external/io_grpc_grpc_java
vim repositories.bzl
```
- 输入如下字符进行批量替换server_urls中的值
```
:%s#repo.maven.apache.org#repo1.maven.org#g
# wq保存退出
```

4. 再次执行构建layers_calculator
**注意：本步骤用时较长，而且可能中途会多次失败，注意看提示信息，如果是超时的可以切换代理后再次执行，会从上次失败的步骤继续执行**
```
# 设置使用代理
proxy
# 设置git使用代理
git config --global http.proxy 'socks5://192.168.31.135:1080'
# 取消代理使用如下语句
git config --global --unset http.proxy
# 重新构建
cd /home/compass
bazel run //docker:layers_calculator
```
- 如果出现类似如下报错
```
Caused by: java.nio.file.NoSuchFileException: external/local_jdk
```
**坑4：此处没有链接到jdk11的软连接，会导致构建失败，需要手动创建**
- 设置软连接
```
cd /root/.cache/bazel/_bazel_root/7f1c2cd185de4bf31fb382c563058a5e/external/local_jdk
ln -s /usr/lib/jvm/java-11-openjdk-11.0.9.11-0.el8_2.x86_64/bin bin
ln -s /usr/lib/jvm/java-11-openjdk-11.0.9.11-0.el8_2.x86_64/conf conf
ln -s /usr/lib/jvm/java-11-openjdk-11.0.9.11-0.el8_2.x86_64/legal legal
ln -s /usr/lib/jvm/java-11-openjdk-11.0.9.11-0.el8_2.x86_64/lib lib
ln -s /usr/lib/jvm/java-11-openjdk-11.0.9.11-0.el8_2.x86_64/release release
# 然后重新构建
bazel run //docker:layers_calculator
```

### 3.6 运行calculator
1. Bootstrapping the Coordinator
	* Generate a valid random seed. The seed is going to be used by the COO to generate and sign milestones. Do not lose the generated seed.——特别注意，tangle的seed必须为A-Z的大写字母和数字9。
```
cat /dev/urandom |LC_ALL=C tr -dc 'A-Z9' | fold -w 81 | head -n 1 
# eg：UMJJGDDTCRHQSVIZPVJDKEFVZZTBXJOBTXBADXTMDBIFRFLCVXWPEH9YHRVNNNGRMKQRNRAZBKNHKHPHI
```
2. Copy the config.example.json file to config.json and alter its contents (specifying correct depth & seed).
```
cp /home/compass/docs/private_tangle/config.example.json /home/compass/docs/private_tangle/config.json
vim /home/compass/docs/private_tangle/config.json
# 将seed修改为上面步骤中生成的
"seed": "P9FCPAYGMYYEUIUXTSDBXTCINUXGGWDFJVFWUIKMRJWZCGMLUGKSSIIKBYJCRJHMRWLEGNSQFYBPFNUNF",
```
3. Run the layer calculator via
```
cd /home/compass/docs/private_tangle
# 加载docker镜像
sudo /home/compass/bazel-bin/docker/layers_calculator
/home/compass/docs/private_tangle/01_calculate_layers.sh
# 应该会出现类似如下提示
2020-11-15 13:08:08:152 +0000 [main] INFO org.iota.compass.LayersCalculator - Successfully wrote Merkle Tree with root: 9UZKZZDL9JIOGFZWJEWIQZBKNUJXYGYRYYRCKFBCAQPTFQLUYGPOSY9EJXWQYCKVMCJCPKYPMGC9SHJFZ
```
4. 修改IRI启动脚本，设置重要参数
**坑5：iri脚本需要修改默认参数，否则交易需要费用(需要设置0费用参数)；另外部分API无法使用**
```
vim /home/compass/docs/private_tangle/02_run_iri.sh
# 在--testnet true \下新增如下内容
# 这个是设置可以使用0费用
--testnet-no-coo-validation true \
# 这个是设置远程连接API无限制，确保可以从Mac主机上发送请求
--remote-limit-api "" \
```
- 修改后的启动脚本如下
```
#!/bin/bash
  
scriptdir=$(dirname "$(readlink -f "$0")")
. $scriptdir/lib.sh

load_config

COO_ADDRESS=$(cat $scriptdir/data/layers/layer.0.csv)

docker pull iotaledger/iri:latest
docker run -t --net host --rm -v $scriptdir/db:/iri/data -v $scriptdir/snapshot.txt:/snapshot.txt -p 14265 iotaledger/iri:latest \
       --testnet true \
       --testnet-no-coo-validation true \
       --remote true \
       --remote-limit-api "" \
       --testnet-coordinator $COO_ADDRESS \
       --testnet-coordinator-security-level $security \
       --testnet-coordinator-signature-mode $sigMode \
       --mwm $mwm \
       --milestone-start $milestoneStart \
       --milestone-keys $depth \
       --snapshot /snapshot.txt \
       --max-depth 1000 $@
```

5. Run the IRI
**该步骤耗时较长，会下载IRI镜像文件**
```
cp snapshot.example.txt snapshot.txt
sudo /home/compass/docs/private_tangle/02_run_iri.sh
# 如果要后台运行，请使用如下语句
nohup /home/compass/docs/private_tangle/02_run_iri.sh >iri.log 2>&1 & 
```
- 查看运行日志
```
tail -f -n 100 iri.log
```

6. Shutdown the IRI
```
# 查找所有iri的进程，使用kill -15命令关闭即可
ps -ef|grep iri
kill -15 [pid]
```

### 3.7 运行coordinator
1. 构建coordinator镜像
```
cd /home/compass/
bazel run //docker:coordinator
```
2. 运行docker容器
```
sudo /home/compass/bazel-bin/docker/coordinator
```
3. 运行coordinator
**coordinator运行后，会创建初始里程碑，仅需要运行一次**
```
/home/compass/docs/private_tangle/03_run_coordinator.sh -bootstrap -broadcast
```

## 4. 测试网络与使用
### 4.1 说明
IOTADataOperator.py —— IOTA私链的主要操作
	|-- generateAddress function: 生成一个地址
	|-- sendTransaction function: 发送一笔交易
	|-- findTransactions function: 根据tag查询所有对应交易
iotaParams.py —— 配置Seed和首地址

### 4.1 生成一个可用地址
```
# generate a address
iotaDataOperator = IOTADataOperator()
iotaDataOperator.generateAddress(seed, 0)
```

### 4.2 发送一笔交易
```
# send a trans
iotaDataOperator.sendTransaction("hello world", "TEST")
```

### 4.3 利用tag查询一笔交易
```
# find trans
transMsgs = iotaDataOperator.findTransactions("TEST")
print(transMsgs)
```


