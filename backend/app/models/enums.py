"""列挙型。値はDBのENUM定義(日本語含む)と一致させること。

SQLAlchemyの Enum 列では native_enum=True / create_type=False を使い、
型の生成自体はAlembicマイグレーション(生DDL)側に任せる。
"""
import enum


class UserRole(str, enum.Enum):
    admin = "admin"
    manager = "manager"
    sales = "sales"


class EngineerStatus(str, enum.Enum):
    待機 = "待機"
    稼働中 = "稼働中"
    契約終了予定 = "契約終了予定"
    離脱 = "離脱"


class BusinessType(str, enum.Enum):
    エンド = "エンド"
    SIer = "SIer"
    コンサル = "コンサル"
    BP = "BP"


class ProjectStatus(str, enum.Enum):
    募集中 = "募集中"
    提案中 = "提案中"
    成約 = "成約"
    クローズ = "クローズ"


class ContractType(str, enum.Enum):
    上位 = "上位"
    下位 = "下位"


class ContractStatus(str, enum.Enum):
    契約中 = "契約中"
    更新待ち = "更新待ち"
    終了 = "終了"


class InvoiceStatus(str, enum.Enum):
    未請求 = "未請求"
    請求済 = "請求済"
    入金済 = "入金済"


# ---- employee 系 ----
class GenderType(str, enum.Enum):
    男 = "男"
    女 = "女"
    その他 = "その他"
    未回答 = "未回答"


class EmployeeStatus(str, enum.Enum):
    在籍 = "在籍"
    休職 = "休職"
    退職 = "退職"


class EmergencyContactKind(str, enum.Enum):
    母国親族 = "母国親族"
    在日緊急連絡 = "在日緊急連絡"
    その他 = "その他"


class DocumentKind(str, enum.Enum):
    在留カード表 = "在留カード表"
    在留カード裏 = "在留カード裏"
    パスポート = "パスポート"
    証明写真 = "証明写真"
    源泉徴収票 = "源泉徴収票"
    マイナンバーカード = "マイナンバーカード"
    その他 = "その他"
