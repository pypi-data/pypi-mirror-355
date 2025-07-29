#!/usr/bin/env python
# -*- coding: UTF-8 -*-
__author__ = 'haoyang'
__date__ = '2025/6/9 09:49'

import asyncio
import json
import os
import sys
import uuid

from aiohttp import web

import base64
import mimetypes

class ROLE:
  ASSISTANT = "assistant"
  USER = "user"
  SYSTEM = "system"

def build_message(role_type: ROLE, content):
  return {"role": role_type, "content": content}

def build_image_message(content: str, file: bytes=None, file_path: str=None):
  rep = _get_image_data_and_mime(file, file_path)
  img_content = [{
    "type": "image_url",
    "image_url": {
      "url": f'data:{rep["mime_type"]};base64,{rep["data"]}'
    }
  }, {
    "type": "text",
    "text": content
  }]
  return build_message(ROLE.USER, img_content)

def build_call_back(debug=False):
  call_id = uuid.uuid4()
  queue = asyncio.Queue()
  async def on_msg(cid, role, msg):
    if debug: print(msg, file=sys.__stdout__, end='', flush=True)
    await queue.put({"id": cid, "role": role, "msg": msg})
  async def on_final(cid, is_final, msg):
    if debug: print(cid, is_final, msg, file=sys.__stdout__, flush=True)
    if is_final:
      await queue.put("[DONE]")
    else:
      nonlocal call_id
      call_id = uuid.uuid4()
  def get_call_id():
    return call_id.hex
  async def process_sse_resp(response: web.StreamResponse, e: Exception = None):
    if e:
      await response.write(b"data: " + f'{{"code": 500, "error": "{e}"}}'.encode('utf-8') + b"\n\n")
      await response.write(b"data: [DONE]\n\n")
      return
    while True:
      msg = await queue.get()
      if msg == "[DONE]":
        await response.write(b"data: [DONE]\n\n")
        break
      await response.write(f"data: {json.dumps(msg)}\n\n".encode("utf-8"))
  return process_sse_resp, {"get_call_id": get_call_id, "get_event_msg_func": on_msg, "get_full_msg_func": on_final}




















def _get_image_data_and_mime(file: bytes = None, file_path: str = None):
  if file_path:
    with open(file_path, "rb") as f:
      file = f.read()
  if not file:
    raise ValueError("file 和 file_path 至少要提供一个")
  mime_type = "application/octet-stream"
  if file_path:
    mime_type_guess, _ = mimetypes.guess_type(file_path)
    if mime_type_guess:
      mime_type = mime_type_guess
  data = base64.b64encode(file).decode("utf-8")
  return {
    "mime_type": mime_type,
    "data": data
  }
