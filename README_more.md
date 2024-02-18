# 更多
## 画图工具
1. **启动diffusion服务**
```
python diffusion/server.py --host=127.0.0.1 --port=8080 --external_access_url=http://127.0.0.1:8080
```
2. **画图工具调用**
声明一些环境变量
```
export DIFFUSION_SERVER_URL=http://127.0.0.1:8080
```
## 代码解析器
**安装docker**

## 数学计算器
**依赖代码解析器**

## 知识库 MEMORY
**声明一些环境变量**
```
# CHROMA 和 POSTGRES 两种保存方式
export MEMORY_TYPE=CHROMA
# CHROMA配置存储目录
export CHROMADB_STORAGE_PATH=chromadb
# POSTGRES配置数据库链接 (同时需要启动docker-compose-postgres.yml)
export POSTGRES_CONNECTION_STRING=postgres://postgres:memory2024@localhost:5432/postgres
```