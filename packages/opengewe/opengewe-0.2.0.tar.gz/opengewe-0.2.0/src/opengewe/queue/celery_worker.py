#!/usr/bin/env python
"""
Celery worker 启动脚本

用法:
    python -m opengewe.queue.celery_worker
    python -m opengewe.queue.celery_worker --type redis
    python -m opengewe.queue.celery_worker --type rabbitmq
    python -m opengewe.queue.celery_worker --type redis --concurrency 8 --log-level debug
    celery -A opengewe.queue.advanced worker --loglevel=info --queues=opengewe_messages

命令行参数:
    --type {redis,rabbitmq}     选择消息代理类型 (默认: redis)
    --broker BROKER_URL         自定义消息代理URL (优先级高于--type)
    --backend BACKEND_URL       自定义结果存储URL
    --queue QUEUE_NAME          队列名称 (默认: opengewe_messages)
    --concurrency CONCURRENCY   worker并发数 (默认: 4)
    --log-level LOG_LEVEL       日志级别 (默认: info)
    --help                      显示帮助信息

环境变量 (低优先级):
    OPENGEWE_BROKER_URL: Celery broker URL
    OPENGEWE_RESULT_BACKEND: Celery result backend URL
    OPENGEWE_QUEUE_NAME: Celery 队列名称
    OPENGEWE_CONCURRENCY: Celery worker 并发数
    OPENGEWE_LOG_LEVEL: 日志级别

示例:
    # 使用Redis (默认)
    python -m opengewe.queue.celery_worker

    # 使用RabbitMQ
    python -m opengewe.queue.celery_worker --type rabbitmq

    # 自定义配置
    python -m opengewe.queue.celery_worker --type redis --concurrency 8 --log-level debug

    # 完全自定义broker
    python -m opengewe.queue.celery_worker --broker redis://redis.example.com:6379/1
"""

import argparse
import os
import sys
from opengewe.logger import init_default_logger, get_logger

init_default_logger()
# 预设配置常量
BROKER_PRESETS = {
    "redis": "redis://localhost:6379/0",
    "rabbitmq": "amqp://guest:guest@localhost:5672//",
}

BACKEND_PRESETS = {
    "redis": "redis://localhost:6379/0",
    "rabbitmq": "redis://localhost:6379/0",  # RabbitMQ通常使用Redis作为结果存储
}


def create_argument_parser():
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description="OpenGewe Celery Worker 启动脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  %(prog)s                                    # 使用默认Redis配置
  %(prog)s --type rabbitmq                    # 使用RabbitMQ
  %(prog)s --type redis --concurrency 8      # Redis + 8个工作进程
  %(prog)s --broker redis://host:6379/1      # 自定义broker
        """,
    )

    parser.add_argument(
        "--type",
        choices=["redis", "rabbitmq"],
        default="redis",
        help="选择消息代理类型 (默认: redis)",
    )

    parser.add_argument(
        "--broker",
        help="自定义消息代理URL (优先级高于--type预设)",
    )

    parser.add_argument(
        "--backend",
        help="自定义结果存储URL",
    )

    parser.add_argument(
        "--queue",
        default=None,
        help="队列名称 (默认: opengewe_messages)",
    )

    parser.add_argument(
        "--concurrency",
        type=int,
        default=None,
        help="worker并发数 (默认: 4)",
    )

    parser.add_argument(
        "--log-level",
        choices=["debug", "info", "warning", "error", "critical"],
        default=None,
        help="日志级别 (默认: info)",
    )

    return parser


def get_effective_config(args):
    """获取有效配置，按优先级合并命令行参数、环境变量和默认值

    优先级: 命令行参数 > 环境变量 > 预设默认值

    Args:
        args: argparse解析后的参数对象

    Returns:
        dict: 包含所有配置的字典
    """
    config = {}

    # 1. 确定broker URL (命令行 > 环境变量 > 类型预设)
    if args.broker:
        config["broker"] = args.broker
    elif os.environ.get("OPENGEWE_BROKER_URL"):
        config["broker"] = os.environ.get("OPENGEWE_BROKER_URL")
    else:
        config["broker"] = BROKER_PRESETS[args.type]

    # 2. 确定backend URL (命令行 > 环境变量 > 类型预设)
    if args.backend:
        config["backend"] = args.backend
    elif os.environ.get("OPENGEWE_RESULT_BACKEND"):
        config["backend"] = os.environ.get("OPENGEWE_RESULT_BACKEND")
    else:
        config["backend"] = BACKEND_PRESETS[args.type]

    # 3. 确定队列名称 (命令行 > 环境变量 > 默认值)
    config["queue_name"] = (
        args.queue or os.environ.get(
            "OPENGEWE_QUEUE_NAME") or "opengewe_messages"
    )

    # 4. 确定并发数 (命令行 > 环境变量 > 默认值)
    config["concurrency"] = args.concurrency or int(
        os.environ.get("OPENGEWE_CONCURRENCY", "4")
    )

    # 5. 确定日志级别 (命令行 > 环境变量 > 默认值)
    config["log_level"] = (
        args.log_level or os.environ.get("OPENGEWE_LOG_LEVEL") or "info"
    )

    return config


def main():
    """主函数，解析命令行参数并启动Celery worker"""
    logger = get_logger("CeleryWorker")

    parser = create_argument_parser()
    args = parser.parse_args()

    # 构建配置
    config = get_effective_config(args)

    logger.info("正在启动OpenGewe Celery Worker...")
    logger.info(f"消息代理类型: {args.type}")
    logger.info(f"Broker: {config['broker']}")
    logger.info(f"Backend: {config['backend']}")
    logger.info(f"队列名称: {config['queue_name']}")
    logger.info(f"并发数: {config['concurrency']}")
    logger.info(f"日志级别: {config['log_level']}")
    logger.info("-" * 50)

    try:
        # 动态导入celery_app和任务注册函数
        from opengewe.queue.app import create_celery_app
        from opengewe.queue.tasks import register_tasks

        celery_app = create_celery_app(
            broker=config["broker"],
            backend=config["backend"],
            queue_name=config["queue_name"],
        )

        # 注册任务，如果失败会抛出ValueError
        register_tasks(celery_app)

        # 构建启动参数
        argv = [
            "worker",
            f"--loglevel={config['log_level']}",
            f"--concurrency={config['concurrency']}",
            f"--queues={config['queue_name']}",
        ]

        # 启动worker
        logger.info(f"启动Celery worker，参数: {' '.join(argv)}")
        celery_app.worker_main(argv)

    except ValueError as e:
        logger.error(f"Celery任务注册失败: {e}")
        logger.error("Worker启动中止。")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("正在关闭Celery worker...")
    except Exception as e:
        logger.error(f"启动Celery worker时发生未知错误: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
