from opencmd_tinge.styled import styled, Bold, Red

def test_simple_styling():
    s = styled().space(2).with_(Bold, Red).text("Hello").to_string()
    assert "Hello" in s
    assert "\x1b[" in s

def test_newline_and_indent():
    s = styled().newline().indent_(4).text("Indented").to_string()
    assert "Indented" in s
    assert s.splitlines()[1].startswith("    ")

def test_chained_styles():
    output = (
        styled()
        .newline()
        .space(1)
        .bold("Hello")
        .space()
        .red("World")
        .to_string()
    )
    assert "Hello" in output
    assert "World" in output
