#!/usr/bin/env bash
set -euo pipefail

compose_file="${COMPOSE_FILE:-compose.yaml}"

default_docker_config="${HOME}/.docker/config.json"
if [[ -f "$default_docker_config" ]] && grep -q '"credsStore"[[:space:]]*:[[:space:]]*"desktop"' "$default_docker_config"; then
  if ! command -v docker-credential-desktop >/dev/null 2>&1; then
    fallback_docker_config_dir="${HOME}/.docker/codex-nocreds"
    mkdir -p "$fallback_docker_config_dir"
    cat >"${fallback_docker_config_dir}/config.json" <<'JSON'
{"auths": {}}
JSON
    export DOCKER_CONFIG="$fallback_docker_config_dir"
    echo "Using fallback DOCKER_CONFIG at ${fallback_docker_config_dir}" >&2
  fi
fi

if docker ps >/dev/null 2>&1; then
  exec docker compose -f "$compose_file" "$@"
fi

current_user="$(id -un)"
in_docker_group_now="false"
in_docker_group_membership="false"

if id -nG | tr " " "\n" | grep -qx "docker"; then
  in_docker_group_now="true"
fi

if getent group docker >/dev/null 2>&1; then
  if getent group docker | awk -F: '{print $4}' | tr "," "\n" | grep -qx "$current_user"; then
    in_docker_group_membership="true"
  fi
fi

if [[ "$in_docker_group_now" == "true" || "$in_docker_group_membership" == "true" ]]; then
  quoted_args="$(printf "%q " "$@")"
  exec sg docker -c "docker compose -f \"$compose_file\" ${quoted_args}"
fi

echo "Docker access denied. Run 'newgrp docker' or re-login, then retry." >&2
exit 1
