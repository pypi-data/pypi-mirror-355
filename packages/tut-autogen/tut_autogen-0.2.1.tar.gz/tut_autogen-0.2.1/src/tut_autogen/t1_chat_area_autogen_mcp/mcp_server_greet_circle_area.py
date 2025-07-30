import math
from fastmcp import FastMCP

mcp = FastMCP(name="MyServer")


@mcp.tool
def greet(name: str) -> str:
    """Greet a user by name."""
    return f"Hello, {name}!"


@mcp.tool
def calculate_circle_area(radius: float) -> dict:
    """
    计算圆的面积

    Args:
        radius: 圆的半径

    Returns:
        包含计算结果和相关信息的字典
    """
    if radius < 0:
        raise ValueError("半径不能为负数")

    area = math.pi * (radius ** 2)

    return {
        "radius": radius,
        "area": area,
        "formula": "π × radius²",
        "details": f"半径为{radius}的圆的面积是π乘以半径的平方，即{area:.4f}"
    }


if __name__ == "__main__":
    mcp.run(transport='sse')
