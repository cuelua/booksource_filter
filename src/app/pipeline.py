import time
from classifier import classify_and_sort_sources
from url_checker import check_urls_parallel, deduplicate_by_domain
from file_manager import base_dir, load_sources, save_sources_grouped


# 上下文：保存整个流程的数据
class PipelineContext:
    def __init__(self):
        self.sources = []  # 原始书源
        self.grouped = {}  # 分类分组结果
        self.valid = []  # 有效书源（有域名）
        self.invalid = []  # 其他书源（无域名）
        self.unreachable = []  # 无效书源（域名无法访问或被排除）
        self.duplicates = []  # 重复书源（同域名）
        self.stats = {}  # 统计信息（可扩展）


# 步骤基类：每个步骤都继承它
class Step:
    name = ""  # 步骤名称
    requires = []  # 执行条件（依赖配置开关）

    def run(self, context, config):
        raise NotImplementedError

    def enabled(self, config) -> bool:
        # 判断配置中是否启用该步骤
        return all(getattr(config, r, True) for r in self.requires)


# 流水线：按顺序执行步骤
class Pipeline:
    def __init__(self, steps: list[Step]):
        self.steps = steps

    def run(self, context, config):
        total_start = time.perf_counter()
        for step in self.steps:
            if not step.enabled(config):
                continue
            print(f"[{step.name}]")
            start = time.perf_counter()
            try:
                message = step.run(context, config)  # 执行步骤
                print(message)
            except Exception as e:
                print(f"[{step.name}] 发生错误: {e}")
                raise
            finally:
                elapsed = time.perf_counter() - start
                print(f"耗时 {elapsed:.2f}s")
        print(f"全部执行完成，总耗时 {time.perf_counter() - total_start:.2f}s")
        return context


# ---- 各个步骤 ----


# 1. 加载书源
class LoadStep(Step):
    name = "加载书源"

    def run(self, context, config):
        context.sources = load_sources()
        return f"共加载书源 {len(context.sources)} 条"


# 2. 分类书源（按类型和标签）
class ClassifyStep(Step):
    name = "书源分类"

    def run(self, context, config):
        grouped, valid, invalid = classify_and_sort_sources(context.sources, config)
        context.grouped, context.valid, context.invalid = grouped, valid, invalid
        return f"可检测书源数量：{len(valid)}，其他书源数量：{len(invalid)}"


# 3. URL 检测（并发请求，过滤无效）
class UrlCheckStep(Step):
    name = "书源检测"
    requires = ["url_check"]  # 依赖配置开关

    def run(self, context, config):
        reachable, unreachable = check_urls_parallel(context.valid, config)
        context.valid, context.unreachable = reachable, unreachable
        return f"书源检测完成，可用：{len(reachable)}，无效：{len(unreachable)}"


# 4. 域名去重（保留最快响应的书源）
class DedupeStep(Step):
    name = "域名去重"
    requires = ["deduplicate_by_domain"]

    def run(self, context, config):
        unique, duplicates = deduplicate_by_domain(context.valid)
        context.valid, context.duplicates = unique, duplicates
        return f"域名去重完成，保留：{len(unique)}，重复：{len(duplicates)}"


# 5. 保存结果（导出到文件夹）
class SaveStep(Step):
    name = "保存结果"

    def run(self, context, config):
        save_sources_grouped(context, config)
        return f"全部处理完成，输出目录：{base_dir() / '导出'}"
