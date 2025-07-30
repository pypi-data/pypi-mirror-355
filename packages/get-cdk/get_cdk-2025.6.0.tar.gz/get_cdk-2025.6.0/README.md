# get-cdk: CDK环境安装工具

本工具旨在简化CDK环境的安装，提供基于服务的隔离运行环境，支持并行服务部署。

## 安装

### 堡垒机

无需任何操作，get-cdk已经安装在堡垒机上，直接使用即可。

### 本地开发机

使用pip安装get_cdk

```bash
pip install get-cdk
```

## Usage

```shell
$ get-cdk --help
usage: get-cdk [-h] [--cdk-tag CDK_TAG] [--cdk-branch CDK_BRANCH] [--cdk-commit CDK_COMMIT] --service SERVICE args

安装cdk

options:
  -h, --help            show this help message and exit
  --cdk-tag CDK_TAG     cdk的tag
  --cdk-branch CDK_BRANCH
                        cdk的分支
  --cdk-commit CDK_COMMIT
                        cdk的commit
  --service SERVICE     要部署的服务名称, 跟服务所在的 github project 名称相同
  args                  run_cdk的参数
```

## 开发流程说明

### 开发服务

在本地开发机上使用 get-cdk, get-cdk 生成的 venv 放置在 `$CDK_VENV_DIR` 目录下, cdk 运行需要的临时文件放置在 `$CDK_DIR` 目录下。
- 当没有设置 `CDK_VENV_DIR` 环境变量时默认值为 `~/.get_cdk/<service>/venv` 
- 当没有设置 `CDK_DIR` 环境变量时默认值为 `~/.get_cdk/<service>/config`

其中 `<service>` 为服务名

```shell
get-cdk --service=otg-sim
# 不添加 run_cdk 参数时仅创建 venv 并打印其路径
```

> 默认使用最新版的 cdk, 可以通过 `--cdk-branch` 和 `--cdk-commit` 参数指定 cdk 的分支和 commit 创建 venv

venv创建完成后，可以在pycharm中添加 `<venv_path>/bin/python3` 为python解释器，然后在pycharm中开发cdk和服务。

> 如需开发cdk本身可以直接clone cdk后attach到项目中。

在 venv 中可以直接运行 deploy.py 部署服务。

### 本地打包

需将 deploy.py 以及对应的依赖打成 sdist 包, 如使用了 airflow dag 可以和 deploy.py 打到一个 sdist 包中或分开独立打包.

在本地开发机上使用本地的打包结果部署服务:
+ 需设置环境变量 `CDK_LOCAL_DIST` 为 `<service>=<dist_path>;` 其中 `<service>` 为服务名, `<dist_path>` 为本地打包结果的目录
+ 在 venv 中运行 `python3 -m cdk.run_cdk --service=<service> --tag=dummy-local` 部署服务, 其中 `dummy-local` 表示使用本地打包结果

### ci 打包

ci 打包完成后可以在开发机上部署，部署命令如下：

```shell
get-cdk --service=otg-sim --cdk-branch=master --cdk-commit=196c3de --branch=master --commit=4b5d056 --action apply
# 添加 run_cdk 的参数会直接传递给 run_cdk 进行服务部署
```

也可以在堡垒机上执行以上命令部署.
