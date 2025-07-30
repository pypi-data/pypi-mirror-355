import numpy as np
import matplotlib.pyplot as plt
import nltk
import itertools
from collections import Counter
from sklearn.decomposition import PCA
from sklearn.metrics.pairwise import cosine_similarity


class Glove:
    def __init__(self, n_epochs=100, eps=0.001, n_sents=10, embedding_size=50, alpha=0.1, delta=0.8, window_size=5, save_weights=True, save_filepath="./"):
        self.hyperparameters = {
            'n_epochs': n_epochs,  # number of training epochs
            'eps': eps,  # tolerance
            'n_sents': n_sents,  # number of sentences to consider
            'embedding_size': embedding_size,  # weight embedding size
            'alpha': alpha,  # learning rate
            'delta': delta,  # AdaGrad parameter
            'window_size': window_size,  # context_window_size
        }
        self.save_weights = save_weights
        self.save_filepath = save_filepath
        self.IS_FIT = False
        self.IS_TRAIN = False

    def fit(self, tokens, processed_sents, token2int, int2token):
        self.tokens = tokens
        self.n_tokens = len(tokens)
        self.processed_sents = processed_sents
        self.token2int = token2int
        self.int2token = int2token
        self.IS_FIT = True
        return self

    def train(self):
        if not self.IS_FIT:
            raise TypeError('Please fit your data first!')
        embedding_size = self.hyperparameters['embedding_size']
        n_tokens = self.n_tokens

        # train procedure
        self.co_occurence_matrix = self.__get_co_occurence_matrix()
        weights_init = np.random.random((2 * n_tokens, embedding_size))
        bias_init = np.random.random((2 * n_tokens,))
        self.weights, self.bias, self.norm_grad_weights, self.norm_grad_bias, self.costs, self.last_n_epochs = self.__adagrad(
            weights_init, bias_init)  # glove training procedure

        self.IS_TRAIN = True
        # saving weights
        if self.save_weights:
            self.__save_weights()

        return self

    def retrieve_trained_weights(self):
        if not self.IS_TRAIN:
            raise TypeError('Please train your glove first!')

        return self.weights

    def plot_training_results(self):
        """
        Function for plotting learning curves
        """
        if not self.IS_TRAIN:
            raise TypeError('Please train your glove first!')

        costs = self.costs
        norm_grad_weights = self.norm_grad_weights
        norm_grad_bias = self.norm_grad_bias
        last_n_epochs = self.last_n_epochs

        plt.figure(figsize=(20, 5))

        plt.subplot(131)
        plt.plot(costs[-last_n_epochs:], c='k')
        plt.title('cost')
        plt.xlabel('epochs')
        plt.ylabel('value')

        plt.subplot(132)
        plt.plot(norm_grad_weights[-last_n_epochs:], c='k')
        plt.title('norm_weights')
        plt.xlabel('epochs')
        plt.ylabel('value')

        plt.subplot(133)
        plt.plot(norm_grad_bias[-last_n_epochs:], c='k')
        plt.title('norm_bias')
        plt.xlabel('epochs')
        plt.ylabel('value')
        plt.show()

    def plotting_word_vectors(self, weights, n_tokens):
        """
        Function for plotting word vectors in 2D using PCA based on inputted weights
        """
        tokens = self.tokens

        pca = PCA(n_components=2)
        weights = pca.fit_transform(weights[:n_tokens])
        explained_var = (100 * sum(pca.explained_variance_)).round(2)
        print(f'Variance explained by 2 components: {explained_var}%')

        fig, ax = plt.subplots(figsize=(20, 10))
        for word, x1, x2 in zip(tokens, weights[:, 0], weights[:, 1]):
            ax.annotate(word, (x1, x2))

        x_pad = 0.5
        y_pad = 1.5
        x_axis_min = np.amin(weights, axis=0)[0] - x_pad
        x_axis_max = np.amax(weights, axis=0)[0] + x_pad
        y_axis_min = np.amin(weights, axis=1)[1] - y_pad
        y_axis_max = np.amax(weights, axis=1)[1] + y_pad

        plt.xlim(x_axis_min, x_axis_max)
        plt.ylim(y_axis_min, y_axis_max)
        plt.rcParams["figure.figsize"] = (10, 10)
        plt.show()

    def most_similar(self, token, topN):
        """
        Function for finding topN similar words for inputted token
        """
        if not self.IS_TRAIN:
            raise TypeError('Please train your glove first!')

        n_tokens = self.n_tokens
        weights = self.weights

        # getting cosine similarities between all combinations of word vectors
        csim = cosine_similarity(weights[:n_tokens])
        # masking diagonal values since they will be most similar
        np.fill_diagonal(csim, 0)

        # find similar words based on cosine similarity matrix
        token_idx = self.token2int[token]
        closest_words = list(
            map(lambda x: self.int2token[x], np.argsort(csim[token_idx])[::-1][:topN]))

        return closest_words

    def loading_weights(self, filepath):
        """
        Function for loading pretrained glove weights saved in filepath. The pretrained glove embedding was saved using *.npy format
        """
        print(f'Loading weights from {filepath}')
        loaded_weights = np.load(filepath, allow_pickle=True)
        return loaded_weights

    def __get_co_occurences(self, token):
        window_size = self.hyperparameters['window_size']
        processed_sents = self.processed_sents
        token2int = self.token2int

        co_occurences = []
        for sent in processed_sents:
            for idx in (np.array(sent) == token).nonzero()[0]:
                co_occurences.append(
                    sent[max(0, idx-window_size):min(idx+window_size+1, len(sent))])

        co_occurences = list(itertools.chain(*co_occurences))
        co_occurence_idxs = list(map(lambda x: token2int[x], co_occurences))
        co_occurence_dict = Counter(co_occurence_idxs)
        co_occurence_dict = dict(sorted(co_occurence_dict.items()))
        return co_occurence_dict

    def __get_co_occurence_matrix(self):
        tokens = self.tokens
        processed_sents = self.processed_sents
        window_size = self.hyperparameters['window_size']
        token2int = self.token2int

        co_occurence_matrix = np.zeros(
            shape=(len(tokens), len(tokens)), dtype='int')
        for token in tokens:
            token_idx = token2int[token]
            co_occurence_dict = self.__get_co_occurences(token)
            co_occurence_matrix[token_idx, list(co_occurence_dict.keys())] = list(
                co_occurence_dict.values())

        np.fill_diagonal(co_occurence_matrix, 0)
        return co_occurence_matrix

    def __f(self, X_wc, X_max):
        alpha = self.hyperparameters['alpha']
        if X_wc < X_max:
            return (X_wc/X_max)**alpha
        else:
            return 1

    def __gradient(self, weights, bias, co_occurence_matrix, X_max):
        n_tokens = self.n_tokens
        embedding_size = self.hyperparameters['embedding_size']
        alpha = self.hyperparameters['alpha']

        dw = np.zeros((2*n_tokens, embedding_size))
        db = np.zeros(2*n_tokens)

        # building word vectors
        for idx_word in range(n_tokens):
            w_word = weights[idx_word]
            b_word = bias[idx_word]

            for idx_context in range(n_tokens):
                w_context = weights[n_tokens+idx_context]
                b_context = bias[n_tokens+idx_context]
                X_wc = co_occurence_matrix[idx_word, idx_context]
                value = self.__f(X_wc, X_max) * 2 * (np.dot(w_word.T,
                                                            w_context) + b_word + b_context - np.log(1 + X_wc))
                db[idx_word] += value
                dw[idx_word] += value * w_context

        # building context vectors
        for idx_context in range(n_tokens):
            w_context = weights[n_tokens + idx_context]
            b_context = bias[n_tokens + idx_context]

            for idx_word in range(n_tokens):
                w_word = weights[idx_word]
                b_word = bias[idx_word]
                X_wc = co_occurence_matrix[idx_word, idx_context]
                value = self.__f(X_wc, X_max) * 2 * (np.dot(w_word.T,
                                                            w_context) + b_word + b_context - np.log(1 + X_wc))
                db[n_tokens + idx_context] += value
                dw[n_tokens + idx_context] += value * w_word
        return dw, db

    def __loss_fn(self, weights, bias, co_occurence_matrix, X_max):
        n_tokens = self.n_tokens
        alpha = self.hyperparameters['alpha']
        total_cost = 0
        for idx_word in range(n_tokens):
            for idx_context in range(n_tokens):
                w_word = weights[idx_word]
                w_context = weights[n_tokens+idx_context]
                b_word = bias[idx_word]
                b_context = bias[n_tokens+idx_context]
                X_wc = co_occurence_matrix[idx_word, idx_context]
                total_cost += self.__f(X_wc, X_max) * (np.dot(w_word.T,
                                                              w_context) + b_word + b_context - np.log(1 + X_wc))**2
        return total_cost

    def __adagrad(self, weights_init, bias_init):
        """
        Adam gradient function to train Glove model
        """
        n_epochs = self.hyperparameters['n_epochs']
        alpha = self.hyperparameters['alpha']
        eps = self.hyperparameters['eps']
        delta = self.hyperparameters['delta']
        co_occurence_matrix = self.co_occurence_matrix.copy()

        # adagrad procedure
        # 1. initialization
        weights = weights_init
        bias = bias_init
        r1 = np.zeros(weights.shape)
        r2 = np.zeros(bias.shape)
        X_max = np.max(co_occurence_matrix)

        # 2. loops
        norm_grad_weights = []
        norm_grad_bias = []
        costs = []
        n_iter = 0
        cost = 1
        convergence = 1
        while cost > eps:
            dw, db = self.__gradient(weights, bias, co_occurence_matrix, X_max)

            r1 += (dw)**2
            r2 += (db)**2
            weights -= np.multiply(alpha / (delta + np.sqrt(r1)), dw)
            bias -= np.multiply(alpha / (delta + np.sqrt(r2)), db)

            cost = self.__loss_fn(weights, bias, co_occurence_matrix, X_max)

            if n_iter % 200 == 0:
                print(f'Cost at {n_iter} iterations:', cost.round(3))

            norm_grad_weights.append(np.linalg.norm(dw))
            norm_grad_bias.append(np.linalg.norm(db))
            costs.append(cost)
            n_iter += 1

            if n_iter >= n_epochs:
                convergence = 0
                break
        last_n_epochs = n_iter
        if convergence:
            print(f'Converged in {len(costs)} epochs..')
        else:
            print(f'Training complete with {n_epochs} epochs..')
        return weights, bias, norm_grad_weights, norm_grad_bias, costs, last_n_epochs

    def __save_weights(self):
        filename = f"{self.save_filepath}/{self.hyperparameters['embedding_size']}_glove_model.npy"
        np.save(filename, self.weights)
        print(f'Model was succesfully saved in {filename}!')
