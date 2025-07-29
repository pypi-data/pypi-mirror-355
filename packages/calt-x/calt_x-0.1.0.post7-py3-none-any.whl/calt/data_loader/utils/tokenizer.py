from transformers import PreTrainedTokenizerFast
from tokenizers import Tokenizer
from tokenizers.models import WordLevel
from tokenizers.processors import TemplateProcessing
from tokenizers.pre_tokenizers import CharDelimiterSplit

SPECIAL_TOKENS = ["[PAD]", "<s>", "</s>", "[CLS]"]
# Create mapping from token names to special token values
SPECIAL_TOKEN_MAP = dict(
    zip(["pad_token", "bos_token", "eos_token", "cls_token"], SPECIAL_TOKENS)
)


def set_tokenizer(
    num_vars: int,
    field: str = "GF",
    max_coeff: int = 100,
    max_degree: int = 10,
    max_length: int = 512,
) -> PreTrainedTokenizerFast:
    """Create and configure a tokenizer for polynomial expressions.

    Args:
        num_vars: Number of variables (x0, x1, ...) in the polynomial
        field: Field specification ("QQ"/"ZZ" for rational/integer, or
               "GF<p>" for finite field)
        max_coeff: Maximum absolute value for coefficients in the vocabulary
        max_degree: Maximum degree allowed for any variable
        max_length: Maximum sequence length the tokenizer will process

    Returns:
        tokenizer: A pre-configured HuggingFace tokenizer for polynomial expressions
    """
    CONSTS = ["[C]"]
    ECONSTS = ["[E]"]

    if field in ("QQ", "ZZ"):
        # For rational/integer fields, use coefficients from -max_coeff to +max_coeff
        CONSTS += [f"C{i}" for i in range(-max_coeff, max_coeff + 1)]
    elif field[:2] == "GF":
        # For finite fields GF(p), use coefficients from -p+1 to p-1
        assert field[2:].isdigit()
        p = int(field[2:])
        CONSTS += [f"C{i}" for i in range(-p, p)]
    else:
        raise ValueError(f"unknown field: {field}")

    # Create exponent tokens from E0 to E<max_degree>
    ECONSTS = [f"E{i}" for i in range(max_degree + 1)]

    # Combine all tokens to build vocabulary
    vocab = CONSTS + ECONSTS + ["[SEP]"]
    vocab = dict(zip(vocab, range(len(vocab))))

    # Build the tokenizer with space delimiter
    tok = Tokenizer(WordLevel(vocab))
    tok.pre_tokenizer = CharDelimiterSplit(" ")
    tok.add_special_tokens(SPECIAL_TOKENS)
    tok.enable_padding()
    tok.no_truncation()

    # Configure processing with beginning/end tokens
    bos_token = SPECIAL_TOKEN_MAP["bos_token"]
    eos_token = SPECIAL_TOKEN_MAP["eos_token"]
    tok.post_processor = TemplateProcessing(
        single=f"{bos_token} $A {eos_token}",
        special_tokens=[
            (bos_token, tok.token_to_id(bos_token)),
            (eos_token, tok.token_to_id(eos_token)),
        ],
    )

    # Wrap with HuggingFace's fast tokenizer interface
    tokenizer = PreTrainedTokenizerFast(
        tokenizer_object=tok, model_max_length=max_length, **SPECIAL_TOKEN_MAP
    )
    return tokenizer
