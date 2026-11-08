#!/bin/sh
# Bootstrap an existing CPython >=3.10 without requiring python on PATH.
# No installs and no shell-evaluation of discovered paths.
case "$0" in */*) stca_parent=${0%/*} ;; *) stca_parent=. ;; esac
stca_dir=$(CDPATH= cd -P "$stca_parent" && pwd) || exit 2
stca_script="$stca_dir/agent_runtime.py"
stca_explicit=${STCA_BOOTSTRAP_PY:-}
while [ "$#" -gt 0 ]; do
    case "$1" in
        --script) [ "$#" -ge 2 ] || exit 2; stca_script=$2; shift 2 ;;
        --bootstrap-python) [ "$#" -ge 2 ] || exit 2; stca_explicit=$2; shift 2 ;;
        --) shift; break ;;
        *) break ;;
    esac
done
# Preserve global --python for agent_runtime and use the same strict boot choice.
stca_previous=
for stca_argument in "$@"; do
    if [ "$stca_previous" = --python ]; then stca_explicit=$stca_argument; break; fi
    case "$stca_argument" in
        --python=*) stca_explicit=${stca_argument#--python=}; break ;;
        ensure|discover|run|prepare|status) break ;;
    esac
    stca_previous=$stca_argument
done
stca_attempts=0
stca_try() {
    stca_attempts=$((stca_attempts + 1))
    [ "$stca_attempts" -le 96 ] || return 1
    [ -n "$1" ] || return 1
    "$1" -c 'import platform,sys;sys.exit(0 if platform.python_implementation()=="CPython" and sys.version_info[:2]>=(3,10) else 1)' >/dev/null 2>&1 || return 1
    stca_selected=$1
    return 0
}
if [ -n "$stca_explicit" ]; then
    if ! stca_try "$stca_explicit"; then
        echo 'STCA: the explicitly selected Python is unavailable or below Python 3.10; no other interpreter was substituted.' >&2
        exit 2
    fi
else
    stca_selected=
    if [ -n "${STCA_PY:-}" ]; then stca_try "$STCA_PY" || :; fi
    for stca_prefix in "${VIRTUAL_ENV:-}" "${CONDA_PREFIX:-}"; do
        [ -n "$stca_selected" ] && break
        [ -n "$stca_prefix" ] && stca_try "$stca_prefix/bin/python" && break
    done
    if [ -z "$stca_selected" ]; then
        for stca_command in python3 python python3.10 python3.11 python3.12 python3.13 python3.14 python3.15; do
            stca_candidate=$(command -v "$stca_command" 2>/dev/null) || continue
            stca_try "$stca_candidate" && break
        done
    fi
    if [ -z "$stca_selected" ]; then
        for stca_candidate in \
            "$PWD"/.venv/bin/python "$PWD"/venv/bin/python \
            "${HOME:-}"/.venvs/*/bin/python "${HOME:-}"/.virtualenvs/*/bin/python \
            "${HOME:-}"/.local/share/virtualenvs/*/bin/python \
            "${HOME:-}"/.local/share/uv/python/*/bin/python3 \
            "${HOME:-}"/miniconda3/bin/python "${HOME:-}"/anaconda3/bin/python \
            "${HOME:-}"/miniforge3/bin/python "${HOME:-}"/mambaforge/bin/python \
            "${HOME:-}"/miniconda3/envs/*/bin/python "${HOME:-}"/anaconda3/envs/*/bin/python \
            "${HOME:-}"/miniforge3/envs/*/bin/python /opt/conda/envs/*/bin/python \
            /opt/homebrew/bin/python3* /usr/local/bin/python3* \
            /Library/Frameworks/Python.framework/Versions/*/bin/python3 /usr/bin/python3; do
            [ -f "$stca_candidate" ] || continue
            stca_try "$stca_candidate" && break
        done
    fi
    if [ -z "$stca_selected" ] && [ -r "${HOME:-}/.conda/environments.txt" ]; then
        stca_count=0
        while IFS= read -r stca_prefix; do
            stca_count=$((stca_count + 1))
            [ "$stca_count" -gt 64 ] && break
            stca_try "$stca_prefix/bin/python" && break
        done < "${HOME:-}/.conda/environments.txt"
    fi
    if [ -z "$stca_selected" ]; then
        echo 'STCA: no usable Python 3.10+ was found in local environment locations. Select an existing Python interpreter or prepare Python, then retry. No packages were installed.' >&2
        exit 2
    fi
fi
exec "$stca_selected" "$stca_script" "$@"
