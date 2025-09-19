"""
安全な数学計算エンジン

数式の前処理、サニタイゼーション、安全な評価を担当
"""

import math
import re
from typing import Union, Dict, Any
import operator


class SafeCalculator:
    """安全な数式評価クラス"""

    def __init__(self):
        # 許可されている演算子
        self.operators = {
            '+': operator.add,
            '-': operator.sub,
            '*': operator.mul,
            '/': operator.truediv,
            '**': operator.pow,
            '^': operator.pow,  # ^ を ** に変換
        }

        # 許可されている数学関数
        self.functions = {
            'abs': abs,
            'round': round,
            'ceil': math.ceil,
            'floor': math.floor,
            'sqrt': math.sqrt,
            'sin': math.sin,
            'cos': math.cos,
            'tan': math.tan,
            'log': math.log,
            'log10': math.log10,
            'exp': math.exp,
            'pi': math.pi,
            'e': math.e,
        }

        # 危険なパターン（実行を拒否）
        self.dangerous_patterns = [
            r'__.*__',      # dunder methods
            r'import\s',    # import statements
            r'exec\s*\(',   # exec function
            r'eval\s*\(',   # eval function
            r'open\s*\(',   # file operations
            r'input\s*\(',  # input function
            r'print\s*\(',  # print function
            r'del\s+',      # delete statement
            r'global\s+',   # global statement
            r'nonlocal\s+', # nonlocal statement
        ]

    def sanitize_expression(self, expression: str) -> str:
        """数式のサニタイゼーション"""
        if not expression or not isinstance(expression, str):
            raise ValueError("数式が指定されていません")

        # 危険なパターンをチェック
        for pattern in self.dangerous_patterns:
            if re.search(pattern, expression, re.IGNORECASE):
                raise ValueError(f"安全でない式が検出されました: {pattern}")

        # 基本的なクリーニング
        expression = expression.strip()
        expression = re.sub(r'\s+', ' ', expression)  # 複数スペースを1つに

        # ^ を ** に変換（指数演算）
        expression = expression.replace('^', '**')

        # 数学関数のプレフィックス追加
        for func_name in self.functions.keys():
            if func_name not in ['pi', 'e']:  # 定数は除外
                pattern = rf'\b{func_name}\b'
                replacement = f'math.{func_name}'
                expression = re.sub(pattern, replacement, expression)

        # 定数の置換
        expression = re.sub(r'\bpi\b', 'math.pi', expression)
        expression = re.sub(r'\be\b', 'math.e', expression)

        return expression

    def validate_expression(self, expression: str) -> Dict[str, Any]:
        """数式の妥当性チェック"""
        try:
            sanitized = self.sanitize_expression(expression)

            # 基本的な構文チェック
            if not re.match(r'^[0-9+\-*/().\s\w]+$', sanitized.replace('math.', '')):
                return {
                    "valid": False,
                    "error": "許可されていない文字が含まれています",
                    "error_type": "invalid_characters"
                }

            # 括弧のバランスチェック
            if sanitized.count('(') != sanitized.count(')'):
                return {
                    "valid": False,
                    "error": "括弧の数が一致しません",
                    "error_type": "unbalanced_parentheses"
                }

            return {
                "valid": True,
                "sanitized_expression": sanitized
            }

        except Exception as e:
            return {
                "valid": False,
                "error": str(e),
                "error_type": "validation_error"
            }

    def calculate(self, expression: str) -> Dict[str, Any]:
        """安全な数式計算"""
        try:
            # 前処理・バリデーション
            validation = self.validate_expression(expression)
            if not validation["valid"]:
                return {
                    "success": False,
                    "error": validation["error"],
                    "error_type": validation["error_type"]
                }

            sanitized_expr = validation["sanitized_expression"]

            # 安全な環境で評価
            safe_dict = {
                "__builtins__": {},
                "math": math,
            }

            result = eval(sanitized_expr, safe_dict, {})

            # 結果の型チェック・変換
            if isinstance(result, complex):
                if result.imag == 0:
                    result = result.real
                else:
                    return {
                        "success": False,
                        "error": "複素数の結果はサポートされていません",
                        "error_type": "complex_result"
                    }

            # 無限大・NaNチェック
            if math.isinf(result):
                return {
                    "success": False,
                    "error": "結果が無限大になりました",
                    "error_type": "infinite_result"
                }

            if math.isnan(result):
                return {
                    "success": False,
                    "error": "結果が数値ではありません (NaN)",
                    "error_type": "nan_result"
                }

            return {
                "success": True,
                "result": result,
                "original_expression": expression,
                "sanitized_expression": sanitized_expr,
                "result_type": type(result).__name__
            }

        except ZeroDivisionError:
            return {
                "success": False,
                "error": "ゼロで除算しようとしました",
                "error_type": "division_by_zero"
            }
        except ValueError as e:
            return {
                "success": False,
                "error": f"数値エラー: {str(e)}",
                "error_type": "value_error"
            }
        except SyntaxError as e:
            return {
                "success": False,
                "error": f"構文エラー: {str(e)}",
                "error_type": "syntax_error"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"計算エラー: {str(e)}",
                "error_type": "calculation_error"
            }