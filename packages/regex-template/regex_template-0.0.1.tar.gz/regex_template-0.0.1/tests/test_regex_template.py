# SPDX-FileCopyrightText: 2025-present Trey Hunner
#
# SPDX-License-Identifier: MIT
import re
import pytest
from string.templatelib import Template
from hypothesis import given, strategies as st

import regex_template as ret


class TestCompileWithRegularStrings:
    """Test compile() function rejection of regular string inputs."""

    def test_compile_rejects_regular_string(self):
        with pytest.raises(TypeError, match="only accepts t-string Templates"):
            ret.compile("hello")

    def test_compile_rejects_various_types(self):
        # Test various non-Template types
        with pytest.raises(TypeError, match="only accepts t-string Templates"):
            ret.compile(123)
        
        with pytest.raises(TypeError, match="only accepts t-string Templates"):
            ret.compile(["hello"])
        
        with pytest.raises(TypeError, match="only accepts t-string Templates"):
            ret.compile(None)

    def test_error_message_suggests_re_compile(self):
        with pytest.raises(TypeError, match="Use re.compile\\(\\) for regular strings"):
            ret.compile("hello world")


class TestCompileWithTStrings:
    """Test ret.compile() function with t-string Template inputs."""

    def test_compile_tstring_basic(self):
        text = "hello"
        pattern = ret.compile(t"{text}")
        assert pattern.match("hello")
        assert not pattern.match("world")

    def test_compile_tstring_with_flags(self):
        text = "Hello"
        pattern = ret.compile(t"{text}", flags=re.IGNORECASE, verbose=False)
        assert pattern.match("hello")
        assert pattern.match("HELLO")
        assert pattern.match("Hello")

    def test_compile_tstring_verbose_mode_default(self):
        # Verbose mode should be enabled by default
        text = "hello"
        pattern = ret.compile(t"""
            {text}       # Match hello
            \\s+         # One or more spaces
            world        # Match world
        """)
        assert pattern.match("hello world")
        assert pattern.match("hello   world")

    def test_compile_tstring_verbose_mode_disabled(self):
        pattern = ret.compile(t"hello world", verbose=False)
        assert pattern.match("hello world")
        assert not pattern.match("hello   world")

    def test_compile_tstring_empty_interpolation(self):
        empty = ""
        pattern = ret.compile(t"start{empty}end")
        assert pattern.match("startend")

    def test_compile_tstring_regex_special_chars_safe(self):
        digits = r"\d+"
        pattern = ret.compile(t"{digits:safe}")
        assert pattern.match("123")
        assert not pattern.match("abc")

    def test_compile_tstring_auto_escape(self):
        special_chars = ".+*?[]{}()|^$\\"
        pattern = ret.compile(t"{special_chars}")
        # Should match literally, not as regex special chars
        assert pattern.match(".+*?[]{}()|^$\\")
        assert not pattern.match("anything")

    def test_compile_tstring_mixed_pattern(self):
        filename = "test.txt"
        pattern = ret.compile(t"^{filename}$")
        assert pattern.match("test.txt")
        assert not pattern.match("testxtxt")  # . should be escaped

    def test_compile_tstring_safe_format_spec(self):
        regex_part = r"\d+"
        literal_part = "file.txt" 
        pattern = ret.compile(t"{regex_part:safe}_{literal_part}")
        assert pattern.match("123_file.txt")
        assert not pattern.match("abc_file.txt")
        assert not pattern.match("123_filextxt")  # . should be escaped in literal_part

    def test_compile_tstring_format_specifiers(self):
        number = 42
        pattern = ret.compile(t"value_{number:03d}")
        assert pattern.match("value_042")
        assert not pattern.match("value_42")

    def test_compile_tstring_format_spec_then_escape(self):
        # Format spec should be applied first, then escaping
        value = 3.14
        pattern = ret.compile(t"{value:.1f}")  # Should format to "3.1" then escape
        assert pattern.match("3.1")

    def test_compile_tstring_conversion_specifiers(self):
        value = "hello"
        pattern = ret.compile(t"{value!r}")  # Should convert to "'hello'" then escape
        assert pattern.match("'hello'")

    def test_compile_tstring_multiple_interpolations(self):
        start = "^"
        filename = "test.txt"
        end = "$"
        pattern = ret.compile(t"{start:safe}{filename}{end:safe}")
        assert pattern.match("test.txt")
        assert not pattern.match("prefix_test.txt")
        assert not pattern.match("test.txt_suffix")

    def test_compile_tstring_verbose_mode(self):
        username = "john_doe"
        domain = "example.com"
        pattern = ret.compile(t"""
            ^                   # Start of string
            {username}          # Username (escaped)
            @                   # Literal @
            {domain}            # Domain (escaped)
            $                   # End of string
        """)
        assert pattern.match("john_doe@example.com")
        assert not pattern.match("john_doe@examplexcom")  # . should be escaped

    def test_compile_tstring_numeric_interpolation(self):
        number = 123
        pattern = ret.compile(t"id_{number}")
        assert pattern.match("id_123")
        assert not pattern.match("id_456")


class TestSafeFormatSpecifier:
    """Test the :safe format specifier that bypasses escaping."""

    def test_safe_regex_patterns(self):
        digit_pattern = r"\d+"
        word_pattern = r"\w+"
        pattern = ret.compile(t"{digit_pattern:safe}-{word_pattern:safe}")
        assert pattern.match("123-abc")
        assert not pattern.match("abc-123")

    def test_safe_vs_escaped_comparison(self):
        regex_chars = ".+"  # Valid regex pattern
        
        # With :safe - should be treated as regex
        safe_pattern = ret.compile(t"{regex_chars:safe}")
        assert safe_pattern.match("abcd")  # .+ matches multiple chars
        
        # Without :safe - should be escaped
        escaped_pattern = ret.compile(t"{regex_chars}")
        assert escaped_pattern.match(".+")  # Literal match
        assert not escaped_pattern.match("abcd")

    def test_safe_with_other_format_specs(self):
        # :safe should work with other format specifiers
        pattern_template = r"\d"
        count = 3
        pattern = ret.compile(t"^{pattern_template:safe}{{{count}}}$")
        # Should create ^\d{3}$
        assert pattern.match("123")
        assert not pattern.match("12")
        assert not pattern.match("1234")


class TestRegexFlags:
    """Test regex flags functionality."""

    def test_custom_flags(self):
        text = "Hello"
        pattern = ret.compile(t"{text}", flags=re.IGNORECASE, verbose=False)
        assert pattern.match("hello")
        assert pattern.match("HELLO")
        assert pattern.match("Hello")

    def test_verbose_flag_override(self):
        # When verbose=True (default), re.VERBOSE should be added
        comment_pattern = "hello # comment"
        pattern = ret.compile(t"{comment_pattern:safe}")
        assert pattern.match("hello")
        
        # When verbose=False, comments should not be ignored
        pattern = ret.compile(t"{comment_pattern:safe}", verbose=False)
        assert not pattern.match("hello")
        assert pattern.match("hello # comment")

    def test_multiline_flag(self):
        text = "test"
        pattern = ret.compile(t"^{text}$", flags=re.MULTILINE, verbose=False)
        assert pattern.match("test")
        assert pattern.search("prefix\ntest\nsuffix")


class TestEdgeCases:
    """Test edge cases and complex scenarios."""

    def test_literal_braces_in_template(self):
        value = "test"
        # Double braces should be literal
        pattern = ret.compile(t"{{{value}}}")  # Should create {test}
        assert pattern.match("{test}")

    def test_complex_regex_with_interpolation(self):
        username = "john.doe"
        domain = "example.com"
        # Complex email validation pattern
        pattern = ret.compile(t"""
            ^                           # Start
            {username}                  # Username (escaped)
            @                           # Literal @
            {domain}                    # Domain (escaped)  
            $                           # End
        """)
        assert pattern.match("john.doe@example.com")
        # Dots should be escaped, so this shouldn't match
        assert not pattern.match("johnXdoe@exampleXcom")

    def test_nested_quantifiers(self):
        char_class = "[a-z]"
        pattern = ret.compile(t"^{char_class:safe}{{2,4}}$")  # ^[a-z]{2,4}$
        assert pattern.match("ab")
        assert pattern.match("abcd")
        assert not pattern.match("a")
        assert not pattern.match("abcde")

    def test_interpolation_with_backslashes(self):
        escape_seq = r"\n"
        pattern = ret.compile(t"line1{escape_seq}")
        # Should match literal \n, not newline
        assert pattern.match("line1\\n")
        assert not pattern.match("line1\n")

    def test_unicode_in_interpolation(self):
        unicode_text = "café"
        pattern = ret.compile(t"{unicode_text}")
        assert pattern.match("café")

    def test_very_long_interpolation(self):
        long_text = "x" * 1000
        pattern = ret.compile(t"{long_text}")
        assert pattern.match("x" * 1000)
        assert not pattern.match("x" * 999)

    def test_multiple_safe_interpolations(self):
        start = "^"
        middle = r"\d+"
        end = "$"
        pattern = ret.compile(t"{start:safe}{middle:safe}{end:safe}")
        assert pattern.match("123")
        assert not pattern.match("abc")
        assert not pattern.match("123a")

    def test_mixed_safe_and_escaped(self):
        boundary = r"\b"
        word = "hello.world"
        pattern = ret.compile(t"{boundary:safe}{word}{boundary:safe}")
        # Should match literal "hello.world" with word boundaries
        assert pattern.search("say hello.world please")
        # Should not match "helloxworld" since . is escaped
        assert not pattern.search("say helloxworld please")


class TestErrorHandling:
    """Test error handling and invalid inputs."""

    def test_invalid_format_spec(self):
        # This should still work - invalid format specs are handled by Python
        with pytest.raises(ValueError):
            value = 42
            ret.compile(t"{value:invalid_spec}")

    def test_compilation_errors(self):
        # Invalid regex should raise re.error
        invalid_pattern = "[invalid"
        with pytest.raises(re.error):
            ret.compile(t"{invalid_pattern:safe}")

    def test_tstring_compilation_errors(self):
        # Invalid regex in t-string should also raise re.error
        with pytest.raises(re.error):
            pattern = "[invalid"
            ret.compile(t"{pattern:safe}")


class TestPropertyBasedTests:
    """Property-based tests using Hypothesis."""

    @given(st.text(min_size=0, max_size=100))
    def test_escaped_text_matches_literally(self, text):
        """Property test: any text interpolated without :safe should match literally."""
        pattern = ret.compile(t"{text}")
        assert pattern.match(text)

    @given(st.text(alphabet=st.characters(blacklist_characters=r"\.+*?[]{}()|^$\r\n\t "), min_size=1, max_size=50))
    def test_safe_text_without_special_chars(self, text):
        """Property test: text without regex special chars should work the same with/without :safe."""
        # Use verbose=False to avoid issues with whitespace characters
        safe_pattern = ret.compile(t"{text:safe}", verbose=False)
        escaped_pattern = ret.compile(t"{text}", verbose=False)
        # Both should match the text
        assert safe_pattern.match(text)
        assert escaped_pattern.match(text)

    @given(st.integers(min_value=0, max_value=999))
    def test_numeric_interpolation(self, number):
        """Property test: numeric interpolation should always work."""
        pattern = ret.compile(t"{number}")
        assert pattern.match(str(number))

    @given(st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=20))
    def test_alphabetic_interpolation(self, text):
        """Property test: alphabetic text should always match literally."""
        pattern = ret.compile(t"{text}")
        assert pattern.match(text)
