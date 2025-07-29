
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer


def summarize_text(text: str, ratio=0.2, language='english'):

    parser = PlaintextParser.from_string(text, Tokenizer(language))
    summarizer = LsaSummarizer()
    sentence_count = max(1, int(len(parser.document.sentences) * ratio))
    summary = summarizer(parser.document, sentence_count)
    return ' '.join(str(sentence) for sentence in summary)
