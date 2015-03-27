"""
Given abstracts stored in database, this file extract topic models from the all abstracts
"""
import onlineldavb
import sys
import numpy
from database_messager.mysql_messager import MysqlMessenger
from pickle import load
from contextlib import contextmanager
from sys import stderr


@contextmanager
def read_pickle_file(pickle_file_path):
    """
    This file reads information according from a pickler file path and return the content.
    """
    try:
        with open(pickle_file_path) as f:
            yield load(f)
    except IOError, e:
        print >> stderr, e
    finally:
        pass


def main():
    """
    Downloads and analyzes a bunch of random Wikipedia articles using
    online VB for LDA.
    """
    # The number of documents to analyze each iteration
    batch_size = 4

    # Total number of documents in the population. For a fixed corpus,
    # this is the size of the corpus. In the truly online setting

    number_of_documents = 71

    # The number of topics
    number_of_topics = 1

    # establish mysql database connection
    database = MysqlMessenger(database="keyword_app")
    sql = "select Abstract from PreprocessedAbstracts;"
    database.execute_sql(sql)
    row_iteration = database.fetch()
    abstracts = [row[0] for row in row_iteration]

    # How many documents to look at
    if len(sys.argv) < 2:
        documents_to_analyze = int(number_of_documents/batch_size)
    else:
        documents_to_analyze = int(sys.argv[1])

    # Our vocabulary
    all_keywords_file_path = "../../keywords/abstract_109.txt"
    with read_pickle_file(all_keywords_file_path) as content:
        vocab = list(content)

    # Initialize the algorithm with alpha=1/K, eta=1/K, tau_0=1024, kappa=0.7
    olda = onlineldavb.OnlineLDA(vocab, number_of_topics, number_of_documents, 1./number_of_topics, 1./number_of_topics, 1024., 0.7)

    # Run until we've seen D documents. (Feel free to interrupt *much*
    # sooner than this.)

    for iteration in range(0, documents_to_analyze):

        # set dataset as list that stores all abstracts
        doc_set = abstracts

        # Give them to online LDA
        (gamma, bound) = olda.update_lambda(doc_set)

        # Compute an estimate of held-out perplexity
        (word_ids, word_count_times) = onlineldavb.parse_doc_list(doc_set, olda.vocab)
        
        per_word_bound = bound * len(doc_set) / (number_of_documents * sum(map(sum, word_count_times)))
        print '%d:  rho_t = %f,  held-out perplexity estimate = %f' % \
            (iteration, olda.rhot, numpy.exp(-per_word_bound))

        # Save lambda, the parameters to the variational distributions
        # over topics, and gamma, the parameters to the variational
        # distributions over topic weights for the articles analyzed in
        # the last iteration.

        if iteration % 10 == 0:
            numpy.savetxt('lambda-%d.dat' % iteration, olda._lambda)
            numpy.savetxt('gamma-%d.dat' % iteration, gamma)

if __name__ == '__main__':
    main()
