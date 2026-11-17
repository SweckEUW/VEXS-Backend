from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    shotgrid_project_id: int = 518
    shotgrid_server_path: str = "https://th-owl.shotgrid.autodesk.com/"
    shotgrid_script_name: str = "vexs_api_service"
    shotgrid_graph_entity: str = "CustomEntity01"
    shotgrid_hook_connection_entity: str = "CustomEntity02"
    shotgrid_script_key: str

    # Folder watch hook, an empty folder disables the watcher
    watch_folder: str = ""
    watch_folder_extensions: str = ".blend"  # comma separated
    watch_folder_poll_seconds: float = 2.0

settings = Settings()