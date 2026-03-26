#!/bin/bash

# 사용자 지정 버추얼 환경 설정 (필요한 경우)
VENV_NAME="pyenv-indicator" # 기존 버추얼 환경 이름
USE_VENV=true  # true로 설정하면 버추얼 환경에서 실행

# 설치할 패키지 목록
PACKAGES=(
  "yfinance"
)

# pyenv 초기화
if command -v pyenv &> /dev/null; then
  eval "$(pyenv init --path)"
  eval "$(pyenv init -)"
  eval "$(pyenv virtualenv-init -)"
else
  echo "pyenv가 설치되지 않았습니다. 설치 후 다시 시도하세요."
  exit 1
fi

# pyenv 가상환경 활성화
if $USE_VENV; then
  if pyenv versions | grep -q "$VENV_NAME"; then
    echo "pyenv 가상환경 '$VENV_NAME' 활성화 중..."
    pyenv activate "$VENV_NAME"
    if [ "$(pyenv version-name)" != "$VENV_NAME" ]; then
      echo "가상환경 활성화에 실패했습니다."
      exit 1
    fi
  else
    echo "가상환경 '$VENV_NAME'가 존재하지 않습니다."
    exit 1
  fi
fi

# pip 패키지 설치
echo "필요한 패키지를 설치 중..."
for PACKAGE in "${PACKAGES[@]}"; do
  echo "설치 중: $PACKAGE"
  pip install "$PACKAGE"
  if [ $? -ne 0 ]; then
    echo "패키지 '$PACKAGE' 설치 중 오류 발생!"
    exit 1
  fi
done

echo "모든 패키지 설치가 완료되었습니다!"

# pyenv 가상환경 비활성화
if $USE_VENV; then
  echo "pyenv 가상환경 비활성화 중..."
  pyenv deactivate
fi
