from backend.app.services.document_processing.clause_extractors.strategies.list_item_detector import (
    detect_items,
    classify_item_level,
)


class TestListItemDetector:
    def test_detects_alpha_lower(self):
        text = "(a) Name and contact information\n(b) Financial information\n(c) Usage data\n"
        items = detect_items(text)
        assert len(items) == 3
        assert items[0].marker == "(a)"
        assert items[0].marker_type == "alpha_lower"
        assert items[0].text == "Name and contact information"
        assert items[1].text == "Financial information"
        assert items[2].text == "Usage data"

    def test_detects_alpha_upper(self):
        text = "(A) Option one\n(B) Option two\n"
        items = detect_items(text)
        assert len(items) == 2
        assert items[0].marker_type == "alpha_upper"

    def test_detects_decimal_paren(self):
        text = "(1) First item\n(2) Second item\n(3) Third item\n"
        items = detect_items(text)
        assert len(items) == 3
        assert items[0].marker_type == "decimal_paren"

    def test_detects_decimal_dot(self):
        text = "1. First item\n2. Second item\n3. Third item\n"
        items = detect_items(text)
        assert len(items) == 3
        assert items[0].marker_type == "decimal_dot"

    def test_detects_bullets(self):
        text = "- Item one\n- Item two\n* Item three\n• Item four\n"
        items = detect_items(text)
        assert len(items) == 4
        for item in items:
            assert item.marker_type == "bullet"

    def test_detects_roman_lower(self):
        text = "(i) First sub-item\n(ii) Second sub-item\n(iii) Third sub-item\n"
        items = detect_items(text)
        assert len(items) == 3
        assert items[0].marker_type == "roman_lower"

    def test_detects_roman_upper(self):
        text = "(I) First section\n(II) Second section\n(III) Third section\n"
        items = detect_items(text)
        assert len(items) == 3
        assert items[0].marker_type == "roman_upper"

    def test_empty_text(self):
        assert detect_items("") == []
        assert detect_items("   ") == []

    def test_plain_text_no_items(self):
        text = "This is just a regular paragraph with no list items."
        items = detect_items(text)
        assert len(items) == 0

    def test_mixed_items(self):
        text = "(a) First\n(b) Second\n(c) Third\n"
        items = detect_items(text)
        assert len(items) == 3

    def test_tracks_char_positions(self):
        text = "(a) First\n(b) Second\n"
        items = detect_items(text)
        assert items[0].start == 0
        assert items[0].end == len("(a) First")
        assert items[1].start == len("(a) First\n")
        assert items[1].end == len("(a) First\n(b) Second")

    def test_classify_levels(self):
        assert classify_item_level("bullet") == 1
        assert classify_item_level("decimal_dot") == 1
        assert classify_item_level("alpha_lower") == 2
        assert classify_item_level("alpha_upper") == 2
        assert classify_item_level("roman_lower") == 3
        assert classify_item_level("roman_upper") == 3
        assert classify_item_level("decimal_paren") == 3

    def test_legal_list_nested(self):
        text = (
            "(a) Personal data\n"
            "(i) Name\n"
            "(ii) Address\n"
            "(b) Sensitive data\n"
            "(i) Health info\n"
            "(ii) Biometrics\n"
        )
        items = detect_items(text)
        assert len(items) == 6

    def test_bullet_with_line_text(self):
        text = "- Item with multiple words in it\n- Another item here\n"
        items = detect_items(text)
        assert len(items) == 2
