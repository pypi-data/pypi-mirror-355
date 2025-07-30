from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP

# 初始化 FastMCP server
mcp = FastMCP("equipment_mcp_server")

# Constants
API_PREV = "http://dev-openapi.jiayihn.com/api/open"

async def post_request(
        url: str,
        headers: dict[str, str] | None = None,
        request_body: dict[str, Any] | None = None
    ) -> dict[str, Any] | None:
    """jiayihn open api发送请求,并进行适当的错误处理。"""
    headers = {
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=headers, timeout=30.0, json=request_body)
            response.raise_for_status()
            return response.json()
        except Exception:
            return '提交失败'

@mcp.tool()
async def equipment_repair_submit(
    storeCode: str,
    reporterPhone: str,
    equipmentCategory: str,
    equipmentSubcategory: str,
    brandManufacturer: str,
    equipmentImagesUrl: list[str],
    faultSymptom: str,
    additionalDescription: str
) -> str:
    """提交设备维修单

    Args:
    
    storeCode (str): 门店编号
    reporterPhone (str): 报修人手机号
    equipmentCategory (str): 设备大类
    equipmentSubcategory (str): 设备小类
    brandManufacturer (str): 品牌厂家
    equipmentImagesUrl (list[str]): 设备图片链接
    faultSymptom (str): 故障现象
    additionalDescription (str): 其它补充描述

    Returns:
        str: 提交结果(成功|失败)

    """
    url = f"{API_PREV}/franchisee-equipment-maintenance/submit"
    params = {
        "storeCode": storeCode,
        "reporterPhone": reporterPhone,
        "equipmentCategory": equipmentCategory,
        "equipmentSubcategory": equipmentSubcategory,
        "brandManufacturer": brandManufacturer,
        "equipmentImagesUrl": equipmentImagesUrl,
        "faultSymptom": faultSymptom,
        "additionalDescription": additionalDescription
    }
    request_body = {
        "merchantId": 100004,
        "timeStamp": 1000000000,
        "sign": "asdfasfsafsa",
        "params": params
    }

    result = await post_request(url=url, request_body=request_body)
    print(f"设备维修提交结果:{result}")
    return result

def run():
    mcp.run(transport='stdio')
    print("equipment-repair server start success!")

if __name__ == "__main__":
    # 初始化并运行 server
   run()