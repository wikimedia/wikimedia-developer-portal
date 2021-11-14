#!/usr/bin/env bash
cat > ${1:?Missing target file} << _EOF
LOCAL_UID=$(id -u)
LOCAL_GID=$(id -g)
_EOF
