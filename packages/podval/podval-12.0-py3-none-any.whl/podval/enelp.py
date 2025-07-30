import pyperclip as pc

def links():
    """
1 - https://drive.google.com/drive/folders/18xjxd7g-Q3q6OwiPgZtb-Li-7cmF3Lhp?usp=sharing
2 - https://colab.research.google.com/drive/1OT99f0iv6Sy6wn6-Axbjc9-rR7UutODIusp=sharing
3 - https://drive.google.com/drive/folders/1lBniWY3kxMjwC0nCHhuAFMJrGpQlv-LY?usp=sharing
    """
    text = """
1 - https://drive.google.com/drive/folders/18xjxd7g-Q3q6OwiPgZtb-Li-7cmF3Lhp?usp=sharing
2 - https://colab.research.google.com/drive/1OT99f0iv6Sy6wn6-Axbjc9-rR7UutODIusp=sharing
3 - https://drive.google.com/drive/folders/1lBniWY3kxMjwC0nCHhuAFMJrGpQlv-LY?usp=sharing
    """
    pc.copy(text)


def imports():
    """
import pandas as pd
import torch
import torch.nn as nn
import numpy as np
import matplotlib.pyplot as plt
import pymorphy2
import re
import time
import json
import gensim
import multiprocessing

from tqdm.auto import tqdm
from nltk.stem.snowball import SnowballStemmer
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize, sent_tokenize
from collections import Counter, defaultdict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.naive_bayes import MultinomialNB
from torch.nn.utils.rnn import pad_sequence
from torch.utils.data import DataLoader, TensorDataset, Dataset
from sklearn.metrics import accuracy_score, f1_score, classification_report
from sklearn.linear_model import LogisticRegression
from sklearn.metrics.pairwise import cosine_similarity

from gensim.models import KeyedVectors, Word2Vec
from sklearn.preprocessing import LabelEncoder

import nltk
nltk.download('stopwords')
nltk.download('wordnet')
    """
    text = """
import pandas as pd
import torch
import torch.nn as nn
import numpy as np
import matplotlib.pyplot as plt
import pymorphy2
import re
import time
import json
import gensim
import multiprocessing

from tqdm.auto import tqdm
from nltk.stem.snowball import SnowballStemmer
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize, sent_tokenize
from collections import Counter, defaultdict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.naive_bayes import MultinomialNB
from torch.nn.utils.rnn import pad_sequence
from torch.utils.data import DataLoader, TensorDataset, Dataset
from sklearn.metrics import accuracy_score, f1_score, classification_report
from sklearn.linear_model import LogisticRegression
from sklearn.metrics.pairwise import cosine_similarity

from gensim.models import KeyedVectors, Word2Vec
from sklearn.preprocessing import LabelEncoder

import nltk
nltk.download('stopwords')
nltk.download('wordnet')
    
    """
    pc.copy(text)
    
    
def data_preproc():
    """
stemmer = SnowballStemmer("english")
morph = pymorphy2.MorphAnalyzer()
lemmatizer = WordNetLemmatizer()

class Preprocessing():
    def __init__(self, text):
        self.text = text
        
    def text_cleaning(self):
        '''Приведение к нижнему регистру'''
        self.text = self.text.lower()

        '''Замена различных кавычек на стандартные ASCII'''
        self.text = self.text.replace('“', '"').replace('”', '"'
                                                       ).replace('‘', "'").replace('’', "'").replace('«','"').replace('»','"')
    
        '''Замена специальных символов (например, @, #, $, %, &, *) на пробел'''
        self.text = re.sub(r'[@#$%^&*]—', ' ', self.text)
        
        '''Удаление стоп-слов'''
        self.tokens = word_tokenize(self.text)
        stop_words = set(stopwords.words('english'))
        text_words = [word for word in self.tokens if word.lower() not in stop_words]
        self.text = ' '.join(text_words)
        
        '''Удаление знаков препинания'''
        self.text = re.sub(r'[^\w\s.]', ' ', self.text)
        
#         '''Замена цифр на специальный токен <ЧИСЛО>'''
#         self.text = re.sub(r'\d+', '<ЧИСЛО>', self.text)
#         '''Оставляем только eng буквы'''
        # text = "Hello! Привет! 123 ¿Cómo estás?"
        # cleaned_text = re.sub(r"[^a-zA-Z]", "", text)
        # print(cleaned_text)  # Вывод: HelloПриветCmoests
        
        # удаление однобуквенных слов
#         self.text = [word for word in self.tokens if len(word) > 1]
#         self.text = ' '.join(self.text)
    
        '''Удаление лишних пробелов'''
        self.text = re.sub(r'\s+', ' ', self.text).strip()
        
    def remove_noise(self, min_freq=1, max_freq=3):
        '''Подсчет частоты слов'''
        tokens = word_tokenize(self.text)
        word_freq = Counter(tokens)

        '''Удаление редко и часто используемых слов'''
        self.text = [
            word for word in tokens
            if word_freq[word] >= min_freq and word_freq[word] <= max_freq
        ]
        self.text = ' '.join(self.text)

    def stemming(self):
        tokens = word_tokenize(self.text)
        self.text = [stemmer.stem(word) for word in tokens]
        
        self.text = ' '.join(self.text)
        self.text = re.sub(r'\.', '', self.text)
        self.text = re.sub(r'\s+', ' ', self.text).strip()
       
    def lemmatization(self):
        tokens = word_tokenize(self.text)
        # for russian
#         self.text = ' '.join([morph.parse(token)[0].normal_form for token in tokens])
        self.text = ' '.join([lemmatizer.lemmatize(token) for token in tokens])
        self.text = re.sub(r'\.', '', self.text)
        self.text = re.sub(r'\s+', ' ', self.text).strip()
        
    def get_embeding(self):
        self.model = FastText([self.text], vector_size=50, window=2, min_count=1, sg=0)
        
def preprocessing_text(text):
    obj = Preprocessing(text)
    obj.text_cleaning()
    obj.lemmatization()
    return obj.text
    """
    text = """
stemmer = SnowballStemmer("english")
morph = pymorphy2.MorphAnalyzer()
lemmatizer = WordNetLemmatizer()

class Preprocessing():
    def __init__(self, text):
        self.text = text
        
    def text_cleaning(self):
        '''Приведение к нижнему регистру'''
        self.text = self.text.lower()

        '''Замена различных кавычек на стандартные ASCII'''
        self.text = self.text.replace('“', '"').replace('”', '"'
                                                       ).replace('‘', "'").replace('’', "'").replace('«','"').replace('»','"')
    
        '''Замена специальных символов (например, @, #, $, %, &, *) на пробел'''
        self.text = re.sub(r'[@#$%^&*]—', ' ', self.text)
        
        '''Удаление стоп-слов'''
        self.tokens = word_tokenize(self.text)
        stop_words = set(stopwords.words('english'))
        text_words = [word for word in self.tokens if word.lower() not in stop_words]
        self.text = ' '.join(text_words)
        
        '''Удаление знаков препинания'''
        self.text = re.sub(r'[^\w\s.]', ' ', self.text)
        
#         '''Замена цифр на специальный токен <ЧИСЛО>'''
#         self.text = re.sub(r'\d+', '<ЧИСЛО>', self.text)
#         '''Оставляем только eng буквы'''
        # text = "Hello! Привет! 123 ¿Cómo estás?"
        # cleaned_text = re.sub(r"[^a-zA-Z]", "", text)
        # print(cleaned_text)  # Вывод: HelloПриветCmoests
        
        # удаление однобуквенных слов
#         self.text = [word for word in self.tokens if len(word) > 1]
#         self.text = ' '.join(self.text)
    
        '''Удаление лишних пробелов'''
        self.text = re.sub(r'\s+', ' ', self.text).strip()
        
    def remove_noise(self, min_freq=1, max_freq=3):
        '''Подсчет частоты слов'''
        tokens = word_tokenize(self.text)
        word_freq = Counter(tokens)

        '''Удаление редко и часто используемых слов'''
        self.text = [
            word for word in tokens
            if word_freq[word] >= min_freq and word_freq[word] <= max_freq
        ]
        self.text = ' '.join(self.text)

    def stemming(self):
        tokens = word_tokenize(self.text)
        self.text = [stemmer.stem(word) for word in tokens]
        
        self.text = ' '.join(self.text)
        self.text = re.sub(r'\.', '', self.text)
        self.text = re.sub(r'\s+', ' ', self.text).strip()
       
    def lemmatization(self):
        tokens = word_tokenize(self.text)
        # for russian
#         self.text = ' '.join([morph.parse(token)[0].normal_form for token in tokens])
        self.text = ' '.join([lemmatizer.lemmatize(token) for token in tokens])
        self.text = re.sub(r'\.', '', self.text)
        self.text = re.sub(r'\s+', ' ', self.text).strip()
        
    def get_embeding(self):
        self.model = FastText([self.text], vector_size=50, window=2, min_count=1, sg=0)
        
def preprocessing_text(text):
    obj = Preprocessing(text)
    obj.text_cleaning()
    obj.lemmatization()
    return obj.text
    """
    pc.copy(text)
    
    
def datasets_imports():
    """
data = pd.read_csv("exam_data/sms_data.csv")
data.head()
data["prep_text"] = data["sms"].progress_apply(preprocessing_text)

data = pd.read_csv("exam_data/activities.csv")
data.head()
data["Review-Activity"].value_counts()
le = LabelEncoder()
le.fit(data["Review-Activity"])
data["label"] = le.transform(data["Review-Activity"])
data["prep_text"] = data["Text"].progress_apply(preprocessing_text)

data = pd.read_csv("exam_data/corona.csv")
data.head()
le = LabelEncoder()
data["label"] = le.fit_transform(data["Sentiment"])
data.label.value_counts()
data["prep_text"] = data["OriginalTweet"].progress_apply(preprocessing_text)

data = pd.read_csv("exam_data/news.csv")
data.head()
data["label"] = data["Class Index"]
data["prep_text"] = data["Title"].progress_apply(preprocessing_text)

data = pd.read_csv("exam_data/tweet_cat.csv")
data.head()
le = LabelEncoder()
data["label"] = le.fit_transform(data["type"])
data.label.value_counts()
data["prep_text"] = data["text"].progress_apply(preprocessing_text)

data = pd.read_csv("exam_data/tweets_disaster.csv")
data.head()
data["label"] = data["target"]
data["prep_text"] = data["text"].progress_apply(preprocessing_text)

data = []
with open("exam_data/reviews.json", "r") as f:
    for line in f:
        data.append(json.loads(line))
data = pd.DataFrame(data)
data["label"] = data["overall"].astype(int) - 1
data["prep_text"] = data["reviewText"].progress_apply(preprocessing_text)
    """
    text = """
data = pd.read_csv("exam_data/sms_data.csv")
data.head()
data["prep_text"] = data["sms"].progress_apply(preprocessing_text)

data = pd.read_csv("exam_data/activities.csv")
data.head()
data["Review-Activity"].value_counts()
le = LabelEncoder()
le.fit(data["Review-Activity"])
data["label"] = le.transform(data["Review-Activity"])
data["prep_text"] = data["Text"].progress_apply(preprocessing_text)

data = pd.read_csv("exam_data/corona.csv")
data.head()
le = LabelEncoder()
data["label"] = le.fit_transform(data["Sentiment"])
data.label.value_counts()
data["prep_text"] = data["OriginalTweet"].progress_apply(preprocessing_text)

data = pd.read_csv("exam_data/news.csv")
data.head()
data["label"] = data["Class Index"]
data["prep_text"] = data["Title"].progress_apply(preprocessing_text)

data = pd.read_csv("exam_data/tweet_cat.csv")
data.head()
le = LabelEncoder()
data["label"] = le.fit_transform(data["type"])
data.label.value_counts()
data["prep_text"] = data["text"].progress_apply(preprocessing_text)

data = pd.read_csv("exam_data/tweets_disaster.csv")
data.head()
data["label"] = data["target"]
data["prep_text"] = data["text"].progress_apply(preprocessing_text)

data = []
with open("exam_data/reviews.json", "r") as f:
    for line in f:
        data.append(json.loads(line))
data = pd.DataFrame(data)
data["label"] = data["overall"].astype(int) - 1
data["prep_text"] = data["reviewText"].progress_apply(preprocessing_text)
    """
    pc.copy(text)
    
    
def classific_rnn_plus_training():
    """
def preprocess_data(df):
    tokenized_texts = [text.split() for text in df['prep_text'].values]
    
    word_counts = Counter([word for text in tokenized_texts for word in text])
    vocab = {word: idx+2 for idx, (word, _) in enumerate(word_counts.most_common())}
    vocab['<PAD>'] = 0
    vocab['<UNK>'] = 1
    sequences = [[vocab.get(word, vocab['<UNK>']) for word in text] 
                for text in tokenized_texts]
    
    return sequences, df['label'].values, vocab

def create_padded_sequences(sequences, max_len=None):
    sequences = [torch.tensor(seq) for seq in sequences]
    padded = pad_sequence(sequences, batch_first=True, padding_value=0)
    if max_len:
        padded = padded[:, :max_len]
    return padded

sequences, labels, vocab = preprocess_data(data)
X_train, X_test, y_train, y_test = train_test_split(
    sequences, labels, test_size=0.2, stratify=labels, random_state=42
)
max_len = max([len(seq) for seq in sequences])
X_train_padded = create_padded_sequences(X_train, max_len)
X_test_padded = create_padded_sequences(X_test, max_len)

# Создание DataLoader
batch_size = 32
train_data = TensorDataset(X_train_padded, torch.tensor(y_train))
test_data = TensorDataset(X_test_padded, torch.tensor(y_test))

train_loader = DataLoader(train_data, batch_size=batch_size, shuffle=True)
test_loader = DataLoader(test_data, batch_size=batch_size)


class RNNClassifier(nn.Module):
    def __init__(self, vocab_size, embed_dim, hidden_dim, 
                 num_layers, bidirectional, num_classes=2):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.rnn = nn.RNN(
            embed_dim, hidden_dim, num_layers, 
            batch_first=True, bidirectional=bidirectional
        )
        self.dropout = nn.Dropout(0.5)
        self.fc = nn.Linear(hidden_dim * (2 if bidirectional else 1), num_classes)
        
    def forward(self, x):
        embedded = self.embedding(x)
        output, _ = self.rnn(embedded)
        # Берем последний скрытый состояние
        output = output[:, -1, :]  
#         output = self.dropout(output)
        return self.fc(output)
        
        
def train_model(model, train_loader, test_loader, epochs=10, lr=0.001):
    device = torch.device('cpu')
    model = model.to(device)
    criterion = nn.CrossEntropyLoss(ignore_index=0)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr)
    
    train_losses, test_accs = [], []
    start_time = time.time()
    
    for epoch in range(epochs):
        model.train()
        total_loss = 0
        train_labels = []
        train_outputs = []
        for inputs, labels in train_loader:
            inputs, labels = inputs.to(device), labels.to(device)
            
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels.long())
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            preds = torch.argmax(outputs, dim=1)
            
            train_labels.extend(labels)
            train_outputs.extend(preds)
            
        train_losses.append(total_loss / len(train_loader))
        f1_train = f1_score(train_labels, train_outputs, average='macro')
        acc_train = accuracy_score(train_labels, train_outputs)
        
        # Оценка на тестовых данных
        model.eval()
        correct, total = 0, 0
        test_labels = []
        test_outputs = []
        with torch.no_grad():
            for inputs, labels in test_loader:
                inputs, labels = inputs.to(device), labels.to(device)
                outputs = model(inputs)
                preds = torch.argmax(outputs, dim=1)

                test_labels.extend(labels)
                test_outputs.extend(preds)
        
        f1_test = f1_score(test_labels, test_outputs, average='macro')
        acc_test = accuracy_score(test_labels, test_outputs)
        test_accs.append(acc_test)
        print(f"Epoch {epoch+1}/{epochs} | Loss: {train_losses[-1]:.4f} "
              f"| F1 Train: {f1_train:.4f} | F1 Test: {f1_test:.4f} "
              f"| Acc Train: {acc_train:.4f} | Acc Test: {acc_test:.4f}")
        
    training_time = time.time() - start_time
    print(f'Training Time: {training_time:.2f} seconds')
    return model, train_losses, test_accs, training_time
    
vocab_size = len(vocab)
embed_dim = 100
hidden_dim = 64
num_layers = 1
epochs = 30

# Однонаправленная RNN
print("Training Unidirectional RNN:")
uni_model, uni_losses, uni_accs, uni_time = train_model(
    RNNClassifier(vocab_size, embed_dim, hidden_dim, num_layers, bidirectional=False),
    train_loader, test_loader, epochs
)

# Двунаправленная RNN
print("\nTraining Bidirectional RNN:")
bi_model, bi_losses, bi_accs, bi_time = train_model(
    RNNClassifier(vocab_size, embed_dim, hidden_dim, num_layers, bidirectional=True),
    train_loader, test_loader, epochs
)

# Сравнение результатов
print("\nResults Comparison:")
print(f"Unidirectional RNN | Training Time: {uni_time:.2f}s | Final Accuracy: {uni_accs[-1]:.4f}")
print(f"Bidirectional RNN  | Training Time: {bi_time:.2f}s | Final Accuracy: {bi_accs[-1]:.4f}")

# Визуализация результатов
plt.figure(figsize=(12, 5))
plt.subplot(1, 2, 1)
plt.plot(uni_losses, label='Uni RNN')
plt.plot(bi_losses, label='Bi RNN')
plt.title('Training Loss')
plt.legend()

plt.subplot(1, 2, 2)
plt.plot(uni_accs, label='Uni RNN')
plt.plot(bi_accs, label='Bi RNN')
plt.title('Test Accuracy')
plt.legend()
plt.show()
    """
    text = """
def preprocess_data(df):
    tokenized_texts = [text.split() for text in df['prep_text'].values]
    
    word_counts = Counter([word for text in tokenized_texts for word in text])
    vocab = {word: idx+2 for idx, (word, _) in enumerate(word_counts.most_common())}
    vocab['<PAD>'] = 0
    vocab['<UNK>'] = 1
    sequences = [[vocab.get(word, vocab['<UNK>']) for word in text] 
                for text in tokenized_texts]
    
    return sequences, df['label'].values, vocab

def create_padded_sequences(sequences, max_len=None):
    sequences = [torch.tensor(seq) for seq in sequences]
    padded = pad_sequence(sequences, batch_first=True, padding_value=0)
    if max_len:
        padded = padded[:, :max_len]
    return padded

sequences, labels, vocab = preprocess_data(data)
X_train, X_test, y_train, y_test = train_test_split(
    sequences, labels, test_size=0.2, stratify=labels, random_state=42
)
max_len = max([len(seq) for seq in sequences])
X_train_padded = create_padded_sequences(X_train, max_len)
X_test_padded = create_padded_sequences(X_test, max_len)

# Создание DataLoader
batch_size = 32
train_data = TensorDataset(X_train_padded, torch.tensor(y_train))
test_data = TensorDataset(X_test_padded, torch.tensor(y_test))

train_loader = DataLoader(train_data, batch_size=batch_size, shuffle=True)
test_loader = DataLoader(test_data, batch_size=batch_size)


class RNNClassifier(nn.Module):
    def __init__(self, vocab_size, embed_dim, hidden_dim, 
                 num_layers, bidirectional, num_classes=2):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.rnn = nn.RNN(
            embed_dim, hidden_dim, num_layers, 
            batch_first=True, bidirectional=bidirectional
        )
        self.dropout = nn.Dropout(0.5)
        self.fc = nn.Linear(hidden_dim * (2 if bidirectional else 1), num_classes)
        
    def forward(self, x):
        embedded = self.embedding(x)
        output, _ = self.rnn(embedded)
        # Берем последний скрытый состояние
        output = output[:, -1, :]  
#         output = self.dropout(output)
        return self.fc(output)
        
        
def train_model(model, train_loader, test_loader, epochs=10, lr=0.001):
    device = torch.device('cpu')
    model = model.to(device)
    criterion = nn.CrossEntropyLoss(ignore_index=0)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr)
    
    train_losses, test_accs = [], []
    start_time = time.time()
    
    for epoch in range(epochs):
        model.train()
        total_loss = 0
        train_labels = []
        train_outputs = []
        for inputs, labels in train_loader:
            inputs, labels = inputs.to(device), labels.to(device)
            
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels.long())
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            preds = torch.argmax(outputs, dim=1)
            
            train_labels.extend(labels)
            train_outputs.extend(preds)
            
        train_losses.append(total_loss / len(train_loader))
        f1_train = f1_score(train_labels, train_outputs, average='macro')
        acc_train = accuracy_score(train_labels, train_outputs)
        
        # Оценка на тестовых данных
        model.eval()
        correct, total = 0, 0
        test_labels = []
        test_outputs = []
        with torch.no_grad():
            for inputs, labels in test_loader:
                inputs, labels = inputs.to(device), labels.to(device)
                outputs = model(inputs)
                preds = torch.argmax(outputs, dim=1)

                test_labels.extend(labels)
                test_outputs.extend(preds)
        
        f1_test = f1_score(test_labels, test_outputs, average='macro')
        acc_test = accuracy_score(test_labels, test_outputs)
        test_accs.append(acc_test)
        print(f"Epoch {epoch+1}/{epochs} | Loss: {train_losses[-1]:.4f} "
              f"| F1 Train: {f1_train:.4f} | F1 Test: {f1_test:.4f} "
              f"| Acc Train: {acc_train:.4f} | Acc Test: {acc_test:.4f}")
        
    training_time = time.time() - start_time
    print(f'Training Time: {training_time:.2f} seconds')
    return model, train_losses, test_accs, training_time
    
vocab_size = len(vocab)
embed_dim = 100
hidden_dim = 64
num_layers = 1
epochs = 30

# Однонаправленная RNN
print("Training Unidirectional RNN:")
uni_model, uni_losses, uni_accs, uni_time = train_model(
    RNNClassifier(vocab_size, embed_dim, hidden_dim, num_layers, bidirectional=False),
    train_loader, test_loader, epochs
)

# Двунаправленная RNN
print("\nTraining Bidirectional RNN:")
bi_model, bi_losses, bi_accs, bi_time = train_model(
    RNNClassifier(vocab_size, embed_dim, hidden_dim, num_layers, bidirectional=True),
    train_loader, test_loader, epochs
)

# Сравнение результатов
print("\nResults Comparison:")
print(f"Unidirectional RNN | Training Time: {uni_time:.2f}s | Final Accuracy: {uni_accs[-1]:.4f}")
print(f"Bidirectional RNN  | Training Time: {bi_time:.2f}s | Final Accuracy: {bi_accs[-1]:.4f}")

# Визуализация результатов
plt.figure(figsize=(12, 5))
plt.subplot(1, 2, 1)
plt.plot(uni_losses, label='Uni RNN')
plt.plot(bi_losses, label='Bi RNN')
plt.title('Training Loss')
plt.legend()

plt.subplot(1, 2, 2)
plt.plot(uni_accs, label='Uni RNN')
plt.plot(bi_accs, label='Bi RNN')
plt.title('Test Accuracy')
plt.legend()
plt.show()
    """
    pc.copy(text)
    
    
def classific_additional():
    """
class RNN(nn.Module):
    def __init__(self, input_size, hidden_size, batch_first=True):
        super().__init__()
        self.hidden_size = hidden_size

        self.batch_first = batch_first
        self.rnn_cell = nn.RNNCell(input_size=input_size, hidden_size=hidden_size)


    def forward(self, x, h=None):
        '''
        x.shape = (batch_size, seq_len, feature_size) - тензор входных данных
        h.shape = (batch_size, hidden_size) - тензор со скрытым состоянием RNN
        '''
        if not self.batch_first:
            # (seq, batch, feature) -> (batch, seq, feature)
            x = x.transpose(0, 1)
        batch_size, seq_len, input_size = x.shape
        if h is None:
            h = torch.zeros(batch_size, self.hidden_size, device=x.device)

        outputs = []

        for t in range(seq_len):

            x_t = x[:, t, :] # (batch_size, input_size)
            h = self.rnn_cell(x_t, h)  # (batch_size, hidden_size)
            # print(h.unsqueeze(1).shape)
            outputs.append(h.unsqueeze(1))


        outputs = torch.cat(outputs, dim=1) # (batch_size, seq_len, hidden_size)
        # print(outputs.shape)

        return outputs, h
        
class CustomRNNClassifier(nn.Module):
    def __init__(self, vocab_size, embed_dim, hidden_size, num_classes=2, pad_idx=0):
        super().__init__()

        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=pad_idx)

        self.rnn = RNN(input_size=embed_dim, hidden_size=hidden_size)

        self.fc1 = nn.Linear(hidden_size, 64)
        self.fc2 = nn.Linear(64, 16)
        self.fc3 = nn.Linear(16, num_classes)
        self.relu = nn.ReLU()


    def forward(self, x):
        embedded = self.embedding(x)
        outputs, h = self.rnn(embedded)
        logits = self.fc3(self.relu(self.fc2(self.relu(self.fc1(h)))))
        return logits
        
# На всякий случай
def train_word2vec(sequences, vector_size=100, window=5, min_count=1):
    # sequences: список токенизированных предложений
    # Например: [["это", "пример", "текста"], ["еще", "одно", "предложение"]]
    model = Word2Vec(
        sentences=sequences,
        vector_size=vector_size,
        window=window,
        min_count=min_count,
        workers=4,
        epochs=10
    )
    return model

# 2. Модифицированный RNNClassifier с настраиваемыми эмбеддингами
class CustomEmbeddingRNN(nn.Module):
    def __init__(self, vocab, word2vec_model, hidden_dim=128, 
                 num_layers=1, bidirectional=False, num_classes=2,
                 freeze_embeddings=True):
        super().__init__()
        
        # Создаем матрицу эмбеддингов
        embedding_matrix = self._create_embedding_matrix(vocab, word2vec_model)
        embed_dim = embedding_matrix.shape[1]
        
        # Инициализируем embedding слой
        self.embedding = nn.Embedding.from_pretrained(
            torch.FloatTensor(embedding_matrix),
            padding_idx=vocab['<PAD>'],
            freeze=freeze_embeddings
        )
        
        self.rnn = nn.RNN(
            embed_dim, hidden_dim, num_layers,
            batch_first=True, bidirectional=bidirectional
        )
        self.dropout = nn.Dropout(0.5)
        
        # Учитываем bidirectional в выходном слое
        rnn_output_size = hidden_dim * (2 if bidirectional else 1)
        self.fc = nn.Linear(rnn_output_size, num_classes)
    
    def _create_embedding_matrix(self, vocab, word2vec_model):
        #Создает матрицу эмбеддингов на основе обученного Word2Vec
        embed_dim = word2vec_model.vector_size
        embedding_matrix = np.zeros((len(vocab), embed_dim))
        
        for word, idx in vocab.items():
            if word in word2vec_model.wv:
                embedding_matrix[idx] = word2vec_model.wv[word]
            elif word == '<PAD>':
                continue  # уже инициализирован нулями
            else:
                # Случайная инициализация для неизвестных слов
                embedding_matrix[idx] = np.random.normal(scale=0.6, size=(embed_dim,))
        
        return embedding_matrix
    
    def forward(self, x):
        embedded = self.embedding(x)
        output, _ = self.rnn(embedded)
        output = output[:, -1, :]  # Берем последний hidden state
        output = self.dropout(output)
        return self.fc(output)
    
# Пример использования:
# word2vec_model = train_word2vec([text.split() for text in data['prep_sms']])
    """
    text = """
class RNN(nn.Module):
    def __init__(self, input_size, hidden_size, batch_first=True):
        super().__init__()
        self.hidden_size = hidden_size

        self.batch_first = batch_first
        self.rnn_cell = nn.RNNCell(input_size=input_size, hidden_size=hidden_size)


    def forward(self, x, h=None):
        '''
        x.shape = (batch_size, seq_len, feature_size) - тензор входных данных
        h.shape = (batch_size, hidden_size) - тензор со скрытым состоянием RNN
        '''
        if not self.batch_first:
            # (seq, batch, feature) -> (batch, seq, feature)
            x = x.transpose(0, 1)
        batch_size, seq_len, input_size = x.shape
        if h is None:
            h = torch.zeros(batch_size, self.hidden_size, device=x.device)

        outputs = []

        for t in range(seq_len):

            x_t = x[:, t, :] # (batch_size, input_size)
            h = self.rnn_cell(x_t, h)  # (batch_size, hidden_size)
            # print(h.unsqueeze(1).shape)
            outputs.append(h.unsqueeze(1))


        outputs = torch.cat(outputs, dim=1) # (batch_size, seq_len, hidden_size)
        # print(outputs.shape)

        return outputs, h
        
class CustomRNNClassifier(nn.Module):
    def __init__(self, vocab_size, embed_dim, hidden_size, num_classes=2, pad_idx=0):
        super().__init__()

        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=pad_idx)

        self.rnn = RNN(input_size=embed_dim, hidden_size=hidden_size)

        self.fc1 = nn.Linear(hidden_size, 64)
        self.fc2 = nn.Linear(64, 16)
        self.fc3 = nn.Linear(16, num_classes)
        self.relu = nn.ReLU()


    def forward(self, x):
        embedded = self.embedding(x)
        outputs, h = self.rnn(embedded)
        logits = self.fc3(self.relu(self.fc2(self.relu(self.fc1(h)))))
        return logits
        
# На всякий случай
def train_word2vec(sequences, vector_size=100, window=5, min_count=1):
    # sequences: список токенизированных предложений
    # Например: [["это", "пример", "текста"], ["еще", "одно", "предложение"]]
    model = Word2Vec(
        sentences=sequences,
        vector_size=vector_size,
        window=window,
        min_count=min_count,
        workers=4,
        epochs=10
    )
    return model

# 2. Модифицированный RNNClassifier с настраиваемыми эмбеддингами
class CustomEmbeddingRNN(nn.Module):
    def __init__(self, vocab, word2vec_model, hidden_dim=128, 
                 num_layers=1, bidirectional=False, num_classes=2,
                 freeze_embeddings=True):
        super().__init__()
        
        # Создаем матрицу эмбеддингов
        embedding_matrix = self._create_embedding_matrix(vocab, word2vec_model)
        embed_dim = embedding_matrix.shape[1]
        
        # Инициализируем embedding слой
        self.embedding = nn.Embedding.from_pretrained(
            torch.FloatTensor(embedding_matrix),
            padding_idx=vocab['<PAD>'],
            freeze=freeze_embeddings
        )
        
        self.rnn = nn.RNN(
            embed_dim, hidden_dim, num_layers,
            batch_first=True, bidirectional=bidirectional
        )
        self.dropout = nn.Dropout(0.5)
        
        # Учитываем bidirectional в выходном слое
        rnn_output_size = hidden_dim * (2 if bidirectional else 1)
        self.fc = nn.Linear(rnn_output_size, num_classes)
    
    def _create_embedding_matrix(self, vocab, word2vec_model):
        #Создает матрицу эмбеддингов на основе обученного Word2Vec
        embed_dim = word2vec_model.vector_size
        embedding_matrix = np.zeros((len(vocab), embed_dim))
        
        for word, idx in vocab.items():
            if word in word2vec_model.wv:
                embedding_matrix[idx] = word2vec_model.wv[word]
            elif word == '<PAD>':
                continue  # уже инициализирован нулями
            else:
                # Случайная инициализация для неизвестных слов
                embedding_matrix[idx] = np.random.normal(scale=0.6, size=(embed_dim,))
        
        return embedding_matrix
    
    def forward(self, x):
        embedded = self.embedding(x)
        output, _ = self.rnn(embedded)
        output = output[:, -1, :]  # Берем последний hidden state
        output = self.dropout(output)
        return self.fc(output)
    
# Пример использования:
# word2vec_model = train_word2vec([text.split() for text in data['prep_sms']])
    """
    pc.copy(text)
    
    
def classific_tf_idf():
    """
X_train_data, X_test_data, y_train, y_test = train_test_split(
    data["prep_text"].values, data["label"].values, test_size=0.2, stratify=data["label"].values, random_state=42
)


alpha = 0.1 # параметр сглаживания
fit_prior = False

tfidf_vectorizer = TfidfVectorizer()
X_train_tfidf = tfidf_vectorizer.fit_transform(X_train_data)
X_test_tfidf = tfidf_vectorizer.transform(X_test_data)

classifier = MultinomialNB(alpha=alpha, fit_prior=fit_prior,)

classifier.fit(X_train_tfidf, y_train)

y_pred = classifier.predict(X_test_tfidf)

accuracy = accuracy_score(y_test, y_pred)
f1 = f1_score(y_test, y_pred, average='macro')

print(f"Test Accuracy: {accuracy}, Test F1-Score: {f1}")
    """
    text = """
X_train_data, X_test_data, y_train, y_test = train_test_split(
    data["prep_text"].values, data["label"].values, test_size=0.2, stratify=data["label"].values, random_state=42
)


alpha = 0.1 # параметр сглаживания
fit_prior = False

tfidf_vectorizer = TfidfVectorizer()
X_train_tfidf = tfidf_vectorizer.fit_transform(X_train_data)
X_test_tfidf = tfidf_vectorizer.transform(X_test_data)

classifier = MultinomialNB(alpha=alpha, fit_prior=fit_prior,)

classifier.fit(X_train_tfidf, y_train)

y_pred = classifier.predict(X_test_tfidf)

accuracy = accuracy_score(y_test, y_pred)
f1 = f1_score(y_test, y_pred, average='macro')

print(f"Test Accuracy: {accuracy}, Test F1-Score: {f1}")
    """
    pc.copy(text)
    
    
def classific_word2vec():
    """
best_params = {
    'vector_size': 100,
    'window': 5,
    'sg': 1, # 0 - CBOW, 1 - Skip-gram
    'negative': 10,
}

texts = [text.split() for text in tqdm(data["prep_text"])]
labels = data["label"].values

cores = multiprocessing.cpu_count()
cores

w2v_model = Word2Vec(
    sentences=texts,
    seed=42,
    workers=cores-1,
    **best_params
)

# Функция: преобразование текста в средний вектор
def get_vector(text, model, vector_size):
    vectors = [model.wv[word] for word in text if word in model.wv]
    return np.mean(vectors, axis=0) if vectors else np.zeros(vector_size)
    
X = np.array([get_vector(text, w2v_model, best_params["vector_size"]) for text in tqdm(texts)])

clf = LogisticRegression(
    max_iter=1000,
    random_state=42
)

skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

all_preds = []
all_true = []

for fold, (train_idx, val_idx) in enumerate(skf.split(X, labels)):
    print(f"\nFold {fold + 1}/{5}")

    X_train, X_val = X[train_idx], X[val_idx]
    y_train, y_val = labels[train_idx], labels[val_idx]

    clf.fit(X_train, y_train)
    y_pred = clf.predict(X_val)

    all_preds.extend(y_pred)
    all_true.extend(y_val)

    acc = accuracy_score(y_val, y_pred)
    f1 = f1_score(y_val, y_pred, average="macro")

    print(f"Fold {fold + 1} — Accuracy: {acc:.4f}, F1: {f1:.4f}")

# Метрики по всем фолдам
final_accuracy = accuracy_score(all_true, all_preds)
final_f1 = f1_score(all_true, all_preds, average="macro")

print(f"\nFinal Accuracy: {final_accuracy:.4f}")
print(f"Final F1 Score: {final_f1:.4f}")
    """
    text = """
best_params = {
    'vector_size': 100,
    'window': 5,
    'sg': 1, # 0 - CBOW, 1 - Skip-gram
    'negative': 10,
}

texts = [text.split() for text in tqdm(data["prep_text"])]
labels = data["label"].values

cores = multiprocessing.cpu_count()
cores

w2v_model = Word2Vec(
    sentences=texts,
    seed=42,
    workers=cores-1,
    **best_params
)

# Функция: преобразование текста в средний вектор
def get_vector(text, model, vector_size):
    vectors = [model.wv[word] for word in text if word in model.wv]
    return np.mean(vectors, axis=0) if vectors else np.zeros(vector_size)
    
X = np.array([get_vector(text, w2v_model, best_params["vector_size"]) for text in tqdm(texts)])

clf = LogisticRegression(
    max_iter=1000,
    random_state=42
)

skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

all_preds = []
all_true = []

for fold, (train_idx, val_idx) in enumerate(skf.split(X, labels)):
    print(f"\nFold {fold + 1}/{5}")

    X_train, X_val = X[train_idx], X[val_idx]
    y_train, y_val = labels[train_idx], labels[val_idx]

    clf.fit(X_train, y_train)
    y_pred = clf.predict(X_val)

    all_preds.extend(y_pred)
    all_true.extend(y_val)

    acc = accuracy_score(y_val, y_pred)
    f1 = f1_score(y_val, y_pred, average="macro")

    print(f"Fold {fold + 1} — Accuracy: {acc:.4f}, F1: {f1:.4f}")

# Метрики по всем фолдам
final_accuracy = accuracy_score(all_true, all_preds)
final_f1 = f1_score(all_true, all_preds, average="macro")

print(f"\nFinal Accuracy: {final_accuracy:.4f}")
print(f"Final F1 Score: {final_f1:.4f}")
    """
    pc.copy(text)
    
    
def part_od_speech_pipeline():
    """
with open("exam_data/pos.json", "r") as f:
    data_pos = json.load(f)
    
sentences = [d["sentence"].split() for d in data_pos]
tags = [d["tags"] for d in data_pos]

lens = [len(i) for i in sentences]
quant = torch.quantile(torch.tensor(lens, dtype=torch.float32), 0.75)
print(quant)

new_sentences = [d["sentence"].split() for d in data_pos if len(d["sentence"].split()) <= quant]
new_tags = [d["tags"] for d in data_pos if len(d["sentence"].split()) <= quant]

print(len(new_sentences), len(new_tags))

X_train, X_test, y_train, y_test = train_test_split(new_sentences, new_tags, test_size=0.2, random_state=42)

special = ["<PAD>", "<UNK>", "<beg>", "<end>"]

count_words_X = Counter(word for words in X_train for word in words)
vocab_X = {word: len(special)+i for i, (word, _) in enumerate(count_words_X.most_common())}

count_words_y = Counter(word for words in y_train for word in words)
vocab_y = {word: len(special)+i for i, (word, _) in enumerate(count_words_y.most_common())}

for i, spe in enumerate(special):
    vocab_X[spe] = i
    vocab_y[spe] = i
    
class POSTaggingDataset(Dataset):
    def __init__(self, vocab_X, vocab_y, X, y, max_len):
        self.X = []
        for sent in X:
            tokens = [vocab_X.get(i, 1) for i in sent]   # vocab_X.get(i, 1), 1 = unk
            if len(tokens) < max_len:
                tokens += [0] * (max_len - len(tokens))  # 0 = pad
            self.X.append(tokens)

        self.y = []
        for sent in y:
            tokens = [vocab_y.get(i, 1) for i in sent]   # vocab_y.get(i, 1), 1 = unk
            if len(tokens) < max_len:
                tokens += [0] * (max_len - len(tokens))  # 0 = pad
            self.y.append(tokens)

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        return torch.tensor(self.X[idx], dtype=torch.long), torch.tensor(self.y[idx], dtype=torch.long)
        
class POSTaggingModel(nn.Module):
    def __init__(self, vocab_size, embed_dim, hidden_size, num_classes, pad_idx=0):
        super().__init__()

        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=pad_idx)
        self.rnn = nn.LSTM(input_size=embed_dim, hidden_size=hidden_size, batch_first=True)

        self.fc1 = nn.Linear(hidden_size, 32)
        self.fc2 = nn.Linear(32, num_classes)
        self.relu = nn.ReLU()

    def forward(self, x):
        embedded = self.embedding(x)
        outputs, (h, c) = self.rnn(embedded)
        logits = self.fc2(self.relu(self.fc1(outputs))) # вводим o потому что нужны токены каждого слова
        return logits
        
def train_model_pos(model, train_loader, test_loader, epochs=10, lr=0.0001):
    device = torch.device('cpu')
    model = model.to(device)
    criterion = nn.CrossEntropyLoss(ignore_index=0)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr)
    
    train_losses, test_accs = [], []
    start_time = time.time()
    
    for epoch in range(epochs):
        model.train()
        total_loss = 0
        train_labels = []
        train_outputs = []
        for inputs, labels in train_loader:
            inputs, labels = inputs.to(device), labels.to(device)
            
            optimizer.zero_grad()
            outputs = model(inputs)
#             print(outputs.shape)
#             print(outputs.view(-1, outputs.shape[-1]).shape)
#             print(labels.long().shape)
#             print(labels.view(-1).shape)
            loss = criterion(outputs.view(-1, outputs.shape[-1]), labels.long().view(-1))
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            preds = torch.argmax(outputs, dim=-1)
            
            mask = labels != 0  # паддинг маска
            train_outputs.extend(preds[mask].tolist())
            train_labels.extend(labels[mask].tolist())
            
        train_losses.append(total_loss / len(train_loader))
        acc_train = accuracy_score(train_labels, train_outputs)
        
        # Оценка на тестовых данных
        model.eval()
        correct, total = 0, 0
        test_labels = []
        test_outputs = []
        with torch.no_grad():
            for inputs, labels in test_loader:
                inputs, labels = inputs.to(device), labels.to(device)
                outputs = model(inputs)
                preds = torch.argmax(outputs, dim=-1)

                mask = labels != 0  # паддинг маска
                test_outputs.extend(preds[mask].tolist())
                test_labels.extend(labels[mask].tolist())
        
        acc_test = accuracy_score(test_labels, test_outputs)
        test_accs.append(acc_test)
        print(f"Epoch {epoch+1}/{epochs} | Loss: {train_losses[-1]:.4f} "
              f"| Acc Train: {acc_train:.4f} | Acc Test: {acc_test:.4f}")
        
    training_time = time.time() - start_time
    print(f'Training Time: {training_time:.2f} seconds')
    return model, train_losses, test_accs, training_time, test_labels, test_outputs
    
    
train_dataset = POSTaggingDataset(vocab_X=vocab_X, vocab_y=vocab_y, X=X_train, y=y_train, max_len=int(quant.item()))
test_dataset = POSTaggingDataset(vocab_X=vocab_X, vocab_y=vocab_y, X=X_test, y=y_test, max_len=int(quant.item()))

train_loader = DataLoader(train_dataset, batch_size=64, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=64)

print(len(vocab_X), len(vocab_y))

x, y = train_dataset[:5]
print(x.shape, y.shape)


vocab_size = len(vocab_X)
embed_dim = 100
hidden_dim = 32
epochs = 250

model, uni_losses, uni_accs, uni_time, test_labels, test_preds = train_model_pos(
    POSTaggingModel(
        vocab_size=vocab_size,
        embed_dim=embed_dim,
        hidden_size=hidden_dim,
        num_classes=len(vocab_y)
    ),
    train_loader, test_loader, epochs
)

idx2tag = {idx: tag for tag, idx in vocab_y.items()}

tag_names = [idx2tag[i] for i in sorted(idx2tag) if i > 1]
tag_indices = list(range(2, len(idx2tag)))  

print("Classification Report:")
print(classification_report(test_labels, test_preds, labels=tag_indices, target_names=tag_names))

idx2word = {idx: word for word, idx in vocab_X.items()}

model.eval()
with torch.no_grad():
    for x_sample, y_sample in test_loader:
        x_sample, y_sample = x_sample[0:1], y_sample[0:1]
        logits = model(x_sample)  
        preds = torch.argmax(logits, dim=-1)  
        break 


x_tokens = [idx2word.get(idx.item(), "<UNK>") for idx in x_sample[0] if idx.item() != 0]
y_true_tags = [idx2tag.get(idx.item(), "<UNK>") for idx in y_sample[0] if idx.item() != 0]
y_pred_tags = [idx2tag.get(idx.item(), "<UNK>") for idx in preds[0] if idx.item() != 0]


print(f"{'word':15} | {'true':15} | {'pred'}")
print('-------------------------------------------')
for token, true_tag, pred_tag in zip(x_tokens, y_true_tags, y_pred_tags):
    print(f"{token:15} | {true_tag:15} | {pred_tag}")
    """
    text = """
with open("exam_data/pos.json", "r") as f:
    data_pos = json.load(f)
    
sentences = [d["sentence"].split() for d in data_pos]
tags = [d["tags"] for d in data_pos]

lens = [len(i) for i in sentences]
quant = torch.quantile(torch.tensor(lens, dtype=torch.float32), 0.75)
print(quant)

new_sentences = [d["sentence"].split() for d in data_pos if len(d["sentence"].split()) <= quant]
new_tags = [d["tags"] for d in data_pos if len(d["sentence"].split()) <= quant]

print(len(new_sentences), len(new_tags))

X_train, X_test, y_train, y_test = train_test_split(new_sentences, new_tags, test_size=0.2, random_state=42)

special = ["<PAD>", "<UNK>", "<beg>", "<end>"]

count_words_X = Counter(word for words in X_train for word in words)
vocab_X = {word: len(special)+i for i, (word, _) in enumerate(count_words_X.most_common())}

count_words_y = Counter(word for words in y_train for word in words)
vocab_y = {word: len(special)+i for i, (word, _) in enumerate(count_words_y.most_common())}

for i, spe in enumerate(special):
    vocab_X[spe] = i
    vocab_y[spe] = i
    
class POSTaggingDataset(Dataset):
    def __init__(self, vocab_X, vocab_y, X, y, max_len):
        self.X = []
        for sent in X:
            tokens = [vocab_X.get(i, 1) for i in sent]   # vocab_X.get(i, 1), 1 = unk
            if len(tokens) < max_len:
                tokens += [0] * (max_len - len(tokens))  # 0 = pad
            self.X.append(tokens)

        self.y = []
        for sent in y:
            tokens = [vocab_y.get(i, 1) for i in sent]   # vocab_y.get(i, 1), 1 = unk
            if len(tokens) < max_len:
                tokens += [0] * (max_len - len(tokens))  # 0 = pad
            self.y.append(tokens)

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        return torch.tensor(self.X[idx], dtype=torch.long), torch.tensor(self.y[idx], dtype=torch.long)
        
class POSTaggingModel(nn.Module):
    def __init__(self, vocab_size, embed_dim, hidden_size, num_classes, pad_idx=0):
        super().__init__()

        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=pad_idx)
        self.rnn = nn.LSTM(input_size=embed_dim, hidden_size=hidden_size, batch_first=True)

        self.fc1 = nn.Linear(hidden_size, 32)
        self.fc2 = nn.Linear(32, num_classes)
        self.relu = nn.ReLU()

    def forward(self, x):
        embedded = self.embedding(x)
        outputs, (h, c) = self.rnn(embedded)
        logits = self.fc2(self.relu(self.fc1(outputs))) # вводим o потому что нужны токены каждого слова
        return logits
        
def train_model_pos(model, train_loader, test_loader, epochs=10, lr=0.0001):
    device = torch.device('cpu')
    model = model.to(device)
    criterion = nn.CrossEntropyLoss(ignore_index=0)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr)
    
    train_losses, test_accs = [], []
    start_time = time.time()
    
    for epoch in range(epochs):
        model.train()
        total_loss = 0
        train_labels = []
        train_outputs = []
        for inputs, labels in train_loader:
            inputs, labels = inputs.to(device), labels.to(device)
            
            optimizer.zero_grad()
            outputs = model(inputs)
#             print(outputs.shape)
#             print(outputs.view(-1, outputs.shape[-1]).shape)
#             print(labels.long().shape)
#             print(labels.view(-1).shape)
            loss = criterion(outputs.view(-1, outputs.shape[-1]), labels.long().view(-1))
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            preds = torch.argmax(outputs, dim=-1)
            
            mask = labels != 0  # паддинг маска
            train_outputs.extend(preds[mask].tolist())
            train_labels.extend(labels[mask].tolist())
            
        train_losses.append(total_loss / len(train_loader))
        acc_train = accuracy_score(train_labels, train_outputs)
        
        # Оценка на тестовых данных
        model.eval()
        correct, total = 0, 0
        test_labels = []
        test_outputs = []
        with torch.no_grad():
            for inputs, labels in test_loader:
                inputs, labels = inputs.to(device), labels.to(device)
                outputs = model(inputs)
                preds = torch.argmax(outputs, dim=-1)

                mask = labels != 0  # паддинг маска
                test_outputs.extend(preds[mask].tolist())
                test_labels.extend(labels[mask].tolist())
        
        acc_test = accuracy_score(test_labels, test_outputs)
        test_accs.append(acc_test)
        print(f"Epoch {epoch+1}/{epochs} | Loss: {train_losses[-1]:.4f} "
              f"| Acc Train: {acc_train:.4f} | Acc Test: {acc_test:.4f}")
        
    training_time = time.time() - start_time
    print(f'Training Time: {training_time:.2f} seconds')
    return model, train_losses, test_accs, training_time, test_labels, test_outputs
    
    
train_dataset = POSTaggingDataset(vocab_X=vocab_X, vocab_y=vocab_y, X=X_train, y=y_train, max_len=int(quant.item()))
test_dataset = POSTaggingDataset(vocab_X=vocab_X, vocab_y=vocab_y, X=X_test, y=y_test, max_len=int(quant.item()))

train_loader = DataLoader(train_dataset, batch_size=64, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=64)

print(len(vocab_X), len(vocab_y))

x, y = train_dataset[:5]
print(x.shape, y.shape)


vocab_size = len(vocab_X)
embed_dim = 100
hidden_dim = 32
epochs = 250

model, uni_losses, uni_accs, uni_time, test_labels, test_preds = train_model_pos(
    POSTaggingModel(
        vocab_size=vocab_size,
        embed_dim=embed_dim,
        hidden_size=hidden_dim,
        num_classes=len(vocab_y)
    ),
    train_loader, test_loader, epochs
)

idx2tag = {idx: tag for tag, idx in vocab_y.items()}

tag_names = [idx2tag[i] for i in sorted(idx2tag) if i > 1]
tag_indices = list(range(2, len(idx2tag)))  

print("Classification Report:")
print(classification_report(test_labels, test_preds, labels=tag_indices, target_names=tag_names))

idx2word = {idx: word for word, idx in vocab_X.items()}

model.eval()
with torch.no_grad():
    for x_sample, y_sample in test_loader:
        x_sample, y_sample = x_sample[0:1], y_sample[0:1]
        logits = model(x_sample)  
        preds = torch.argmax(logits, dim=-1)  
        break 


x_tokens = [idx2word.get(idx.item(), "<UNK>") for idx in x_sample[0] if idx.item() != 0]
y_true_tags = [idx2tag.get(idx.item(), "<UNK>") for idx in y_sample[0] if idx.item() != 0]
y_pred_tags = [idx2tag.get(idx.item(), "<UNK>") for idx in preds[0] if idx.item() != 0]


print(f"{'word':15} | {'true':15} | {'pred'}")
print('-------------------------------------------')
for token, true_tag, pred_tag in zip(x_tokens, y_true_tags, y_pred_tags):
    print(f"{token:15} | {true_tag:15} | {pred_tag}")
    """
    pc.copy(text)
    
    
def text_generation_pipeline():
    """
with open('exam_data/quotes.json', 'r', encoding='utf-8') as file:
    data_quotes = json.load(file)
    
special = ["<PAD>", "<SOS>", "<EOS>"]

authors = list(set([re.sub(r"[^a-zA-Z\s]", "", aut["Author"]).strip() for aut in data_quotes]))
authors = [aut for aut in authors if len(aut) <= 50]
tokenizer = {letter:i+2 for i, letter in enumerate(list(set([nn for n in authors for nn in n])))}

for i, spe in enumerate(special):
    tokenizer[spe] = i
    
class NameDataset(Dataset):
    def __init__(self, df, tokenizer, max_len):
        self.df = df
        self.tokenizer = tokenizer
        self.max_len = max_len

        # uniq = df['класс'].unique()
        # self.label = {cls: idx for idx, cls in enumerate(uniq)}


    def __len__(self):
        return len(self.df)


    def __getitem__(self, idx):
        row = self.df[idx]
        name = row#['имя']
        # cls = row['класс']
        tokens = [self.tokenizer[i] for i in name]

        tokens = [1] + tokens + [2] + [0] * (self.max_len - len(tokens)) # add start and end

        return torch.tensor(tokens[:-1], dtype=torch.long), torch.tensor(tokens[1:], dtype=torch.long)
        # return torch.tensor(tokens, dtype=torch.long), torch.tensor(self.label[cls], dtype=torch.long)
        
max_len = max([len(aut) for aut in authors])
names = NameDataset(authors, tokenizer, max_len)

dataloader = DataLoader(names, batch_size=128, shuffle=True)
for x, y in dataloader:
    print(x.shape)
    print(y.shape)
    break
    
def generate_name(model, tokenizer, max_len):
    t2v = {v: k for k, v in tokenizer.items()}

    res = [1]
    h_t = None

    for i in range(max_len):
        input_token = res[-1]
        if input_token == 2:
            break
        logits, h_t = model(torch.tensor([[input_token]], dtype=torch.long), h_t)
        probs = torch.softmax(logits.squeeze(0), dim=-1)
        res.append(torch.multinomial(probs, num_samples=1).item())

    word = [t2v[i] for i in res if i not in [0, 1, 2]]

    return ''.join(word).capitalize()
    
    
class NameModel(nn.Module):
    def __init__(self, vocab_size, embedding_size, hidden_size):
        super().__init__()

        self.embedding = nn.Embedding(vocab_size, embedding_size, padding_idx=0)
        self.rnn = nn.GRU(embedding_size, hidden_size, batch_first=True)
        self.fc = nn.Sequential(
            nn.Linear(hidden_size, 64),
            nn.ReLU(),
            nn.Linear(64, vocab_size)
        )


    def forward(self, x, h_t=None):
        emb_X = self.embedding(x)
        o, h_t = self.rnn(emb_X, h_t)
        b, seq, h = o.size()

        o = o.reshape(b*seq, h)

        logits = self.fc(o)
        return logits, h_t
        
        
vocab_size = len(tokenizer)
embedding_size = 100

hidden_size = 128
epochs = 100

print_out = 5


model = NameModel(vocab_size, embedding_size, hidden_size)
criterion = nn.CrossEntropyLoss(ignore_index=0)
optimizer = torch.optim.AdamW(model.parameters(), lr=0.001)
loss_result = []

for epoch in range(1, epochs+1):
    model.train()
    epoch_loss = 0
    loop = tqdm(dataloader, desc=f"Epoch {epoch}/{epochs}", leave=False)
    for inputs, targets in loop:
        optimizer.zero_grad()

        logits, _ = model(inputs)
        loss = criterion(logits, targets.view(-1))
        loss.backward()
        optimizer.step()
        epoch_loss += loss.item()

    avg_loss = epoch_loss / len(dataloader)
    loss_result.append(avg_loss)

    print(f"Epoch {epoch}/{epochs} - Average Loss: {avg_loss:.4f}")

    if epoch % print_out == 0:
        model.eval()

        print(generate_name(model, tokenizer, max_len))
    """
    text = """
with open('exam_data/quotes.json', 'r', encoding='utf-8') as file:
    data_quotes = json.load(file)
    
special = ["<PAD>", "<SOS>", "<EOS>"]

authors = list(set([re.sub(r"[^a-zA-Z\s]", "", aut["Author"]).strip() for aut in data_quotes]))
authors = [aut for aut in authors if len(aut) <= 50]
tokenizer = {letter:i+2 for i, letter in enumerate(list(set([nn for n in authors for nn in n])))}

for i, spe in enumerate(special):
    tokenizer[spe] = i
    
class NameDataset(Dataset):
    def __init__(self, df, tokenizer, max_len):
        self.df = df
        self.tokenizer = tokenizer
        self.max_len = max_len

        # uniq = df['класс'].unique()
        # self.label = {cls: idx for idx, cls in enumerate(uniq)}


    def __len__(self):
        return len(self.df)


    def __getitem__(self, idx):
        row = self.df[idx]
        name = row#['имя']
        # cls = row['класс']
        tokens = [self.tokenizer[i] for i in name]

        tokens = [1] + tokens + [2] + [0] * (self.max_len - len(tokens)) # add start and end

        return torch.tensor(tokens[:-1], dtype=torch.long), torch.tensor(tokens[1:], dtype=torch.long)
        # return torch.tensor(tokens, dtype=torch.long), torch.tensor(self.label[cls], dtype=torch.long)
        
max_len = max([len(aut) for aut in authors])
names = NameDataset(authors, tokenizer, max_len)

dataloader = DataLoader(names, batch_size=128, shuffle=True)
for x, y in dataloader:
    print(x.shape)
    print(y.shape)
    break
    
def generate_name(model, tokenizer, max_len):
    t2v = {v: k for k, v in tokenizer.items()}

    res = [1]
    h_t = None

    for i in range(max_len):
        input_token = res[-1]
        if input_token == 2:
            break
        logits, h_t = model(torch.tensor([[input_token]], dtype=torch.long), h_t)
        probs = torch.softmax(logits.squeeze(0), dim=-1)
        res.append(torch.multinomial(probs, num_samples=1).item())

    word = [t2v[i] for i in res if i not in [0, 1, 2]]

    return ''.join(word).capitalize()
    
    
class NameModel(nn.Module):
    def __init__(self, vocab_size, embedding_size, hidden_size):
        super().__init__()

        self.embedding = nn.Embedding(vocab_size, embedding_size, padding_idx=0)
        self.rnn = nn.GRU(embedding_size, hidden_size, batch_first=True)
        self.fc = nn.Sequential(
            nn.Linear(hidden_size, 64),
            nn.ReLU(),
            nn.Linear(64, vocab_size)
        )


    def forward(self, x, h_t=None):
        emb_X = self.embedding(x)
        o, h_t = self.rnn(emb_X, h_t)
        b, seq, h = o.size()

        o = o.reshape(b*seq, h)

        logits = self.fc(o)
        return logits, h_t
        
        
vocab_size = len(tokenizer)
embedding_size = 100

hidden_size = 128
epochs = 100

print_out = 5


model = NameModel(vocab_size, embedding_size, hidden_size)
criterion = nn.CrossEntropyLoss(ignore_index=0)
optimizer = torch.optim.AdamW(model.parameters(), lr=0.001)
loss_result = []

for epoch in range(1, epochs+1):
    model.train()
    epoch_loss = 0
    loop = tqdm(dataloader, desc=f"Epoch {epoch}/{epochs}", leave=False)
    for inputs, targets in loop:
        optimizer.zero_grad()

        logits, _ = model(inputs)
        loss = criterion(logits, targets.view(-1))
        loss.backward()
        optimizer.step()
        epoch_loss += loss.item()

    avg_loss = epoch_loss / len(dataloader)
    loss_result.append(avg_loss)

    print(f"Epoch {epoch}/{epochs} - Average Loss: {avg_loss:.4f}")

    if epoch % print_out == 0:
        model.eval()

        print(generate_name(model, tokenizer, max_len))
    """
    pc.copy(text)
    
    
def embedding():
    """
    3 вопрос (20 баллов) Используя базовые операции для работы с тензорами PyTorch, создайте слой, повторяющий логику nn.Embedding из пакета PyTorch. Созданный модуль должен иметь следующие параметры: num_embeddings, embedding_dim, padding_idx, max_norm, norm_type. Продемонстрируйте все возможности разработанного слоя на примерах. Запрещается использовать готовый слой nn.Embedding.

import torch
import torch.nn as nn

class CustomEmbedding(nn.Module):
    def __init__(self, num_embeddings, embedding_dim, padding_idx=None, max_norm=None, norm_type=None):
        super().__init__()
        self.num_embeddings = num_embeddings
        self.embedding_dim = embedding_dim
        self.padding_idx = padding_idx
        self.max_norm = max_norm
        self.norm_type = norm_type
        
        emb_layer = torch.randn(size=(self.num_embeddings, self.embedding_dim))
        self.emb_layer = emb_layer
                    
    def forward(self, x):
        if self.padding_idx is not None:
            self.emb_layer[self.padding_idx] = torch.zeros(self.embedding_dim)
        
        if self.max_norm:
            current_norm = torch.norm(self.emb_layer, dim=1, p=self.norm_type)
            mask = current_norm > self.max_norm
            self.emb_layer[mask] /= current_norm[mask].unsqueeze(1)

        return self.emb_layer[x]

vocab_size = 5
emb_dim = 8

embedding_layer = CustomEmbedding(vocab_size, emb_dim, padding_idx=0, max_norm=1, norm_type=None)
print(embedding_layer(torch.tensor([0, 1, 2, 3, 4])))

    """
    text = """
import torch
import torch.nn as nn

class CustomEmbedding(nn.Module):
    def __init__(self, num_embeddings, embedding_dim, padding_idx=None, max_norm=None, norm_type=None):
        super().__init__()
        self.num_embeddings = num_embeddings
        self.embedding_dim = embedding_dim
        self.padding_idx = padding_idx
        self.max_norm = max_norm
        self.norm_type = norm_type
        
        emb_layer = torch.randn(size=(self.num_embeddings, self.embedding_dim))
        self.emb_layer = emb_layer
                    
    def forward(self, x):
        if self.padding_idx is not None:
            self.emb_layer[self.padding_idx] = torch.zeros(self.embedding_dim)
        
        if self.max_norm:
            current_norm = torch.norm(self.emb_layer, dim=1, p=self.norm_type)
            mask = current_norm > self.max_norm
            self.emb_layer[mask] /= current_norm[mask].unsqueeze(1)

        return self.emb_layer[x]

vocab_size = 5
emb_dim = 8

embedding_layer = CustomEmbedding(vocab_size, emb_dim, padding_idx=0, max_norm=1, norm_type=None)
print(embedding_layer(torch.tensor([0, 1, 2, 3, 4])))
    
    """
    pc.copy(text)

def rnn():
    """
    Реализация RNN
class RNN(nn.Module):
  def __init__(self, input_size, hidden_size):
      super(RNN, self).__init__()
      self.input_size = input_size
      self.hidden_size = hidden_size
      self.RNNCell = nn.RNNCell(input_size, hidden_size)

  def forward(self, x, h=None):
    '''
    x.shape = (batch_size, seq_len, feature_size) - тензор входных данных
    h.shape = (batch_size, hidden_size) - тензор со скрытым состоянием RNN
    '''
    if x.shape[1] == self.input_size:
        x = x.transpose(0, 1)
    batch_size, seq_len, _ = x.shape
    if h is None:
        h = torch.zeros(batch_size, self.hidden_size, device=x.device)
    outputs = torch.zeros(batch_size, seq_len, self.hidden_size, device=x.device)
    for t in range(seq_len):
        h = self.RNNCell(x[:, t, :], h)
        outputs[:, t, :] = h
    return outputs, h

batch_size, seq_len, input_size, hidden_size = 16, 8, 32, 64
inputs1 = torch.randn(batch_size, seq_len, input_size)
model = RNN(input_size, hidden_size)
outputs, h = model(inputs1)

print(outputs.shape)
print(h.shape)
print(torch.allclose(outputs[:, -1, :], h))

    """
    text = """
class RNN(nn.Module):
  def __init__(self, input_size, hidden_size):
      super(RNN, self).__init__()
      self.input_size = input_size
      self.hidden_size = hidden_size
      self.RNNCell = nn.RNNCell(input_size, hidden_size)

  def forward(self, x, h=None):
    '''
    x.shape = (batch_size, seq_len, feature_size) - тензор входных данных
    h.shape = (batch_size, hidden_size) - тензор со скрытым состоянием RNN
    '''
    if x.shape[1] == self.input_size:
        x = x.transpose(0, 1)
    batch_size, seq_len, _ = x.shape
    if h is None:
        h = torch.zeros(batch_size, self.hidden_size, device=x.device)
    outputs = torch.zeros(batch_size, seq_len, self.hidden_size, device=x.device)
    for t in range(seq_len):
        h = self.RNNCell(x[:, t, :], h)
        outputs[:, t, :] = h
    return outputs, h

batch_size, seq_len, input_size, hidden_size = 16, 8, 32, 64
inputs1 = torch.randn(batch_size, seq_len, input_size)
model = RNN(input_size, hidden_size)
outputs, h = model(inputs1)

print(outputs.shape)
print(h.shape)
print(torch.allclose(outputs[:, -1, :], h))
    
    """
    pc.copy(text)
    

def lstm():
    """
    Реализация LSTM

# LSTM

class LSTM(nn.Module):
    def __init__(self, input_size, hidden_size):
        super(LSTM, self).__init__()
        self.input_size = input_size
        self.hidden = hidden_size
        self.lstm = nn.LSTM(input_size, hidden_size, batch_first=True)

    def forward(self, x, h=None):
        batch_size = x.size(0)
        if h is None:
            h_0 = torch.zeros(self.lstm.num_layers, batch_size, self.lstm.hidden_size, device=x.device)
            c_0 = torch.zeros(self.lstm.num_layers, batch_size, self.lstm.hidden_size, device=x.device)
            h = (h_0, c_0)
        outputs, (h, c) = self.lstm(x, h)
        return outputs, h[-1]

batch_size, seq_len, input_size, hidden_size = 16, 8, 32, 64
inputs1 = torch.randn(batch_size, seq_len, input_size)
model = LSTM(input_size, hidden_size)
outputs, h = model(inputs1)

print(outputs.shape)
print(h.shape)
print(torch.allclose(outputs[:, -1, :], h))

    """
    text = """
# LSTM

class LSTM(nn.Module):
    def __init__(self, input_size, hidden_size):
        super(LSTM, self).__init__()
        self.input_size = input_size
        self.hidden = hidden_size
        self.lstm = nn.LSTM(input_size, hidden_size, batch_first=True)

    def forward(self, x, h=None):
        batch_size = x.size(0)
        if h is None:
            h_0 = torch.zeros(self.lstm.num_layers, batch_size, self.lstm.hidden_size, device=x.device)
            c_0 = torch.zeros(self.lstm.num_layers, batch_size, self.lstm.hidden_size, device=x.device)
            h = (h_0, c_0)
        outputs, (h, c) = self.lstm(x, h)
        return outputs, h[-1]

batch_size, seq_len, input_size, hidden_size = 16, 8, 32, 64
inputs1 = torch.randn(batch_size, seq_len, input_size)
model = LSTM(input_size, hidden_size)
outputs, h = model(inputs1)

print(outputs.shape)
print(h.shape)
print(torch.allclose(outputs[:, -1, :], h))
    
    """
    pc.copy(text)
    
    
def gru():
    """
    Реализация GRU

# GRU

# GRU
class GRU(nn.Module):
    def __init__(self, input_size, hidden_size):
        super(GRU, self).__init__()
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.gru = nn.GRU(input_size, hidden_size, batch_first=True)

    def forward(self, x, h=None):
        x = self.embedding(x)
        batch_size = x.size(0)
        if h is None:
            h = torch.zeros(self.gru.num_layers, batch_size, self.gru.hidden_size, device=x.device)
        rnn_out, h = self.gru(x, h)
        h_n = h[-1]
        return rnn_out, h_n

batch_size, seq_len, input_size, hidden_size = 16, 8, 32, 64
inputs1 = torch.randn(batch_size, seq_len, input_size)
model = LSTM(input_size, hidden_size)
outputs, h = model(inputs1)

print(outputs.shape)
print(h.shape)
print(torch.allclose(outputs[:, -1, :], h))

    """
    text = """
    
# GRU
class GRU(nn.Module):
    def __init__(self, input_size, hidden_size):
        super(GRU, self).__init__()
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.gru = nn.GRU(input_size, hidden_size, batch_first=True)

    def forward(self, x, h=None):
        x = self.embedding(x)
        batch_size = x.size(0)
        if h is None:
            h = torch.zeros(self.gru.num_layers, batch_size, self.gru.hidden_size, device=x.device)
        rnn_out, h = self.gru(x, h)
        h_n = h[-1]
        return rnn_out, h_n

batch_size, seq_len, input_size, hidden_size = 16, 8, 32, 64
inputs1 = torch.randn(batch_size, seq_len, input_size)
model = LSTM(input_size, hidden_size)
outputs, h = model(inputs1)

print(outputs.shape)
print(h.shape)
print(torch.allclose(outputs[:, -1, :], h))
    
    """
    pc.copy(text)

    
def RNNCell_and_gate():
    """
    Реализация RNNCell
# RNNCell
import torch
import torch.nn as nn

class MyRNNCell(nn.Module):
    def __init__(self, input_size, hidden_size):
        super(MyRNNCell, self).__init__()
        self.input_size = input_size  # Размер входного вектора (например, размер эмбеддинга слова)
        self.hidden_size = hidden_size  # Размер скрытого состояния

        # Матрица весов для входа (input → hidden)
        self.W_ih = nn.Parameter(torch.Tensor(hidden_size, input_size))

        # Матрица весов для скрытого состояния (hidden → hidden)
        self.W_hh = nn.Parameter(torch.Tensor(hidden_size, hidden_size))

        # Вектор смещения для входа
        self.b_ih = nn.Parameter(torch.Tensor(hidden_size))

        # Вектор смещения для скрытого состояния
        self.b_hh = nn.Parameter(torch.Tensor(hidden_size))

        # Инициализация весов
        self.reset_parameters()

    def reset_parameters(self):
        stdv = 1.0 / torch.sqrt(torch.tensor(self.hidden_size))
        for weight in self.parameters():
            nn.init.uniform_(weight, -stdv, stdv)

    def forward(self, x, h_prev):
        linear_input = torch.mm(x, self.W_ih.t()) + self.b_ih  # W_ih * x + b_ih
        linear_hidden = torch.mm(h_prev, self.W_hh.t()) + self.b_hh  # W_hh * h_prev + b_hh
        h = linear_input + linear_hidden  # Новое скрытое состояние
        return h
    
rnn_cell = MyRNNCell(input_size=10, hidden_size=20)
x = torch.randn(3, 10)  # [batch_size=3, input_size=10]
h_prev = torch.zeros(3, 20)  # Начальное скрытое состояние
h_next = rnn_cell(x, h_prev)  # Новое скрытое состояние
print(h_next.shape)  # [3, 20]

# RNN 1-Gate

import torch
import torch.nn as nn

class OneGateRNNCell(nn.Module):
    def __init__(self, input_size, hidden_size):
        #Инициализация RNN ячейки с одним гейтом.
        #
        #Args:
            #input_size (int): Размер входного вектора
            #hidden_size (int): Размер скрытого состояния
                
        super(OneGateRNNCell, self).__init__()
        self.input_size = input_size
        self.hidden_size = hidden_size

        # Веса для основного преобразования входа
        self.W_ih = nn.Parameter(torch.Tensor(hidden_size, input_size))
        # Веса для основного преобразования скрытого состояния
        self.W_hh = nn.Parameter(torch.Tensor(hidden_size, hidden_size))
        
        # Веса для гейта (объединяет вход и предыдущее состояние)
        self.W_gate = nn.Parameter(torch.Tensor(hidden_size, input_size + hidden_size))
        
        # Смещения для основных преобразований
        self.b_ih = nn.Parameter(torch.Tensor(hidden_size))
        self.b_hh = nn.Parameter(torch.Tensor(hidden_size))
        # Смещение для гейта
        self.b_gate = nn.Parameter(torch.Tensor(hidden_size))

        # Инициализация весов
        self.reset_parameters()

    def reset_parameters(self):
        #Инициализация весов равномерным распределением
        stdv = 1.0 / torch.sqrt(torch.tensor(self.hidden_size))
        for weight in self.parameters():
            nn.init.uniform_(weight, -stdv, stdv)

    def forward(self, x, h_prev):
        #Прямой проход через ячейку.
        #
        #Args:
         #   x (torch.Tensor): Входной тензор размера [batch_size, input_size]
          #  h_prev (torch.Tensor): Предыдущее скрытое состояние [batch_size, hidden_size]
            
        #Returns:
         #   torch.Tensor: Новое скрытое состояние [batch_size, hidden_size]
        
        # Объединяем вход и предыдущее состояние для гейта
        combined = torch.cat((x, h_prev), dim=1)
        
        # Вычисляем гейт (сигмоида дает значение между 0 и 1)
        gate = torch.sigmoid(torch.mm(combined, self.W_gate.t()) + self.b_gate)
        
        candidate = torch.tanh(
            torch.mm(x, self.W_ih.t()) + self.b_ih +  # Вклад от входа
            torch.mm(h_prev, self.W_hh.t()) + self.b_hh  # Вклад от предыдущего состояния
        )
        
        # Комбинируем кандидата и предыдущее состояние с помощью гейта
        h_new = gate * candidate + (1 - gate) * h_prev
        
        return h_new
    
# Создаем ячейку
input_size = 10
hidden_size = 20
rnn_cell = OneGateRNNCell(input_size, hidden_size)

# Создаем тестовые данные
batch_size = 3
x = torch.randn(batch_size, input_size)  # Входные данные
h_prev = torch.zeros(batch_size, hidden_size)  # Начальное скрытое состояние

# Прямой проход
h_new = rnn_cell(x, h_prev)

print("Размер нового скрытого состояния:", h_new.shape)  # [3, 20]

    """
    text = """
# RNNCell
import torch
import torch.nn as nn

class MyRNNCell(nn.Module):
    def __init__(self, input_size, hidden_size):
        super(MyRNNCell, self).__init__()
        self.input_size = input_size  # Размер входного вектора (например, размер эмбеддинга слова)
        self.hidden_size = hidden_size  # Размер скрытого состояния

        # Матрица весов для входа (input → hidden)
        self.W_ih = nn.Parameter(torch.Tensor(hidden_size, input_size))

        # Матрица весов для скрытого состояния (hidden → hidden)
        self.W_hh = nn.Parameter(torch.Tensor(hidden_size, hidden_size))

        # Вектор смещения для входа
        self.b_ih = nn.Parameter(torch.Tensor(hidden_size))

        # Вектор смещения для скрытого состояния
        self.b_hh = nn.Parameter(torch.Tensor(hidden_size))

        # Инициализация весов
        self.reset_parameters()

    def reset_parameters(self):
        stdv = 1.0 / torch.sqrt(torch.tensor(self.hidden_size))
        for weight in self.parameters():
            nn.init.uniform_(weight, -stdv, stdv)

    def forward(self, x, h_prev):
        linear_input = torch.mm(x, self.W_ih.t()) + self.b_ih  # W_ih * x + b_ih
        linear_hidden = torch.mm(h_prev, self.W_hh.t()) + self.b_hh  # W_hh * h_prev + b_hh
        h = linear_input + linear_hidden  # Новое скрытое состояние
        return h
    
rnn_cell = MyRNNCell(input_size=10, hidden_size=20)
x = torch.randn(3, 10)  # [batch_size=3, input_size=10]
h_prev = torch.zeros(3, 20)  # Начальное скрытое состояние
h_next = rnn_cell(x, h_prev)  # Новое скрытое состояние
print(h_next.shape)  # [3, 20]

# RNN 1-Gate

import torch
import torch.nn as nn

class OneGateRNNCell(nn.Module):
    def __init__(self, input_size, hidden_size):
        #Инициализация RNN ячейки с одним гейтом.
        
        #Args:
         #   input_size (int): Размер входного вектора
          #  hidden_size (int): Размер скрытого состояния
        
        super(OneGateRNNCell, self).__init__()
        self.input_size = input_size
        self.hidden_size = hidden_size

        # Веса для основного преобразования входа
        self.W_ih = nn.Parameter(torch.Tensor(hidden_size, input_size))
        # Веса для основного преобразования скрытого состояния
        self.W_hh = nn.Parameter(torch.Tensor(hidden_size, hidden_size))
        
        # Веса для гейта (объединяет вход и предыдущее состояние)
        self.W_gate = nn.Parameter(torch.Tensor(hidden_size, input_size + hidden_size))
        
        # Смещения для основных преобразований
        self.b_ih = nn.Parameter(torch.Tensor(hidden_size))
        self.b_hh = nn.Parameter(torch.Tensor(hidden_size))
        # Смещение для гейта
        self.b_gate = nn.Parameter(torch.Tensor(hidden_size))

        # Инициализация весов
        self.reset_parameters()

    def reset_parameters(self):
        #Инициализация весов равномерным распределением
        stdv = 1.0 / torch.sqrt(torch.tensor(self.hidden_size))
        for weight in self.parameters():
            nn.init.uniform_(weight, -stdv, stdv)

    def forward(self, x, h_prev):
        #Прямой проход через ячейку.
        
        #Args:
         #   x (torch.Tensor): Входной тензор размера [batch_size, input_size]
          #  h_prev (torch.Tensor): Предыдущее скрытое состояние [batch_size, hidden_size]
            
        #Returns:
         #   torch.Tensor: Новое скрытое состояние [batch_size, hidden_size]
         
        # Объединяем вход и предыдущее состояние для гейта
        combined = torch.cat((x, h_prev), dim=1)
        
        # Вычисляем гейт (сигмоида дает значение между 0 и 1)
        gate = torch.sigmoid(torch.mm(combined, self.W_gate.t()) + self.b_gate)
        
        candidate = torch.tanh(
            torch.mm(x, self.W_ih.t()) + self.b_ih +  # Вклад от входа
            torch.mm(h_prev, self.W_hh.t()) + self.b_hh  # Вклад от предыдущего состояния
        )
        
        # Комбинируем кандидата и предыдущее состояние с помощью гейта
        h_new = gate * candidate + (1 - gate) * h_prev
        
        return h_new
    
# Создаем ячейку
input_size = 10
hidden_size = 20
rnn_cell = OneGateRNNCell(input_size, hidden_size)

# Создаем тестовые данные
batch_size = 3
x = torch.randn(batch_size, input_size)  # Входные данные
h_prev = torch.zeros(batch_size, hidden_size)  # Начальное скрытое состояние

# Прямой проход
h_new = rnn_cell(x, h_prev)

print("Размер нового скрытого состояния:", h_new.shape)  # [3, 20]
    
    """
    pc.copy(text)
    

def tf_idf():
    """
    Реализация tf_idf

news = pd.read_csv("exam_data/news.csv")
news["descr_prep"] = news["Description"].progress_apply(preprocessing_text)

M = len(news)
index = {}
inverse_index = defaultdict(list)
for i in range(M):
    index[i] = news["descr_prep"].iloc[i].split()
    for word in news["descr_prep"].iloc[i].split():
        inverse_index[word].append(i)

tfidf = defaultdict(dict)

for k, v in index.items():
    n = len(v)
    x = dict(Counter(v))
    for k1, v1 in x.items():
        x[k1] = (v1 / n) * (np.log10((M+1) / (len(inverse_index[k1])+1)))

    tfidf[k] = x

N = len(inverse_index)
M = len(news)
matr = np.zeros(shape=(M, N))
matr.shape

id_inverse = dict()
counter = 0
for k in inverse_index:
    id_inverse[k] = counter
    counter += 1

for i in range(M):
    for k, v in tfidf[i].items():
        matr[i][id_inverse[k]] = v
        
ex = dict(Counter(news["descr_prep"].iloc[28].split()))
vector = np.zeros(N)
n = len(ex)

for k, v in ex.items():
    ex[k] = (v/n) * (np.log10((M+1) / (len(inverse_index[k])+1)))
    
for k, v in ex.items():
    vector[id_inverse[k]] = v
    
def similarity(x, y):
    return cosine_similarity(x.reshape(1, -1), y.reshape(1, -1))
    
compare = []
for i in range(500):
    res = similarity(matr[i], vector)
    compare.append([i, res[0][0]])
    
compare.sort(key=lambda x: -x[1])

for i in range(0, 6):
    print(f'Документ № {compare[i][0]}')
    print(f'Схожесть по косинусному расстоянию: {compare[i][1]}')
    print(news.iloc[compare[i][0]]["descr_prep"], end='\n\n')

    """
    text = """
    
    Реализация tf_idf

news = pd.read_csv("exam_data/news.csv")
news["descr_prep"] = news["Description"].progress_apply(preprocessing_text)

M = len(news)
index = {}
inverse_index = defaultdict(list)
for i in range(M):
    index[i] = news["descr_prep"].iloc[i].split()
    for word in news["descr_prep"].iloc[i].split():
        inverse_index[word].append(i)

tfidf = defaultdict(dict)

for k, v in index.items():
    n = len(v)
    x = dict(Counter(v))
    for k1, v1 in x.items():
        x[k1] = (v1 / n) * (np.log10((M+1) / (len(inverse_index[k1])+1)))

    tfidf[k] = x

N = len(inverse_index)
M = len(news)
matr = np.zeros(shape=(M, N))
matr.shape

id_inverse = dict()
counter = 0
for k in inverse_index:
    id_inverse[k] = counter
    counter += 1

for i in range(M):
    for k, v in tfidf[i].items():
        matr[i][id_inverse[k]] = v
        
ex = dict(Counter(news["descr_prep"].iloc[28].split()))
vector = np.zeros(N)
n = len(ex)

for k, v in ex.items():
    ex[k] = (v/n) * (np.log10((M+1) / (len(inverse_index[k])+1)))
    
for k, v in ex.items():
    vector[id_inverse[k]] = v
    
def similarity(x, y):
    return cosine_similarity(x.reshape(1, -1), y.reshape(1, -1))
    
compare = []
for i in range(500):
    res = similarity(matr[i], vector)
    compare.append([i, res[0][0]])
    
compare.sort(key=lambda x: -x[1])

for i in range(0, 6):
    print(f'Документ № {compare[i][0]}')
    print(f'Схожесть по косинусному расстоянию: {compare[i][1]}')
    print(news.iloc[compare[i][0]]["descr_prep"], end='\n\n')

    
    """
    pc.copy(text)


def word2vec():
    """
Реализация Word2vec: CBOW, Skip-gram

class W2VDataset(Dataset):
    def __init__(self, data, window_size=5, min_count=20):
        self.window_size = window_size
        self.min_count = min_count
        self.texts = data

        self.tokens = []
        for text in data:
            self.tokens.extend(text)

        self.index, self.idx_token, self.token_idx = self.make_index()
        self.pairs = self.make_pairs()

    def make_index(self):
        counter = Counter(self.tokens)
        vocab = [token for token, count in counter.items() if count >= self.min_count]

        token_idx = {token: idx for idx, token in enumerate(vocab)}
        idx_token = {idx: token for idx, token in enumerate(vocab)}

        index = [
            [token_idx[token] for token in sent if token in token_idx]
            for sent in self.texts
        ]
        return index, idx_token, token_idx

    def make_pairs(self):
        pairs = []
        for sent in self.index:
            for idx, target in enumerate(sent):
                start = max(0, idx - self.window_size)
                end = min(len(sent), idx + self.window_size + 1)
                context = sent[start:idx] + sent[idx+1:end]
                for context_word in context:
                    pairs.append((target, context_word))
        return pairs

    def __len__(self):
        return len(self.pairs)

    def __getitem__(self, idx):
        target, context = self.pairs[idx]
        return torch.tensor(target), torch.tensor(context)

dataset = W2VDataset(data["prep_text"].apply(lambda x: x.split()))
dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)


import torch.nn as nn

class SkipGram(nn.Module):
    def __init__(self, vocab_size, embedding_dim):
        super().__init__()
        self.embeddings = nn.Embedding(vocab_size, embedding_dim)
        self.linear = nn.Linear(embedding_dim, vocab_size)
        self.log_softmax = nn.LogSoftmax(dim=1)

    def forward(self, x):
        x = self.embeddings(x)
        x = self.linear(x)
        x = self.log_softmax(x)
        return x
        
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

def get_nearest_words(model, dataset, word, top_k=3):
    if word not in dataset.token_idx:
        return []

    word_idx = dataset.token_idx[word]
    embs = model.embeddings.weight.detach().numpy()
    word_emb = embs[word_idx]

    similarities = cosine_similarity([word_emb], embs)[0]
    similarities[word_idx] = -1

    top_indices = np.argsort(similarities)[-top_k:][::-1]
    nearest_words = [dataset.idx_token[idx] for idx in top_indices]
    return nearest_words
    
    
import torch.optim as optim
import random

def train(model, dataset, epochs=10, batch_size=64, lr=0.01):
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
    criterion = nn.CrossEntropyLoss() # или кросс энтропия
    optimizer = optim.AdamW(model.parameters(), lr=lr)
    losses = []

    for epoch in tqdm(range(epochs)):
        total_loss = 0
        for target, context in tqdm(dataloader):
            optimizer.zero_grad()
            output = model(target)
            loss = criterion(output, context)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        avg_loss = total_loss / len(dataloader)
        losses.append(avg_loss)
        print()
        print(f"Epoch {epoch+1}/{epochs}, Loss: {avg_loss:.4f}")

        for word in validation_words:
            nearest = get_nearest_words(model, dataset, word)
            print(f"ближайшие слова для {word}: {nearest}")

    return losses

random.seed(42)
validation_words = random.sample(list(dataset.idx_token.values()), 5)
model = SkipGram(vocab_size=len(dataset.idx_token), embedding_dim=100)
losses = train(model, dataset, epochs=10)

    """
    
    text = """
Реализация Word2vec: CBOW, Skip-gram

class W2VDataset(Dataset):
    def __init__(self, data, window_size=5, min_count=20):
        self.window_size = window_size
        self.min_count = min_count
        self.texts = data

        self.tokens = []
        for text in data:
            self.tokens.extend(text)

        self.index, self.idx_token, self.token_idx = self.make_index()
        self.pairs = self.make_pairs()

    def make_index(self):
        counter = Counter(self.tokens)
        vocab = [token for token, count in counter.items() if count >= self.min_count]

        token_idx = {token: idx for idx, token in enumerate(vocab)}
        idx_token = {idx: token for idx, token in enumerate(vocab)}

        index = [
            [token_idx[token] for token in sent if token in token_idx]
            for sent in self.texts
        ]
        return index, idx_token, token_idx

    def make_pairs(self):
        pairs = []
        for sent in self.index:
            for idx, target in enumerate(sent):
                start = max(0, idx - self.window_size)
                end = min(len(sent), idx + self.window_size + 1)
                context = sent[start:idx] + sent[idx+1:end]
                for context_word in context:
                    pairs.append((target, context_word))
        return pairs

    def __len__(self):
        return len(self.pairs)

    def __getitem__(self, idx):
        target, context = self.pairs[idx]
        return torch.tensor(target), torch.tensor(context)

dataset = W2VDataset(data["prep_text"].apply(lambda x: x.split()))
dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)


import torch.nn as nn

class SkipGram(nn.Module):
    def __init__(self, vocab_size, embedding_dim):
        super().__init__()
        self.embeddings = nn.Embedding(vocab_size, embedding_dim)
        self.linear = nn.Linear(embedding_dim, vocab_size)
        self.log_softmax = nn.LogSoftmax(dim=1)

    def forward(self, x):
        x = self.embeddings(x)
        x = self.linear(x)
        x = self.log_softmax(x)
        return x
        
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

def get_nearest_words(model, dataset, word, top_k=3):
    if word not in dataset.token_idx:
        return []

    word_idx = dataset.token_idx[word]
    embs = model.embeddings.weight.detach().numpy()
    word_emb = embs[word_idx]

    similarities = cosine_similarity([word_emb], embs)[0]
    similarities[word_idx] = -1

    top_indices = np.argsort(similarities)[-top_k:][::-1]
    nearest_words = [dataset.idx_token[idx] for idx in top_indices]
    return nearest_words
    
    
import torch.optim as optim
import random

def train(model, dataset, epochs=10, batch_size=64, lr=0.01):
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
    criterion = nn.CrossEntropyLoss() # или кросс энтропия
    optimizer = optim.AdamW(model.parameters(), lr=lr)
    losses = []

    for epoch in tqdm(range(epochs)):
        total_loss = 0
        for target, context in tqdm(dataloader):
            optimizer.zero_grad()
            output = model(target)
            loss = criterion(output, context)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        avg_loss = total_loss / len(dataloader)
        losses.append(avg_loss)
        print()
        print(f"Epoch {epoch+1}/{epochs}, Loss: {avg_loss:.4f}")

        for word in validation_words:
            nearest = get_nearest_words(model, dataset, word)
            print(f"ближайшие слова для {word}: {nearest}")

    return losses

random.seed(42)
validation_words = random.sample(list(dataset.idx_token.values()), 5)
model = SkipGram(vocab_size=len(dataset.idx_token), embedding_dim=100)
losses = train(model, dataset, epochs=10)
        
    """
    pc.copy(text)

def jaccard():
    """
PATH = '/content/sents_pairs.pt'
data = torch.load(PATH)
data.shape

class EmbeddingModel(nn.Module):
    def __init__(self, vocab_size=10000, embedding_dim=128, hidden_dim=256, output_dim=64):
        super().__init__()
        # Слой эмбеддинга (если на входе индексы токенов)
        self.embedding = nn.Embedding(vocab_size, embedding_dim)

        # Полносвязные слои
        self.fc = nn.Sequential(
            nn.Linear(50 * embedding_dim, hidden_dim),  # Разворачиваем в вектор
            nn.ReLU(),
            nn.Linear(hidden_dim, output_dim)  # Финальный эмбединг
        )

    def forward(self, x):
        # x: [batch_size, seq_len] → [batch_size, seq_len, embedding_dim]
        x = self.embedding(x)

        # Разворачиваем в [batch_size, seq_len * embedding_dim]
        x = x.view(x.size(0), -1)

        # Проходим через FC
        return self.fc(x)
        
# Предположим, что:
vocab_size = 10000  # Размер словаря
model = EmbeddingModel(vocab_size=vocab_size)
device = torch.device("cpu")
model = model.to(device)

# Пример данных (у вас уже есть `data`)
data = data.to(device)  # [31125, 2, 50]

def get_embeddings(model, data, batch_size=128):
    model.eval()
    embeddings = []

    with torch.no_grad():
        for i in tqdm(range(0, len(data), batch_size), desc="Generating embeddings"):
            batch = data[i:i + batch_size]  # [batch_size, 2, 50]

            # Получаем эмбединги для обоих предложений в паре
            emb1 = model(batch[:, 0])  # [batch_size, output_dim]
            emb2 = model(batch[:, 1])  # [batch_size, output_dim]

            embeddings.append((emb1, emb2))

    return embeddings

embeddings = get_embeddings(model, data)

def soft_jaccard(emb1, emb2):
   #Вычисляет Soft Jaccard для эмбедингов.

    #Args:
     #   emb1, emb2: Тензоры размерности [batch_size, embedding_dim]

    #Returns:
     #   Тензор коэффициентов Жаккара размерности [batch_size]
    # Минимумы и максимумы по элементам
    intersection = torch.minimum(emb1, emb2).sum(dim=1)
    union = torch.maximum(emb1, emb2).sum(dim=1)

    # Защита от деления на 0
    return intersection / (union + 1e-8)

# Собираем все коэффициенты
jaccard_scores = []
for emb1, emb2 in tqdm(embeddings, desc="Calculating Jaccard"):
    scores = soft_jaccard(emb1, emb2)
    jaccard_scores.append(scores)

jaccard_scores = torch.cat(jaccard_scores)
print("\n Final scores shape:", jaccard_scores.shape)  # [31125]
jaccard_scores.max()
### из вектора дата

from tqdm import tqdm  # Импортируем tqdm

def jaccard(data: torch.Tensor) -> torch.Tensor:
    
    #Вычисляет коэффициент Жаккара для всех пар предложений с прогресс-баром.

    #Args:
     #   data: Тензор размерности [N, 2, L], где N — число пар, L — длина предложений.

    #Returns:
     #   Тензор коэффициентов Жаккара размерности [N].

    N = data.shape[0]
    jaccards = torch.zeros(N)

    # Оборачиваем range в tqdm для отображения прогресса
    for i in tqdm(range(N), desc="Calculating Jaccard scores"):
        s1 = data[i, 0]  # Первое предложение в паре
        s2 = data[i, 1]  # Второе предложение

        # Убираем паддинг (токены с 0) и находим уникальные токены
        unique_s1 = torch.unique(s1[s1 != 0])
        unique_s2 = torch.unique(s2[s2 != 0])

        # Вручную вычисляем пересечение и объединение
        intersection = torch.sum(torch.isin(unique_s1, unique_s2)).float()
        union = len(unique_s1) + len(unique_s2) - intersection

        jaccards[i] = intersection / union if union != 0 else 0.0

    return jaccards
# Пример использования
jaccard_scores = jaccard(data)
jaccard_scores
    """
    
    text = """
PATH = '/content/sents_pairs.pt'
data = torch.load(PATH)
data.shape

class EmbeddingModel(nn.Module):
    def __init__(self, vocab_size=10000, embedding_dim=128, hidden_dim=256, output_dim=64):
        super().__init__()
        # Слой эмбеддинга (если на входе индексы токенов)
        self.embedding = nn.Embedding(vocab_size, embedding_dim)

        # Полносвязные слои
        self.fc = nn.Sequential(
            nn.Linear(50 * embedding_dim, hidden_dim),  # Разворачиваем в вектор
            nn.ReLU(),
            nn.Linear(hidden_dim, output_dim)  # Финальный эмбединг
        )

    def forward(self, x):
        # x: [batch_size, seq_len] → [batch_size, seq_len, embedding_dim]
        x = self.embedding(x)

        # Разворачиваем в [batch_size, seq_len * embedding_dim]
        x = x.view(x.size(0), -1)

        # Проходим через FC
        return self.fc(x)
        
# Предположим, что:
vocab_size = 10000  # Размер словаря
model = EmbeddingModel(vocab_size=vocab_size)
device = torch.device("cpu")
model = model.to(device)

# Пример данных (у вас уже есть `data`)
data = data.to(device)  # [31125, 2, 50]

def get_embeddings(model, data, batch_size=128):
    model.eval()
    embeddings = []

    with torch.no_grad():
        for i in tqdm(range(0, len(data), batch_size), desc="Generating embeddings"):
            batch = data[i:i + batch_size]  # [batch_size, 2, 50]

            # Получаем эмбединги для обоих предложений в паре
            emb1 = model(batch[:, 0])  # [batch_size, output_dim]
            emb2 = model(batch[:, 1])  # [batch_size, output_dim]

            embeddings.append((emb1, emb2))

    return embeddings

embeddings = get_embeddings(model, data)

def soft_jaccard(emb1, emb2):
    #Вычисляет Soft Jaccard для эмбедингов.

    #Args:
     #   emb1, emb2: Тензоры размерности [batch_size, embedding_dim]

    #Returns:
     #   Тензор коэффициентов Жаккара размерности [batch_size]
    # Минимумы и максимумы по элементам
    intersection = torch.minimum(emb1, emb2).sum(dim=1)
    union = torch.maximum(emb1, emb2).sum(dim=1)

    # Защита от деления на 0
    return intersection / (union + 1e-8)

# Собираем все коэффициенты
jaccard_scores = []
for emb1, emb2 in tqdm(embeddings, desc="Calculating Jaccard"):
    scores = soft_jaccard(emb1, emb2)
    jaccard_scores.append(scores)

jaccard_scores = torch.cat(jaccard_scores)
print("\n Final scores shape:", jaccard_scores.shape)  # [31125]
jaccard_scores.max()
### из вектора дата

from tqdm import tqdm  # Импортируем tqdm

def jaccard(data: torch.Tensor) -> torch.Tensor:
    
    #Вычисляет коэффициент Жаккара для всех пар предложений с прогресс-баром.

    #Args:
     #   data: Тензор размерности [N, 2, L], где N — число пар, L — длина предложений.

    #Returns:
     #   Тензор коэффициентов Жаккара размерности [N].

    N = data.shape[0]
    jaccards = torch.zeros(N)

    # Оборачиваем range в tqdm для отображения прогресса
    for i in tqdm(range(N), desc="Calculating Jaccard scores"):
        s1 = data[i, 0]  # Первое предложение в паре
        s2 = data[i, 1]  # Второе предложение

        # Убираем паддинг (токены с 0) и находим уникальные токены
        unique_s1 = torch.unique(s1[s1 != 0])
        unique_s2 = torch.unique(s2[s2 != 0])

        # Вручную вычисляем пересечение и объединение
        intersection = torch.sum(torch.isin(unique_s1, unique_s2)).float()
        union = len(unique_s1) + len(unique_s2) - intersection

        jaccards[i] = intersection / union if union != 0 else 0.0

    return jaccards
# Пример использования
jaccard_scores = jaccard(data)
jaccard_scores
        
    """
    pc.copy(text)
    
    
def jaccard_2_mini():
    """
    # некоторые расчеты брать из реализации tf-idf
ex_token = news["descr_prep"].iloc[28].split()

top = []
top_2 = []
for i in ex_token:
    top.append(inverse_index[i])
    top_2 += inverse_index[i]
    
x = sorted(list(dict(Counter(top_2)).items()), key=lambda x: -x[1])
x[0]

ex = set(ex_token)

result = []
for i, k in x:
    result.append([i, k, k / len(set(news["descr_prep"].iloc[i].split()) | ex)])
    
result.sort(key=lambda x: -x[2])

for i in range(0, 5):
    print(f'Строка № {result[i][0]}\nКоэф. Жаккара: {result[i][2]}\n{news.iloc[result[i][0]]["descr_prep"]}')
    """
    text = """
    # некоторые расчеты брать из реализации tf-idf
ex_token = news["descr_prep"].iloc[28].split()

top = []
top_2 = []
for i in ex_token:
    top.append(inverse_index[i])
    top_2 += inverse_index[i]
    
x = sorted(list(dict(Counter(top_2)).items()), key=lambda x: -x[1])
x[0]

ex = set(ex_token)

result = []
for i, k in x:
    result.append([i, k, k / len(set(news["descr_prep"].iloc[i].split()) | ex)])
    
result.sort(key=lambda x: -x[2])

for i in range(0, 5):
    print(f'Строка № {result[i][0]}\nКоэф. Жаккара: {result[i][2]}\n{news.iloc[result[i][0]]["descr_prep"]}')
    """
    pc.copy(text)