#!/usr/bin/env python3
"""Entrypoint for Cursor Mini Chat server."""

import uvicorn

from chat.app.config import HOST, PORT


def main() -> None:
    uvicorn.run("chat.app.main:app", host=HOST, port=PORT, reload=False)


if __name__ == "__main__":
    main()
