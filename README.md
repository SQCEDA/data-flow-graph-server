# data-flow-graph-server




## 演示版

加个演示版本的server。先只提交快照和节点。同时思考怎么约定和提交报告

python server + mongodb
docker部署

用户和认证放在settings  
项目id、git hash放在config

+ 提交的步骤
前提是git是clean的
要发送的东西 工程文件一共4个json, record可以考虑把history覆盖成`[]`
每个有快照的节点提供的索引缓存和报告等的机制->文件本体和机制本体, 机制只提取用到的部分
git 的当前状态, hash url branch
用户id
父提交hash
用工程文件算一个hash

+ 展示的步骤
整体的展示, 展示类似git节点图的东西
单个hash的展示, 用iframe引入node, 正好继承了用message通信

+ 拉取的步骤
覆盖拉取时全覆盖
合并拉取时把hash塞到父hash数组里, 以被拉取者为优先合并所有有效快照, 约等于全覆盖, 仅仅目标快照不存在, 己方快照存在时保留. 前提是节点图本体完全一致(正常是要先git merge做到这一点后, 在把这套系统merge)

?放弃hash全面使用git hash, 否, 提供用git hash对应快照hash的手段

目标先git checkout xx
在拉取xx就完全完全复原

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
