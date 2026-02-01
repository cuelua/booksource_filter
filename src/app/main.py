import msvcrt
from file_manager import load_configs
from pipeline import (
    Pipeline,
    PipelineContext,
    LoadStep,
    ClassifyStep,
    UrlCheckStep,
    DedupeStep,
    SaveStep,
)


# 程序入口函数
def run():
    # 1. 加载配置（配置.json）
    config = load_configs()
    # 2. 初始化上下文（保存书源、分类结果等）
    context = PipelineContext()
    # 3. 构建流水线（按顺序执行各步骤）
    pipeline = Pipeline(
        [
            LoadStep(),  # 加载书源
            ClassifyStep(),  # 分类书源
            UrlCheckStep(),  # URL 检测（并发请求）
            DedupeStep(),  # 域名去重
            SaveStep(),  # 保存结果
        ]
    )
    # 4. 执行流水线
    pipeline.run(context, config)
    # 5. 如果未开启自动关闭 → 等待用户按键
    if not config.auto_close:
        print("按任意键继续")
        msvcrt.getch()


# 程序入口点
if __name__ == "__main__":
    run()
