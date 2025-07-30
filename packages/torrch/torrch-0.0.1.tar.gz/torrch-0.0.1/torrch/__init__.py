import pyperclip as pc


def classifier_binary_tfidf():
    s = """import pandas as pd
  import numpy as np
  import time
  import psutil
  import matplotlib.pyplot as plt
  import torch
  import torch.nn as nn
  from torch.utils.data import DataLoader, TensorDataset
  from sklearn.model_selection import train_test_split
  from sklearn.feature_extraction.text import TfidfVectorizer
  from sklearn.metrics import classification_report

  def classifier_binary_tfidf(path_to_csv, text_column, label_column, pos_class, neg_class, epochs=20):
      start_time = time.time()
      process = psutil.Process()
      start_memory = process.memory_info().rss / 1024 ** 2

      df = pd.read_csv(path_to_csv)
      df = df[df[label_column].isin([pos_class, neg_class])].copy()
      df[label_column] = df[label_column].map({neg_class: 0, pos_class: 1})

      X_train, X_test, y_train, y_test = train_test_split(
          df[text_column], df[label_column], test_size=0.2, stratify=df[label_column], random_state=42
      )

      vectorizer = TfidfVectorizer(max_features=5000)
      X_train_vec = torch.tensor(vectorizer.fit_transform(X_train).toarray(), dtype=torch.float32)
      X_test_vec = torch.tensor(vectorizer.transform(X_test).toarray(), dtype=torch.float32)

      y_train_tensor = torch.tensor(y_train.values, dtype=torch.long)
      y_test_tensor = torch.tensor(y_test.values, dtype=torch.long)

      train_loader = DataLoader(TensorDataset(X_train_vec, y_train_tensor), batch_size=64, shuffle=True)
      test_loader = DataLoader(TensorDataset(X_test_vec, y_test_tensor), batch_size=64)

      input_dim = X_train_vec.shape[1]
      model = nn.Sequential(
          nn.Linear(input_dim, 5),
          nn.ReLU(),
          nn.Linear(5, 2)
      )

      optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
      criterion = nn.CrossEntropyLoss()

      losses = []
      for epoch in range(epochs):
          total_loss = 0
          model.train()
          for x_batch, y_batch in train_loader:
              out = model(x_batch)
              loss = criterion(out, y_batch)
              optimizer.zero_grad()
              loss.backward()
              optimizer.step()
              total_loss += loss.item()
          losses.append(total_loss / len(train_loader))
          if (epoch+1) % 5 == 0 or epoch == 0:
              print(f"Epoch {epoch+1}, Loss: {losses[-1]:.4f}")

      plt.figure(figsize=(8, 4))
      plt.plot(range(1, epochs+1), losses, marker='o')
      plt.title("График потерь")
      plt.xlabel("Эпоха")
      plt.ylabel("Loss")
      plt.grid()
      plt.show()

      model.eval()
      y_true, y_pred = [], []
      with torch.no_grad():
          for x_batch, y_batch in test_loader:
              out = model(x_batch)
              pred = torch.argmax(out, dim=1)
              y_true.extend(y_batch.tolist())
              y_pred.extend(pred.tolist())

      print(classification_report(y_true, y_pred))

      end_time = time.time()
      end_memory = process.memory_info().rss / 1024 ** 2
      print(f"Время выполнения: {end_time - start_time:.2f} секунд")
      print(f"Память: {end_memory - start_memory:.2f} MB")

  classifier_binary_tfidf(
    path_to_csv="activities.csv",
    text_column="Text",
    label_column="Review-Activity",
    pos_class="ACTIVITY",
    neg_class="REVIEW"
)
  """
    return pc.copy(s)


def classifier_multiclass_tfidf():
    s = """def classifier_multiclass_tfidf(path_to_csv, text_column, label_column, epochs=20):
      start_time = time.time()
      process = psutil.Process()
      start_memory = process.memory_info().rss / 1024 ** 2

      df = pd.read_csv(path_to_csv)
      df = df[[text_column, label_column]].dropna().copy()
      label2id = {label: idx for idx, label in enumerate(df[label_column].unique())}
      df[label_column] = df[label_column].map(label2id)

      X_train, X_test, y_train, y_test = train_test_split(
          df[text_column], df[label_column], test_size=0.2, stratify=df[label_column], random_state=42
      )

      vectorizer = TfidfVectorizer(max_features=5000)
      X_train_vec = torch.tensor(vectorizer.fit_transform(X_train).toarray(), dtype=torch.float32)
      X_test_vec = torch.tensor(vectorizer.transform(X_test).toarray(), dtype=torch.float32)

      y_train_tensor = torch.tensor(y_train.values, dtype=torch.long)
      y_test_tensor = torch.tensor(y_test.values, dtype=torch.long)

      train_loader = DataLoader(TensorDataset(X_train_vec, y_train_tensor), batch_size=64, shuffle=True)
      test_loader = DataLoader(TensorDataset(X_test_vec, y_test_tensor), batch_size=64)

      input_dim = X_train_vec.shape[1]
      n_classes = len(label2id)
      model = nn.Sequential(
          nn.Linear(input_dim, 5),
          nn.ReLU(),
          nn.Linear(5, n_classes)
      )

      optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
      criterion = nn.CrossEntropyLoss()

      losses = []
      for epoch in range(epochs):
          total_loss = 0
          model.train()
          for x_batch, y_batch in train_loader:
              out = model(x_batch)
              loss = criterion(out, y_batch)
              optimizer.zero_grad()
              loss.backward()
              optimizer.step()
              total_loss += loss.item()
          losses.append(total_loss / len(train_loader))
          if (epoch+1) % 5 == 0 or epoch == 0:
              print(f"Epoch {epoch+1}, Loss: {losses[-1]:.4f}")

      plt.figure(figsize=(8, 4))
      plt.plot(range(1, epochs+1), losses, marker='o')
      plt.title("График потерь")
      plt.xlabel("Эпоха")
      plt.ylabel("Loss")
      plt.grid()
      plt.show()

      model.eval()
      y_true, y_pred = [], []
      with torch.no_grad():
          for x_batch, y_batch in test_loader:
              out = model(x_batch)
              pred = torch.argmax(out, dim=1)
              y_true.extend(y_batch.tolist())
              y_pred.extend(pred.tolist())

      print(classification_report(y_true, y_pred))

      end_time = time.time()
      end_memory = process.memory_info().rss / 1024 ** 2
      print(f"Время выполнения: {end_time - start_time:.2f} секунд")
      print(f"Память: {end_memory - start_memory:.2f} MB")

  classifier_multiclass_tfidf(
    path_to_csv="tweet_cat.csv",
    text_column="text",
    label_column="type"
    )

  """
    return pc.copy(s)


def rrn_model():
    s = """  import time
  import psutil
  import torch
  import torch.nn as nn
  import torch.optim as optim
  import numpy as np
  import pandas as pd
  import matplotlib.pyplot as plt
  from sklearn.model_selection import train_test_split
  from sklearn.metrics import classification_report
  from sklearn.preprocessing import LabelEncoder
  from sklearn.feature_extraction.text import TfidfVectorizer
  from torch.utils.data import DataLoader, TensorDataset
  from torch.nn.utils.rnn import pad_sequence
  from collections import Counter

  from torch.nn import Embedding
  from torch.nn.utils.rnn import pack_padded_sequence, pad_packed_sequence


  def rrn_model(
      path_to_csv,
      text_column,
      label_column,
      model_type="lstm",          # "rnn", "gru"
      vectorizer_type="embedding",  # "tfidf" or "embedding"
      bidirectional=False,
      batch_size=64,
      num_epochs=5,
      max_vocab_size=10000,
      embedding_dim=100,
      max_seq_len=100
  ):
      start_time = time.time()
      process = psutil.Process()

      df = pd.read_csv(path_to_csv)
      df = df[[text_column, label_column]].dropna()

      texts = df[text_column].astype(str).str.lower()
      labels = df[label_column].astype(str)  # important

      label_encoder = LabelEncoder()
      y = label_encoder.fit_transform(labels)
      n_classes = len(label_encoder.classes_)

      X_train_texts, X_test_texts, y_train, y_test = train_test_split(
          texts, y, stratify=y, random_state=42
      )

      if vectorizer_type == "tfidf":
          # TF-IDF vectorization
          vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=5000)  # включаем биграммы!
          X_train = torch.tensor(vectorizer.fit_transform(X_train_texts).toarray(), dtype=torch.float32)
          X_test = torch.tensor(vectorizer.transform(X_test_texts).toarray(), dtype=torch.float32)

          input_dim = X_train.shape[1]
          train_dataset = TensorDataset(X_train, torch.tensor(y_train))
          test_dataset = TensorDataset(X_test, torch.tensor(y_test))

      else:
          # for embedding
          def tokenize(text):
              return text.split()

          counter = Counter()
          for text in X_train_texts:
              counter.update(tokenize(text))

          vocab = {word: i + 2 for i, (word, _) in enumerate(counter.most_common(max_vocab_size))}
          vocab["<PAD>"] = 0
          vocab["<UNK>"] = 1

          def encode(text):
              return [vocab.get(token, 1) for token in tokenize(text)][:max_seq_len]

          def pad_encoded(encoded):
              return torch.tensor(encoded + [0] * (max_seq_len - len(encoded)))

          X_train = [pad_encoded(encode(text)) for text in X_train_texts]
          X_test = [pad_encoded(encode(text)) for text in X_test_texts]

          X_train = torch.stack(X_train)
          X_test = torch.stack(X_test)

          train_dataset = TensorDataset(X_train, torch.tensor(y_train))
          test_dataset = TensorDataset(X_test, torch.tensor(y_test))

          input_dim = X_train.shape[1]

      train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
      test_loader = DataLoader(test_dataset, batch_size=batch_size)

      class RecurrentClassifier(nn.Module):
          def __init__(self, model_type, input_dim, hidden_dim=64, num_classes=2, bidirectional=False):
              super().__init__()
              self.bidirectional = bidirectional
              self.model_type = model_type

              if vectorizer_type == "embedding":
                  self.embedding = Embedding(len(vocab), embedding_dim, padding_idx=0)
                  rnn_input_dim = embedding_dim
              else:
                  rnn_input_dim = input_dim

              if model_type == "rnn":
                  self.rnn = nn.RNN(rnn_input_dim, hidden_dim, batch_first=True, bidirectional=bidirectional)
              elif model_type == "gru":
                  self.rnn = nn.GRU(rnn_input_dim, hidden_dim, batch_first=True, bidirectional=bidirectional)
              elif model_type == "lstm":
                  self.rnn = nn.LSTM(rnn_input_dim, hidden_dim, batch_first=True, bidirectional=bidirectional)

              multiplier = 2 if bidirectional else 1
              self.fc = nn.Linear(hidden_dim * multiplier, num_classes)

          def forward(self, x):
              if vectorizer_type == "embedding":
                  x = self.embedding(x)
              else:
                  x = x.unsqueeze(1)  # [B, 1, input_dim]

              if self.model_type == "lstm":
                  output, (hn, cn) = self.rnn(x)
              else:
                  output, hn = self.rnn(x)

              if self.bidirectional:
                  out = torch.cat((hn[-2], hn[-1]), dim=1)
              else:
                  out = hn[-1]

              return self.fc(out)

      model = RecurrentClassifier(
          model_type=model_type,
          input_dim=input_dim,
          num_classes=n_classes,
          bidirectional=bidirectional
      )

      device = "cuda" if torch.cuda.is_available() else "cpu"
      model.to(device)

      criterion = nn.CrossEntropyLoss()
      optimizer = optim.Adam(model.parameters(), lr=0.001)

      train_losses = []

      for epoch in range(num_epochs):
          model.train()
          epoch_loss = 0

          for xb, yb in train_loader:
              xb, yb = xb.to(device), yb.to(device)

              preds = model(xb)
              loss = criterion(preds, yb)

              loss.backward()
              optimizer.step()
              optimizer.zero_grad()

              epoch_loss += loss.item()

          train_losses.append(epoch_loss / len(train_loader))
          print(f"Epoch {epoch+1}/{num_epochs} - Loss: {epoch_loss:.4f}")

      plt.plot(train_losses)
      plt.title("Train Loss")
      plt.xlabel("Epoch")
      plt.ylabel("Loss")
      plt.grid(True)
      plt.show()

      model.eval()
      y_true, y_pred = [], []

      with torch.no_grad():
          for xb, yb in test_loader:
              xb = xb.to(device)
              preds = model(xb)
              y_true.extend(yb.cpu().numpy())
              y_pred.extend(torch.argmax(preds, dim=1).cpu().numpy())

      print(classification_report(
          y_true,
          y_pred,
          target_names=[str(cls) for cls in label_encoder.classes_]
      ))

      print(f"\nTotal Time: {time.time() - start_time:.2f} sec")
      print(f"RAM Used: {(process.memory_info().rss / 1024 / 1024):.2f} MB")

  rrn_model(
      path_to_csv="news.csv",
      text_column="Description",
      label_column="Class Index",
      model_type="gru",               # "rnn", "lstm", "gru"
      vectorizer_type="tfidf",     # "embedding" or "tfidf"
      bidirectional=True
  )
  """
    return pc.copy(s)


def read_json():
    s = """def load_json_as_dataframe(path, text_key='text', label_key='label'):
    import json
    import pandas as pd

    with open(path, 'r') as f:
        data = json.load(f)

    df = pd.DataFrame(data)
    df = df[[text_key, label_key]].dropna()
    df.columns = ['text', 'label']  # стандартизация
    return df

import json
# 'reviews.json', 'pos.json'
data = []
with open('pos.json', 'r', encoding='utf-8') as f:
    for line in f:
        data.append(json.loads(line))

#  'pos.json', 'quotes.json'
with open('quotes.json', 'r', encoding='utf-8') as f:
    data = json.load(f) """
    return pc.copy(s)


def MyEmbedding():
    s = """import torch
    import torch.nn as nn

    class MyEmbedding(nn.Module):
        def __init__(self,
                    num_embeddings,
                    embedding_dim,
                    max_norm=1.0,
                    norm_type=2,
                    padding_idx=None):
            super().__init__()
            self.emb = nn.Parameter(torch.randn(num_embeddings, embedding_dim))
            self.max_norm = max_norm
            self.norm_type = norm_type
            self.padding_idx = padding_idx

            if self.padding_idx is not None:
                with torch.no_grad():
                    self.emb[self.padding_idx].zero_()

        def forward(self, X):
            norms = torch.norm(self.emb.data, p=self.norm_type, dim=1, keepdim=True)
            mask = norms > self.max_norm
            with torch.no_grad():
                self.emb.data = torch.where(
                    mask,
                    self.emb.data / norms * self.max_norm,
                    self.emb.data
                )
            return self.emb[X]


    model = MyEmbedding(num_embeddings=10, embedding_dim=4, max_norm=1.0, padding_idx=0)
    X = torch.tensor([[1, 2, 0], [3, 4, 5]])
    output = model(X)
    print("Входные индексы:\n", X)
    print("Эмбеддинги:\n", output)"""
    return pc.copy(s)


def rnn_logic():
    s = """import torch
    import torch.nn as nn

    def rnn_logic():
        x_t = torch.randn(1, 5)  # [batch_size, input_size]
        h_prev = torch.zeros(1, 10)  # [batch_size, hidden_size]

        input_size = 5
        hidden_size = 10

        W_ih = torch.randn(input_size, hidden_size)
        W_hh = torch.randn(hidden_size, hidden_size)
        b_ih = torch.randn(hidden_size)
        b_hh = torch.randn(hidden_size)

        # Шаг RNN: h_t = tanh(x_t @ W_ih + b_ih + h_prev @ W_hh + b_hh)
        h_t = torch.tanh(x_t @ W_ih + b_ih + h_prev @ W_hh + b_hh)

        print("x_t:", x_t)
        print("h_prev:", h_prev)
        print("h_t:", h_t)

    rnn_logic()
    """
    return pc.copy(s)


def word2vec_cbow():
    s = """import torch
  import torch.nn as nn
  import torch.optim as optim

  def word2vec_cbow():
      vocab = {'i': 0, 'love': 1, 'nlp': 2, 'pytorch': 3}
      idx2word = {i: w for w, i in vocab.items()}
      vocab_size = len(vocab)
      embedding_dim = 10

      context_target_pairs = [
          ([0, 2], 1),  # 'i', 'nlp' -> 'love'
          ([1, 3], 2),  # 'love', 'pytorch' -> 'nlp'
      ]

      class CBOW(nn.Module):
          def __init__(self, vocab_size, embedding_dim):
              super().__init__()
              self.emb = nn.Embedding(vocab_size, embedding_dim)
              self.linear = nn.Linear(embedding_dim, vocab_size)

          def forward(self, context_idxs):
              emb = self.emb(context_idxs)      # [batch_size, context_len, emb_dim]
              mean_emb = emb.mean(dim=1)        # усреднение
              out = self.linear(mean_emb)
              return out

      model = CBOW(vocab_size, embedding_dim)
      loss_fn = nn.CrossEntropyLoss()
      optimizer = optim.Adam(model.parameters(), lr=0.01)

      for epoch in range(10):
          total_loss = 0
          for context, target in context_target_pairs:
              context_var = torch.tensor([context])  # [1, context_len]
              target_var = torch.tensor([target])    # [1]

              optimizer.zero_grad()
              output = model(context_var)
              loss = loss_fn(output, target_var)
              loss.backward()
              optimizer.step()

              total_loss += loss.item()
          print(f"Epoch {epoch+1}, Loss: {total_loss:.4f}")

  word2vec_cbow()
  """
    return pc.copy(s)


def jaccard_formula():
    a = '''import json
import torch

pairs = np.load('sents_pairs.npy')

# Укажите путь к вашему файлу
file_path = 'sents_pairs_itos.json'

# Открываем и читаем файл
with open(file_path, 'r', encoding='utf-8') as f:
    tokens = json.load(f)

def jaccard_index(set1, set2):
    set1, set2 = set(set1), set(set2)
    intersection = set1 & set2
    union = set1 | set2
    if not union:
        return 0.0
    return len(intersection) / len(union)


jaccard_scores = []

for idx1, idx2 in pairs:
    score = jaccard_index(idx1, idx2)
    jaccard_scores.append(score)

# Если хочешь сохранить в .pt
jaccard_tensor = torch.tensor(jaccard_scores)
# torch.save(jaccard_tensor, 'jaccard.pt')
print(jaccard_tensor)

# np.array(tokens)[pairs[2][0]], np.array(tokens)[pairs[2][1]]'''
    return pc.copy(a)


def word2vec_from_json():
    s = """import json
    import torch
    import torch.nn as nn
    import torch.optim as optim
    import matplotlib.pyplot as plt
    from collections import Counter
    from sklearn.metrics.pairwise import cosine_similarity
    from torch.nn.functional import log_softmax
    import numpy as np

    def word2vec_from_json(json_path, text_key='reviewText', limit=500, context_size=2, embedding_dim=50, epochs=5, word_to_check='filters'):

        texts = []
        with open(json_path, 'r', encoding='utf-8') as f:
            for line in f:
                if limit and len(texts) >= limit:
                    break
                try:
                    obj = json.loads(line)
                    if text_key in obj:
                        texts.append(obj[text_key])
                except:
                    continue

        def tokenize(text):
            return [w.lower() for w in text.split() if w.isalpha()]

        tokens = []
        for text in texts:
            tokens.extend(tokenize(text))

        vocab = list(set(tokens))
        word2idx = {w: i for i, w in enumerate(vocab)}
        idx2word = {i: w for w, i in word2idx.items()}


        data = []
        for text in texts:
            words = tokenize(text)
            for i, word in enumerate(words):
                for j in range(max(0, i - context_size), min(len(words), i + context_size + 1)):
                    if i != j:
                        data.append((word, words[j]))

        data = [(word2idx[a], word2idx[b]) for a, b in data if a in word2idx and b in word2idx]


        class Word2Vec(nn.Module):
            def __init__(self, vocab_size, emb_dim):
                super().__init__()
                self.in_emb = nn.Embedding(vocab_size, emb_dim)
                self.out_emb = nn.Embedding(vocab_size, emb_dim)

            def forward(self, center_words):
                return self.in_emb(center_words)

            def loss(self, center_words, target_words):
                in_vecs = self.in_emb(center_words)
                out_vecs = self.out_emb(target_words)
                scores = torch.matmul(in_vecs, self.out_emb.weight.T)
                return -log_softmax(scores, dim=1).gather(1, target_words.view(-1, 1)).mean()


        model = Word2Vec(len(vocab), embedding_dim)
        optimizer = optim.Adam(model.parameters(), lr=0.01)

        losses = []
        for epoch in range(epochs):
            total_loss = 0
            for i in range(0, len(data), 64):
                batch = data[i:i+64]
                if not batch:
                    continue
                center, context = zip(*batch)
                center = torch.tensor(center)
                context = torch.tensor(context)

                loss = model.loss(center, context)
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                total_loss += loss.item()

            losses.append(total_loss)
            print(f'Epoch {epoch+1}/{epochs}, Loss: {total_loss:.4f}')


        plt.plot(losses)
        plt.title('Loss over Epochs')
        plt.xlabel('Epoch')
        plt.ylabel('Loss')
        plt.grid(True)
        plt.show()


        def find_similar_words(word, top_n=5):
            if word not in word2idx:
                print(f"Слово '{word}' не найдено в словаре.")
                return

            vec = model.in_emb.weight[word2idx[word]].detach().numpy().reshape(1, -1)
            emb_matrix = model.in_emb.weight.detach().numpy()
            sims = cosine_similarity(vec, emb_matrix)[0]
            top_idx = np.argsort(sims)[-top_n-1:-1][::-1]

            print(f"\n Слова, похожие на '{word}':")
            for i in top_idx:
                print(f"{idx2word[i]} (сходство {sims[i]:.3f})")

        find_similar_words(word_to_check)

    word2vec_from_json(
        json_path='reviews.json',
        text_key='reviewText',
        limit=500,
        context_size=2,
        embedding_dim=50,
        word_to_check='filters'  # любое слово из текста
    )"""
    return pc.copy(s)


def jaccard_model():
    s = '''
import torch
import json
from sklearn.model_selection import train_test_split

def calculate_jaccard_labels(sents_pairs_tensor):
    """Вычисляет коэффициенты Жаккара для всех пар в тензоре."""
    num_pairs = sents_pairs_tensor.shape[0]
    jaccard_labels = torch.zeros(num_pairs, dtype=torch.float32)
    PAD_TOKEN_ID = 0

    for i in range(num_pairs):
        sent1_ids = [token_id for token_id in sents_pairs_tensor[i, 0, :].tolist() if token_id != PAD_TOKEN_ID]
        sent2_ids = [token_id for token_id in sents_pairs_tensor[i, 1, :].tolist() if token_id != PAD_TOKEN_ID]

        set1 = set(sent1_ids)
        set2 = set(sent2_ids)

        intersection_len = len(set1.intersection(set2))
        union_len = len(set1.union(set2))

        score = 0.0 if union_len == 0 else intersection_len / union_len
        jaccard_labels[i] = score

    return jaccard_labels

sents_pairs = torch.load('sents_pairs.pt')

jaccard_labels = calculate_jaccard_labels(sents_pairs)

with open('sents_pairs_itos.json', 'r', encoding='utf-8') as f:
    itos = json.load(f)
VOCAB_SIZE = len(itos)
PADDING_IDX = 0

print(f"Данные готовы. Всего пар: {sents_pairs.shape[0]}. Размер словаря: {VOCAB_SIZE}")
print("Пример входных данных (первая пара):", sents_pairs[0])
print("Пример целевого значения (для первой пары):", jaccard_labels[0])

X_train, X_val, y_train, y_val = train_test_split(
    sents_pairs, jaccard_labels, test_size=0.2, random_state=42
)

print(f"Размер обучающей выборки: {X_train.shape[0]}")
print(f"Размер валидационной выборки: {X_val.shape[0]}")



import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader

class JaccardPredictor(nn.Module):
    def __init__(self, vocab_size, embedding_dim, hidden_dim, padding_idx):
        super(JaccardPredictor, self).__init__()

        self.embedding = nn.Embedding(vocab_size, embedding_dim, padding_idx=padding_idx)

        self.lstm = nn.LSTM(embedding_dim, hidden_dim, batch_first=True)

        self.fc1 = nn.Linear(hidden_dim * 2, hidden_dim)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(hidden_dim, 1)
        self.sigmoid = nn.Sigmoid() 

    def forward(self, sent1, sent2):
        emb1 = self.embedding(sent1)
        emb2 = self.embedding(sent2)

        _, (h_n1, _) = self.lstm(emb1)
        _, (h_n2, _) = self.lstm(emb2)

        sent1_vec = h_n1.squeeze(0)
        sent2_vec = h_n2.squeeze(0)

        combined_vec = torch.cat((sent1_vec, sent2_vec), dim=1)

        out = self.fc1(combined_vec)
        out = self.relu(out)
        out = self.fc2(out)

        prediction = self.sigmoid(out)

        return prediction.squeeze(1)



EMBEDDING_DIM = 100
HIDDEN_DIM = 128
BATCH_SIZE = 64
EPOCHS = 5
LEARNING_RATE = 0.00001

train_dataset = TensorDataset(X_train, y_train)
train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)

val_dataset = TensorDataset(X_val, y_val)
val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE)

model = JaccardPredictor(VOCAB_SIZE, EMBEDDING_DIM, HIDDEN_DIM, PADDING_IDX)

criterion = nn.L1Loss()
optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)

print("\nНачинаем обучение модели...")
for epoch in range(EPOCHS):
    model.train() 
    total_train_loss = 0

    for batch_pairs, batch_labels in train_loader:
        sent1 = batch_pairs[:, 0, :]
        sent2 = batch_pairs[:, 1, :]


        optimizer.zero_grad()
        predictions = model(sent1, sent2)
        loss = criterion(predictions, batch_labels)
        loss.backward()
        optimizer.step()

        total_train_loss += loss.item()

    avg_train_loss = total_train_loss / len(train_loader)

    model.eval() 
    total_val_loss = 0
    with torch.no_grad(): 
        for batch_pairs, batch_labels in val_loader:
            sent1 = batch_pairs[:, 0, :]
            sent2 = batch_pairs[:, 1, :]

            predictions = model(sent1, sent2)
            loss = criterion(predictions, batch_labels)
            total_val_loss += loss.item()

    avg_val_loss = total_val_loss / len(val_loader)

    print(f"Эпоха {epoch+1}/{EPOCHS} | Train Loss: {avg_train_loss:.4f} | Val Loss: {avg_val_loss:.4f}")

print("\nОбучение завершено!")

model.eval()
with torch.no_grad():
    sample_pair = X_val[0].unsqueeze(0)
    true_label = y_val[0]

    sent1 = sample_pair[:, 0, :]
    sent2 = sample_pair[:, 1, :]

    prediction = model(sent1, sent2)

    print(f"\nПример предсказания:")
    print(f"Истинный коэффициент Жаккарда: {true_label.item():.4f}")
    print(f"Предсказанный моделью:          {prediction.item():.4f}")'''
    return pc.copy(s)


def CharGenerationRNN():
    a = '''import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import random

# Подготовка данных
text = "hello world. this is a simple test for character level generation."
chars = sorted(list(set(text)))
char2idx = {ch: idx for idx, ch in enumerate(chars)}
idx2char = {idx: ch for ch, idx in char2idx.items()}
vocab_size = len(chars)

# Гиперпараметры
seq_length = 30
hidden_size = 128
num_layers = 1
lr = 0.003
num_epochs = 1000

# Датасет
def get_batches(text, seq_length):
    input_seqs = []
    target_seqs = []
    for i in range(len(text) - seq_length):
        input_seq = text[i:i+seq_length]
        target_seq = text[i+1:i+seq_length+1]
        input_seqs.append([char2idx[ch] for ch in input_seq])
        target_seqs.append([char2idx[ch] for ch in target_seq])
    return torch.tensor(input_seqs), torch.tensor(target_seqs)

X, Y = get_batches(text, seq_length)

# Модель
class CharRNN(nn.Module):
    def __init__(self, vocab_size, hidden_size, num_layers):
        super().__init__()
        self.embed = nn.Embedding(vocab_size, hidden_size)
        self.rnn = nn.RNN(hidden_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, vocab_size)

    def forward(self, x, hidden):
        x = self.embed(x)
        out, hidden = self.rnn(x, hidden)
        out = self.fc(out)
        return out, hidden

model = CharRNN(vocab_size, hidden_size, num_layers)
optimizer = torch.optim.Adam(model.parameters(), lr=lr)
criterion = nn.CrossEntropyLoss()

# Обучение
for epoch in range(num_epochs):
    hidden = torch.zeros(num_layers, X.size(0), hidden_size)
    output, hidden = model(X, hidden)
    loss = criterion(output.view(-1, vocab_size), Y.view(-1))

    optimizer.zero_grad()
    loss.backward()
    optimizer.step()

    if epoch % 100 == 0:
        print(f"Epoch {epoch}, Loss: {loss.item():.4f}")

# Генерация текста
def generate(model, start_seq, length=100):
    model.eval()
    input_seq = torch.tensor([[char2idx[c] for c in start_seq]])
    hidden = torch.zeros(num_layers, 1, hidden_size)
    output_str = start_seq

    for _ in range(length):
        out, hidden = model(input_seq, hidden)
        probs = F.softmax(out[:, -1, :], dim=-1).detach().numpy().flatten()
        char_id = np.random.choice(len(probs), p=probs)
        output_str += idx2char[char_id]
        input_seq = torch.tensor([[char_id]])

    return output_str

print("\nGenerated text:\n", generate(model, "hello "))
'''

    pc.copy(a)


def WordGenerationRNN():
    a = '''import torch
import torch.nn as nn
import torch.nn.functional as F
from collections import Counter
import numpy as np

# Подготовка данных
text = "this is a simple test this is only a test for word level generation"
words = text.split()
vocab = sorted(set(words))
word2idx = {w: i for i, w in enumerate(vocab)}
idx2word = {i: w for w, i in word2idx.items()}
vocab_size = len(vocab)

seq_length = 4
hidden_size = 64
num_layers = 1
lr = 0.01
num_epochs = 500

# Датасет
def get_word_batches(words, seq_length):
    X, Y = [], []
    for i in range(len(words) - seq_length):
        seq_x = words[i:i + seq_length]
        seq_y = words[i + seq_length]
        X.append([word2idx[w] for w in seq_x])
        Y.append(word2idx[seq_y])
    return torch.tensor(X), torch.tensor(Y)

X, Y = get_word_batches(words, seq_length)

# Модель
class WordRNN(nn.Module):
    def __init__(self, vocab_size, hidden_size, num_layers):
        super().__init__()
        self.embed = nn.Embedding(vocab_size, hidden_size)
        self.rnn = nn.RNN(hidden_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, vocab_size)

    def forward(self, x, hidden):
        x = self.embed(x)
        out, hidden = self.rnn(x, hidden)
        out = self.fc(out[:, -1, :])  # используем только последний шаг
        return out, hidden

model = WordRNN(vocab_size, hidden_size, num_layers)
optimizer = torch.optim.Adam(model.parameters(), lr=lr)
criterion = nn.CrossEntropyLoss()

# Обучение
for epoch in range(num_epochs):
    hidden = torch.zeros(num_layers, X.size(0), hidden_size)
    output, hidden = model(X, hidden)
    loss = criterion(output, Y)
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()

    if epoch % 100 == 0:
        print(f"Epoch {epoch}, Loss: {loss.item():.4f}")

# Генерация
def generate_words(model, start_words, length=10):
    model.eval()
    input_seq = torch.tensor([[word2idx[w] for w in start_words]])
    hidden = torch.zeros(num_layers, 1, hidden_size)
    result = start_words.copy()

    for _ in range(length):
        out, hidden = model(input_seq, hidden)
        probs = F.softmax(out, dim=-1).detach().numpy().flatten()
        word_id = np.random.choice(len(probs), p=probs)
        result.append(idx2word[word_id])
        input_seq = torch.tensor([[word_id]])

    return ' '.join(result)

print("\nGenerated word sequence:\n", generate_words(model, ["this", "is", "a", "simple"]))
'''
    pc.copy(a)


def AllRNNs_logic():
    s = '''
import torch
import torch.nn as nn

class CustomRNNCell(nn.Module):
    def __init__(self, input_size, hidden_size, output_size):
        super().__init__()
        self.W_xh = nn.Parameter(torch.randn(input_size, hidden_size) * 0.1)
        self.W_hh = nn.Parameter(torch.randn(hidden_size, hidden_size) * 0.1)
        self.b_h = nn.Parameter(torch.zeros(hidden_size))
        self.W_hy = nn.Parameter(torch.randn(hidden_size, output_size) * 0.1)
        self.b_y = nn.Parameter(torch.zeros(output_size))

    def forward(self, x_t, h_prev):
        h_t = torch.tanh(x_t @ self.W_xh + h_prev @ self.W_hh + self.b_h)
        o_t = h_t @ self.W_hy + self.b_y
        return o_t, h_t

class CustomRNN(nn.Module):
    def __init__(self, input_size, hidden_size, output_size):
        super().__init__()
        self.cell = CustomRNNCell(input_size, hidden_size, output_size)

    def forward(self, x, h0=None):
        seq_len, batch_size, _ = x.size()
        h_t = h0 if h0 is not None else torch.zeros(batch_size, self.cell.b_h.size(0), device=x.device)
        outputs = []
        for t in range(seq_len):
            o_t, h_t = self.cell(x[t], h_t)
            outputs.append(o_t)
        out_seq = torch.stack(outputs, dim=0)
        return out_seq, h_t

class CustomLSTMCell(nn.Module):
    def __init__(self, input_size, hidden_size, output_size):
        super().__init__()
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.W = nn.Parameter(torch.randn(input_size + hidden_size, 4 * hidden_size) * 0.1)
        self.b = nn.Parameter(torch.zeros(4 * hidden_size))
        self.W_hy = nn.Parameter(torch.randn(hidden_size, output_size) * 0.1)
        self.b_y = nn.Parameter(torch.zeros(output_size))

    def forward(self, x_t, states):
        h_prev, c_prev = states
        combined = torch.cat([x_t, h_prev], dim=1)
        gates = combined @ self.W + self.b
        i, f, g, o = gates.chunk(4, dim=1)
        i = torch.sigmoid(i)
        f = torch.sigmoid(f)
        g = torch.tanh(g)
        o = torch.sigmoid(o)
        c_t = f * c_prev + i * g
        h_t = o * torch.tanh(c_t)
        y_t = h_t @ self.W_hy + self.b_y
        return y_t, (h_t, c_t)

class CustomLSTM(nn.Module):
    def __init__(self, input_size, hidden_size, output_size):
        super().__init__()
        self.cell = CustomLSTMCell(input_size, hidden_size, output_size)

    def forward(self, x, states=None):
        seq_len, batch_size, _ = x.size()
        h_t = torch.zeros(batch_size, self.cell.hidden_size, device=x.device)
        c_t = torch.zeros(batch_size, self.cell.hidden_size, device=x.device)
        if states is not None:
            h_t, c_t = states
        outputs = []
        for t in range(seq_len):
            y_t, (h_t, c_t) = self.cell(x[t], (h_t, c_t))
            outputs.append(y_t)
        out_seq = torch.stack(outputs, dim=0)
        return out_seq, (h_t, c_t)

class CustomGRUCell(nn.Module):
    def __init__(self, input_size, hidden_size, output_size):
        super().__init__()
        self.hidden_size = hidden_size
        self.W_z = nn.Parameter(torch.randn(input_size + hidden_size, hidden_size) * 0.1)
        self.b_z = nn.Parameter(torch.zeros(hidden_size))
        self.W_r = nn.Parameter(torch.randn(input_size + hidden_size, hidden_size) * 0.1)
        self.b_r = nn.Parameter(torch.zeros(hidden_size))
        self.W_h = nn.Parameter(torch.randn(input_size + hidden_size, hidden_size) * 0.1)
        self.b_h = nn.Parameter(torch.zeros(hidden_size))
        self.W_hy = nn.Parameter(torch.randn(hidden_size, output_size) * 0.1)
        self.b_y = nn.Parameter(torch.zeros(output_size))

    def forward(self, x_t, h_prev):
        combined = torch.cat([x_t, h_prev], dim=1)
        z = torch.sigmoid(combined @ self.W_z + self.b_z)
        r = torch.sigmoid(combined @ self.W_r + self.b_r)
        combined_r = torch.cat([x_t, r * h_prev], dim=1)
        h_hat = torch.tanh(combined_r @ self.W_h + self.b_h)
        h_t = (1 - z) * h_prev + z * h_hat
        y_t = h_t @ self.W_hy + self.b_y
        return y_t, h_t

class CustomGRU(nn.Module):
    def __init__(self, input_size, hidden_size, output_size):
        super().__init__()
        self.cell = CustomGRUCell(input_size, hidden_size, output_size)

    def forward(self, x, h0=None):
        seq_len, batch_size, _ = x.size()
        h_t = h0 if h0 is not None else torch.zeros(batch_size, self.cell.hidden_size, device=x.device)
        outputs = []
        for t in range(seq_len):
            y_t, h_t = self.cell(x[t], h_t)
            outputs.append(y_t)
        out_seq = torch.stack(outputs, dim=0)
        return out_seq, h_t

seq_len, batch_size, input_size, hidden_size, output_size = 5, 2, 3, 4, 2
x = torch.randn(seq_len, batch_size, input_size)

rnn = CustomRNN(input_size, hidden_size, output_size)
lstm = CustomLSTM(input_size, hidden_size, output_size)
gru = CustomGRU(input_size, hidden_size, output_size)

out_rnn, h_rnn = rnn(x)
out_lstm, states_lstm = lstm(x)
out_gru, h_gru = gru(x)

print(out_rnn.shape, h_rnn.shape)
print(out_lstm.shape, states_lstm[0].shape)
print(out_gru.shape, h_gru.shape)'''
    pc.copy(s)


def quotes_json_multilabel_class():
    s = '''
если задача - многоклассовая многометочная классификация (Multi-label Classification) - в том чтобы Category объединить в один список и пытаться сразу несколько категорий предсказывать   

import pandas as pd
import numpy as np
from collections import Counter
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from torch.nn.utils.rnn import pad_sequence

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.metrics import classification_report

quotes_df = pd.read_json('quotes.json')

print(f"Строк до агрегации: {len(quotes_df)}")
quotes_df = quotes_df.groupby(['Quote', 'Author']).agg({
    'Tags': 'first',
    'Popularity': 'first',
    'Category': lambda x: list(x.unique())
}).reset_index()
print(f"Строк после агрегации: {len(quotes_df)}")

quotes_df = quotes_df[quotes_df['Category'].apply(lambda x: len(x) > 0)]

texts = quotes_df['Quote'].tolist()
categories = quotes_df['Category'].tolist()

X_train_texts, X_test_texts, y_train_cats, y_test_cats = train_test_split(
    texts, categories, test_size=0.2, random_state=42
)

word_counts = Counter(word for text in X_train_texts for word in text.lower().split())
word_to_idx = {word: i + 2 for i, (word, _) in enumerate(word_counts.most_common(20000))}
word_to_idx['<PAD>'] = 0
word_to_idx['<UNK>'] = 1

mlb = MultiLabelBinarizer()
y_train_bin = mlb.fit_transform(y_train_cats)
y_test_bin = mlb.transform(y_test_cats)

num_classes = len(mlb.classes_)
print(f"\nВсего уникальных категорий: {num_classes}")
print(f"Пример бинарного вектора для {y_train_cats[0]}: {y_train_bin[0]}")

class QuotesDataset(Dataset):
    def __init__(self, texts, labels, word_to_idx):
        self.texts = texts
        self.labels = labels
        self.word_to_idx = word_to_idx

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        text = self.texts[idx].lower().split()
        text_indices = [self.word_to_idx.get(w, word_to_idx['<UNK>']) for w in text]
        label_vector = self.labels[idx]
        return torch.tensor(text_indices), torch.tensor(label_vector, dtype=torch.float32)

def collate_fn(batch):
    texts, labels = zip(*batch)
    texts_padded = pad_sequence(texts, batch_first=True, padding_value=word_to_idx['<PAD>'])
    labels = torch.stack(labels)
    return texts_padded, labels

train_dataset = QuotesDataset(X_train_texts, y_train_bin, word_to_idx)
test_dataset = QuotesDataset(X_test_texts, y_test_bin, word_to_idx)

train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True, collate_fn=collate_fn)
test_loader = DataLoader(test_dataset, batch_size=32, collate_fn=collate_fn)


class MultiLabelClassifier(nn.Module):
    def __init__(self, vocab_size, embedding_dim, hidden_dim, num_classes, padding_idx):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embedding_dim, padding_idx=padding_idx)
#         self.rnn = nn.RNN(embedding_dim, hidden_dim, batch_first=True, bidirectional=True, num_layers=2, dropout=0.5)
        self.rnn = nn.GRU(embedding_dim, hidden_dim, batch_first=True, bidirectional=True, num_layers=2, dropout=0.5)
#         self.rnn = nn.LSTM(embedding_dim, hidden_dim, batch_first=True, bidirectional=True, num_layers=2, dropout=0.5)
        self.fc = nn.Linear(hidden_dim * 2, num_classes)

    def forward(self, text):
        embedded = self.embedding(text)
        rnn_out, _ = self.rnn(embedded)
        pooled = torch.mean(rnn_out, 1)
        return self.fc(pooled)


EMBEDDING_DIM = 100
HIDDEN_DIM = 128
VOCAB_SIZE = len(word_to_idx)
NUM_EPOCHS = 5

model = MultiLabelClassifier(VOCAB_SIZE, EMBEDDING_DIM, HIDDEN_DIM, num_classes, padding_idx=word_to_idx['<PAD>'])
device = "cuda" if torch.cuda.is_available() else "cpu"
model.to(device)

criterion = nn.BCEWithLogitsLoss()
optimizer = optim.Adam(model.parameters(), lr=0.005)

print("\nНачинаем обучение... (подождать)")
for epoch in range(NUM_EPOCHS):
    model.train()
    total_loss = 0
    for texts_batch, labels_batch in train_loader:
        texts_batch, labels_batch = texts_batch.to(device), labels_batch.to(device)
        optimizer.zero_grad()
        outputs = model(texts_batch)
        loss = criterion(outputs, labels_batch)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
    print(f"Эпоха {epoch+1}/{NUM_EPOCHS}, Loss: {total_loss / len(train_loader):.4f}")

model.eval()
y_true_all = []
y_pred_all = []

with torch.no_grad():
    for texts_batch, labels_batch in test_loader:
        texts_batch = texts_batch.to(device)
        outputs = model(texts_batch)
        probs = torch.sigmoid(outputs)
        preds = (probs > 0.35).int()  # Порог можно настроить
        y_true_all.extend(labels_batch.cpu().numpy())
        y_pred_all.extend(preds.cpu().numpy())

y_true_all = np.array(y_true_all)
y_pred_all = np.array(y_pred_all)

print("\n--- Отчет по классификации ---")
print(classification_report(y_true_all, y_pred_all, target_names=mlb.classes_, zero_division=0))

def predict_categories(quote, model, word_to_idx, mlb_instance, device):
    model.eval()
    words = quote.lower().split()
    indices = [word_to_idx.get(w, word_to_idx['<UNK>']) for w in words]
    tensor = torch.tensor(indices).unsqueeze(0).to(device)
    with torch.no_grad():
        outputs = model(tensor)
        probs = torch.sigmoid(outputs)
        preds = (probs > 0.35).cpu().numpy() # порог можно выбрать другой
    predicted_categories = mlb_instance.inverse_transform(preds)
    return predicted_categories[0]

test_quote = "The only way to do great work is to love what you do."
predicted = predict_categories(test_quote, model, word_to_idx, mlb, device)
print(f"\nЦитата: '{test_quote}'")
print(f"Предсказанные категории: {predicted}")

test_quote_2 = "To be or not to be, that is the question."
predicted_2 = predict_categories(test_quote_2, model, word_to_idx, mlb, device)
print(f"\nЦитата: '{test_quote_2}'")
print(f"Предсказанные категории: {predicted_2}")'''
    pc.copy(s)


def pos_jso_sentence_to_tags():
    s = '''
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from collections import Counter
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from torch.nn.utils.rnn import pad_sequence

pos_df = pd.read_json('pos.json')
sentences = [s.lower().split() for s in pos_df['sentence']]
tags = pos_df['tags'].tolist()

X_train, X_test, y_train, y_test = train_test_split(sentences, tags, test_size=0.2, random_state=42)

print(f"Размер обучающей выборки: {len(X_train)}")
print(f"Размер тестовой выборки: {len(X_test)}")

word_counts = Counter(word for sentence in X_train for word in sentence)
tag_counts = Counter(tag for tag_list in y_train for tag in tag_list)

word_to_idx = {word: i + 2 for i, (word, _) in enumerate(word_counts.most_common())}
word_to_idx['<PAD>'] = 0
word_to_idx['<UNK>'] = 1

tag_to_idx = {tag: i + 1 for i, tag in enumerate(tag_counts)}
tag_to_idx['<PAD>'] = 0

idx_to_tag = {i: tag for tag, i in tag_to_idx.items()}

class POSDataset(Dataset):
    def __init__(self, sentences, tags, word_to_idx, tag_to_idx):
        self.sentences = sentences
        self.tags = tags
        self.word_to_idx = word_to_idx
        self.tag_to_idx = tag_to_idx

    def __len__(self):
        return len(self.sentences)

    def __getitem__(self, idx):
        sentence = self.sentences[idx]
        tag_list = self.tags[idx]
        sent_indices = [self.word_to_idx.get(w, self.word_to_idx['<UNK>']) for w in sentence]
        tag_indices = [self.tag_to_idx.get(t, 0) for t in tag_list]
        return torch.tensor(sent_indices), torch.tensor(tag_indices)

def collate_fn(batch):
    sentences, tags = zip(*batch)
    sentences_padded = pad_sequence(sentences, batch_first=True, padding_value=word_to_idx['<PAD>'])
    tags_padded = pad_sequence(tags, batch_first=True, padding_value=tag_to_idx['<PAD>'])
    return sentences_padded, tags_padded

train_dataset = POSDataset(X_train, y_train, word_to_idx, tag_to_idx)
test_dataset = POSDataset(X_test, y_test, word_to_idx, tag_to_idx)

train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True, collate_fn=collate_fn)
test_loader = DataLoader(test_dataset, batch_size=32, collate_fn=collate_fn)

class SequenceTagger(nn.Module):
    def __init__(self, vocab_size, embedding_dim, hidden_dim, tagset_size, padding_idx):
        super(SequenceTagger, self).__init__()
        self.embedding = nn.Embedding(vocab_size, embedding_dim, padding_idx=padding_idx)
        self.rnn = nn.RNN(embedding_dim, hidden_dim, batch_first=True, bidirectional=True, num_layers=2)
#         self.rnn = nn.GRU(embedding_dim, hidden_dim, batch_first=True, bidirectional=True, num_layers=2)
#         self.rnn = nn.LSTM(embedding_dim, hidden_dim, batch_first=True, bidirectional=True, num_layers=2)
        self.fc = nn.Linear(hidden_dim * 2, tagset_size)

    def forward(self, sentence):
        embeds = self.embedding(sentence)
        rnn_out, _ = self.rnn(embeds)
        tag_space = self.fc(rnn_out)
        return tag_space

EMBEDDING_DIM = 100
HIDDEN_DIM = 128
VOCAB_SIZE = len(word_to_idx)
TAGSET_SIZE = len(tag_to_idx)
NUM_EPOCHS = 10

model = SequenceTagger(VOCAB_SIZE, EMBEDDING_DIM, HIDDEN_DIM, TAGSET_SIZE, padding_idx=word_to_idx['<PAD>'])
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Обучение будет происходить на устройстве: {device}")
model.to(device)

loss_function = nn.CrossEntropyLoss(ignore_index=tag_to_idx['<PAD>'])
optimizer = optim.Adam(model.parameters(), lr=0.001)

print("\nНачинаем обучение...")
for epoch in range(NUM_EPOCHS):
    model.train()
    total_loss = 0
    for sentences_batch, tags_batch in train_loader:
        sentences_batch, tags_batch = sentences_batch.to(device), tags_batch.to(device)
        optimizer.zero_grad()
        tag_scores = model(sentences_batch)
        loss = loss_function(tag_scores.view(-1, TAGSET_SIZE), tags_batch.view(-1))
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
    print(f"Эпоха {epoch+1}/{NUM_EPOCHS}, Loss: {total_loss / len(train_loader):.4f}")

print("Обучение завершено!")

model.eval()
y_true = []
y_pred = []

with torch.no_grad():
    for sentences_batch, tags_batch in test_loader:
        sentences_batch, tags_batch = sentences_batch.to(device), tags_batch.to(device)
        tag_scores = model(sentences_batch)
        preds = torch.argmax(tag_scores, dim=2)
        for i in range(tags_batch.shape[0]):
            true_len = (tags_batch[i] != tag_to_idx['<PAD>']).sum().item()
            true_tags = tags_batch[i][:true_len].cpu().numpy()
            pred_tags = preds[i][:true_len].cpu().numpy()
            y_true.extend(true_tags)
            y_pred.extend(pred_tags)

labels = [idx_to_tag[i] for i in range(1, len(tag_to_idx))]
target_names = [tag for tag in labels if tag != '<PAD>']

y_true_named = [idx_to_tag[i] for i in y_true]
y_pred_named = [idx_to_tag[i] for i in y_pred]

print("\n--- Отчет по классификации ---")
print(classification_report(y_true_named, y_pred_named, labels=target_names, zero_division=0))

def predict_tags(sentence, model, word_to_idx, idx_to_tag):
    model.eval()
    words = sentence.lower().split()
    indices = [word_to_idx.get(w, word_to_idx['<UNK>']) for w in words]
    tensor = torch.tensor(indices).unsqueeze(0).to(device)
    with torch.no_grad():
        scores = model(tensor)
        preds = torch.argmax(scores, dim=2)
    pred_tags = [idx_to_tag[i] for i in preds[0].cpu().numpy()]
    return list(zip(words, pred_tags))

test_sentence = "who wrote the lord of the rings"
predicted_tags = predict_tags(test_sentence, model, word_to_idx, idx_to_tag)
print(f"\nПример разметки для предложения: '{test_sentence}'")
print(predicted_tags)'''
    pc.copy(s)



