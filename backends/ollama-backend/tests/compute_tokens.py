import torch
import torch.nn.functional as F
from transformers import AutoTokenizer
from config import EXAMPLE_ABSTRACT

sentences = [EXAMPLE_ABSTRACT]

tokenizer = AutoTokenizer.from_pretrained('bert-base-uncased')
encoded_input = tokenizer(sentences, padding=True, truncation=True, return_tensors='pt')

encoded_sentences = encoded_input["input_ids"]

EXAMPLE_ABSTRACT_TOKENS_COUNT = len(encoded_sentences[0])