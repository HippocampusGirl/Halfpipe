#!/usr/bin/env bash

opts=$(getopt -o r: --long requirements-file: -n 'enigma-qc' -- "$@")
eval set -- "$opts"

verbose=1

requirements_files=()

fail() {
    printf '%s\n' "$1" >&2
    exit "${2-1}"
}

while true; do
    case "$1" in
    -r | --requirements-file)
        case "$2" in
        "") shift 2 ;;
        *)
            requirements_files+=("$2")
            shift 2
            ;;
        esac
        ;;
    --)
        shift
        break
        ;;
    *) fail "internal error!" ;;
    esac
done

if [[ "${#requirements_files[@]}" -lt 1 ]]; then
    fail "missing required --requirements-file parameter"
fi

run_cmd() {
    command="$*"

    printf '%s\n' --------------------

    if [ "${verbose}" = "1" ]; then
        printf "%s\n" "${command}"
    fi

    eval "$@"

    exit_code=$?

    if [[ ${exit_code} -gt 0 ]]; then
        echo "ERROR: command exited with nonzero status ${exit_code}"
    fi

    printf '%s\n' --------------------

    return ${exit_code}
}

conda_packages=()
pip_packages=()

while read -r requirement; do
    if [ -z "${requirement}" ]; then
        continue
    fi

    printf '%s\n' --------------------

    if run_cmd "${MAMBA_EXE} install --dry-run \"${requirement}\" >/dev/null"; then
        printf "Using $(basename "${MAMBA_EXE}") for package \"%s\"\n" "${requirement}"
        conda_packages+=("${requirement}")
    else
        printf 'Using pip for package "%s"\n' "${requirement}"
        pip_packages+=("\"${requirement}\"")
    fi

    printf '%s\n' --------------------

done < <(grep --no-filename -v '#' "${requirements_files[@]}")

if ! run_cmd "${MAMBA_EXE}" install --yes "${conda_packages[@]}"; then
    exit 1
fi
# We assume that all python dependencies have already been resolved by `pip-compile`,
# so there will be no conflicts when we ask `pip` to install them.
if ! run_cmd pip install --no-deps "${pip_packages[@]}"; then
    exit 1
fi
