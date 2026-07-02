"""RBAC編集権限判定（純粋関数）の単体テスト。

対象: DD-16 can_edit_resource / DD-17 ensure_can_edit
DD-16 はDBアクセスせず User と created_by(int|None) のみ参照する純粋関数。
User インスタンスは role/id 属性のみ参照されるため、ORMに紐づけず生成して検証する。
"""
import pytest
from fastapi import HTTPException

from app.core.deps import can_edit_resource, ensure_can_edit
from app.models.enums import UserRole
from app.models.user import User


def _user(role: UserRole, uid: int = 1) -> User:
    """role と id のみ持つ User を生成（DBに保存しない・属性参照のみ）。"""
    u = User()
    u.id = uid
    u.role = role
    return u


class TestCanEditResource:
    def test_UT_50_adminは他人作成でもTrue(self):
        """UT-50 / DD-16 / 正常: admin は created_by が他人(99)でも True。"""
        assert can_edit_resource(_user(UserRole.admin, 1), 99) is True

    def test_UT_51_managerは他人作成でもTrue(self):
        """UT-51 / DD-16 / 正常: manager は他人作成でも True。"""
        assert can_edit_resource(_user(UserRole.manager, 1), 99) is True

    def test_UT_52_salesは自分作成のみTrue(self):
        """UT-52 / DD-16 / 正常: sales は created_by==自分id のとき True。"""
        assert can_edit_resource(_user(UserRole.sales, 1), 1) is True

    def test_UT_53_salesは他人作成でFalse(self):
        """UT-53 / DD-16 / 境界: sales は created_by が他人ならFalse。"""
        assert can_edit_resource(_user(UserRole.sales, 1), 99) is False

    def test_UT_54_salesはcreated_by_NoneでFalse(self):
        """UT-54 / DD-16 / 異常: sales は created_by が None なら False。"""
        assert can_edit_resource(_user(UserRole.sales, 1), None) is False

    def test_UT_55_adminはcreated_by_NoneでもTrue(self):
        """UT-55 / DD-16 / 境界: admin は created_by None でも True。"""
        assert can_edit_resource(_user(UserRole.admin, 1), None) is True


class TestEnsureCanEdit:
    def test_UT_56_権限ありは例外なし(self):
        """UT-56 / DD-17 / 正常: 編集可なら何も起こさない(None)。"""
        assert ensure_can_edit(_user(UserRole.admin, 1), 99) is None

    def test_UT_57_権限なしは403(self):
        """UT-57 / DD-17 / 異常: 編集不可なら HTTPException 403。"""
        with pytest.raises(HTTPException) as ei:
            ensure_can_edit(_user(UserRole.sales, 1), 99)
        assert ei.value.status_code == 403
