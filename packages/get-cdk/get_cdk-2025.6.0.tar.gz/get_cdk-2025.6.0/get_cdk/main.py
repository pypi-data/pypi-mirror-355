#!/usr/bin/env python
#  -*- coding: utf-8 -*-

"""
get_cdk负责获取特定版本的cdk软件包
"""

__author__ = "taojiachun"

import argparse
import logging
import os
import pathlib
import site
import subprocess
import textwrap
import venv
from logging.handlers import RotatingFileHandler
from typing import Optional, List
from urllib.parse import urlparse

import git
from shinny_structlog import ShinnyLoggerAdapter, JSONFormatter


def install_from_oss(logger: ShinnyLoggerAdapter, venv_dir: pathlib.Path, prompt: str = None,
                     system_site_packages: bool = False, base_venv_path_list: Optional[List[str]] = None, tag_name: Optional[str] = None, branch: Optional[str] = None,
                     commit: Optional[str] = None) -> pathlib.Path:
    """
    安装cdk
    :param logger: logger
    :param venv_dir: venv的目录
    :param prompt: venv的prompt
    :param system_site_packages: 是否使用系统的site-packages，默认为False。当此选项为True时，windows将以copy形式继承，而linux为symlink形式继承
    :param base_venv_path_list: 继承的venv根目录列表，如果不指定，则不继承
    :param tag_name: cdk版本
    :param branch: cdk分支
    :param commit: cdk提交
    :return: python interpreter path
    """
    if (branch and not commit) or (not branch and commit):
        raise ValueError("--branch 与 --commit 参数需同时填写")

    # 准备pip环境
    python = venv_dir / "bin" / "python"
    pip_prefix = [python, "-m", "pip"]
    shinny_pip_prefix = [python, "-m", "shinny_pip_index"]
    if python.exists():
        logger.info("cdk的venv环境已经存在，跳过创建")
        subprocess.run(pip_prefix + ["uninstall", "-y", "cdk"], check=True)
    else:
        venv.create(venv_dir, with_pip=True, clear=True, system_site_packages=system_site_packages,
                    prompt=prompt, upgrade_deps=True)

        # write pth file
        # 参考：
        #   - https://stackoverflow.com/questions/9809557/use-a-relative-path-in-requirements-txt-to-install-a-tar-gz-file-with-pip
        #   - https://docs.python.org/3/library/site.html
        # 写入pth文件
        if base_venv_path_list:
            assert isinstance(base_venv_path_list, list), "base_venv_path_list应该是一个list"
            # 将base_venv的site-packages目录写入新建的venv中site-packages目录下的pth文件
            venv_site_packages_path = pathlib.Path(site.getsitepackages(prefixes=[str(venv_dir.absolute())])[0])
            with (venv_site_packages_path / "get-cdk.pth").open("w") as f:
                f.writelines("\n".join(site.getsitepackages(prefixes=base_venv_path_list)))
        logger.info(f"cdk的venv环境创建成功: {venv_dir}")

    subprocess.run(pip_prefix + ["install", "--upgrade", "wheel", "setuptools", "packaging", "shinny-pip-index"], check=True)

    if commit:
        commit = commit[:7]
        args = ["install", "--upgrade", f"cdk==0.0.0+{branch}.{commit}"]
    elif tag_name:
        args = ["install", "--upgrade", f"cdk=={tag_name}"]
    else:
        args = ["install", "--upgrade", "cdk"]

    subprocess.run(shinny_pip_prefix + args, check=True)

    # summary
    logger.info("cdk安装成功")
    return python


def main():
    """
    运行入口
    分为两个场景：
    1. 开发机运行： 支持 override venv 路径
    2. 堡垒机运行： 不能指定安装目录
    :return: None
    """
    parser = argparse.ArgumentParser(description='安装cdk')
    parser.add_argument('--cdk-tag', type=str, help='cdk的tag')
    parser.add_argument('--cdk-branch', type=str, help='cdk的分支')
    parser.add_argument('--cdk-commit', type=str, help='cdk的commit')
    parser.add_argument('--service', required=True, help='要部署的服务名称, 跟服务所在的 github project 名称相同')
    args, cdk_args = parser.parse_known_args()

    service_name_info = urlparse(args.service)
    if service_name_info.netloc == "github.com":
        service_name = pathlib.PurePosixPath(service_name_info.path).name
    else:
        service_name = args.service

    if os.getenv("CDK_IS_BASTION", "") == "1":
        # 堡垒机上的cdk安装目录为固定的 /var/lib/ef/bastion/cdk/venv/{service}
        # 此目录应该在堡垒机上提前创建好且位于独立数据盘上
        venv_dir = pathlib.Path("/var/lib/ef/bastion/cdk") / service_name / "venv"

        # 目前堡垒机有以下CDK相关的变量，隔离cdk环境需要通过命令行参数指定这些变量
        # CDK_PACKAGE_DIR： cdk代码中未使用
        # CDK_ENV_DIR： cdk代码中未使用
        # CDK_DIR： cdk相关配置文件目录，下辖多个子目录，默认"/home/ops/.cdk"， 对应--cdk-dir参数
        # CDK_AIRFLOW_DIR： airflow独立服务器上dag目录，默认"~/.cdk/ dags"， 应保留默认值
        # CDK_ANSIBLE_INVENTORY_DIR： airflow独立服务器上ansible inventory目录，默认"~/.cdk/inventory"， 应保留默认值
        # 此处cdk_dir为对应CDK_DIR
        cdk_dir = pathlib.Path("/var/lib/ef/bastion/cdk") / service_name / "config"

        # 堡垒机上需要将日志写入到单独的日志目录
        sh = RotatingFileHandler("/var/log/ef/get-cdk/install.log", maxBytes=1024 * 1024 * 100, backupCount=5)
    else:
        venv_dir = pathlib.Path(os.path.expanduser(os.getenv("CDK_VENV_DIR", f'~/.get_cdk/{service_name}/venv')))
        cdk_dir = pathlib.Path(os.path.expanduser(os.getenv("CDK_DIR", f'~/.get_cdk/{service_name}/config')))
        sh = logging.StreamHandler()

    # 设置logger
    logger = ShinnyLoggerAdapter(logging.getLogger(__name__))
    sh.setLevel(logging.NOTSET)
    sh.setFormatter(JSONFormatter(log_keys=["func_name", "line_no"]))
    logger.logger.addHandler(sh)

    # 创建cdk目录和上级目录，便于venv目录的创建
    cdk_dir.mkdir(parents=True, exist_ok=True)

    python = install_from_oss(
        logger=logger,
        tag_name=args.cdk_tag,
        branch=args.cdk_branch,
        commit=args.cdk_commit,
        venv_dir=venv_dir,
    )

    # 初始化git目录
    try:
        git.Repo(cdk_dir)
        logger.info(f"{cdk_dir}已经是git目录，跳过初始化")
    except git.exc.InvalidGitRepositoryError:
        logger.info(f"{cdk_dir}不是git目录，初始化git")
        repo = git.Repo.init(cdk_dir)
        # write .gitignore
        with open(cdk_dir / ".gitignore", "w") as f:
            f.write(textwrap.dedent("""\
                /ansible_log/
                /artifacts/
                /packages/
                /old_packages/
                __pycache__/
                **/.terraform/providers/
                .terraform.lock.hcl
                """))
        repo.index.add([".gitignore"])
        repo.index.commit("init")
        logger.info("git初始化完成")

    if cdk_args:
        logger.info("执行cdk命令", cdk_args=cdk_args)
        # 执行cdk命令
        os.execv(python, [python, "-m", "cdk.run_cdk",
                          "--service", args.service,
                          "--cdk-dir", str(cdk_dir),
                          ] + cdk_args)
    else:
        logger.info("cdk安装成功", python=python)
        print(f"\n==========\ncdk安装成功，venv目录为{venv_dir}\n==========\n")


if __name__ == '__main__':
    main()
