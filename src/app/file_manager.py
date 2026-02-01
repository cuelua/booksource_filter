import msvcrt
import shutil
import sys
import orjson
import msgspec
from pathlib import Path
from models import BookSource
from configs import AppConfig


# 获取程序运行目录
def base_dir():
    # 如果是打包后的可执行文件，返回其所在目录
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    # 否则返回源码所在目录
    return Path(__file__).resolve().parent


# 加载配置文件（配置.json）
def load_configs():
    file_path = base_dir() / "配置.json"
    config = AppConfig()
    if not file_path.exists():
        # 如果配置文件不存在 → 生成默认配置文件
        file_path.write_bytes(
            orjson.dumps(msgspec.to_builtins(config), option=orjson.OPT_INDENT_2)
        )
        print("配置文件已生成，按任意键继续")
        msvcrt.getch()
    try:
        # 尝试读取配置文件
        config = msgspec.json.decode(file_path.read_bytes(), type=AppConfig)
    except Exception:
        # 如果读取失败 → 回退到默认配置
        file_path.write_bytes(
            orjson.dumps(msgspec.to_builtins(config), option=orjson.OPT_INDENT_2)
        )
        print("配置读取出错，已切回默认配置")
    return config


# 加载书源文件（导入/*.json）
def load_sources():
    sources = []
    input_path = base_dir() / "导入"
    input_path.mkdir(parents=True, exist_ok=True)
    if not any(input_path.glob("*.json")):
        # 如果没有书源文件 → 提示用户添加
        print("请将书源添加至导入中，按任意键继续")
        msvcrt.getch()
    for file_path in Path(input_path).glob("*.json"):
        try:
            # 解码为 BookSource 列表
            data = msgspec.json.decode(file_path.read_bytes(), type=list[BookSource])
            sources.extend(data)
        except (OSError, msgspec.DecodeError) as e:
            print(f"读取 {file_path.name} 失败: {e}")
        except Exception as e:
            print(f"未知错误 {file_path.name}: {e}")
    return sources


# 清空导出目录
def clear_output(config):
    output_path = Path(base_dir() / "导出")
    if config.clear_output and output_path.exists():
        for item in output_path.iterdir():
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)


# 保存书源到导出目录
def save_sources(name, sources, config):
    if not sources:
        return
    output_path = Path(base_dir() / "导出")
    output_path.mkdir(parents=True, exist_ok=True)

    # 内部函数：写入文件
    def dump(file_path, sources):
        try:
            if config.use_format:
                # 格式化输出（带缩进）
                file_path.write_bytes(
                    orjson.dumps(
                        msgspec.to_builtins(sources), option=orjson.OPT_INDENT_2
                    )
                )
            else:
                # 紧凑输出
                file_path.write_bytes(msgspec.json.encode(sources))
        except Exception as e:
            print(f"文件写入失败 {file_path}: {e}")

    total = len(sources)
    items_per_file = 1000  # 每个文件最多保存 1000 条

    # ---- 复杂逻辑：切片保存 ----
    # 如果总数不大 → 保存到单个文件
    if not config.use_slice or total <= items_per_file * 1.5:
        file_path = output_path / f"{name}.json"
        dump(file_path, sources)
        return

    # 如果总数很大 → 按切片保存
    slice_dir = output_path / name
    slice_dir.mkdir(parents=True, exist_ok=True)
    for part, i in enumerate(range(0, total, items_per_file), start=1):
        # 最后一片如果不足一半 → 合并到最后一个文件
        if total - i <= items_per_file * 0.5:
            chunk = sources[i:]
        else:
            chunk = sources[i : i + items_per_file]
        file_path = slice_dir / f"{name}_{part:02d}.json"
        dump(file_path, chunk)
