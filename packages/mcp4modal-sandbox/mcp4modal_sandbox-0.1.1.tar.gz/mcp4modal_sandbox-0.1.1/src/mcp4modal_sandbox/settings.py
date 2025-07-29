from pydantic import Field, BaseModel

class MCPServerSettings(BaseModel):
    mcp_host: str
    mcp_port: int 
    modal_token_id: str 
    modal_token_secret: str 