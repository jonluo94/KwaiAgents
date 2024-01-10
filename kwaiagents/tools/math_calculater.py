"""Commands to execute code"""
from kwaiagents.tools import CodeInterpreterTool
from kwaiagents.tools.base import BaseResult


class MathCalculaterResult(BaseResult):
    @property
    def answer(self):
        return self.json_data


class MathCalculaterTool(CodeInterpreterTool):
    """
    Mathematical calculations are performed by using python code

    Args:
        code (str): The Mathematical Expressions Python code to run.

    Returns:
         str: The calculate result from the code when it ran.
    """
    name = "math_calculater"
    zh_name = "数学计算器"
    description = 'Math Calculater:"math_calculater", args:"code": "<str: the mathematical expressions python code, required>"'
    tips = ""

    def __init__(
            self,
            lang="wt-wt",
            max_retry_times=5,
            *args,
            **kwargs,
    ):
        self.max_retry_times = max_retry_times
        self.lang = lang

    def __call__(self, code, *args, **kwargs):
        result = self.run_code_interpreter(code=code)
        return MathCalculaterResult(result)
