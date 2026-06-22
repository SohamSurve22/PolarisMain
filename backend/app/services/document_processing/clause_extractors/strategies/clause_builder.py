from typing import Any

from .base import ClauseExtractionStrategy
from .list_item_detector import detect_items, classify_item_level
from .sentence_splitter import split_sentences
from ...models import (
    Clause,
    ClauseDocument,
    CleanedDocument,
    DocumentStructure,
    StructuralElement,
    StructuralElementType,
    StructuredDocument,
)


class ClauseBuilderStrategy(ClauseExtractionStrategy):
    operation = "build_clauses"

    def process(self, document: CleanedDocument, structure: StructuredDocument) -> ClauseDocument:
        text = document.text
        doc_structure = structure.structure

        if not text.strip() or not doc_structure.elements:
            return ClauseDocument(
                structured_id=document.extracted_id,
                extraction_strategy="clause_builder",
            )

        elements_in_order = self._elements_in_order(doc_structure)
        clauses: dict[str, Clause] = {}
        root_clause_ids: list[str] = []
        clause_counter = 0
        order_counter = 0
        elem_to_clause: dict[str, str] = {}

        heading_path: list[StructuralElement] = []

        for elem in elements_in_order:
            if elem.type in (StructuralElementType.HEADING, StructuralElementType.SUBHEADING, StructuralElementType.SCHEDULE):
                clause_counter += 1
                order_counter += 1
                clause = self._make_clause_from_heading(
                    elem, clause_counter, order_counter, heading_path, doc_structure, elem_to_clause
                )
                clauses[clause.clause_id] = clause
                elem_to_clause[elem.element_id] = clause.clause_id
                heading_path = self._update_heading_path(heading_path, elem)

            elif elem.type == StructuralElementType.PARAGRAPH:
                gathered = self._extract_clauses_from_paragraph(
                    elem, clause_counter, order_counter, heading_path
                )
                for c in gathered:
                    clause_counter += 1
                    order_counter += 1
                    clauses[c.clause_id] = c

        self._build_clause_tree(clauses)

        root_clause_ids = [
            cid for cid, c in clauses.items()
            if c.parent_clause_id is None
        ]

        return ClauseDocument(
            structured_id=document.extracted_id,
            root_clause_ids=root_clause_ids,
            clauses=clauses,
            extraction_strategy="clause_builder",
        )

    def _make_clause_from_heading(
        self,
        elem: StructuralElement,
        counter: int,
        order: int,
        heading_path: list[StructuralElement],
        doc_structure: DocumentStructure,
        elem_to_clause: dict[str, str],
    ) -> Clause:
        parent_id = None
        if elem.parent_id and elem.parent_id in doc_structure.elements:
            parent = doc_structure.elements[elem.parent_id]
            if parent.type in (StructuralElementType.HEADING, StructuralElementType.SUBHEADING, StructuralElementType.SCHEDULE):
                parent_id = elem_to_clause.get(elem.parent_id)

        section, subsection = self._get_section_context(heading_path, elem)
        char_start = elem.metadata.get("char_start", 0)
        char_end = elem.metadata.get("char_end", 0)

        return Clause(
            clause_id=f"cl_{counter}",
            clause_number=elem.text.split()[0] if elem.text else None,
            heading=section,
            body=elem.text,
            level=max(0, elem.level),
            parent_clause_id=parent_id,
            structural_path=[p.element_id for p in heading_path] + [elem.element_id],
            page_range=None,
            element_ids=[elem.element_id],
            confidence=1.0,
            metadata={
                "char_start": char_start,
                "char_end": char_end,
                "order": order,
                "type": "heading",
                "pattern_type": elem.metadata.get("pattern_type", "unknown"),
            },
        )

    def _extract_clauses_from_paragraph(
        self,
        elem: StructuralElement,
        counter: int,
        order: int,
        heading_path: list[StructuralElement],
    ) -> list[Clause]:
        section, subsection = self._get_section_context(heading_path, elem)
        elem_text = elem.text
        char_start = elem.metadata.get("char_start", 0)
        char_end = elem.metadata.get("char_end", 0)

        items = detect_items(elem_text)

        if items:
            return self._clauses_from_list_items(
                items, elem, counter, order, section, subsection, heading_path, char_start
            )

        sentences = split_sentences(elem_text)

        if len(sentences) > 1:
            return self._clauses_from_sentences(
                sentences, elem, counter, order, section, subsection, heading_path, char_start
            )

        new_counter = counter + 1
        clause = Clause(
            clause_id=f"cl_{new_counter}",
            clause_number=None,
            heading=section,
            body=elem_text,
            level=max(1, len([h for h in heading_path if h.level >= 1])),
            parent_clause_id=None,
            structural_path=[p.element_id for p in heading_path] + [elem.element_id],
            page_range=None,
            element_ids=[elem.element_id],
            confidence=0.9,
            metadata={
                "char_start": char_start,
                "char_end": char_end,
                "order": order + 1,
                "type": "paragraph",
            },
        )
        return [clause]

    def _clauses_from_list_items(
        self,
        items: list,
        elem: StructuralElement,
        counter: int,
        order: int,
        section: str | None,
        subsection: str | None,
        heading_path: list[StructuralElement],
        base_char_start: int,
    ) -> list[Clause]:
        clauses = []
        for idx, item in enumerate(items):
            new_counter = counter + 1 + idx
            new_order = order + 1 + idx
            level = classify_item_level(item.marker_type)
            char_start = base_char_start + item.start
            char_end = base_char_start + item.end
            clause = Clause(
                clause_id=f"cl_{new_counter}",
                clause_number=item.marker,
                heading=section,
                body=item.text,
                level=level,
                parent_clause_id=None,
                structural_path=[p.element_id for p in heading_path] + [elem.element_id],
                page_range=None,
                element_ids=[elem.element_id],
                confidence=0.95,
                metadata={
                    "char_start": char_start,
                    "char_end": char_end,
                    "order": new_order,
                    "marker_type": item.marker_type,
                    "type": "list_item",
                },
            )
            clauses.append(clause)
        return clauses

    def _clauses_from_sentences(
        self,
        sentences: list[str],
        elem: StructuralElement,
        counter: int,
        order: int,
        section: str | None,
        subsection: str | None,
        heading_path: list[StructuralElement],
        base_char_start: int,
    ) -> list[Clause]:
        clauses = []
        for idx, sentence in enumerate(sentences):
            new_counter = counter + 1 + idx
            new_order = order + 1 + idx
            sentence_start = self._find_sentence_offset(elem.text, sentence, idx, sentences)
            char_start = base_char_start + sentence_start
            char_end = base_char_start + sentence_start + len(sentence)
            clause = Clause(
                clause_id=f"cl_{new_counter}",
                clause_number=None,
                heading=section,
                body=sentence,
                level=max(1, len([h for h in heading_path if h.level >= 1])),
                parent_clause_id=None,
                structural_path=[p.element_id for p in heading_path] + [elem.element_id],
                page_range=None,
                element_ids=[elem.element_id],
                confidence=0.7,
                metadata={
                    "char_start": char_start,
                    "char_end": char_end,
                    "order": new_order,
                    "sentence_index": idx,
                    "type": "sentence",
                },
            )
            clauses.append(clause)
        return clauses

    def _find_sentence_offset(self, text: str, sentence: str, idx: int, all_sentences: list[str]) -> int:
        pos = 0
        for j in range(idx):
            pos += len(all_sentences[j]) + 1
        return pos

    def _update_heading_path(
        self, heading_path: list[StructuralElement], new_heading: StructuralElement
    ) -> list[StructuralElement]:
        path = list(heading_path)
        while path and path[-1].level >= new_heading.level:
            path.pop()
        path.append(new_heading)
        return path

    def _get_section_context(
        self, heading_path: list[StructuralElement], elem: StructuralElement
    ) -> tuple[str | None, str | None]:
        if not heading_path:
            return None, None
        section = None
        subsection = None
        for h in heading_path:
            if h.level <= 1:
                section = h.text
            elif h.level == 2:
                subsection = h.text
        return section, subsection

    def _build_clause_tree(self, clauses: dict[str, Clause]) -> None:
        sorted_clauses = sorted(
            clauses.items(),
            key=lambda x: (x[1].metadata.get("order", 0), x[1].metadata.get("char_start", 0)),
        )

        heading_stack: list[str] = []
        body_parent: str | None = None

        for cid, clause in sorted_clauses:
            ctype = clause.metadata.get("type", "")
            is_heading = ctype == "heading"

            if is_heading:
                level = clause.level
                while heading_stack and clauses[heading_stack[-1]].level >= level:
                    heading_stack.pop()

                if heading_stack:
                    parent_id = heading_stack[-1]
                    clause.parent_clause_id = parent_id
                    if parent_id in clauses:
                        if cid not in clauses[parent_id].child_clause_ids:
                            clauses[parent_id].child_clause_ids.append(cid)

                heading_stack.append(cid)
                body_parent = cid

            else:
                if heading_stack:
                    parent_id = heading_stack[-1]
                    clause.parent_clause_id = parent_id
                    if parent_id in clauses:
                        if cid not in clauses[parent_id].child_clause_ids:
                            clauses[parent_id].child_clause_ids.append(cid)

    def _elements_in_order(self, structure: DocumentStructure) -> list[StructuralElement]:
        elements = list(structure.elements.values())
        elements.sort(key=lambda e: (
            e.metadata.get("char_start", 0),
            e.metadata.get("line_number", 0),
        ))
        return elements
