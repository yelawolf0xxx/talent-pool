import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """全局应用配置"""

    # 数据库
    db_host: str = "127.0.0.1"
    db_port: int = 3306
    db_user: str = "root"
    db_password: str = ""
    db_name: str = "talent_pool"

    # AI（匹配 CodingPlan / DashScope 环境变量名）
    auth_token: str = Field(default="", alias="ANTHROPIC_AUTH_TOKEN")
    base_url: str = Field(default="", alias="ANTHROPIC_BASE_URL")
    model: str = Field(default="claude-sonnet-4-6-20251014", alias="ANTHROPIC_MODEL")

    # 简历目录（支持多个路径，逗号分隔）
    resume_dir: str = str(Path(__file__).parent.parent / "resumes")

    @property
    def resume_dirs(self) -> list[str]:
        """解析多个简历目录路径"""
        result = []
        for p in self.resume_dir.split(","):
            p = p.strip()
            if not p:
                continue
            # UNC 路径（\\server\share）不做 resolve，保持原始格式
            if p.startswith("\\\\") or p.startswith("//"):
                result.append(p)
            else:
                result.append(str(Path(p).resolve()))
        return result

    # 扫描间隔（秒）
    scan_interval: int = 300

    # 日志配置
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    class Config:
        env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
        populate_by_name = True

    @property
    def database_url(self) -> str:
        """构建 SQLAlchemy MySQL 连接 URL"""
        pwd = f":{self.db_password}" if self.db_password else ""
        return (
            f"mysql+pymysql://{self.db_user}{pwd}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
            f"?charset=utf8mb4"
        )

    @field_validator("resume_dir")
    @classmethod
    def validate_resume_dir(cls, v: str) -> str:
        paths = [p.strip() for p in v.split(",") if p.strip()]
        for p in paths:
            # UNC 路径不做 mkdir
            if p.startswith("\\\\") or p.startswith("//"):
                continue
            path = Path(p)
            if not path.exists():
                path.mkdir(parents=True, exist_ok=True)
        return v


settings = Settings()
