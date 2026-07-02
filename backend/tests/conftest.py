"""単体テスト用の共通設定。

- テスト対象モジュール（app パッケージ）を import できるよう sys.path を調整。
- JWT/暗号化テストのため設定値（JWT_SECRET）を固定。
  config.Settings は import 時に評価されるため、ここで先に環境変数を確定させる。
- 単体テストはDB非依存（純粋関数中心）。boto3等の外部I/Oは行わない。
"""
import os
import sys
from pathlib import Path

# backend/ をパスに追加（app パッケージを解決）
BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

# 設定固定（JWT署名・Fernet鍵導出を決定的にする）。app import 前に設定する。
os.environ.setdefault("JWT_SECRET", "unit-test-secret")
