from pathlib import Path

from backend.app.services.bhc_config_db import (
    DEFAULT_ADMIN_EMAIL,
    authenticate_user_credentials,
    change_user_password,
    create_user_account,
    create_user_session,
    get_session_user,
    get_user_by_email,
    init_config_db,
    reset_user_password_by_email,
    set_security_question,
)


def test_bootstrap_admin_account_uses_fixed_email(tmp_path, monkeypatch):
    db_path = Path(tmp_path) / "bhc_config.db"
    monkeypatch.setenv("BHC_CONFIG_DB_PATH", str(db_path))

    init_config_db(db_path)

    admin_user = authenticate_user_credentials(DEFAULT_ADMIN_EMAIL, "ChangeThisAdmin123")

    assert admin_user["email"] == DEFAULT_ADMIN_EMAIL.lower()
    assert admin_user["is_admin"] is True
    assert admin_user["must_change_password"] is True


def test_user_create_session_change_and_reset_password(tmp_path, monkeypatch):
    db_path = Path(tmp_path) / "bhc_config.db"
    monkeypatch.setenv("BHC_CONFIG_DB_PATH", str(db_path))
    init_config_db(db_path)

    user = create_user_account(
        email="engineer@ind.tuv.com",
        full_name="Site Engineer",
        password="TempPass123",
        is_admin=False,
        created_by=DEFAULT_ADMIN_EMAIL,
    )
    authenticated = authenticate_user_credentials("engineer@ind.tuv.com", "TempPass123")
    session_token = create_user_session(authenticated["email"])
    session_user = get_session_user(session_token)

    assert user["must_change_password"] is True
    assert authenticated["email"] == "engineer@ind.tuv.com"
    assert session_user is not None
    assert session_user["email"] == "engineer@ind.tuv.com"

    change_user_password("engineer@ind.tuv.com", "TempPass123", "FreshPass123")
    updated_user = authenticate_user_credentials("engineer@ind.tuv.com", "FreshPass123")

    assert updated_user["must_change_password"] is False

    set_security_question("engineer@ind.tuv.com", "What is your first pet?", "buddy")
    reset_user = reset_user_password_by_email("engineer@ind.tuv.com", "ResetPass123", "buddy")
    final_user = authenticate_user_credentials("engineer@ind.tuv.com", "ResetPass123")

    assert reset_user["must_change_password"] is False
    assert final_user["must_change_password"] is False
    assert get_user_by_email("engineer@ind.tuv.com")["email"] == "engineer@ind.tuv.com"