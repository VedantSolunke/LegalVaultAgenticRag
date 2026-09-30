def test_me_returns_admin_flag_for_test_tokens(client) -> None:
    user = client.get(
        "/me",
        headers={"Authorization": "Bearer test-user-token"},
    )
    assert user.status_code == 200
    assert user.json()["is_admin"] is False

    admin = client.get(
        "/me",
        headers={"Authorization": "Bearer test-admin-token"},
    )
    assert admin.status_code == 200
    assert admin.json()["is_admin"] is True
