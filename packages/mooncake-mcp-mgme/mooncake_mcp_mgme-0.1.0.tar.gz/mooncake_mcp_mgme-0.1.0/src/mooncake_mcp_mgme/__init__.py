# server.py
from azure.identity import AzureCliCredential
from azure.mgmt.resource import ResourceManagementClient


from mcp.server.fastmcp import FastMCP
# Create an MCP server
mcp = FastMCP("Mooncake")


# Add an addition tool
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b


# Add an addition tool
@mcp.tool()
def getresourcebysubscription(subscription_id: str) -> list[{str}]:
    """Find all resources in a subscription from mooncake(azure china)"""
    """获取 Mooncake(中国 Azure) 订阅下的所有资源"""
    # 替换为你的订阅 ID
    if not subscription_id or subscription_id == "":
        # 如果没有提供订阅 ID，则使用默认值
        # If no subscription ID is provided, use a default value
        print("Please set your subscription id")
        print("请设置你的订阅 ID")
    # 使用 Azure CLI 登录凭据
    credential = AzureCliCredential()

    print(credential.get_token("https://management.chinacloudapi.cn/.default"))

    # 创建资源管理客户端
    resource_client = ResourceManagementClient(credential, subscription_id, base_url="https://management.chinacloudapi.cn/",credential_scopes=["https://management.chinacloudapi.cn/.default"])

    # 获取所有资源
    resources = resource_client.resources.list()

    results = []
    # 打印资源信息
    for resource in resources:
        print(f"Name: {resource.name}")
        print(f"Type: {resource.type}")
        print(f"Location: {resource.location}")
        print(f"Resource Group: {resource.id.split('/')[4]}")
        print("-" * 40)

        results.append({
                    "Name": resource.name,
                    "Type": resource.type,
                    "Location":resource.location,
                    "ResourceGroup": resource.id.split('/')[4]
                })
              
    
    return results



# Add a dynamic greeting resource
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    return f"Hello, {name}!"



# if __name__ == "__main__":
#     #mcp.run(transport='stdio')
#     mcp.run(transport='sse')



def main() -> None:
    mcp.run(transport='stdio')
