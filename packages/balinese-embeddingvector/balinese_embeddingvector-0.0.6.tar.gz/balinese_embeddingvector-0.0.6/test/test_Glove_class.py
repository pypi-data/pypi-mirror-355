import pickle
import pickle
import os
import itertools
from collections import Counter
import numpy as np
from balinese_embeddingvector.model import Glove

filename = "./dataset/BALINESE_WORD_EMBEDDING_INPUT_CORPUS.pkl"
CORPUS_MODEL_WORD_EMBEDDING = pickle.load(open(filename, 'rb'))

# convert all the tokens (alphabets and numerics only) to lower case
print('Processing sentences..\n')
processed_sents = []
for sent in CORPUS_MODEL_WORD_EMBEDDING:
    processed_sents.append([word.lower() for word in sent if word.isalnum()])

# hilangkan list kosong [] dari processed_sents
cleaned_processed_sents = [s for s in processed_sents if s and isinstance(
    s, list) and all(isinstance(item, str) for item in s)]
cleaned_processed_sents = cleaned_processed_sents[0:120]

tokens = list(set(list(itertools.chain(*cleaned_processed_sents))))
n_tokens = len(tokens)
n_sents = len(cleaned_processed_sents)
print('Number of Sentences:', n_sents)
print('Number of Tokens:', n_tokens)

token2int = dict(zip(tokens, range(len(tokens))))
int2token = {v: k for k, v in token2int.items()}

VECTOR_SIZE = 50
PATH_TO_SAVED_PRETRAINED_MODEL = "../saved_model/"
WINDOW = 5
MIN_COUNT = 5
EPOCHS = 100
EPS = 0.001
ALPHA = 0.1
DELTA = 0.8

model_glove = Glove(
    n_epochs=EPOCHS,
    eps=EPS,
    n_sents=n_sents,
    embedding_size=VECTOR_SIZE,
    alpha=ALPHA,
    delta=DELTA,
    window_size=WINDOW,
    save_filepath="./"
)
model_glove.fit(tokens, cleaned_processed_sents, token2int, int2token)
model_glove.train()


# test1: finding word vector
test_word = 'parikrama'
print(model_glove.get_word_vector(test_word))

# test2: finding word context vector
print(model_glove.get_word_context_vector(test_word))

# test3: finding final word embedding vector
print(model_glove.get_final_embedding_vector(test_word))

# test4: get weights final embedding
print(model_glove.update_weights_final_embedding_vector())

# test5: finding most similar words (final embedding vectors)
print(model_glove.most_similar(test_word, 5))
