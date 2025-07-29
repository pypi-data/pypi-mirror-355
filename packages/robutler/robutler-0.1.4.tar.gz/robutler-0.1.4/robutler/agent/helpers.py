"""
RobutlerAgent Helpers - Utility functions to simplify agent creation

This module provides helper functions and decorators to make it even easier
to create AI agents with RobutlerServer.
"""

import asyncio
import json
import uuid
from typing import List, Optional, Callable, Any, Union
from datetime import datetime

from agents import Agent, Runner, function_tool
from openai.types.responses import ResponseTextDeltaEvent
from fastapi.responses import StreamingResponse

from robutler.server import RobutlerServer, ReportUsage, get_server_context
from robutler.server.server import ChatMessage
from .agent import RobutlerAgent, convert_messages_to_input_list
