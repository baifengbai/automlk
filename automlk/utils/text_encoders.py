import string
import logging
import numpy as np
from random import shuffle
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer

log = logging.getLogger(__name__)

try:
    from gensim.models import Word2Vec, Doc2Vec, fasttext
    from gensim.models.doc2vec import TaggedDocument
    import_gensim = True
except:
    import_gensim = False


TABLE_TRANS = str.maketrans({key: ' ' for key in string.punctuation})
TABLE_TRANS['.'] = ' . '
TABLE_TRANS['?'] = ' . '
TABLE_TRANS['!'] = ' . '
TABLE_TRANS[':'] = ' . '
TABLE_TRANS[';'] = ' . '
TABLE_TRANS['('] = ' '
TABLE_TRANS[')'] = ' '
TABLE_TRANS['['] = ' '
TABLE_TRANS[']'] = ' '
TABLE_TRANS[','] = ' '
TABLE_TRANS['{'] = ' '
TABLE_TRANS['}'] = ' '


def clean_text(s):
    """
    clean the sentence for text processing: lowercase, punctuation

    :param s: input string
    :return: string
    """
    words = str(s).lower().translate(TABLE_TRANS).split()
    return " ".join(words)


def model_bow(text, params):
    """
    generate a bag of words model from a text (list of sentences)

    :param text: text, as a list of sentences (strings)
    :param params: dictionary of parameter space for word2vec
    :return: trained encoder model for bag of words
    """
    train_text = [clean_text(s) for s in text]
    model_params = {key: params[key] for key in params.keys() if key not in ['tfidf']}
    if params['tfidf']:
        model = TfidfVectorizer(**model_params)
    else:
        model = CountVectorizer(**model_params)
    model.fit(train_text)
    return model


def model_word2vec(text, params):
    """
    generate a word2vec model from a text (list of sentences)

    :param text: text, as a list of sentences (strings)
    :param params: dictionary of parameter space for word2vec
    :return: trained encoder model for word2vec
    """
    train_text = [clean_text(s).split() for s in text]
    model = Word2Vec(**params)
    model.build_vocab(train_text)
    model.train(train_text, total_examples=model.corpus_count, epochs=model.iter)
    return model


def vector_word2vec(model, text, params):
    """
    generate an aggregate vector with words of the text

    :param model: trained word2vec model
    :param text: text, as a list of sentences (strings)
    :param params: parameters of the word2vec model
    :return: array of vectors (dim text x size of word2vec)
    """
    v = []
    vector_text = [clean_text(s).split() for s in text]
    for s in vector_text:
        ww = np.zeros(model.vector_size)
        n = 0
        for k, w in enumerate(s):
            if w in model.wv:
                ww += model.wv[w]
                n += 1
        if n > 0:
            v.append(ww / n)
        else:
            v.append(ww)

    # create vector with word vectors and paragraph lenght
    v = np.array(v)
    text_len = np.array([len(str(s)) for s in text]).reshape(len(vector_text), 1)
    return np.concatenate((text_len, v), axis=1)


def model_fasttext(text, params):
    """
    generate a fasttext model from a text (list of sentences)

    :param text: text, as a list of sentences (strings)
    :param params: dictionary of parameter space for word2vec
    :return: trained encoder model for fasttext
    """
    train_text = [clean_text(s).split() for s in text]
    model = fasttext.FastText(**params)
    model.build_vocab(train_text)
    model.train(train_text, total_examples=model.corpus_count, epochs=model.iter)
    return model


def vector_fasttext(model, text, params):
    """
    generate an aggregate vector with words of the text

    :param model: trained fasttext model
    :param text: text, as a list of sentences (strings)
    :param params: parameters of the word2vec model
    :return: array of vectors (dim text x size of fasttext)
    """
    v = []
    vector_text = [clean_text(s).split() for s in text]
    for s in vector_text:
        ww = np.zeros((params['size']))
        n = 0
        for k, w in enumerate(s):
            if w in model.wv:
                ww += model.wv[w]
                n += 1
        if n > 0:
            v.append(ww / n)
        else:
            v.append(ww)

    # create vector with word vectors and paragraph length
    v = np.array(v)
    text_len = np.array([len(str(s)) for s in text]).reshape(len(vector_text), 1)
    return np.concatenate((text_len, v), axis=1)


def model_doc2vec(text, params):
    """
    generate a doc2vec model from a text (list of sentences)

    :param text: text, as a list of sentences (strings)
    :param params: dictionary of parameter space for word2vec
    :return: trained encoder model for doc2vec
    """
    train_text = [TaggedDocument(words=clean_text(s).split(), tags=[i]) for i, s in enumerate(text)]
    model = Doc2Vec(**params)
    model.build_vocab(train_text)
    model.train(train_text, total_examples=model.corpus_count, epochs=model.iter)
    return model


def vector_doc2vec(model, text, params):
    """
    generate an a doc2vec vector from text

    :param model: trained doc2vec model
    :param text: text, as a list of sentences (strings)
    :param params: parameters of the word2vec model
    :return: array of vectors (dim text x size of doc2vec)
    """
    return [model.infer_vector(clean_text(s).split()) for s in text]
