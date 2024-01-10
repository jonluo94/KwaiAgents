from .commons import NoTool, NoToolResult, FinishTool, FinishResult
from .search import SearchTool
from .browser import BrowserTool
from .weather import WeatherTool
from .calendars import CalendarTool
from .timedelta import TimeDeltaTool
from .solarterms import SolarTermsTool
from .diffusion import DiffusionTool

ALL_NO_TOOLS = [NoTool, FinishTool]
ALL_AUTO_TOOLS = [SearchTool, BrowserTool, WeatherTool, CalendarTool, TimeDeltaTool, SolarTermsTool, DiffusionTool]
ALL_TOOLS = [SearchTool, BrowserTool, WeatherTool, CalendarTool, TimeDeltaTool, SolarTermsTool, DiffusionTool]
