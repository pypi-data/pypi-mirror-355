from textminer.detector import detect_language

def test_detect_language():
    text = "This is an English sentence."
    lang = detect_language(text)
    assert lang == "en"
