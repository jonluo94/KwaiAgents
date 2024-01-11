from .code_interpreter import CodeInterpreterTool
from .commons import NoTool, NoToolResult, FinishTool, FinishResult
from .math_calculater import MathCalculaterTool
from .search import SearchTool
from .browser import BrowserTool
from .weather import WeatherTool
from .calendars import CalendarTool
from .timedelta import TimeDeltaTool
from .solarterms import SolarTermsTool
from .diffusion import DiffusionTool

ALL_NO_TOOLS = [NoTool, FinishTool]
ALL_AUTO_TOOLS = [SearchTool, BrowserTool, WeatherTool, CalendarTool, TimeDeltaTool, SolarTermsTool, DiffusionTool,CodeInterpreterTool,MathCalculaterTool]
ALL_TOOLS = [SearchTool, BrowserTool, WeatherTool, CalendarTool, TimeDeltaTool, SolarTermsTool, DiffusionTool,CodeInterpreterTool,MathCalculaterTool]
