#!/usr/bin/env bash
# Ожидает доступности указанного хоста и порта

set -e

host="$1"
port="$2"
shift 2
cmd="$@"

until nc -z "$host" "$port"; do
  echo "Ожидание базы данных $host:$port..."
  sleep 1
done

echo "База данных доступна, выполняем команду: $cmd"
exec $cmd
