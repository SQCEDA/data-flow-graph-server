# data-flow-graph-server




## 演示版

加个演示版本的server。先只提交快照和节点。同时思考怎么约定和提交报告
fgProject.filenames ->
filenames.json {'filename':[files]}

权限管理先不做

用户和认证放在settings  
项目id、git hash放在config

+ 提交的步骤
前提是git是clean的(靠自觉吧,反正只取git hash,`git rev-parse HEAD`,=`git log --pretty=format:"%H" -1`)
要发送的东西 工程文件一共4个json, record可以考虑把history覆盖成`[]`
每个有快照的节点提供的索引缓存和报告等的机制->文件本体和机制本体, 机制只提取用到的部分
git 的当前状态, hash url branch
用户id

没有合并提交(只有合并拉取)
提交时快照状态总是进行完整覆盖. 以及会制作一个hash map `{'path/to/a.bin':'[hash of a.bin]'}`, 然后a.bin会以`[hash of a.bin]`为文件名存在objs里
在数据库里就是`[git hash]:{time,'hash map',工程文件一共4个json}`

上传一个想要进数据库的状态后, 返回一个去除掉已有文件的列表, 再提交一次状态+文件的post. 这次会真进数据库和写文件. 先写文件, 都成功后最后写数据库

+ 展示的步骤
整体的展示, 提交时间线的hash图
单个hash的展示, 用iframe引入node, 正好继承了用message通信

+ 拉取的步骤
覆盖拉取时全覆盖
合并拉取时把hash塞到父hash数组里, 以被拉取者为优先合并所有有效快照, 约等于全覆盖, 仅仅目标快照不存在, 己方快照存在时保留. 前提是节点图本体完全一致(正常是要先git merge做到这一点后, 在把这套系统merge)

全面使用git hash, somehow 就是一种git release

目标先git checkout xx
在拉取xx就完全完全复原

服务器里维护这些东西, 数据库用mongodb还是sqlite要再想想, 用mongodb省事, sqlite轻量而且不困难
+ 文件夹 objs -> hash命名的数据对象
+ 数据映射 git hash -> file hash map, 工程文件一共4个json, 日期, owner, projectname, commiter (project = "owner/projectname")
+ 数据映射 file hash -> 每次使用这个hash的git hash和文件名

? .. 要怎么处理, 上传下载没问题, 在线显示时不行. 引入一个/parent/的设定, 在flask里替换成..

提交文件的获取:
filenames或者写死在node里

前端: 用iframe引入data-flow-graph-node

### server

server后端: server层 + 数据库包装层

应对上传下载的:

/checkFile [hashes] -> hashes:[hashes] 返回已包含的hashs

/submitFile {hashes:bin64} -> {} 

/downloadFile [hashes] -> {hashes:bin64} null代表不存在

/deleteRelease {git hash, owner, projectname} -> {count} 返回删除的数量

/queryRelease {git hash,owner, projectname} -> [{git hash, hash map, 工程文件一共4个json, 日期, owner, projectname, commiter}]

/submitRelease {git hash, hash map, 工程文件一共4个json, 日期, owner, projectname, commiter} -> {count,files} 覆盖的条目数, 文件缺失

应对前端的:

GET /static/path
GET /owner/projectname/githash/path

/query null -> ["owner/projectname"]

/query owner/projectname -> [git hash]


### 指令

docker run --name mongodb -d -p 27017:27017 -v $(pwd)/data:/data/db mongodb/mongodb-community-server:8.0-ubi8

docker run --name mongodb -d -p 27017:27017 -e MONGO_INITDB_ROOT_USERNAME=user -e MONGO_INITDB_ROOT_PASSWORD=pass mongodb/mongodb-community-server:8.0-ubi8

mongodb://localhost:27017

docker-compose.yaml
```yaml
version: '3'
services:
  myapplication:
    image: mongodb/mongodb-community-server:8.0-ubi8
    environment:
      - CONN_STR=mongodb://user:pass@mongodb
    command: '/bin/bash -c "sleep 5; mongosh $$CONN_STR --eval \"show dbs;\""'
    depends_on:
      - mongodb
  mongodb:
    image: mongodb/mongodb-community-server:8.0-ubi8
    environment:
      - MONGO_INITDB_ROOT_USERNAME=user
      - MONGO_INITDB_ROOT_PASSWORD=pass
    volumes:
      - type: bind
        source: ./data
        target: /data/db
```
