"""安全模块单元测试"""

import os
import pytest
from security import (
    detect_pii, mask_pii, sanitize_query, validate_file_path,
    encrypt_text, decrypt_text, generate_api_key, verify_api_key,
    SecurityConfig,
)


class TestPIIDetection:
    def test_detect_phone(self):
        findings = detect_pii("联系我 13812341234")
        types = [f["type"] for f in findings]
        assert "phone_cn" in types

    def test_detect_email(self):
        findings = detect_pii("发邮件到 test@example.com")
        types = [f["type"] for f in findings]
        assert "email" in types

    def test_detect_id_card(self):
        findings = detect_pii("身份证号 110101199001011234")
        types = [f["type"] for f in findings]
        assert "id_card_cn" in types

    def test_detect_multiple(self):
        text = "手机 13912345678，邮箱 a@b.com"
        findings = detect_pii(text)
        types = {f["type"] for f in findings}
        assert "phone_cn" in types
        assert "email" in types

    def test_no_pii(self):
        assert detect_pii("今天天气真好") == []


class TestPIIMasking:
    def test_mask_phone(self):
        result = mask_pii("联系 13812341234")
        assert "138****1234" in result
        assert "13812341234" not in result

    def test_mask_email(self):
        result = mask_pii("邮箱 test@example.com")
        assert "te***@example.com" in result
        assert "test@example.com" not in result

    def test_no_pii_unchanged(self):
        text = "没有敏感信息的文本"
        assert mask_pii(text) == text


class TestInputSanitization:
    def test_normal_query(self):
        assert sanitize_query("你好世界") == "你好世界"

    def test_strips_whitespace(self):
        assert sanitize_query("  hello  ") == "hello"

    def test_empty_query_raises(self):
        with pytest.raises(ValueError, match="不能为空"):
            sanitize_query("")

    def test_blank_query_raises(self):
        with pytest.raises(ValueError, match="不能为空"):
            sanitize_query("   ")

    def test_too_long_raises(self):
        with pytest.raises(ValueError, match="过长"):
            sanitize_query("x" * 5000)

    def test_xss_blocked(self):
        with pytest.raises(ValueError, match="不允许"):
            sanitize_query("<script>alert(1)</script>")

    def test_template_injection_blocked(self):
        with pytest.raises(ValueError, match="不允许"):
            sanitize_query("{{config.__class__}}")

    def test_python_escape_blocked(self):
        with pytest.raises(ValueError, match="不允许"):
            sanitize_query("__import__('os').system('rm -rf /')")


class TestPathSandbox:
    def test_valid_path(self):
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(project_root, "data")
        os.makedirs(data_dir, exist_ok=True)
        result = validate_file_path(
            os.path.join(data_dir, "test.txt"),
            allowed_dirs=[data_dir],
        )
        assert result.endswith("test.txt")

    def test_traversal_blocked(self):
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(project_root, "data")
        with pytest.raises(PermissionError, match="访问被拒绝"):
            validate_file_path(
                os.path.join(data_dir, "..", "..", "etc", "passwd"),
                allowed_dirs=[data_dir],
            )

    def test_empty_path_raises(self):
        with pytest.raises(ValueError, match="不能为空"):
            validate_file_path("")


class TestEncryption:
    def test_round_trip(self, monkeypatch, tmp_path):
        monkeypatch.setenv("AURA_MASTER_KEY", "test-secret-key-12345")
        salt_file = tmp_path / ".aura_salt"
        import security
        monkeypatch.setattr(security, "_SALT_FILE", str(salt_file))
        security.get_fernet.cache_clear()

        plaintext = "这是一段隐私数据"
        ciphertext = encrypt_text(plaintext)
        assert ciphertext != plaintext
        assert decrypt_text(ciphertext) == plaintext

        security.get_fernet.cache_clear()


class TestAPIKey:
    def test_generate_format(self):
        key = generate_api_key()
        assert key.startswith("aura_")
        assert len(key) > 10

    def test_verify_disabled_when_no_env(self, monkeypatch):
        monkeypatch.delenv("AURA_API_KEY", raising=False)
        assert verify_api_key("anything") is True

    def test_verify_correct_key(self, monkeypatch):
        monkeypatch.setenv("AURA_API_KEY", "aura_test123")
        assert verify_api_key("aura_test123") is True

    def test_verify_wrong_key(self, monkeypatch):
        monkeypatch.setenv("AURA_API_KEY", "aura_test123")
        assert verify_api_key("aura_wrong") is False
