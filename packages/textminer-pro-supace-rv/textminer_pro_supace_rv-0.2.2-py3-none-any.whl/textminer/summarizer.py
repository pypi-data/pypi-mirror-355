from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lex_rank import LexRankSummarizer
import nltk

# NLTK punkt tokenizer 다운로드 (최초 1회)
nltk.download('punkt')

def summarize_text(text: str, num_sentences: int = 2) -> str:
    try:
        if len(text.strip().split()) < 30:
            return "요약 실패! 텍스트가 너무 짧습니다. 최소 3~5 문장 이상 입력해주세요."

        parser = PlaintextParser.from_string(text, Tokenizer("english"))
        summarizer = LexRankSummarizer()
        summary = summarizer(parser.document, num_sentences)

        if not summary:
            return "요약 실패! 의미 있는 문장 추출에 실패했습니다."

        return " ".join(str(sentence) for sentence in summary)

    except Exception as e:
        return f"요약 실패! 오류: {str(e)}"
