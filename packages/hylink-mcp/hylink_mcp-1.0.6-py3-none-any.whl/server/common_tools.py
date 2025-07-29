#!/usr/bin/env python
# -*- coding: UTF-8 -*-
__author__ = 'haoyang'
__date__ = '2025/4/27 08:29'

import datetime
from contextlib import asynccontextmanager
from typing import AsyncIterator

from mcp.server import Server
from mcp.server.fastmcp import FastMCP


@asynccontextmanager
async def server_lifespan(server: Server) -> AsyncIterator[dict]:
  yield {}

# 创建 MCP 服务器实例
mcp = FastMCP("common-tools-server", lifespan=server_lifespan)

@mcp.tool()
def get_date_time() -> dict:
  """
  获取当前时间
  :return: 当前时间(yyyy-mm-dd HH:MM:SS)
  """
  return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def main():
  mcp.run()

if __name__ == '__main__':
  main()

