#!/bin/bash

# ===============================
#  项目一键管理命令集
#  具体用法参考底部usage()方法
#  该文件保存于项目根目录
#  在配置区域，根据项目实际信息进行配置
#  Date: 2025-04-27 23:03:31
# ===============================

# ==================== 配置区域 ====================
SERVICE_NAME="ssl_manager"  # systemd 服务名称
APP_MODULE="app.main:app"   # FastAPI 应用模块:对象，比如 app/main.py -> app
HOST="0.0.0.0"
PORT="8030"
WORKERS=4
VENV_DIR="venv"             # 虚拟环境目录，相对路径
RELOAD_DIR="app"            # 热重载监听的目录
REQUIREMENTS_FILE="requirements.txt"  # 项目依赖组织文件名，相对路径
CELERY_MODULE="app.tasks.celery_task"  # Celery 应用模块路径，未设置则跳过 Celery 控制
# ==================================================

# 当前脚本所在目录
PROJECT_DIR=$(dirname "$(realpath "$0")")

# 激活虚拟环境
activate_venv() {
    if [[ -d "$PROJECT_DIR/$VENV_DIR" ]]; then
        source "$PROJECT_DIR/$VENV_DIR/bin/activate"
    else
        echo "❌ 虚拟环境不存在，请先创建: python3 -m venv $VENV_DIR"
        exit 1
    fi
}

# 升级pip
sh_upgrade_pip() {
    pip install --upgrade pip
}

# 安装依赖
sh_install_deps() {
    pip install -r "$PROJECT_DIR/$REQUIREMENTS_FILE"
}

# 安装依赖（独立提取）
setup_deps() {
    echo "🔧 正在安装依赖..."
    activate_venv
    sh_upgrade_pip

    # 自动检测并安装 gunicorn 和 uvicorn
    if ! "$PROJECT_DIR/$VENV_DIR/bin/gunicorn" --version &>/dev/null; then
        echo "⚙️  gunicorn 未检测到，正在补充安装..."
        pip install gunicorn
    else
        echo "✅ gunicorn 已安装"
    fi

    if ! "$PROJECT_DIR/$VENV_DIR/bin/uvicorn" --version &>/dev/null; then
        echo "⚙️  uvicorn 未检测到，正在补充安装..."
        pip install uvicorn
    else
        echo "✅ uvicorn 已安装"
    fi

    # 安装项目依赖
    sh_install_deps
}

# 升级依赖
upgrade_deps() {
    activate_venv
    echo "⬆️ 正在升级项目依赖..."
    sh_upgrade_pip
    sh_install_deps
    echo "✅ 依赖升级完成"
}

# 本地开发模式（热重载）
dev_mode() {
    echo "🚀 启动本地开发模式 (Uvicorn 热重载，仅监听 $RELOAD_DIR)..."
    activate_venv
    uvicorn "$APP_MODULE" \
        --host "$HOST" \
        --port "$PORT" \
        --reload \
        --reload-dir "$PROJECT_DIR/$RELOAD_DIR"
}

# 生产环境部署（构建 systemd 服务）
build_prod() {
    setup_deps

    echo "🛠️ 准备创建 systemd 服务: $SERVICE_NAME"

    SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

    # 检查是否为 root 用户
    if [[ $EUID -ne 0 ]]; then
       echo "❌ 请使用 sudo 执行 build 命令"
       exit 1
    fi

    # 如果已有旧版 service，备份
    if [[ -f "$SERVICE_FILE" ]]; then
        echo "⚠️ 检测到已有 $SERVICE_FILE"
        read -p "是否要备份并覆盖？(y/n): " confirm
        if [[ "$confirm" =~ ^[Yy]$ ]]; then
            TIMESTAMP=$(date +"%Y%m%d%H%M%S")
            BACKUP_FILE="/etc/systemd/system/${SERVICE_NAME}.service.bak.${TIMESTAMP}"
            echo "🗂️ 正在备份为 $BACKUP_FILE"
            sudo cp "$SERVICE_FILE" "$BACKUP_FILE"
        else
            echo "❌ 操作已取消"
            exit 1
        fi
    fi

    mkdir -p "$PROJECT_DIR/logs"

    # 写入新的 systemd service 配置
    cat > "$SERVICE_FILE" << EOF
[Unit]
Description=FastAPI App powered by Gunicorn + Uvicorn
After=network.target

[Service]
User=$(whoami)
Group=$(id -gn)
WorkingDirectory=$PROJECT_DIR
ExecStart=$PROJECT_DIR/$VENV_DIR/bin/gunicorn $APP_MODULE \
    --workers $WORKERS \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind $HOST:$PORT \
    --timeout 120 \
    --graceful-timeout 30 \
    --log-level info \
    --access-logfile $PROJECT_DIR/logs/access.log \
    --error-logfile $PROJECT_DIR/logs/error.log
Restart=always
RestartSec=3
Environment="PATH=$PROJECT_DIR/$VENV_DIR/bin"

[Install]
WantedBy=multi-user.target
EOF

    echo "🔄 重新加载 systemd 配置..."
    systemctl daemon-reload

    echo "✅ 启用并启动服务..."
    systemctl enable "$SERVICE_NAME"
    systemctl restart "$SERVICE_NAME"

    echo "🚀 服务已部署并启动！"
    systemctl status "$SERVICE_NAME" --no-pager
}

# 管理 systemd 服务
control_service() {
    local cmd=$1

    case "$cmd" in
        start)
            sudo systemctl start "$SERVICE_NAME"
            ;;
        stop)
            sudo systemctl stop "$SERVICE_NAME"
            ;;
        restart)
            sudo systemctl restart "$SERVICE_NAME"
            ;;
        reload)
            sudo systemctl reload "$SERVICE_NAME"
            ;;
        status)
            sudo systemctl status "$SERVICE_NAME" --no-pager
            ;;
        logs)
            sudo journalctl -u "$SERVICE_NAME" -f
            ;;
        *)
            echo "❌ 无效命令: $cmd"
            usage
            exit 1
            ;;
    esac
}

control_celery_worker() {
    if [[ -z "$CELERY_MODULE" ]]; then
        echo "⚠️ 未配置 CELERY_MODULE，跳过 Celery 操作"
        return
    fi

    local cmd=$1
    local PIDFILE="$PROJECT_DIR/logs/celery_worker.pid"
    case "$cmd" in
        start)
            echo "🐇 启动 Celery Worker..."
            activate_venv
            mkdir -p "$PROJECT_DIR/logs"
            cd "$PROJECT_DIR"
            nohup celery -A "$CELERY_MODULE" worker --loglevel=info --concurrency=2 --hostname=worker@%h -n cert_worker@%h > "$PROJECT_DIR/logs/celery.log" 2>&1 &
            echo $! > "$PIDFILE"
            echo "✅ Celery Worker 已启动 (PID=$(cat $PIDFILE))"
            ;;
        stop)
            if [[ -f "$PIDFILE" ]]; then
                kill -TERM "$(cat $PIDFILE)" && rm -f "$PIDFILE"
                echo "🛑 Celery Worker 已停止"
            else
                echo "⚠️ 未找到 PID 文件，Celery Worker 可能未启动"
            fi
            ;;
        restart)
            $0 celery stop
            sleep 2
            $0 celery start
            ;;
        status)
            if [[ -f "$PIDFILE" ]]; then
                if ps -p "$(cat $PIDFILE)" > /dev/null; then
                    echo "✅ Celery Worker 正在运行 (PID=$(cat $PIDFILE))"
                else
                    echo "⚠️ PID 文件存在但进程未运行"
                fi
            else
                echo "⚠️ 未找到 Celery Worker 的 PID 文件"
            fi
            ;;
        logs)
            tail -f "$PROJECT_DIR/logs/celery.log"
            ;;
        *)
            echo "❌ 无效的 celery 子命令: $cmd"
            echo "用法: $0 celery {start|stop|restart|status|logs}"
            exit 1
            ;;
    esac
}

# 帮助信息
usage() {
    echo "重要：在该文件顶部配置区域，根据项目实际信息进行配置，然后再使用下述命令"
    echo "用法: $0 {setup|test|build|upgrade|start|stop|restart|reload|status|logs|celery}"
    echo "本地开发环境：先使用setup，再使用test"
    echo "线上生产环境：先使用build，再根据需要使用stop/restart/upgrade"
    echo ""
    echo "  setup      安装依赖环境（用于本地开发初始化）"
    echo "  test       本地开发，热重载 (仅监听 app/ 目录)"
    echo "  build      部署生产环境，安装依赖并生成 systemd 服务"
    echo "  upgrade    升级项目依赖 (使用 $REQUIREMENTS_FILE)"
    echo "  start      启动生产环境服务"
    echo "  stop       停止服务"
    echo "  restart    重启服务"
    echo "  reload     软重载服务（不中断连接）"
    echo "  status     查看服务状态"
    echo "  logs       实时查看服务日志"
    echo "  celery     控制 Celery Worker，如: $0 celery start|stop|restart|status|logs"
}

# 主入口

# 检查 .env 文件是否存在
if [[ ! -f "$PROJECT_DIR/.env" ]]; then
    echo "❌ 缺少 .env 文件，请先在项目根目录创建 .env 环境配置文件"
    exit 1
fi

ACTION=$1

if [[ -z "$ACTION" ]]; then
    usage
    exit 1
fi

case "$ACTION" in
    test)
        dev_mode
        ;;
    build)
        build_prod
        ;;
    upgrade)
        upgrade_deps
        ;;
    start|stop|restart|reload|status|logs)
        control_service "$ACTION"
        ;;
    celery)
        shift
        control_celery_worker "$1"
        ;;
    setup)
        setup_deps
        ;;
    *)
        usage
        exit 1
        ;;
esac