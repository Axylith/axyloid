#!/usr/bin/env bash
# Action entrypoint. Translates the env vars set by action.yml into
# axyloid CLI invocations.
#
# Required envs:
#   GITHUB_TOKEN, AXYLOID_BOT
# Optional envs depending on bot:
#   AXYLOID_SCOPE, AXYLOID_USERNAME, AXYLOID_OWNER, AXYLOID_REPO,
#   AXYLOID_OUTPUT

set -euo pipefail

if [[ -z "${GITHUB_TOKEN:-}" ]]; then
    echo "error: GITHUB_TOKEN is required" >&2
    exit 1
fi

case "${AXYLOID_BOT}" in
    stats)
        case "${AXYLOID_SCOPE:-repo}" in
            user)
                if [[ -z "${AXYLOID_USERNAME:-}" ]]; then
                    echo "error: stats user scope requires --username (set AXYLOID_USERNAME)" >&2
                    exit 1
                fi
                axyloid stats user \
                    --username "${AXYLOID_USERNAME}" \
                    --output "${AXYLOID_OUTPUT}"
                ;;
            repo)
                axyloid stats repo \
                    --owner "${AXYLOID_OWNER}" \
                    --repo "${AXYLOID_REPO}" \
                    --output "${AXYLOID_OUTPUT}"
                ;;
            *)
                echo "error: unknown scope ${AXYLOID_SCOPE}" >&2
                exit 1
                ;;
        esac
        ;;

    # Future bots dispatch here:
    # axl-diff)  axyloid axl-diff ... ;;
    # validate-roadmap)  axyloid validate-roadmap ... ;;

    *)
        echo "error: unknown bot ${AXYLOID_BOT}" >&2
        echo "supported: stats" >&2
        exit 1
        ;;
esac

echo "axyloid: ${AXYLOID_BOT} completed"