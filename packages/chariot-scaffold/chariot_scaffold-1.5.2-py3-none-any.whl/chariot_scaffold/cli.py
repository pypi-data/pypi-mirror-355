import os
import sys
import argparse
import importlib
from chariot_scaffold.core.plugin import Pack
from chariot_scaffold import version


def main():
    # CLI
    parser = argparse.ArgumentParser(description=f'千乘CLI工具 v{version}', prog="chariot-scaffold")
    parser.add_argument("plugin", help="插件文件 plugin.py", type=str)

    group = parser.add_mutually_exclusive_group()
    group.add_argument("-y", "--yml", help="生成yml文件 plugin.spec.yaml", action="store_true")
    group.add_argument("-g", "--generate", help="生成插件项目文件", action="store_true")
    group.add_argument("-mki", "--mkimg", help="生成离线包, 需要联网", action="store_true")
    group.add_argument("-tb", "--tarball", help="生成在线包", action="store_true")

    general = parser.add_argument_group("test")
    general.add_argument("-c", "--connection", help="运行连接器 [参数1] [参数2] [...]",
                         nargs="*", metavar="params")
    general.add_argument("-r", "--run", help="运行插件动作 [动作名] [参数1] [参数2] [...]",
                         nargs="*", metavar=("action_name", "params"))


    # args
    args = parser.parse_args()
    assert ".py" in args.plugin, ValueError("请检查传入的文件是否是插件文件")


    # path
    path = os.path.split(args.plugin)
    dir_path = os.path.dirname(os.path.abspath(args.plugin))
    file_path = os.path.abspath(args.plugin)
    sys.path.append(dir_path)


    # import
    module = path[-1].replace('.py', '')
    lib = importlib.import_module(module)

    pack: Pack | None = None
    for k, v in lib.__dict__.items():
        if "__" not in k and "Pack" != k:
            try:
                attr = getattr(v, "plugin_config_init")
                if attr:
                    pack = v()
                    break
            except Exception as e:  # noqa
                pass

    assert pack is not None, ImportError("导入插件失败, 请检查插件代码")


    # call
    if args.yml:
        pack.create_yaml(dir_path)

    if args.generate:
        pack.generate_project(dir_path)

    if args.mkimg:
        pack.generate_offline_pack(file_path)

    if args.tarball:
        pack.generate_online_pack(file_path)

    if args.connection:
        if len(args.connection) > 0:
            kwargs = {}
            for i in args.connection:
                params = i.split("=")
                kwargs[params[0]] = params[1]
            pack.connection(**kwargs)

    if args.run:
        if len(args.run) > 0:
            action_name = args.run[0]
            try:
                getattr(pack, action_name)
            except Exception as e:
                print(f"Error: {e}")
                exit(1)

            kwargs = {}
            if args.run[1:]:
                for i in args.run[1:]:
                    params = i.split("=")
                    kwargs[params[0]] = params[1]   # todo int类型转换, json类型转换

                pack.__getattribute__(action_name)(**kwargs)
            else:
                pack.__getattribute__(action_name)()
