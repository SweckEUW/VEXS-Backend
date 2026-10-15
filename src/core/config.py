from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    shotgrid_project_id: int = 518
    shotgrid_server_path: str = "https://th-owl.shotgrid.autodesk.com/"
    shotgrid_script_name: str = "vexs_api_service"
    shotgrid_graph_entity: str = "CustomEntity01"
    shotgrid_hook_connection_entity: str = "CustomEntity02"
    shotgrid_script_key: str

settings = Settings()