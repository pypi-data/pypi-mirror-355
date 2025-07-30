from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lex_rank import LexRankSummarizer
from nltk import sent_tokenize
import nltk

nltk.download('punkt')

def summarize_text(text: str, num_sentences: int = 2) -> str:
    return summarize_limited(text, num_sentences=num_sentences)

def summarize_limited(text: str, num_sentences: int = 2, max_input_sents: int = 100) -> str:
    all_sentences = sent_tokenize(text)
    chunk = " ".join(all_sentences[:max_input_sents])
    try:
        parser = PlaintextParser.from_string(chunk, Tokenizer("english"))
        summarizer = LexRankSummarizer()
        summary = summarizer(parser.document, num_sentences)
        return " ".join(str(s) for s in summary)
    except Exception as e:
        return f"요약 실패: {e}"