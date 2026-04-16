#!/usr/bin/env python3
"""手动重处理脚本：重置已失败或需要重新解析的简历"""

import sys
import os

# 确保能导入后端模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.models.db import SessionLocal, init_db
from app.models.resume_models import ResumeFile
from app.services.parser import parse_resume


def main():
    init_db()
    db = SessionLocal()

    try:
        # 查询所有非 done 状态的简历文件
        files = db.query(ResumeFile).filter(ResumeFile.status != "done").all()
        if not files:
            print("没有需要重处理的简历。")
            return

        print(f"找到 {len(files)} 个需要重处理的简历文件：")
        for f in files:
            print(f"  [{f.status}] {f.file_path}")

        for f in files:
            print(f"\n处理: {f.file_path}")
            f.status = "processing"
            db.commit()
            success = parse_resume(db, f)
            print(f"  {'成功' if success else '失败'}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
