from .base import StructureDetectionStrategy
from ...models import CleanedDocument, DocumentStructure, StructuralElement, StructuralElementType


class HierarchyBuildingStrategy(StructureDetectionStrategy):
    operation = "build_hierarchy"

    def process(self, document: CleanedDocument, structure: DocumentStructure | None = None) -> DocumentStructure:
        text = document.text
        if not text.strip():
            return DocumentStructure(detection_strategy="hierarchy_building")

        if structure is None:
            structure = DocumentStructure(detection_strategy="hierarchy_building")

        headings = self._sorted_headings(structure)
        if not headings:
            return self._build_flat_structure(text, structure)

        elements: dict[str, StructuralElement] = {}
        root_ids: list[str] = []
        element_counter = len(structure.elements)
        heading_idx = 0
        char_pos = 0
        lines = text.split("\n")
        current_line = 0
        char_offset = 0
        line_offsets: list[int] = []
        for line in lines:
            line_offsets.append(char_offset)
            char_offset += len(line) + 1

        while heading_idx < len(headings):
            h = headings[heading_idx]
            h_start = h.metadata.get("char_start", 0)
            h_end = h.metadata.get("char_end", 0)

            if h_start > char_pos:
                para_text = text[char_pos:h_start].strip()
                if para_text:
                    element_counter += 1
                    para = StructuralElement(
                        element_id=f"p_{element_counter}",
                        type=StructuralElementType.PARAGRAPH,
                        text=para_text,
                        level=0,
                        metadata={
                            "char_start": char_pos,
                            "char_end": h_start,
                            "line_number": self._find_line(para_text, line_offsets, lines),
                        },
                    )
                    elements[para.element_id] = para

            elements[h.element_id] = h
            element_counter = max(element_counter, int(h.element_id.split("_")[1]))
            char_pos = h_end
            heading_idx += 1

        remaining = text[char_pos:].strip()
        if remaining:
            element_counter += 1
            para = StructuralElement(
                element_id=f"p_{element_counter}",
                type=StructuralElementType.PARAGRAPH,
                text=remaining,
                level=0,
                metadata={
                    "char_start": char_pos,
                    "char_end": len(text),
                    "line_number": self._find_line(remaining, line_offsets, lines),
                },
            )
            elements[para.element_id] = para

        root_ids = self._build_tree(elements)

        return DocumentStructure(
            elements=elements,
            root_element_ids=root_ids,
            toc=structure.toc,
            detection_strategy="hierarchy_building",
        )

    def _find_line(self, text_fragment: str, offsets: list[int], lines: list[str]) -> int:
        for i, offset in enumerate(offsets):
            if i < len(lines) and offset >= 0 and text_fragment.startswith(lines[i].strip()[:40]):
                return i + 1
        return 1

    def _sorted_headings(self, structure: DocumentStructure) -> list[StructuralElement]:
        headings = [
            e for e in structure.elements.values()
            if e.type in (StructuralElementType.HEADING, StructuralElementType.SUBHEADING, StructuralElementType.SCHEDULE)
        ]
        headings.sort(key=lambda e: e.metadata.get("char_start", 0))
        return headings

    def _build_flat_structure(self, text: str, structure: DocumentStructure) -> DocumentStructure:
        elements: dict[str, StructuralElement] = dict(structure.elements)
        lines = text.strip().split("\n")
        char_offset = 0
        element_counter = len(elements)
        root_ids: list[str] = list(structure.root_element_ids)

        for i, line in enumerate(lines):
            stripped = line.strip()
            line_len = len(line)
            if not stripped:
                char_offset += line_len + 1
                continue

            element_counter += 1
            para = StructuralElement(
                element_id=f"p_{element_counter}",
                type=StructuralElementType.PARAGRAPH,
                text=stripped,
                level=0,
                metadata={
                    "char_start": char_offset,
                    "char_end": char_offset + line_len,
                    "line_number": i + 1,
                },
            )
            elements[para.element_id] = para
            root_ids.append(para.element_id)
            char_offset += line_len + 1

        return DocumentStructure(
            elements=elements,
            root_element_ids=root_ids,
            toc=structure.toc,
            detection_strategy="hierarchy_building_flat",
        )

    def _build_tree(self, elements: dict[str, StructuralElement]) -> list[str]:
        headings = sorted(
            [(eid, e) for eid, e in elements.items() if e.type != StructuralElementType.PARAGRAPH],
            key=lambda x: x[1].metadata.get("char_start", 0),
        )

        stack: list[tuple[str, int]] = []
        root_ids: list[str] = []

        for eid, elem in headings:
            level = elem.level
            while stack and stack[-1][1] >= level:
                stack.pop()
            if stack:
                parent_id = stack[-1][0]
                elem.parent_id = parent_id
                if parent_id in elements:
                    if eid not in elements[parent_id].child_ids:
                        elements[parent_id].child_ids.append(eid)
            else:
                root_ids.append(eid)
            stack.append((eid, level))

        orphan_paragraphs = [
            eid for eid, e in elements.items()
            if e.type == StructuralElementType.PARAGRAPH
               and e.parent_id is None
               and eid not in root_ids
        ]
        for eid in orphan_paragraphs:
            elem = elements[eid]
            elem_start = elem.metadata.get("char_start", 0)
            inserted = False
            for head_id, head_elem in headings:
                head_end = head_elem.metadata.get("char_end", 0)
                if elem_start < head_elem.metadata.get("char_start", 0):
                    continue
                if head_end <= elem_start:
                    if head_elem.parent_id or head_id in root_ids:
                        elements[head_id].child_ids.append(eid)
                        elem.parent_id = head_id
                        inserted = True
                        break
            if not inserted:
                if root_ids:
                    last_root = root_ids[-1]
                    elements[last_root].child_ids.append(eid)
                    elem.parent_id = last_root
                else:
                    root_ids.append(eid)

        return root_ids
