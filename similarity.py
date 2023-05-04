import nltk
nltk.download('stopwords')
nltk.download('wordnet')
from nltk.stem import WordNetLemmatizer
nltk.download('averaged_perceptron_tagger')
from nltk.corpus import wordnet
nltk.download('punkt')
import requests
import io
from pdfminer.high_level import extract_text
import gensim
from gensim.utils import simple_preprocess
from gensim.parsing.preprocessing import STOPWORDS
from gensim.corpora import Dictionary
from gensim.models import LdaModel
from gensim.parsing.preprocessing import remove_stopwords
import csv
import math

n = 0

# IPFS link to the PDF file
# ipfs_link1 = "https://gateway.lighthouse.storage/ipfs/QmXVPN7KubJF7YNLB3SDZG3NhpWbFstegmtAzZztqWbJwC"
# ipfs_link2 = "https://gateway.lighthouse.storage/ipfs/QmNxQDPZmthPKxbKwGcx4xXt2b2jMG1JzmDMFd8FzdA6yB"
# ipfs_link3 = "https://gateway.lighthouse.storage/ipfs/QmP3SS5JwVLL36uSZSCVWm8N81RGPFVAG88ZVoKcPKDig4"

# Open the CSV file for reading
with open('ipfs_links.csv', 'r') as file:
    # Create a CSV reader object
    reader = csv.reader(file)
    # Initialize an empty list to store the IPFS links
    links = []
    # Loop through each row in the CSV file
    for row in reader:
        # Extract the IPFS link from the row and append it to the list
        links.append(row[2])
        n += 1

text = []

# Fetch the PDF file from IPFS and read it into memory
# Loop through the array and print each link
for link in links:
    print(link)
    response = requests.get(link)
    memory_file = io.BytesIO(response.content)
    # Extract text from the PDF
    text.append(''.join(extract_text(memory_file)))  


for i in range(len(text)):
    words = text[i].split()
    if(i==0):
      print(words)
    words = [remove_stopwords(word) for word in words]
    text[i] = ' '.join(words)


lemmatizer = WordNetLemmatizer()

# Define a function to get the WordNet POS tag from the NLTK POS tag
def get_wordnet_pos(nltk_tag):
    if nltk_tag.startswith('J'):
        return wordnet.ADJ
    elif nltk_tag.startswith('V'):
        return wordnet.VERB
    elif nltk_tag.startswith('N'):
        return wordnet.NOUN
    elif nltk_tag.startswith('R'):
        return wordnet.ADV
    else:
        return None

lemmatized = []

# Iterate over each sentence in the text array
for sentence in text:
    # Tokenize the sentence into words
    words = nltk.word_tokenize(sentence)
    # Get the NLTK POS tags for the words
    pos_tags = nltk.pos_tag(words)
    # Map the NLTK POS tags to WordNet POS tags
    wordnet_tags = [(word, get_wordnet_pos(tag)) for word, tag in pos_tags]
    # Lemmatize each word using its WordNet POS tag (if available)
    lemmatized_words = [lemmatizer.lemmatize(word, tag) if tag else word for word, tag in wordnet_tags]
    # Join the lemmatized words back into a sentence
    lemmatized_sentence = ' '.join(lemmatized_words)
    # Add the lemmatized sentence to the lemmatized array
    lemmatized.append(lemmatized_sentence)


# define the texts to analyze
texts=[]
for el in lemmatized:
  texts.append(el)

# define the number of topics to extract
num_topics = 70
# define the number of words in each topic
num_words = 70

lda_models = []
for text in texts:
    # tokenize the text and remove stopwords
    tokens = [token for token in simple_preprocess(text) if token not in STOPWORDS]

    # create a dictionary from the tokens
    dictionary = Dictionary([tokens])

    # convert the tokens to a bag-of-words representation
    bow_corpus = [dictionary.doc2bow(tokens)]

    # define the LDA model
    lda_model = LdaModel(bow_corpus, num_topics=num_topics, id2word=dictionary)
    lda_models.append(lda_model)


topics_dict = {}
for i in range(n):
    topics_dict[i+1] = {}
    for idx, topic in lda_models[i].print_topics(-1, num_words=num_words):
        # extract the words and their weights
        words_weights = topic.split("+")
        # loop over each word and its weight
        for word_weight in words_weights:
            # extract the word and its weight
            word = word_weight.split("*")[1].replace('"', '').strip()
            weight = float(word_weight.split("*")[0])
            # store the word and its weight in the dictionary
            if word in topics_dict[i+1]:
                topics_dict[i+1][word] += weight
            else:
                topics_dict[i+1][word] = weight


def cosine_similarity(dict1, dict2):
    # get the set of keys that appear in both dictionaries
    keys = set(dict1.keys()) & set(dict2.keys())

    # compute the dot product of the vectors
    dot_product = sum(dict1[key] * dict2[key] for key in keys)

    # compute the magnitude of the vectors
    magnitude1 = math.sqrt(sum(dict1[key]**2 for key in dict1.keys()))
    magnitude2 = math.sqrt(sum(dict2[key]**2 for key in dict2.keys()))

    # compute the cosine similarity
    if magnitude1 == 0 or magnitude2 == 0:
        return 0
    else:
        return dot_product / (magnitude1 * magnitude2)



cos_sim = {}
for i in range(1, n+1):
    cos_sim[i] = {}
    for j in range(1, n+1):
        if i == j:
            continue
        wt = cosine_similarity(topics_dict[i], topics_dict[j])
        cos_sim[i][j] = wt
    # print(cos_sim[i])
    temp_list = sorted(cos_sim[i].items(), key=lambda x:x[1], reverse=True)
    cos_sim[i] = dict(temp_list)

print(cos_sim)

id_mapping = {}

# Open CSV file
with open('ipfs_links.csv', 'r') as file:
    reader = csv.DictReader(file)
    for row in reader:
        # Map the serial number to the document ID
        id_mapping[int(row[0])] = int(row[1])


# Open a CSV file for writing
with open('similarities.csv', 'w', newline='') as file:
    writer = csv.writer(file)

    # Write the header row
    writer.writerow(['Doc ID', 'D1', 'Sim1', 'D2', 'Sim2', 'D3', 'Sim3', 'D4', 'Sim4'])

    # Write each inner dictionary as a new row
    for s_no, doc_dict in cos_sim.items():
      row = [id_mapping[s_no]]
      j = 0
      for key, value in doc_dict.items():
        if j>=4:
          break
        row += [key, value]
        j+=1
      writer.writerow(row)
    