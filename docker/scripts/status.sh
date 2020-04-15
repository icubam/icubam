#!/bin/bash

set -e

[ -n "${DEBUG}" ] && set -x

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_DIR="$(dirname "${DIR}")"
PROJECT_DIR="$(dirname "${DOCKER_DIR}")"
WRITE_LOGS="${WRITE_LOGS:-1}"
TMPDIR="${TMPDIR:-/tmp}"
LOGS_DIR="${LOGS_DIR:-"${TMPDIR}"}"
LOGS_NUM_LINES="${LOGS_NUM_LINES:-2}"

function print_status() {
  local cid="${1}"
  echo "----------------------------------------"
  docker inspect --format 'ID: {{.ID}}' "${cid}"
  docker inspect --format 'Name: {{.Name}}' "${cid}"
  docker inspect --format 'Image: {{.Config.Image}}' "${cid}"
  docker inspect --format 'Status: {{.State.Status}}' "${cid}"
  echo "Logs:"
  echo "-----"
  docker logs "${cid}" | tail -n "${LOGS_NUM_LINES}"
}

function container_name() {
  local cid="${1}"
  # inspecting returns "/${container_name}", we therefore remove the leading "/":
  docker inspect --format '{{join (split .Name "/") ""}}' "${cid}"
}

function log_to_file() {
  local cid="${1}"
  docker logs "${cid}" > "${LOGS_DIR}/$(container_name "${cid}").log"
}

function detailed_status() {
  local status_code=0
  for cid in $(docker-compose -f "${DOCKER_DIR}/docker-compose-core.yml" -f "${DOCKER_DIR}/docker-compose-proxy.yml" --project-directory "${PROJECT_DIR}" ps -q); do
    if [ "$(docker inspect -f '{{.State.Status}}' "${cid}")" != "running" ]; then
      status_code=1
      print_status "${cid}"
      if [ "${WRITE_LOGS}" == "1" ]; then
        log_to_file "${cid}"
      fi
    fi
  done
  return ${status_code}
}

function status() {
  docker-compose -f "${DOCKER_DIR}/docker-compose-core.yml"  -f "${DOCKER_DIR}/docker-compose-proxy.yml" --project-directory "${PROJECT_DIR}" ps
}

function main() {
  status
  detailed_status
}

main
