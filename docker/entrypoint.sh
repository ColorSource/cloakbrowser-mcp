#!/bin/sh
set -eu

# 避免 Docker restart 后 Xvfb 旧锁导致 headed 模式启动失败。
rm -f /tmp/.X99-lock /tmp/.X11-unix/X99

Xvfb :99 -screen 0 1920x1080x24 -nolisten tcp >/tmp/xvfb.log 2>&1 &
sleep 1

exec "$@"
