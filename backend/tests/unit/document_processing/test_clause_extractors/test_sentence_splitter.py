from backend.app.services.document_processing.clause_extractors.strategies.sentence_splitter import (
    split_sentences,
)


class TestSentenceSplitter:
    def test_splits_simple_sentences(self):
        text = "This is the first sentence. This is the second sentence."
        result = split_sentences(text)
        assert len(result) == 2
        assert result[0] == "This is the first sentence."
        assert result[1] == "This is the second sentence."

    def test_splits_on_question_mark(self):
        text = "Is this correct? Yes it is."
        result = split_sentences(text)
        assert len(result) == 2
        assert result[0] == "Is this correct?"
        assert result[1] == "Yes it is."

    def test_splits_on_exclamation(self):
        text = "Stop! Do not proceed."
        result = split_sentences(text)
        assert len(result) == 2

    def test_handles_abbreviations(self):
        text = "Dr. Smith is here. He will see you now."
        result = split_sentences(text)
        assert len(result) == 2
        assert result[0] == "Dr. Smith is here."
        assert result[1] == "He will see you now."

    def test_handles_legal_abbreviations(self):
        text = "The company (e.g., Acme Corp.) is liable. It must pay damages."
        result = split_sentences(text)
        assert len(result) == 2

    def test_handles_etc(self):
        text = "We collect name, address, email, etc. This data is used for processing."
        result = split_sentences(text)
        assert len(result) == 2
        assert result[0] == "We collect name, address, email, etc."
        assert result[1] == "This data is used for processing."

    def test_handles_inc_and_ltd(self):
        text = "Acme Inc. is the data controller. Its address is 123 Main St."
        result = split_sentences(text)
        assert len(result) == 2

    def test_handles_single_sentence(self):
        text = "This is a single sentence with no boundaries."
        result = split_sentences(text)
        assert len(result) == 1

    def test_empty_text(self):
        assert split_sentences("") == []
        assert split_sentences("   ") == []

    def test_no_period(self):
        text = "This is a sentence without a period"
        result = split_sentences(text)
        assert len(result) == 1

    def test_multi_sentence_with_trailing_text(self):
        text = "Sentence one. Sentence two. Sentence three."
        result = split_sentences(text)
        assert len(result) == 3

    def test_handles_vs_abbreviation(self):
        text = "The case of Brown v. Board of Education. It was landmark."
        result = split_sentences(text)
        assert len(result) == 2

    def test_single_letter_initial(self):
        text = "J. Smith testified. The court agreed."
        result = split_sentences(text)
        assert len(result) == 2
        assert result[0] == "J. Smith testified."

    def test_handles_numbers_with_dots(self):
        text = "See Section 1.2 for details. The policy applies."
        result = split_sentences(text)
        assert len(result) == 2
        assert result[0] == "See Section 1.2 for details."

    def test_multiple_sentences_in_paragraph(self):
        text = (
            "We collect personal data. We use it for service delivery. "
            "We share it with third parties. You have the right to access."
        )
        result = split_sentences(text)
        assert len(result) == 4

    def test_preserves_quotes(self):
        text = 'The CEO said "We are committed." The policy reflects this.'
        result = split_sentences(text)
        assert len(result) == 2
        assert result[0] == 'The CEO said "We are committed."'
        assert result[1] == "The policy reflects this."

    def test_no_false_split_on_ellipsis(self):
        text = "The list includes items... It continues."
        result = split_sentences(text)
        assert len(result) == 2

    def test_legal_text_with_citations(self):
        text = "Per DPDP Act 2023 s. 4(2). Data fiduciaries must obtain consent."
        result = split_sentences(text)
        assert len(result) == 2
        assert "Data fiduciaries" in result[1]
