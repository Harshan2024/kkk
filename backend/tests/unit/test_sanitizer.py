"""
tests/unit/test_sanitizer.py — Unit Tests for Input Sanitization
================================================================
Coverage target: ≥ 95% of sanitizer.py
Tests XSS prevention, path traversal blocking, null byte handling.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from app.utils.sanitizer import sanitize_text, sanitize_filename, sanitize_search_query


# ─── sanitize_text ────────────────────────────────────────────────────────────

class TestSanitizeText:

    def test_plain_text_unchanged(self):
        assert sanitize_text("Hello World") == "Hello World"

    def test_none_returns_none(self):
        assert sanitize_text(None) is None

    def test_integer_returned_unchanged(self):
        assert sanitize_text(42) == 42

    def test_empty_string(self):
        assert sanitize_text("") == ""

    def test_xss_script_tag_escaped(self):
        result = sanitize_text("<script>alert('XSS')</script>")
        assert "<script>" not in result
        assert "&lt;script&gt;" in result

    def test_xss_img_onerror_escaped(self):
        result = sanitize_text("<img src=x onerror=alert(1)>")
        assert "<img" not in result
        assert "&lt;img" in result

    def test_xss_iframe_escaped(self):
        result = sanitize_text("<iframe src='evil.com'>")
        assert "<iframe" not in result

    def test_javascript_protocol_stripped(self):
        result = sanitize_text("javascript:void(0)")
        assert "javascript:" not in result

    def test_javascript_protocol_case_insensitive(self):
        result = sanitize_text("JAVASCRIPT:alert(1)")
        assert "javascript:" not in result.lower()

    def test_mixed_xss_and_text(self):
        result = sanitize_text("Hello <b>World</b> and <script>evil()</script>")
        assert "<script>" not in result
        assert "&lt;script&gt;" in result

    def test_angle_brackets_escaped(self):
        result = sanitize_text("3 < 5 and 10 > 7")
        assert "&lt;" in result
        assert "&gt;" in result

    def test_unicode_preserved(self):
        result = sanitize_text("Carbon footprint: 2.5 kg CO₂e 🌿")
        assert "CO₂e" in result
        assert "🌿" in result

    def test_newlines_and_whitespace_preserved(self):
        text = "Line 1\nLine 2\t\rEnd"
        result = sanitize_text(text)
        assert "\n" in result
        assert "Line 1" in result


# ─── sanitize_filename ────────────────────────────────────────────────────────

class TestSanitizeFilename:

    def test_normal_filename_preserved(self):
        assert sanitize_filename("my_photo.jpg") == "my_photo.jpg"

    def test_path_traversal_unix_stripped(self):
        result = sanitize_filename("../../../etc/passwd")
        assert ".." not in result
        assert "/" not in result
        assert result == "passwd"

    def test_path_traversal_windows_stripped(self):
        result = sanitize_filename("..\\..\\Windows\\System32\\cmd.exe")
        assert ".." not in result
        assert result == "cmd.exe"

    def test_null_byte_stripped(self):
        result = sanitize_filename("image\x00.jpg")
        assert "\x00" not in result

    def test_special_chars_stripped(self):
        result = sanitize_filename("file;rm -rf *.py")
        assert ";" not in result
        assert "*" not in result

    def test_none_returns_none(self):
        assert sanitize_filename(None) is None

    def test_empty_string_returns_file(self):
        result = sanitize_filename("")
        assert result == "file"

    def test_leading_dot_stripped(self):
        result = sanitize_filename(".hidden")
        assert not result.startswith(".")

    def test_double_dots_collapsed(self):
        result = sanitize_filename("image..jpg")
        assert ".." not in result

    def test_valid_extensions_preserved(self):
        for name in ["photo.png", "scan.pdf", "receipt.jpeg", "data.webp"]:
            result = sanitize_filename(name)
            assert "." in result

    def test_alphanumeric_dashes_underscores_allowed(self):
        result = sanitize_filename("my-photo_2024.jpg")
        assert result == "my-photo_2024.jpg"

    def test_deeply_nested_path(self):
        result = sanitize_filename("/var/www/uploads/../../secret.key")
        assert "/" not in result
        assert ".." not in result


# ─── sanitize_search_query ────────────────────────────────────────────────────

class TestSanitizeSearchQuery:

    def test_normal_query_unchanged(self):
        result = sanitize_search_query("transport activities this week")
        assert "transport activities this week" == result

    def test_xss_in_query_escaped(self):
        result = sanitize_search_query("<script>alert(1)</script>")
        assert "<script>" not in result

    def test_empty_query(self):
        assert sanitize_search_query("") == ""
