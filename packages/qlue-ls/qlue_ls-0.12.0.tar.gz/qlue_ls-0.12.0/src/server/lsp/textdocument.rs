use super::TextDocumentContentChangeEvent;
use log::error;
use serde::{Deserialize, Serialize};
use std::fmt::{self, Display};

pub type DocumentUri = String;

#[derive(Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct TextDocumentItem {
    pub uri: DocumentUri,
    language_id: String,
    version: u32,
    pub text: String,
}

impl TextDocumentItem {
    pub(crate) fn new(uri: &str, text: &str) -> TextDocumentItem {
        TextDocumentItem {
            uri: uri.to_string(),
            text: text.to_string(),
            language_id: "sparql".to_string(),
            version: 0,
        }
    }

    fn apply_text_edit(&mut self, text_edit: TextEdit) {
        match text_edit.range.to_byte_index_range(&self.text) {
            Some(range) => {
                self.text.replace_range(range, &text_edit.new_text);
            }
            None => {
                error!("Received textdocument/didChange notification with a TextEdit thats out ouf bounds:\nedit: {}\ndocument range: {}",text_edit, self.get_full_range());
            }
        };

        // WARNING: Always keep one newline at the end of a document to stay POSIX conform!
        // https://pubs.opengroup.org/onlinepubs/9699919799/basedefs/V1_chap03.html#tag_03_206
        match self.text.chars().next_back() {
            Some('\n') => {}
            _ => self.text.push('\n'),
        };
    }

    pub(crate) fn apply_text_edits(&mut self, text_edits: Vec<TextEdit>) {
        text_edits
            .into_iter()
            .for_each(|text_edit| self.apply_text_edit(text_edit));
    }

    pub fn get_full_range(&self) -> Range {
        if self.text.is_empty() {
            return Range::new(0, 0, 0, 0);
        }
        let line_count = self.text.lines().count();
        let last_char = self
            .text
            .chars()
            .next_back()
            .expect("At least one character has to be in the text");
        match last_char {
            '\n' => Range::new(0, 0, line_count as u32, 0),
            _ => {
                let last_line = self
                    .text
                    .lines()
                    .next_back()
                    .expect("At least one line hat to be in the text");
                Range::new(0, 0, (line_count - 1) as u32, last_line.len() as u32)
            }
        }
    }

    pub(crate) fn get_range(&self, range: &Range) -> Option<&str> {
        self.text.get(range.to_byte_index_range(&self.text)?)
    }

    pub(crate) fn increase_version(&mut self) {
        self.version += 1;
    }

    pub(crate) fn version(&self) -> u32 {
        self.version
    }
}

#[derive(Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct VersionedTextDocumentIdentifier {
    #[serde(flatten)]
    pub base: TextDocumentIdentifier,
    version: u32,
}

#[derive(Debug, Serialize, Deserialize, PartialEq)]
pub struct TextDocumentIdentifier {
    pub uri: Uri,
}

type Uri = String;

#[derive(Debug, Serialize, Deserialize, PartialEq, Eq, Hash, Clone, Copy)]
pub struct Position {
    pub line: u32,
    pub character: u32,
}

// NOTE: By default based on a UTF-16 string representation!
impl Position {
    pub fn new(line: u32, character: u32) -> Self {
        Self { line, character }
    }

    /// Convert UTF-8 byte offset in a text into UTF-16 based Position
    ///
    /// Returs None if:
    /// - offset is outside the given str
    /// - offset is not on the border of a UTF-8 codepoint
    pub fn from_byte_index(offset: usize, text: &str) -> Option<Self> {
        let mut offset_count = 0;
        let mut position = Self::new(0, 0);
        for char in text.chars() {
            if offset_count >= offset {
                break;
            }
            // BUG: Is this platform independent?
            // Or do i need to check of "\r\n" aswell?
            if char == '\n' {
                position.line += 1;
                position.character = 0;
            } else {
                position.character += char.len_utf16() as u32;
            }
            offset_count += char.len_utf8();
        }
        // NOTE: the byte offset MUST be at the start or end of a UTF-8 char.
        // https://datatracker.ietf.org/doc/html/rfc2119
        (offset_count == offset).then_some(position)
    }

    /// Converts a UTF-16 based position within a string to a byte index.
    ///
    /// # Arguments
    ///
    /// * `text` - A reference to the string in which the position is calculated.
    ///
    /// # Returns
    ///
    /// * `Option<usize>` - The byte index corresponding to the UTF-16 position
    ///   if the position is valid. Returns `None` if the position is out of bounds
    ///   or if the conversion cannot be performed.
    ///
    /// # Details
    ///
    /// This function takes into account the difference between UTF-8 and UTF-16
    /// representations. In UTF-16, some characters, such as those outside the
    /// Basic Multilingual Plane (e.g., emoji or certain CJK characters), are
    /// represented as surrogate pairs, which occupy two 16-bit code units.
    /// In contrast, UTF-8 uses a variable-length encoding where these same
    /// characters can take up to four bytes.
    ///
    /// The function ensures that the given UTF-16 position is correctly
    /// mapped to its corresponding byte index in the UTF-8 encoded string,
    /// preserving the integrity of multi-byte characters.
    ///
    /// # Caveats
    ///
    /// * If `text` contains invalid UTF-8 sequences, the behavior of this function
    ///   is undefined.
    /// * Ensure the provided UTF-16 position aligns with the logical structure of
    ///   the string.
    pub fn byte_index(&self, text: &str) -> Option<usize> {
        if self.line == 0 && self.character == 0 && text.is_empty() {
            return Some(0);
        }
        let mut byte_index: usize = 0;
        let mut lines = text.lines();
        for _i in 0..self.line {
            byte_index += lines.next()?.len() + 1;
        }
        let mut utf16_index: usize = 0;
        let last_line = lines.next().unwrap_or("");
        let mut chars = last_line.chars();
        while utf16_index < self.character as usize {
            let char = chars.next()?;
            byte_index += char.len_utf8();
            utf16_index += char.len_utf16();
        }
        Some(byte_index)
    }
}

impl PartialOrd for Position {
    fn partial_cmp(&self, other: &Self) -> Option<std::cmp::Ordering> {
        Some(self.cmp(other))
    }
}

impl Ord for Position {
    fn cmp(&self, other: &Self) -> std::cmp::Ordering {
        match self.line.cmp(&other.line) {
            std::cmp::Ordering::Equal => self.character.cmp(&other.character),
            x => x,
        }
    }
}

impl fmt::Display for Position {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "{:0>2}:{:0>2}", self.line, self.character)
    }
}

#[derive(Debug, Serialize, Deserialize, PartialEq, Eq, Hash, Clone)]
// https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#range
// NOTE: Positions are zero based.
// NOTE: The end position is exclusive.
// NOTE: To include line ending character(s), set end position to the start of next line.
/// LSP text range (UTF-16 based)
pub struct Range {
    pub start: Position,
    pub end: Position,
}

impl Range {
    pub fn new(start_line: u32, start_character: u32, end_line: u32, end_character: u32) -> Self {
        Self {
            start: Position::new(start_line, start_character),
            end: Position::new(end_line, end_character),
        }
    }

    pub fn to_byte_index_range(&self, text: &str) -> Option<std::ops::Range<usize>> {
        match (self.start.byte_index(text), self.end.byte_index(text)) {
            (Some(from), Some(to)) => Some(from..to),
            _ => None,
        }
    }

    #[cfg(test)]
    pub(crate) fn overlaps(&self, other: &Range) -> bool {
        self.start < other.end && self.end > other.start
    }

    fn is_empty(&self) -> bool {
        self.start == self.end
    }

    pub(crate) fn from_byte_offset_range(range: text_size::TextRange, text: &str) -> Option<Range> {
        Some(Range {
            start: Position::from_byte_index(range.start().into(), text)?,
            end: Position::from_byte_index(range.end().into(), text)?,
        })
    }
}

impl Display for Range {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(&format!("{}-{}", self.start, self.end))
    }
}

#[derive(Debug, Serialize, Deserialize, PartialEq, Clone)]
#[serde(rename_all = "camelCase")]
pub struct TextEdit {
    pub range: Range,
    pub new_text: String,
}

impl TextEdit {
    pub fn new(range: Range, new_text: &str) -> Self {
        Self {
            range,
            new_text: new_text.to_string(),
        }
    }

    #[cfg(test)]
    pub fn overlaps(&self, other: &TextEdit) -> bool {
        self.range.overlaps(&other.range)
    }

    pub fn from_text_document_content_change_event(
        change_event: TextDocumentContentChangeEvent,
    ) -> Self {
        // TODO: handle option: change events has no range (whole document got send)
        Self {
            range: change_event.range,
            new_text: change_event.text,
        }
    }

    pub(crate) fn is_empty(&self) -> bool {
        self.range.is_empty() && self.new_text.is_empty()
    }
}

impl Display for TextEdit {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(&format!(
            "{} \"{}\"",
            self.range,
            self.new_text.replace(" ", "␣").replace("\n", "\\n")
        ))
    }
}

#[cfg(test)]
mod tests {

    use indoc::indoc;

    use crate::server::lsp::textdocument::{Position, Range, TextEdit};

    use super::TextDocumentItem;

    #[test]
    fn byte_index_to_position() {
        let s = "aä😀\n123ä\n";
        assert_eq!(
            Position::from_byte_index(0, s).unwrap(),
            Position::new(0, 0)
        );

        assert_eq!(
            Position::from_byte_index(1, s).unwrap(),
            Position::new(0, 1)
        );
        assert_eq!(
            Position::from_byte_index(3, s).unwrap(),
            Position::new(0, 2)
        );
        assert_eq!(
            Position::from_byte_index(7, s).unwrap(),
            Position::new(0, 4)
        );
        assert_eq!(
            Position::from_byte_index(8, s).unwrap(),
            Position::new(1, 0)
        );
        assert_eq!(
            Position::from_byte_index(9, s).unwrap(),
            Position::new(1, 1)
        );
        assert_eq!(
            Position::from_byte_index(10, s).unwrap(),
            Position::new(1, 2)
        );
        assert_eq!(
            Position::from_byte_index(13, s).unwrap(),
            Position::new(1, 4)
        );
        assert_eq!(
            Position::from_byte_index(14, s).unwrap(),
            Position::new(2, 0)
        );
        assert_eq!(Position::from_byte_index(15, s), None);
        assert_eq!(Position::from_byte_index(2, s), None);
    }

    // #[test]
    // fn translate_utf8_utf16() {
    //     let s = "aä😀\n".to_string();
    //     let mut p0 = Position::new(0, 0);
    //     p0.translate_to_utf16_encoding(&s).unwrap();
    //     assert_eq!(p0, Position::new(0, 0));
    //
    //     let mut p1 = Position::new(0, 1);
    //     p1.translate_to_utf16_encoding(&s).unwrap();
    //     assert_eq!(p1, Position::new(0, 1));
    //
    //     let mut p2 = Position::new(0, 3);
    //     p2.translate_to_utf16_encoding(&s).unwrap();
    //     assert_eq!(p2, Position::new(0, 2));
    //
    //     let mut p3 = Position::new(0, 7);
    //     p3.translate_to_utf16_encoding(&s).unwrap();
    //     assert_eq!(p3, Position::new(0, 4));
    //
    //     let mut p4 = Position::new(1, 0);
    //     p4.translate_to_utf16_encoding(&s).unwrap();
    //     assert_eq!(p4, Position::new(1, 0));
    // }

    #[test]
    fn full_range_empty() {
        let document: TextDocumentItem = TextDocumentItem {
            uri: "file:///dings".to_string(),
            language_id: "foo".to_string(),
            version: 1,
            text: "".to_string(),
        };
        assert_eq!(document.get_full_range(), Range::new(0, 0, 0, 0));
    }

    #[test]
    fn full_range_trailing_newline() {
        let document: TextDocumentItem = TextDocumentItem {
            uri: "file:///dings".to_string(),
            language_id: "foo".to_string(),
            version: 1,
            text: "abc\nde\n".to_string(),
        };
        assert_eq!(document.get_full_range(), Range::new(0, 0, 2, 0));
    }

    #[test]
    fn full_range_no_trailing_newline() {
        let document: TextDocumentItem = TextDocumentItem {
            uri: "file:///dings".to_string(),
            language_id: "foo".to_string(),
            version: 1,
            text: "abc\nde".to_string(),
        };
        assert_eq!(document.get_full_range(), Range::new(0, 0, 1, 2));
    }

    #[test]
    fn changes() {
        let mut document: TextDocumentItem = TextDocumentItem {
            uri: "file:///dings".to_string(),
            language_id: "foo".to_string(),
            version: 1,
            text: "".to_string(),
        };
        assert_eq!(document.text, "");
        document.apply_text_edit(TextEdit {
            new_text: "S".to_string(),
            range: Range::new(0, 0, 0, 0),
        });
        assert_eq!(document.text, "S\n");
        document.apply_text_edits(vec![
            TextEdit {
                new_text: "E".to_string(),
                range: Range::new(0, 1, 0, 1),
            },
            TextEdit {
                new_text: "L".to_string(),
                range: Range::new(0, 2, 0, 2),
            },
            TextEdit {
                new_text: "E".to_string(),
                range: Range::new(0, 3, 0, 3),
            },
            TextEdit {
                new_text: "C".to_string(),
                range: Range::new(0, 4, 0, 4),
            },
            TextEdit {
                new_text: "T".to_string(),
                range: Range::new(0, 5, 0, 5),
            },
            TextEdit {
                new_text: " ".to_string(),
                range: Range::new(0, 6, 0, 6),
            },
            TextEdit {
                new_text: "* WHERE{\n  ?s ?p ?o\n}".to_string(),
                range: Range::new(0, 7, 0, 7),
            },
        ]);
        assert_eq!(document.text, "SELECT * WHERE{\n  ?s ?p ?o\n}\n");
        document.apply_text_edits(vec![TextEdit {
            new_text: "select".to_string(),
            range: Range::new(0, 0, 0, 6),
        }]);
        assert_eq!(document.text, "select * WHERE{\n  ?s ?p ?o\n}\n");
        document.apply_text_edits(vec![
            TextEdit {
                new_text: "".to_string(),
                range: Range::new(1, 10, 2, 0),
            },
            TextEdit {
                new_text: "".to_string(),
                range: Range::new(0, 15, 1, 1),
            },
        ]);
        assert_eq!(document.text, "select * WHERE{ ?s ?p ?o}\n");
        document.apply_text_edits(vec![
            TextEdit {
                new_text: "ns1:dings".to_string(),
                range: Range::new(0, 16, 0, 18),
            },
            TextEdit {
                new_text: "PREFIX ns1: <iri>\n".to_string(),
                range: Range::new(0, 0, 0, 0),
            },
        ]);
        assert_eq!(
            document.text,
            "PREFIX ns1: <iri>\nselect * WHERE{ ns1:dings ?p ?o}\n"
        );
        document.apply_text_edits(vec![
            TextEdit {
                new_text: "".to_string(),
                range: Range::new(1, 10, 1, 32),
            },
            TextEdit {
                new_text: "".to_string(),
                range: Range::new(0, 0, 1, 10),
            },
        ]);
        // Whats goning on here
        assert_eq!(document.text, "\n");
    }

    #[test]
    fn apply_change() {
        let mut document: TextDocumentItem = TextDocumentItem {
            uri: "file:///dings".to_string(),
            language_id: "foo".to_string(),
            version: 1,
            text: "\n".to_string(),
        };
        let change = TextEdit {
            new_text: "dings".to_string(),
            range: Range::new(0, 0, 0, 0),
        };
        document.apply_text_edit(change);
        assert_eq!(document.text, "dings\n");
    }

    #[test]
    fn position_to_byte_index() {
        let text = "aä�𐀀".to_string();
        assert_eq!(Position::new(0, 0).byte_index(&text), Some(0));
        assert_eq!(Position::new(0, 1).byte_index(&text), Some(1));
        assert_eq!(Position::new(0, 2).byte_index(&text), Some(3));
        assert_eq!(Position::new(0, 3).byte_index(&text), Some(6));
        assert_eq!(Position::new(0, 5).byte_index(&text), Some(10));
        assert_eq!(Position::new(1, 0).byte_index(&text), Some(11));
        assert_eq!(Position::new(0, 6).byte_index(&text), None);
        assert_eq!(Position::new(2, 0).byte_index(&text), None);
    }

    #[test]
    fn range_to_byte_index_range() {
        let text = indoc!(
            "12345
             12345
             12345
             "
        )
        .to_string();
        assert_eq!(
            Range::new(0, 5, 1, 1).to_byte_index_range(&text),
            Some(5..7)
        );
        let range = Range::new(1, 0, 2, 0);
        let pos = range.start;
        assert_eq!(pos.byte_index(&text), Some(6));
        assert_eq!(
            Range::new(1, 0, 2, 0).to_byte_index_range(&text),
            Some(6..12)
        );
        assert_eq!(
            Range::new(0, 0, 3, 0).to_byte_index_range(&text),
            Some(0..18)
        );

        assert_eq!(Range::new(0, 0, 3, 1).to_byte_index_range(&text), None);
        assert_eq!(Range::new(0, 0, 1, 10).to_byte_index_range(&text), None);
    }

    #[test]
    fn no_changes() {
        let changes: Vec<TextEdit> = vec![];
        let mut document: TextDocumentItem = TextDocumentItem {
            uri: "file:///dings".to_string(),
            language_id: "foo".to_string(),
            version: 1,
            text: "hello world\n".to_string(),
        };
        document.apply_text_edits(changes);
        assert_eq!(document.text, "hello world\n");
    }

    #[test]
    fn overlap() {
        let a = Range::new(1, 1, 2, 2); //      >----<
        let b = Range::new(1, 10, 2, 5); //        >----<
        let c = Range::new(0, 0, 1, 10); //   >--<
        let d = Range::new(1, 10, 2, 6); //         >-<
        let e = Range::new(2, 6, 2, 7); //                >--<

        assert!(a.overlaps(&b));
        assert!(a.overlaps(&c));
        assert!(a.overlaps(&d));
        assert!(!a.overlaps(&e));

        assert!(b.overlaps(&a));
        assert!(!b.overlaps(&c));
        assert!(b.overlaps(&d));
        assert!(!b.overlaps(&e));

        assert!(c.overlaps(&a));
        assert!(!c.overlaps(&b));
        assert!(!c.overlaps(&d));
        assert!(!c.overlaps(&e));

        assert!(d.overlaps(&a));
        assert!(d.overlaps(&b));
        assert!(!d.overlaps(&c));
        assert!(!d.overlaps(&e));

        assert!(!e.overlaps(&a));
        assert!(!e.overlaps(&b));
        assert!(!e.overlaps(&c));
        assert!(!e.overlaps(&d));
    }
}
