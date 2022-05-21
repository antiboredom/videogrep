import sys
import videogrep
from collections import Counter
import random

stopwords = ["i", "we're", "you're", "that's", "it's", "us", "i'm", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your", "yours", "yourself", "yourselves", "he", "him", "his", "himself", "she", "her", "hers", "herself", "it", "its", "itself", "they", "them", "their", "theirs", "themselves", "what", "which", "who", "whom", "this", "that", "these", "those", "am", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "having", "do", "does", "did", "doing", "a", "an", "the", "and", "but", "if", "or", "because", "as", "until", "while", "of", "at", "by", "for", "with", "about", "against", "between", "into", "through", "during", "before", "after", "above", "below", "to", "from", "up", "down", "in", "out", "on", "off", "over", "under", "again", "further", "then", "once", "here", "there", "when", "where", "why", "how", "all", "any", "both", "each", "few", "more", "most", "other", "some", "such", "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very", "s", "t", "can", "will", "just", "don", "should", "now"]

def auto_supercut(vidfile, total_words=3):
    """automatically creates a supercut from a video by selecting three random words"""

    # grab all the words from the transcript
    unigrams = videogrep.get_ngrams(vidfile)

    # remove stop words
    unigrams = [w for w in unigrams if w[0] not in stopwords]

    # get the most common 10 words
    most_common = Counter(unigrams).most_common(10)

    # transform the list into just the words
    words = [w[0][0] for w in most_common]

    # randomize the list
    random.shuffle(words)

    # select the first N words
    words = words[0:total_words]

    # create a query
    query = "|".join(words)

    # create the video
    videogrep.videogrep(vidfile, query, search_type="fragment", output="auto_supercut.mp4")


if __name__ == "__main__":
    vidfile = sys.argv[1]
    auto_supercut(vidfile)
