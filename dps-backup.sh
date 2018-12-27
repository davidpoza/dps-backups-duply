#!/bin/bash

ENV_PATH="`dirname \"$0\"`"
MAIN_PATH="$ENV_PATH/main.py"
ENV_PATH+="/.env"

"exec" "$ENV_PATH/bin/python3" "$MAIN_PATH"
echo $0
