"""
:authors: KingsFrown
:license: Apache License, Version 2.0, see LICENSE file
:copyright: (c) 2025 KingsFrown
"""

from pyperclip import copy

def b():
    copy('''
import pandas as pd
import torch
from sklearn.model_selection import train_test_split
import nltk
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from collections import defaultdict
from torch.utils.data import Dataset, DataLoader
from torch.nn.utils.rnn import pad_sequence
import torch.nn as nn
import torch.optim as optim
from sklearn.metrics import classification_report, accuracy_score

nltk.download('stopwords')

data = pd.read_csv('nlp/tweets_disaster.csv')
X = data['text']
y = data['target']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

stop_words = set(stopwords.words('english'))
stemmer = PorterStemmer()

def preprocess_text(text):
    words = text.split()
    words = [word for word in words if word.lower() not in stop_words]
    words = [stemmer.stem(word) for word in words]
    return ' '.join(words)

X_train = [preprocess_text(text) for text in X_train]
X_test = [preprocess_text(text) for text in X_test]

vocab = defaultdict(lambda: len(vocab))
vocab['<PAD>'] = 0

def text_to_sequence(text, vocab):
    return [vocab[word] for word in text.split()]

X_train_seq = [text_to_sequence(text, vocab) for text in X_train]
X_test_seq = [text_to_sequence(text, vocab) for text in X_test]

label_to_id = {label: idx for idx, label in enumerate(y.unique())}
id_to_label = {idx: label for label, idx in label_to_id.items()}

y_train_num = torch.tensor(y_train.map(label_to_id).values, dtype=torch.float32)
y_test_num = torch.tensor(y_test.map(label_to_id).values, dtype=torch.float32)

class TweetDataset(Dataset):
    def __init__(self, sequences, labels):
        self.sequences = sequences
        self.labels = labels
    
    def __len__(self):
        return len(self.labels)
    
    def __getitem__(self, idx):
        return torch.tensor(self.sequences[idx]), self.labels[idx]

def collate_fn(batch):
    sequences, labels = zip(*batch)
    sequences_padded = pad_sequence(sequences, batch_first=True, padding_value=0)
    return sequences_padded, torch.stack(labels)

train_dataset = TweetDataset(X_train_seq, y_train_num)
test_dataset = TweetDataset(X_test_seq, y_test_num)

batch_size = 64
train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, collate_fn=collate_fn)
test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False, collate_fn=collate_fn)

class RNNModel(nn.Module):
    def __init__(self, vocab_size, embed_dim, hidden_dim, output_dim=1, n_layers=1, bidirectional=False):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.bidirectional = bidirectional
        self.lstm = nn.LSTM(
            embed_dim, 
            hidden_dim, 
            n_layers, 
            batch_first=True,
            bidirectional=bidirectional
        )
        direction_multiplier = 2 if bidirectional else 1
        self.fc = nn.Linear(hidden_dim * direction_multiplier, output_dim)
    
    def forward(self, text):
        embedded = self.embedding(text)
        output, (hidden, cell) = self.lstm(embedded)
        
        if self.bidirectional:
            hidden = torch.cat((hidden[-2,:,:], hidden[-1,:,:]), dim=1)
        else:
            hidden = hidden.squeeze(0)
            
        return self.fc(hidden).squeeze(1)

vocab_size = len(vocab)
embed_dim = 128
hidden_dim = 64
output_dim = 1
n_layers = 1
bidirectional = True

model = RNNModel(vocab_size, embed_dim, hidden_dim, output_dim, n_layers, bidirectional)

criterion = nn.BCEWithLogitsLoss()
optimizer = optim.Adam(model.parameters())

def train(model, iterator, optimizer, criterion):
    model.train()
    epoch_loss = 0
    
    for batch in iterator:
        optimizer.zero_grad()
        text, labels = batch
        predictions = model(text)
        loss = criterion(predictions, labels)
        loss.backward()
        optimizer.step()
        epoch_loss += loss.item()
    
    return epoch_loss / len(iterator)

def evaluate(model, iterator, criterion):
    model.eval()
    epoch_loss = 0
    all_preds = []
    all_labels = []
    
    with torch.no_grad():
        for batch in iterator:
            text, labels = batch
            predictions = model(text)
            loss = criterion(predictions, labels)
            epoch_loss += loss.item()
            
            preds = torch.sigmoid(predictions).round()
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
    
    return epoch_loss / len(iterator), all_preds, all_labels

n_epochs = 10

for epoch in range(n_epochs):
    train_loss = train(model, train_loader, optimizer, criterion)
    valid_loss, valid_preds, valid_labels = evaluate(model, test_loader, criterion)
    
    accuracy = accuracy_score(valid_labels, valid_preds)
    
    print(f'Epoch: {epoch+1:02}')
    print(f'\tTrain Loss: {train_loss:.3f}')
    print(f'\tValid Loss: {valid_loss:.3f}')
    print(f'\tValid Accuracy: {accuracy:.3f}')

_, test_preds, test_labels = evaluate(model, test_loader, criterion)

print(classification_report(test_labels, test_preds, target_names=[id_to_label[0], id_to_label[1]]))
''')
    
def p():
    copy('''
import pandas as pd
import torch
import numpy as np
from sklearn.model_selection import train_test_split
from collections import defaultdict, Counter
from torch.utils.data import Dataset, DataLoader
from torch.nn.utils.rnn import pad_sequence
import torch.nn as nn
import torch.optim as optim
from sklearn.metrics import classification_report, accuracy_score

data = pd.read_json('nlp/pos.json')

X = data['sentence']
y = data['tags']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

word_vocab = defaultdict(lambda: len(word_vocab))
word_vocab['<PAD>'] = 0
word_vocab['<UNK>'] = 1

tag_vocab = defaultdict(lambda: len(tag_vocab))
tag_vocab['<PAD>'] = 0

def text_to_sequence(text, vocab):
    return [vocab[word] if word in vocab else vocab['<UNK>'] for word in text.split()]

def tags_to_sequence(tags, vocab):
    return [vocab[tag] for tag in tags]

X_train_seq = [text_to_sequence(text, word_vocab) for text in X_train]
X_test_seq = [text_to_sequence(text, word_vocab) for text in X_test]

y_train_seq = [tags_to_sequence(tags, tag_vocab) for tags in y_train]
y_test_seq = [tags_to_sequence(tags, tag_vocab) for tags in y_test]

all_tags = [tag for seq in y_train_seq for tag in seq]
tag_counts = Counter(all_tags)

weights = torch.ones(len(tag_vocab))
for tag, id_ in tag_vocab.items():
    if tag != '<PAD>':
        weights[id_] = 1.0 / (tag_counts.get(id_, 1))

weights = weights / weights.mean()

print("Веса классов:")
for tag, id_ in sorted(tag_vocab.items(), key=lambda x: x[1]):
    if tag != '<PAD>':
        print(f"{tag}: {weights[id_]:.4f}")

class POSTagDataset(Dataset):
    def __init__(self, text_sequences, tag_sequences):
        self.text_sequences = text_sequences
        self.tag_sequences = tag_sequences
    
    def __len__(self):
        return len(self.text_sequences)
    
    def __getitem__(self, idx):
        return torch.tensor(self.text_sequences[idx]), torch.tensor(self.tag_sequences[idx])

def collate_fn(batch):
    texts, tags = zip(*batch)
    texts_padded = pad_sequence(texts, batch_first=True, padding_value=0)
    tags_padded = pad_sequence(tags, batch_first=True, padding_value=0)
    return texts_padded, tags_padded

train_dataset = POSTagDataset(X_train_seq, y_train_seq)
test_dataset = POSTagDataset(X_test_seq, y_test_seq)

batch_size = 64
train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, collate_fn=collate_fn)
test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False, collate_fn=collate_fn)

class POSTagModel(nn.Module):
    def __init__(self, vocab_size, embed_dim, hidden_dim, output_dim, n_layers=1, bidirectional=True):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.lstm = nn.LSTM(
            embed_dim, 
            hidden_dim, 
            n_layers, 
            batch_first=True,
            bidirectional=bidirectional
        )
        direction_multiplier = 2 if bidirectional else 1
        self.fc = nn.Linear(hidden_dim * direction_multiplier, output_dim)
    
    def forward(self, text):
        embedded = self.embedding(text)
        lstm_out, _ = self.lstm(embedded)
        tag_space = self.fc(lstm_out)
        return tag_space

vocab_size = len(word_vocab)
embed_dim = 128
hidden_dim = 64
output_dim = len(tag_vocab)
n_layers = 1
bidirectional = True

model = POSTagModel(vocab_size, embed_dim, hidden_dim, output_dim, n_layers, bidirectional)

criterion = nn.CrossEntropyLoss(weight=weights, ignore_index=0)
optimizer = optim.Adam(model.parameters())

def train(model, iterator, optimizer, criterion):
    model.train()
    epoch_loss = 0
    
    for batch in iterator:
        optimizer.zero_grad()
        text, tags = batch
        predictions = model(text)

        predictions = predictions.view(-1, output_dim)
        tags = tags.view(-1)
        
        loss = criterion(predictions, tags)
        loss.backward()
        optimizer.step()
        epoch_loss += loss.item()
    
    return epoch_loss / len(iterator)

def evaluate(model, iterator, criterion):
    model.eval()
    epoch_loss = 0
    all_preds = []
    all_labels = []
    
    with torch.no_grad():
        for batch in iterator:
            text, tags = batch
            predictions = model(text)
            
            predictions = predictions.view(-1, output_dim)
            tags = tags.view(-1)
            
            loss = criterion(predictions, tags)
            epoch_loss += loss.item()
            
            preds = torch.argmax(predictions, dim=1)
            all_preds.extend(preds[tags != 0].cpu().numpy())
            all_labels.extend(tags[tags != 0].cpu().numpy())
    
    return epoch_loss / len(iterator), all_preds, all_labels

n_epochs = 100

for epoch in range(n_epochs):
    train_loss = train(model, train_loader, optimizer, criterion)
    valid_loss, valid_preds, valid_labels = evaluate(model, test_loader, criterion)
    
    accuracy = accuracy_score(valid_labels, valid_preds)
    
    print(f'Epoch: {epoch+1:02}')
    print(f'\tTrain Loss: {train_loss:.3f}')
    print(f'\tValid Loss: {valid_loss:.3f}')
    print(f'\tValid Accuracy: {accuracy:.3f}')

_, test_preds, test_labels = evaluate(model, test_loader, criterion)

id_to_tag = {id_: tag for tag, id_ in tag_vocab.items()}
test_preds_tags = [id_to_tag[idx] for idx in test_preds]
test_labels_tags = [id_to_tag[idx] for idx in test_labels]

print(classification_report(test_labels_tags, test_preds_tags, zero_division=0))      
''')
    
def c(n):
    if n==1:
        copy('''
import pandas as pd
import torch
from sklearn.model_selection import train_test_split

data = pd.read_csv('nlp/tweet_cat.csv')
X = data['text'] 
y = data['type']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
''')
    elif n==2:
        copy('''
import nltk
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer

nltk.download('stopwords')

stop_words = set(stopwords.words('english'))
stemmer = PorterStemmer()

def preprocess_text(text):
    words = text.split()
    words = [word for word in words if word.lower() not in stop_words]
    words = [stemmer.stem(word) for word in words]
    return ' '.join(words)

X_train = [preprocess_text(text) for text in X_train]
X_test = [preprocess_text(text) for text in X_test]
''')
    elif n==3:
        copy('''
from collections import defaultdict
vocab = defaultdict(lambda: len(vocab))
vocab['<PAD>'] = 0

def text_to_sequence(text, vocab):
    return [vocab[word] for word in text.split()]

X_train_seq = [text_to_sequence(text, vocab) for text in X_train]
X_test_seq = [text_to_sequence(text, vocab) for text in X_test]

label_to_id = {label: idx for idx, label in enumerate(y.unique())}
id_to_label = {idx: label for label, idx in label_to_id.items()}

y_train_num = torch.tensor(y_train.map(label_to_id).values)
y_test_num = torch.tensor(y_test.map(label_to_id).values)
''')
    elif n==4:
        copy('''
from torch.utils.data import Dataset, DataLoader
from torch.nn.utils.rnn import pad_sequence
import torch.nn as nn
import torch.optim as optim

class TweetDataset(Dataset):
    def __init__(self, sequences, labels):
        self.sequences = sequences
        self.labels = labels
    
    def __len__(self):
        return len(self.labels)
    
    def __getitem__(self, idx):
        return torch.tensor(self.sequences[idx]), self.labels[idx]


def collate_fn(batch):
    sequences, labels = zip(*batch)
    sequences_padded = pad_sequence(sequences, batch_first=True, padding_value=0)
    return sequences_padded, torch.stack(labels)


train_dataset = TweetDataset(X_train_seq, y_train_num)
test_dataset = TweetDataset(X_test_seq, y_test_num)

batch_size = 64
train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, collate_fn=collate_fn)
test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False, collate_fn=collate_fn)
''')
    elif n==5:
        copy('''
class RNNModel(nn.Module):
    def __init__(self, vocab_size, embed_dim, hidden_dim, output_dim, n_layers=1, bidirectional=False):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.bidirectional = bidirectional
        self.lstm = nn.LSTM(
            embed_dim, 
            hidden_dim, 
            n_layers, 
            batch_first=True,
            bidirectional=bidirectional
        )
        direction_multiplier = 2 if bidirectional else 1
        self.fc = nn.Linear(hidden_dim * direction_multiplier, output_dim)
    
    def forward(self, text):
        embedded = self.embedding(text)
        output, (hidden, cell) = self.lstm(embedded)
        
        if self.bidirectional:
            hidden = torch.cat((hidden[-2,:,:], hidden[-1,:,:]), dim=1)
        else:
            hidden = hidden.squeeze(0)
            
        return self.fc(hidden)

vocab_size = len(vocab)
embed_dim = 128
hidden_dim = 64
output_dim = len(label_to_id)
n_layers = 1
bidirectional = True

model = RNNModel(vocab_size, embed_dim, hidden_dim, output_dim, n_layers, bidirectional)
''')
    elif n==6:
        copy('''
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters())

def train(model, iterator, optimizer, criterion):
    model.train()
    epoch_loss = 0
    
    for batch in iterator:
        optimizer.zero_grad()
        text, labels = batch
        predictions = model(text)
        loss = criterion(predictions, labels)
        loss.backward()
        optimizer.step()
        epoch_loss += loss.item()
    
    return epoch_loss / len(iterator)
''')
    elif n==7:
        copy('''
def evaluate(model, iterator, criterion):
    model.eval()
    epoch_loss = 0
    all_preds = []
    all_labels = []
    
    with torch.no_grad():
        for batch in iterator:
            text, labels = batch
            predictions = model(text)
            loss = criterion(predictions, labels)
            epoch_loss += loss.item()
            all_preds.extend(predictions.argmax(1).tolist())
            all_labels.extend(labels.tolist())
    
    return epoch_loss / len(iterator), all_preds, all_labels
''')
    elif n==8:
        copy('''
n_epochs = 10

for epoch in range(n_epochs):
    train_loss = train(model, train_loader, optimizer, criterion)
    valid_loss, valid_preds, valid_labels = evaluate(model, test_loader, criterion)
    
    print(f'Epoch: {epoch+1:02}')
    print(f'\tTrain Loss: {train_loss:.3f}')
    print(f'\tValid Loss: {valid_loss:.3f}')

from sklearn.metrics import classification_report

_, test_preds, test_labels = evaluate(model, test_loader, criterion)
test_preds = [id_to_label[idx] for idx in test_preds]
test_labels = [id_to_label[idx] for idx in test_labels]

print(classification_report(test_labels, test_preds))
''')