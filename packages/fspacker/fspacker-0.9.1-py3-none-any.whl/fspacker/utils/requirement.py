"""本模块包含库所需常用函数."""

from __future__ import annotations

import re

from packaging.requirements import InvalidRequirement
from packaging.requirements import Requirement

from fspacker.exceptions import ProjectPackError


class RequirementParser:
    """解析需求字符串为Requirement对象."""

    @classmethod
    def normalize(cls, req_str: str) -> str | None:
        """规范化需求字符串.

        处理特殊情况:
        1. 括号包裹的版: shiboken2 (==5.15.2.1) -> shiboken2==5.15.2.1
        2. 不规范的版本分隔符: package@1.0 -> package==1.0
        3. 移除多余空格和注释.

        Args:
            req_str: 需求字符串.

        Returns:
            规范化后的需求字符串, 如果解析失败, 返回 None.
        """
        # 移除注释和首尾空格
        req_str = re.sub(r"#.*$", "", req_str).strip()

        # 替换不规范的版本分隔符
        req_str = re.sub(r"([a-zA-Z0-9_-]+)@([0-9.]+)", r"\1==\2", req_str)

        # 标准化版本运算符(处理 ~= 和意外的空格)
        req_str = re.sub(r"~=\s*", "~=", req_str)
        req_str = re.sub(r"([=<>!~]+)\s*", r"\1", req_str)

        # 处理括号包裹的版本
        req_str = re.sub(r"[()]", "", req_str)

        # 标准化版本运算符
        req_str = re.sub(r";.*", "", req_str)

        # 处理空白符
        return re.sub(r"\s+", "", req_str)

    @classmethod
    def parse(cls, req_str: str) -> Requirement | None:
        """安全解析需求字符串为Requirement对象.

        Args:
            req_str: 需求字符串.

        Returns:
            Requirement对象, 如果解析失败, 返回 None.

        Raises:
            ProjectPackError: 解析失败
        """
        normalized = cls.normalize(req_str)

        try:
            return Requirement(normalized)
        except InvalidRequirement as e:
            msg = f"解析依赖失败, '{req_str}': {e!s}"
            raise ProjectPackError(msg) from e
