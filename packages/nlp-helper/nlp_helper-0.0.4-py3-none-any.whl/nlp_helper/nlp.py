
def quotes_regr_linear():
  """
  ## Tags: quotes.json| Regression | nn.Linear

  1. На основе файлов `IMDB_reviews_cut.json` и `IMDB_movie_details.json` создайте pd.DataFrame. Столбцы таблицы: `review_text (str)`, `rating_movie (float)`. Выведите на экран количество строк и столбцов в полученном фрейме. На основе этих данных создайте датасет `MovieDataset`. Не забудьте добавить специальные токены `<PAD>` для дополнения последовательностей до нужной длины и `<UNK>` для корректной обработке ранее не встречавшихся токенов. В данной задаче рассматривайте отдельные слова как токены. Разбейте выборку на обучающее и тестовое множество.

  Используя слой `nn.Embedding` и слой `nn.Linear` (не используйте RNN), решите задачу предсказания рейтинга фильма (`ЗАДАЧА РЕГРЕССИИ`). Выведите отчет по классификации на тестовом множестве и 3 примера прогнозов (рядом выводите правильные ответы).

  **(Вместо файлов с отзывами используем файл `quotes.json`. Предсказываем popularity по quote.)**
  """

  import pandas as pd
  import numpy as np

  df = pd.read_json("/content/unzipped_07_exam/07_exam/nlp/quotes.json")[["Quote", "Popularity"]]
  print(df.shape)

  df['Popularity'] = df['Popularity'] * 1e4 # умножем на 1000, чтобы привести в удобный диапазон для моели(сейчас: от 0.0 до 0.15566616; убрать для другого датасет)
  df = df[df['Popularity'] > 0].reset_index(drop=True)

  from sklearn.model_selection import train_test_split
  import nltk
  nltk.download('punkt')
  nltk.download('punkt_tab')
  from nltk.tokenize import word_tokenize
  from collections import Counter

  train_df, test_df = train_test_split(
      df, test_size=0.2, random_state=42
  )

  # Строим словарь (отдельные слова = токены, как просили в задании; поэтому решил оставить nltk, а не использовать transformers)

  def tokenize(text):
    tokens = word_tokenize(text.lower())
    return tokens

  ctr = Counter()
  for txt in train_df['Quote']:
    ctr.update(tokenize(txt))

  vocab = {tok: idx+2 for idx, (tok, _) in enumerate(ctr.most_common())}
  vocab['<PAD>'] = 0
  vocab['<UNK>'] = 1

  # Создаем датасет
  import torch

  torch.manual_seed(42)
  class MovieDataset(torch.utils.data.Dataset):
    def __init__(self, texts, ratings, vocab):
      self.texts = texts
      self.ratings = ratings
      self.vocab = vocab

    def __len__(self):
      return len(self.texts)

    def __getitem__(self, idx):
      tokens = tokenize(self.texts.iloc[idx])
      idxs = [self.vocab.get(tok, self.vocab['<UNK>']) for tok in tokens]
      return torch.tensor(idxs, dtype=torch.long), torch.tensor(self.ratings.iloc[idx], dtype=torch.float)

  # collate функция
  from torch.nn.utils.rnn import pad_sequence

  def collate_fn(batch):
    seqs, labels = zip(*batch)
    lengths = torch.tensor([len(s) for s in seqs])
    padded = pad_sequence(seqs, batch_first=True, padding_value=vocab['<PAD>'])
    return padded, lengths, torch.stack(labels)

  # Создаем экземпляры датасет и даталоадеры
  train_ds = MovieDataset(train_df['Quote'], train_df['Popularity'], vocab)
  test_ds = MovieDataset(test_df['Quote'], test_df['Popularity'], vocab)

  batch_size = 64
  train_loader = torch.utils.data.DataLoader(train_ds, batch_size=batch_size, shuffle=True, collate_fn=collate_fn)
  test_loader = torch.utils.data.DataLoader(test_ds, batch_size=batch_size, shuffle=False, collate_fn=collate_fn)

  # Определяем модель (nn.Embedding + nn.Linear)
  class EmbRegressor(torch.nn.Module):
    def __init__(self, vocab_size, emb_dim):
      super().__init__()
      self.emb = torch.nn.Embedding(vocab_size, emb_dim, padding_idx=vocab['<PAD>'])
      self.lin = torch.nn.Linear(emb_dim, 1)

    def forward(self, x, lengths):
      e = self.emb(x)
      mask = (x != vocab['<PAD>']).unsqueeze(-1)
      summed = (e * mask).sum(dim=1)
      meaned = summed / lengths.unsqueeze(1).clamp(min=1)
      return self.lin(meaned).squeeze(1)

  # Цикл обучения
  device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
  embed_dim = 50
  model = EmbRegressor(len(vocab), emb_dim=embed_dim).to(device)
  opt = torch.optim.Adam(model.parameters(), lr=1e-3)
  crit = torch.nn.MSELoss()
  losses = []
  for epoch in range(5):
    model.train()
    total_loss = 0
    for x, lengths, y in train_loader:
      x, lengths, y = x.to(device), lengths.to(device), y.to(device)
      opt.zero_grad()
      pred = model(x, lengths)
      loss = crit(pred, y)
      loss.backward()
      opt.step()
      total_loss += loss.item() * x.size(0)
    losses.append(total_loss)
    print(f"Эпоха {epoch+1}, MSE на обучающей выборке={total_loss/len(train_ds):.4f}")

  plt.plot(losses)

  # Оценка модели
  import numpy as np
  from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

  model.eval()
  ys, preds = [], []
  with torch.no_grad():
    for x, lengths, y in test_loader:
      x, lengths = x.to(device), lengths.to(device)
      p = model(x, lengths).cpu().numpy()
      p_unscaled = p / 1e4 # убрать если датасет другой
      y_unscales = y / 1e4
      ys.extend(y_unscales.numpy())
      preds.extend(p_unscaled)

  print(f"Test MSE = {mean_squared_error(ys, preds)}, MAE = {mean_absolute_error(ys, preds):.4f}, R2 = {r2_score(ys, preds):.4f}")

  # 3 примера прогнозов
  for i in [100, 101, 201]:
    print(f"Текст Цитаты: {test_df['Quote'].iloc[i][:80]}")
    print(f"True: {ys[i]}, Pred: {preds[i]}")

def news_cls_RNN():
  """## Tags: news.csv | classification | RNN

  2.Загрузите набор данных `lenta_news.csv`. Выполните предобработку столбца `Title`. На основе этих данных создайте датасет `NewsDataset`. Не забудьте добавить специальные токены `<PAD>` для дополнения последовательностей до нужной длины и `<UNK>`для корректной обработке ранее не встречавшихся токенов. В данной задаче рассматривайте отдельные слова как токены.

  Создайте модель для классификации, используя слой `nn.Embedding` и слой `nn.RNN`, инициализировав эмбеддинги случайным образом. Обучите модель. Далее обучите еще две модели: модель с двунаправленным рекуррентным слоем и модель с двухуровневым рекуррентным слоем. Сравните качество на тестовой выборке. Результаты сведите в таблицу (модель/метрика качества на тестовом множестве).

  **ИСПОЛЬЗУЕМ news.csv**
  """

  import pandas as pd
  from sklearn.preprocessing import LabelEncoder

  df = pd.read_csv("/content/unzipped_07_exam/07_exam/nlp/news.csv")
  print(df.shape)
  le = LabelEncoder()
  df['Class Index'] = le.fit_transform(df['Class Index'])

  # Токенизация
  import nltk
  nltk.download('punkt')
  nltk.download('punkt_tab')
  from nltk.tokenize import word_tokenize
  from collections import Counter

  def tokenize(text):
    return word_tokenize(str(text).lower())

  # Создаем словарь
  ctr = Counter()
  for txt in df['Title']:
    ctr.update(tokenize(txt))

  vocab = {tok: idx+2 for idx, (tok, _) in enumerate(ctr.most_common())}
  vocab['<PAD>'] = 0
  vocab['<UNK>'] = 1

  # Класс датасета
  import torch
  torch.manual_seed(42)
  class NewsDataset(torch.utils.data.Dataset):
    def __init__(self, texts, labels, vocab):
      self.texts = texts
      self.labels = labels
      self.vocab = vocab

    def __len__(self):
      return len(self.texts)

    def __getitem__(self, i):
      toks = tokenize(self.texts.iloc[i])
      idxs = [self.vocab.get(t, self.vocab["<UNK>"]) for t in toks]
      return torch.tensor(idxs, dtype=torch.long), torch.tensor(self.labels.iloc[i], dtype=torch.long)

  from sklearn.model_selection import train_test_split
  from sklearn.preprocessing import LabelEncoder

  # Функция collate
  def collate_fn(batch):
    seqs, labs = zip(*batch)
    lengths = torch.tensor([len(s) for s in seqs])
    padded = torch.nn.utils.rnn.pad_sequence(seqs, batch_first=True, padding_value=vocab['<PAD>'])
    return padded, lengths, torch.stack(labs)

  df = df.dropna()
  counts = df['Class Index'].value_counts()
  valid_topics = counts[counts >= 2].index
  df = df[df['Class Index'].isin(valid_topics)].reset_index(drop=True)
  encoder = LabelEncoder()
  # Создаем экземпляры датасетов и даталоадеров + train/test split
  train_df, test_df = train_test_split(df[['Title', 'Class Index']], test_size=0.2,
                                      stratify=df['Class Index'], random_state=42)
  train_ds = NewsDataset(train_df['Title'], train_df['Class Index'], vocab)
  test_ds = NewsDataset(test_df['Title'], test_df['Class Index'], vocab)
  batch_size=64
  train_loader = torch.utils.data.DataLoader(train_ds, batch_size=batch_size, shuffle=True, collate_fn=collate_fn)
  test_loader = torch.utils.data.DataLoader(test_ds, batch_size=batch_size, shuffle=False, collate_fn=collate_fn)

  # Модель
  class RNNClassifier(torch.nn.Module):
    def __init__(self, vocab_size, emb_dim, hid_dim, out_dim, num_layers=1, bidir=False):
      super().__init__()
      self.emb = torch.nn.Embedding(vocab_size, emb_dim, padding_idx=vocab['<PAD>'])
      self.rnn = torch.nn.RNN(emb_dim, hid_dim, num_layers=num_layers, batch_first=True, bidirectional=bidir)
      self.num_layers = num_layers
      self.bidir = bidir
      mult = 2 if bidir else 1
      self.fc = torch.nn.Linear(hid_dim * mult, out_dim)

    def forward(self, x, lengths):
      e = self.emb(x)
      packed = torch.nn.utils.rnn.pack_padded_sequence(e, lengths.cpu(), batch_first=True, enforce_sorted=False)
      out_p, hidden = self.rnn(packed)
      # hidden shape: [num_layers * num_directions, B, hid_dim]
      if self.bidir:
        # возьмём последние два вектора (forward & backward) из последнего слоя
        # индексы: -2 и -1
        h_fwd = hidden[-2]
        h_bwd = hidden[-1]
        h = torch.cat([h_fwd, h_bwd], dim=1)
      else:
        # однонаправленный: берём последний слой
        h = hidden[-1]
      return self.fc(h)

  from sklearn.metrics import accuracy_score

  # Функция обучения
  def train_model(model, loader, crit, opt, device):
    model.train()
    total_loss = 0
    for x, lengths, y in loader:
      x, lengths, y = x.to(device), lengths.to(device), y.to(device)
      opt.zero_grad()
      preds = model(x, lengths)
      loss = crit(preds, y)
      loss.backward()
      opt.step()
      total_loss+=loss.item()*y.size(0)
    return total_loss/len(loader.dataset)

  # Функция оценки
  def eval_model(model, loader, device):
    model.eval()
    alls, labs = [], []
    for x, lengths, y in loader:
      x, lengths = x.to(device), lengths.to(device)
      preds = torch.argmax(model(x, lengths), dim=1).cpu().numpy()
      alls.extend(preds)
      labs.extend(y.numpy())
    return accuracy_score(labs, alls)

  # Обучаем RNN, Bi-RNN, 2-layer RNN

  device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
  params = {
      'vocab_size': len(vocab), 'emb_dim': 100, 'hid_dim':128, 'out_dim':df['Class Index'].nunique()
  }
  variants = {
      'RNN': {'num_layers': 1, 'bidir': False},
      'Bi-RNN': {'num_layers':1, 'bidir': True},
      '2-layer RNN': {'num_layers':2, 'bidir': False}
  }
  results={}
  for name, cfg in variants.items():
    model = RNNClassifier(**params, **cfg).to(device)
    crit = torch.nn.CrossEntropyLoss()
    opt = torch.optim.Adam(model.parameters(), lr=0.01)
    losses = []
    for epoch in range(5):
      loss = train_model(model, train_loader, crit, opt, device)
      acc = eval_model(model, test_loader, device)
      results[name] = acc
      losses.append(loss)
      print(f'Эпоха {epoch+1}, модель {name}, лосс = {loss}')
    plt.plot(losses)

  # Результаты обучения
  df_res = pd.DataFrame.from_dict(results, orient='index', columns=['accuracy'])
  print(df_res)

def review_cls_Linear():
  """# Вариант 2
  ## №2 Tags: reviews.json | Classification | Linear

  1. На основе файлов `IMDB_reviews_cut.json` и `IMDB_movie_details.json` создайте `pd.DataFrame`. Столбцы таблицы: review_text (str), rating_review (int). Выведите на экран количество строк и столбцов в полученном фрейме. На основе этих данных создайте датасет `MovieDataset`. Не забудьте добавить специальные токены `<PAD>` для дополнения последовательностей до нужной длины и `<UNK>` для корректной обработке ранее не встречавшихся токенов. В данной задаче рассматривайте отдельные слова как токены. Разбейте выборку на обучающее и тестовое множество.

  Используя слой `nn.Embedding` и слой `nn.Linear` (не используйте RNN), решите задачу предсказания рейтинга отзыва (`ЗАДАЧА КЛАССИФИКАЦИИ`). Выведите отчет по классификации на тестовом множестве, пример правильно и неправильно классифицированного примера из тестового множества.

  **Используем reviews.json булем предсказывать overall по reviewText. КЛАССФИКАЦИЯ**.
  """

  import pandas as pd

  reviews = pd.read_json("/content/unzipped_07_exam/07_exam/nlp/reviews.json", lines=True)
  df = reviews[['reviewText', 'overall']].rename(columns={'reviewText': 'review_text', 'overall': 'rating_review'})
  print(df.shape)

  # Токенизация

  import nltk
  nltk.download('punkt')
  nltk.download('punkt_tab')
  from nltk.tokenize import word_tokenize
  from collections import Counter
  from sklearn.model_selection import train_test_split
  df['rating_review'] = df['rating_review'] - df['rating_review'].min()
  train_df, test_df = train_test_split(df, test_size=0.2, random_state=42, stratify=df['rating_review'])
  def tokenize(input):
    return word_tokenize(input.lower())

  # Создаем словарь
  counter = Counter()
  for txt in train_df['review_text']:
    counter.update(tokenize(txt))
  vocab = {tok: idx+2 for idx, (tok, _) in enumerate(counter.most_common())}
  vocab['<PAD>'] = 0
  vocab['<UNK>'] = 1

  num_classes = df['rating_review'].nunique()

  # Датасет
  import torch

  class MovieDataset(torch.utils.data.Dataset):
    def __init__(self, texts, labels, vocab):
      self.texts=texts
      self.labels=labels
      self.vocab=vocab

    def __len__(self):
      return len(self.texts)

    def __getitem__(self, idx):
      tokens = tokenize(self.texts.iloc[idx])
      idxs = [self.vocab.get(t, self.vocab['<UNK>']) for t in tokens]
      return torch.tensor(idxs, dtype=torch.long), torch.tensor(self.labels.iloc[idx], dtype=torch.long)

  # collate функция

  def collate_fn(batch):
    seqs, labs = zip(*batch)
    lengths = torch.tensor([len(s) for s in seqs])
    padded = torch.nn.utils.rnn.pad_sequence(seqs, batch_first=True, padding_value=vocab['<PAD>'])
    return padded, lengths, torch.stack(labs)

  # Создаем экземпляры датасетов и даталоадеров
  torch.manual_seed(42)
  train_ds = MovieDataset(train_df['review_text'], train_df['rating_review'], vocab)
  test_ds = MovieDataset(test_df['review_text'], test_df['rating_review'], vocab)
  batch_size=64
  train_loader = torch.utils.data.DataLoader(train_ds, batch_size=batch_size, shuffle=True, collate_fn=collate_fn)
  test_loader = torch.utils.data.DataLoader(test_ds, batch_size=batch_size, shuffle=False, collate_fn=collate_fn)

  # Класс модели
  class LinearClassifier(torch.nn.Module):
    def __init__(self, vocab_size, emb_dim, num_classes):
      super().__init__()
      self.emb = torch.nn.Embedding(vocab_size, emb_dim, padding_idx=vocab['<PAD>'])
      self.fc = torch.nn.Linear(emb_dim, num_classes)

    def forward(self, x, lengths):
      e = self.emb(x)
      mask = (x != vocab['<PAD>']).unsqueeze(-1)
      summed = (e*mask).sum(dim=1)
      meaned = summed / lengths.unsqueeze(-1).clamp(min=1)
      return self.fc(meaned)

  # Цикл обучения
  device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
  model = LinearClassifier(len(vocab), emb_dim=50, num_classes=num_classes).to(device)
  optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
  criterion = torch.nn.CrossEntropyLoss()
  num_epochs = 5

  all_losses = []
  for epoch in range(num_epochs):
    model.train()
    total_loss = 0
    for x, lengths, y in train_loader:
      x, lengths, y = x.to(device), lengths.to(device), y.to(device)
      optimizer.zero_grad()
      output = model(x, lengths)
      loss = criterion(output, y)
      loss.backward()
      optimizer.step()
      total_loss += loss.item()*y.size(0)
    epoch_loss = total_loss/len(train_ds)
    all_losses.append(epoch_loss)
    print(f'Эпоха {epoch+1}, функция потерь = {epoch_loss:.4f}')

  plt.plot(all_losses)

  # Оценка модели
  from sklearn.metrics import classification_report

  all_preds = []
  all_labels = []
  model.eval()
  with torch.no_grad():
    for x, lengths, y in test_loader:
      x, lengths, y = x.to(device), lengths.to(device), y.to(device)
      logits = model(x, lengths)
      preds = torch.argmax(logits, dim=1).cpu()
      all_preds.extend(preds)
      all_labels.extend(y.numpy())

  print(f"Classification report\n {classification_report(all_labels, all_preds)}")

  # Пример правильных и неправильных предсказаний

  results = []
  for i, (x_l, y_true) in enumerate(test_ds):
    logits = model(x_l.unsqueeze(0), torch.tensor([len(x_l)]))
    y_pred = torch.argmax(logits, dim=1).item()
    results.append((i, y_true.item(), y_pred, test_ds.texts.iloc[i]))

  correct = [r for r in results if r[1]==r[2]][0]
  incorrect = [r for r in results if r[1]!=r[2]][0]

  print(f'Пример правильного предсказания {correct[1:]}')
  print(f'Пример неправильного предсказания {incorrect[1:]}')

def news_cls_pretrained_emb_RNN():
  """## Tags: news.csv | Classification | Pre-trained embeddings | RNN

  2.Загрузите набор данных `lenta_news.csv`. Выполните предобработку столбца `Title`. На основе этих данных создайте датасет `NewsDataset`. Не забудьте добавить специальные токены `<PAD>` для дополнения последовательностей до нужной длины и `<UNK>` для корректной обработки ранее не встречавшихся токенов. В данной задаче рассматривайте отдельные слова как токены.

  Создайте модель для классификации, используя слой `nn.Embedding` и слой `nn.RNN`. Обучите модель. Для инициализации эмбеддингов используйте эмбеддинги `Glove`. Обратите внимание, что номер строки в этом тензоре должен соответствовать токену (слову), имеющему такой индекс в вашем словаре. Для слов, которых нет в файле с эмбеддингами, инициализуйте эмбеддинг случайным образом. Выведите на экран отчет по классификации на основе тестового множества.

  Эмбеддинги: https://nlp.stanford.edu/projects/glove/ (находите ссылку на архив `glove.6B.zip`, в нем несколько файлов с эмбеддингами слов, выбираете один из файлов в архиве)

  **Используем news.csv**

  """

  import pandas as pd
  from sklearn.preprocessing import LabelEncoder

  df = pd.read_csv("/content/unzipped_07_exam/07_exam/nlp/news.csv")
  print(df.head(2))
  le = LabelEncoder()
  df['Class Index'] = le.fit_transform(df['Class Index'])

  # Токенизация

  import nltk
  nltk.download('punkt_tab')
  from nltk import word_tokenize
  from collections import Counter
  def tokenize(text):
    return word_tokenize(text.lower())

  # Создаем словарь

  counter = Counter()
  for txt in df['Title']:
    counter.update(tokenize(txt))

  vocab = {tok: idx+2 for idx, (tok,_) in enumerate(counter.most_common())}
  vocab['<PAD>'] = 0
  vocab['<UNK>'] = 1

  # !pip install gensim

  from gensim.models import KeyedVectors
  import numpy as np
  import torch
  # Читаем эмбеддинги GLOVE

  EMB_DIM = 50
  glove_path = '/content/glove.6B.50d.txt'

  glove = KeyedVectors.load_word2vec_format(glove_path, binary=False, no_header=True)
  vocab_size = len(vocab)

  # Создаем матрицу эмбеддингов
  emb_matrix = np.random.uniform(-0.05, 0.05, (vocab_size, EMB_DIM)).astype(np.float32)
  emb_matrix[0] = np.zeros(EMB_DIM, dtype=np.float32)
  for tok, idx in vocab.items():
    if tok in glove.key_to_index:
      emb_matrix[idx] = glove.get_vector(tok)

  emb_matrix = torch.from_numpy(emb_matrix).float()

  # Датасет
  import torch
  torch.manual_seed(42)
  class NewsDataset(torch.utils.data.Dataset):
    def __init__(self, texts, labels, vocab):
      self.texts = texts
      self.labels = labels
      self.vocab = vocab

    def __len__(self):
      return len(self.texts)

    def __getitem__(self, idx):
      tokens = tokenize(self.texts.iloc[idx])
      indexes = [self.vocab.get(t, self.vocab['<UNK>']) for t in tokens]
      return torch.tensor(indexes, dtype=torch.long), torch.tensor(self.labels.iloc[idx], dtype=torch.long)

  from sklearn.model_selection import train_test_split

  # collate fn

  def collate_fn(batch):
    sequences, labels = zip(*batch)
    lengths = torch.tensor([len(sequence) for sequence in sequences], dtype=torch.long)
    padded = torch.nn.utils.rnn.pad_sequence(sequences, batch_first=True, padding_value=vocab['<PAD>'])
    return padded, lengths, torch.stack(labels)
  # экземпляры датасетов и даталоадеров

  train_df, test_df = train_test_split(df[['Title', 'Class Index']], train_size=0.8, random_state=42, stratify=df['Class Index'])

  train_ds = NewsDataset(train_df['Title'], train_df['Class Index'], vocab)
  test_ds = NewsDataset(test_df['Title'], test_df['Class Index'], vocab)

  batch_size=64
  train_loader = torch.utils.data.DataLoader(train_ds, batch_size, shuffle=True, collate_fn=collate_fn)
  test_loader = torch.utils.data.DataLoader(test_ds, batch_size, shuffle=False, collate_fn=collate_fn)

  num_classes = train_ds.labels.nunique()

  # Модель
  class RnnClassifier(torch.nn.Module):
    def __init__(self, embedding_matrix, hidden_dim, num_classes, vocab, num_layers=1, bidirectional=False):
      super().__init__()
      num_emb, emb_dim = embedding_matrix.shape
      self.num_classes = num_classes
      self.bidirectional = bidirectional
      self.vocab = vocab
      self.emb = torch.nn.Embedding.from_pretrained(
          embedding_matrix,
          freeze=False,
          padding_idx=self.vocab['<PAD>']
      )
      self.rnn = torch.nn.RNN(
          input_size = emb_dim,
          hidden_size=hidden_dim,
          num_layers=num_layers,
          batch_first=True,
          bidirectional=bidirectional
      )
      mult = 2 if bidirectional else 1
      self.fc = torch.nn.Linear(hidden_dim*mult, self.num_classes)

    def forward(self, x, lengths):
      e = self.emb(x)
      packed = torch.nn.utils.rnn.pack_padded_sequence(e, lengths.cpu(),
                                                      batch_first=True,
                                                      enforce_sorted=False)
      out, hidden = self.rnn(packed)
      if self.bidirectional:
        h = torch.cat([hidden[-2], hidden[-1]], dim=1)
      else:
        h = hidden[-1]
      return self.fc(h)

  # Функция для тренировки
  from sklearn.metrics import classification_report

  device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
  def train(model, loader, optimizer, criterion):
    model.train()
    total_loss = 0
    for x, lengths, y in loader:
      x, lengths, y = x.to(device), lengths.to(device), y.to(device)
      optimizer.zero_grad()
      logits = model(x, lengths)
      loss = criterion(logits, y)
      loss.backward()
      optimizer.step()
      total_loss += loss.item()*y.size(0)
    return total_loss/len(loader.dataset)

  # Функция для оценки
  def evaluate(model, loader):
    model.eval()
    all_preds, all_labels = [], []
    with torch.no_grad():
      for x, lengths, y in loader:
        x, lengths, y = x.to(device), lengths.to(device), y.to(device)
        logits = model(x, lengths)
        preds = torch.argmax(logits, dim=1).cpu().numpy()
        all_preds.extend(preds)
        all_labels.extend(y.numpy())
      return classification_report(all_labels, all_preds, target_names=le.classes_.astype(str))

  import matplotlib.pyplot as plt

  # Цикл обучения

  model = RnnClassifier(emb_matrix, vocab=vocab, num_classes=num_classes, hidden_dim=64, num_layers=1, bidirectional=False)
  optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
  criterion = torch.nn.CrossEntropyLoss()
  all_losses = []
  for epoch in range(5):
    loss = train(model, train_loader, optimizer, criterion)
    all_losses.append(loss)

  print(evaluate(model, test_loader))
  plt.plot(all_losses)

def quotes_miltilabel_cls_linear():
  """# Вариант 3

  ## №2 Tags: quotes.json | MultiLabel |  Linear

  1. На основе файлов `IMDB_reviews_cut.json` и `IMDB_movie_details.json` создайте `pd.DataFrame`. Столбцы таблицы: review_text (str), is_class_X (где X - название жанра). Выведите на экран количество строк и столбцов в полученном фрейме. На основе этих данных создайте датасет `MovieDataset`. Не забудьте добавить специальные токены `<PAD>` для дополнения последовательностей до нужной длины и `<UNK>` для корректной обработке ранее не встречавшихся токенов. В данной задаче рассматривайте отдельные слова как токены. Разбейте выборку на обучающее и тестовое множество.

  Используя слой `nn.Embedding` и слой `nn.Linear` (не используйте RNN), решите задачу предсказания набора жанров фильма по тексту отзыва. Для решения задачи BCELoss (для задачи классификации). Выведите на экран пример предсказаний и правильные ответы для нескольких отзывов.

  **Вместо файлов с отзывами берем файл `quotes.json`. В этом файле тоже мульткиклассовая классификация**
  """

  import pandas as pd
  from sklearn.preprocessing import MultiLabelBinarizer

  df = pd.read_json("/content/unzipped_07_exam/07_exam/nlp/quotes.json")[["Quote", "Tags"]]
  df = df.drop_duplicates(subset=['Quote'], keep='first').reset_index(drop=True)
  print(df.shape)

  tag_counts = Counter(tag for tags in df['Tags'] for tag in tags)

  # Выбираем топ-N самых популярных тегов
  TOP_N = 10
  top_tags = [tag for tag, _ in tag_counts.most_common(TOP_N)]

  # Фильтруем списки тегов, оставляя только топ-N
  df['Tags_filtered'] = df['Tags'].apply(lambda tags: [t for t in tags if t in top_tags])

  # Убираем цитаты, у которых после фильтрации не осталось тегов
  df= df[df['Tags_filtered'].map(len) > 0].reset_index(drop=True)

  print(f"после фильтрации: {len(df)}")
  print("Топ-теги:", top_tags)

  mlb = MultiLabelBinarizer()
  one_hot = mlb.fit_transform(df["Tags_filtered"])
  oh_df = pd.DataFrame(one_hot, columns=[f'is_class{c}' for c in mlb.classes_], index=df.index)

  df = pd.concat([df.drop(columns=["Tags", "Tags_filtered"]),oh_df], axis=1)

  print(df.shape)
  print(df.columns.tolist())

  from sklearn.model_selection import train_test_split
  import nltk
  nltk.download('punkt_tab')
  from nltk import word_tokenize
  from collections import Counter

  train_df, test_df = train_test_split(df, test_size=0.2, random_state=42)
  # Токенизация

  def tokenize(text):
    return word_tokenize(text.lower())

  # Создаем словарь
  counter = Counter()
  for txt in train_df['Quote']:
    counter.update(tokenize(txt))

  vocab = {tok: idx + 2 for idx, (tok, _ ) in enumerate(counter.most_common())}
  vocab['<PAD>'] = 0
  vocab['<UNK>'] = 1

  # Датасет
  import torch
  torch.manual_seed(42)
  class MovieDataset(torch.utils.data.Dataset):
      def __init__(self, texts, labels, vocab):
          self.texts  = texts.reset_index(drop=True)
          self.labels = labels.reset_index(drop=True).values.astype(float)
          self.vocab  = vocab

      def __len__(self):
          return len(self.texts)

      def __getitem__(self, idx):
          toks   = tokenize(self.texts.iloc[idx])
          idxs   = [self.vocab.get(t, self.vocab['<UNK>']) for t in toks]
          return (
              torch.tensor(idxs, dtype=torch.long),
              torch.tensor(self.labels[idx], dtype=torch.float)
          )

  # collate_fn
  def collate_fn(batch):
    seqs, labels = zip(*batch)
    lengths = torch.tensor([len(s) for s in seqs], dtype=torch.long)
    padded = torch.nn.utils.rnn.pad_sequence(seqs, batch_first=True, padding_value=vocab['<PAD>'])
    return padded, lengths, torch.stack(labels)
  # Классы датасетов и даталоадеров
  tag_cols = df.columns.tolist()[1:]

  train_ds = MovieDataset(train_df['Quote'], train_df[tag_cols], vocab)
  test_ds = MovieDataset(test_df['Quote'], test_df[tag_cols], vocab)

  batch_size = 64
  train_loader = torch.utils.data.DataLoader(train_ds, batch_size=batch_size,  shuffle=True, collate_fn=collate_fn)
  test_loader = torch.utils.data.DataLoader(test_ds, batch_size=batch_size, shuffle=False, collate_fn=collate_fn)

  # Модель
  class MultiLabelClassifier(torch.nn.Module):
    def __init__(self, vocab_size, emb_dim, num_tags, pad_idx=0):
      super().__init__()
      self.pad_idx = pad_idx
      self.emb = torch.nn.Embedding(vocab_size, emb_dim, padding_idx=pad_idx)
      self.fc = torch.nn.Linear(emb_dim, num_tags)

    def forward(self, x, lengths):
      e = self.emb(x)
      mask = (x != self.pad_idx).unsqueeze(-1)
      summed = (e*mask).sum(dim=1)
      meaned = summed/lengths.unsqueeze(1).clamp(min=1)
      return self.fc(meaned)

  # Цикл обучения
  import matplotlib.pyplot as plt

  device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
  model = MultiLabelClassifier(len(vocab), emb_dim=50, num_tags=len(tag_cols), pad_idx=vocab['<PAD>']).to(device)
  criterion = torch.nn.BCEWithLogitsLoss()
  optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)

  losses = []
  for epoch in range(5):
    model.train()
    epoch_loss = 0
    total_loss = 0
    for x, lengths, y in train_loader:
      x, lengths, y = x.to(device), lengths.to(device), y.to(device)
      optimizer.zero_grad()
      logits = model(x, lengths)
      loss = criterion(logits, y)
      loss.backward()
      optimizer.step()
      total_loss += loss.item()*y.size(0)
    epoch_loss = total_loss/len(train_ds)
    losses.append(epoch_loss)
    print(f'epoch {epoch+1} loss {epoch_loss}')

  plt.plot(losses)

  # 8. Show predictions for a few examples
  model.eval()
  examples = 5

  with torch.no_grad():
      for i in range(10, 10+examples):
          # 1) Берём i-й пример из test_ds
          tokens, label = test_ds[i]
          text = test_ds.texts.iloc[i]

          # 2) Собираем батч из одного примера
          x      = tokens.unsqueeze(0).to(device)                     # [1, L]
          lengths = torch.tensor([len(tokens)], dtype=torch.long).to(device)

          # 3) Прямой проход
          logits = model(x, lengths)                                  # [1, num_tags]
          probs  = torch.sigmoid(logits).cpu().numpy().ravel()        # [num_tags]

          # 4) Истинные метки как список 0/1
          true_vec = label.cpu().numpy()
          # если у label скаляр — превращаем в vector length=1
          if true_vec.ndim == 0:
              true_vec = np.array([true_vec])
          # список имён истинных тегов
          true_tags = [tag_cols[j] for j, v in enumerate(true_vec) if v == 1.0]

          # 5) Предсказанные метки (p > 0.5)
          pred_tags = [tag_cols[j] for j, p in enumerate(probs) if p > 0.2]

          # 6) Печать
          print(f"\nQuote: {text}\n")
          print(f"True tags: {true_tags}")
          print(f"Pred tags: {pred_tags}")

  from sklearn.metrics import f1_score, hamming_loss

  # Собираем все истинные и предсказанные метки
  y_true, y_pred = [], []
  model.eval()
  with torch.no_grad():
      for x, lengths, y in test_loader:
          logits = model(x.to(device), lengths.to(device))
          preds = (torch.sigmoid(logits) > 0.2).int().cpu().numpy()
          y_pred.extend(preds)
          y_true.extend(y.numpy())

  # Считаем метрики
  micro_f1 = f1_score(y_true, y_pred, average='micro')
  macro_f1 = f1_score(y_true, y_pred, average='macro')
  h_loss   = hamming_loss(y_true, y_pred)

  print(f"Micro-F1: {micro_f1:.4f}")
  print(f"Macro-F1: {macro_f1:.4f}")
  print(f"Hamming Loss: {h_loss:.4f}")

def news_cls_transformers_emb_RNN():
  """## №3 Tags: news.csv | Classification | Transformers | RNN

  2. Загрузите набор данных `lenta_news`.csv. Выполните предобработку столбца `Title`. На основе этих данных создайте датасет `NewsDataset`. Не забудьте добавить специальные токены `<PAD>` для дополнения последовательностей до нужной длины и `<UNK>` для корректной обработке ранее не встречавшихся токенов. В данной задаче рассматривайте отдельные слова как токены.

  Создайте модель для классификации, используя любую подходящую модель для получения эмбеддингов слов из `transformers` и слой `nn.RNN`. Обучите модель.
  Выведите на экран отчет по классификации на основе тестового множества.

  **Используем news.csv**
  """

  from sklearn.preprocessing import LabelEncoder
  from transformers import AutoTokenizer, AutoModel
  import pandas as pd
  import torch
  import torch.nn as nn
  from torch.utils.data import Dataset, DataLoader
  from sklearn.model_selection import train_test_split
  from sklearn.metrics import classification_report
  import numpy as np

  df = pd.read_csv("/content/unzipped_07_exam/07_exam/nlp/news.csv")
  le = LabelEncoder()
  df['Class Index'] = le.fit_transform(df['Class Index'])
  print(df.shape)
  train_df, test_df = train_test_split(df, test_size=0.2, stratify=df['Class Index'], random_state=42)

  tokenizer = AutoTokenizer.from_pretrained('prajjwal1/bert-tiny') # ТОКЕНИЗАТОР

  class NewsDataset(Dataset):
      def __init__(self, texts, labels):
          self.texts  = texts.tolist()
          self.labels = labels.tolist()
      def __len__(self):
          return len(self.texts)
      def __getitem__(self, idx):
          enc = tokenizer(self.texts[idx],
                          truncation=True,
                          max_length=32,
                          return_tensors='pt')
          return {k: v.squeeze(0) for k, v in enc.items()}, self.labels[idx]

  def collate_fn(batch):
      encodings = [item[0] for item in batch]
      labels    = torch.tensor([item[1] for item in batch], dtype=torch.long)
      batch_enc = tokenizer.pad(encodings, return_tensors='pt')
      # compute lengths from attention_mask
      lengths   = batch_enc['attention_mask'].sum(dim=1)
      return batch_enc['input_ids'], batch_enc['attention_mask'], lengths, labels

  train_ds = NewsDataset(train_df['Title'], train_df['Class Index'])
  test_ds  = NewsDataset(test_df['Title'],  test_df['Class Index'])

  train_loader = DataLoader(train_ds, batch_size=32, shuffle=True, collate_fn=collate_fn)
  test_loader  = DataLoader(test_ds,  batch_size=32, shuffle=False, collate_fn=collate_fn)

  class TransformerRNNClassifier(nn.Module):
      def __init__(self, transformer_model, hidden_dim, num_classes, num_layers=1, bidirectional=False):
          super().__init__()
          self.transformer = transformer_model
          emb_dim = transformer_model.config.hidden_size
          self.rnn = nn.RNN(emb_dim, hidden_dim,
                            num_layers=num_layers,
                            batch_first=True,
                            bidirectional=bidirectional)
          mult = 2 if bidirectional else 1
          self.fc = nn.Linear(hidden_dim * mult, num_classes)
      def forward(self, input_ids, attention_mask, lengths):
          # transformer outputs last_hidden_state: [B, L, D]
          outputs = self.transformer(input_ids=input_ids, attention_mask=attention_mask)
          seq_emb = outputs.last_hidden_state
          # pack padded
          packed = nn.utils.rnn.pack_padded_sequence(seq_emb, lengths.cpu(), batch_first=True, enforce_sorted=False)
          _, hidden = self.rnn(packed)
          if self.rnn.bidirectional:
              h = torch.cat([hidden[-2], hidden[-1]], dim=1)
          else:
              h = hidden[-1]
          return self.fc(h)

  device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
  transformer_model = AutoModel.from_pretrained('prajjwal1/bert-tiny') # МОДЕЛЬ

  model = TransformerRNNClassifier(transformer_model, hidden_dim=128, num_classes=len(le.classes_)).to(device)

  optimizer = torch.optim.AdamW(model.parameters(), lr=2e-5)
  criterion = nn.CrossEntropyLoss()

  for epoch in range(3):
      model.train()
      total_loss = 0
      for input_ids, attention_mask, lengths, labels in train_loader:
          input_ids, attention_mask, lengths, labels = input_ids.to(device), attention_mask.to(device), lengths.to(device), labels.to(device)
          optimizer.zero_grad()
          logits = model(input_ids, attention_mask, lengths)
          loss = criterion(logits, labels)
          loss.backward()
          optimizer.step()
          total_loss += loss.item() * labels.size(0)
      print(f"Epoch {epoch+1}, Train loss: {total_loss/len(train_ds):.4f}")

  model.eval()
  all_preds, all_labels = [], []
  with torch.no_grad():
      for input_ids, attention_mask, lengths, labels in test_loader:
          input_ids, attention_mask, lengths = input_ids.to(device), attention_mask.to(device), lengths.to(device)
          logits = model(input_ids, attention_mask, lengths)
          preds = torch.argmax(logits, dim=1).cpu().numpy()
          all_preds.extend(preds)
          all_labels.extend(labels.numpy())

  names = [str(c) for c in le.classes_]
  print(classification_report(all_labels, all_preds, target_names=names))

def sms_cls_bidirectional_RNN():
  """

  ## №2 SMS-spam | classification Bidirectional_RNN

  2 вопрос (20 баллов) Набор данных: https://www.kaggle.com/datasets/thedevastator/sms-spam-collection-a-more-diverse-dataset. Реализовав рекуррентную нейронную сеть при помощи библиотеки PyTorch, решите задачу предсказания столбца label на основе столбца sms (задача классификации). Разделите набор данных на обучающее и тестовое множество с сохранением распределения классов. Обучите одно- и двунаправленную рекуррентную сеть и сравните качество модели на тестовом множестве, а также время обучения.
  """

  import kagglehub

  # Download latest version
  path = kagglehub.dataset_download("thedevastator/sms-spam-collection-a-more-diverse-dataset")

  print("Path to dataset files:", path)

  import torch
  import pandas as pd

  df = pd.read_csv(path + "/train.csv")
  df.head(3)

  # Токенизируем sms
  import nltk
  nltk.download('punkt_tab')
  nltk.download('punkt')
  from nltk.tokenize import word_tokenize

  def tokenize(text):
    return word_tokenize(text.lower())

  # Создаем словарь
  from collections import Counter

  counter = Counter()
  for sms in df.sms:
    counter.update(tokenize(sms))
  vocab = {tok: idx+2 for idx, (tok, _) in enumerate(counter.most_common())}
  vocab['<PAD>'] = 0
  vocab['<UNK>'] = 1

  # Класс датасета

  torch.manual_seed(42)
  class SMSDataset(torch.utils.data.Dataset):
    def __init__(self, texts, labels, vocab):
      self.texts = texts
      self.labels = labels
      self.vocab = vocab

    def __len__(self):
      return len(self.texts)

    def __getitem__(self, idx):
      tokens = tokenize(self.texts[idx])
      idxs = [self.vocab.get(tok, self.vocab['<UNK>']) for tok in tokens]
      return torch.tensor(idxs, dtype=torch.long), torch.tensor(self.labels[idx], dtype=torch.long)

  # collate функция (паддинг)

  def collate(batch):
    texts, labels = zip(*batch)
    lengths = torch.tensor([len(x) for x in texts])
    padded = torch.nn.utils.rnn.pad_sequence(texts, padding_value=vocab['<PAD>'], batch_first=True)
    return padded, lengths, torch.stack(labels)

  # train-test split с сохранением распределения классов

  from sklearn.model_selection import train_test_split

  train_texts, test_texts, train_labels, test_labels = train_test_split(
      df['sms'], df['label'], test_size=0.2, random_state=42, stratify=df['label']
      )

  train_ds = SMSDataset(train_texts.tolist(), train_labels.tolist(), vocab)
  test_ds = SMSDataset(test_texts.tolist(), test_labels.tolist(), vocab)

  batch_size = 64

  dl_train = torch.utils.data.DataLoader(train_ds, batch_size=batch_size, shuffle=True, collate_fn=collate)
  dl_test = torch.utils.data.DataLoader(test_ds, batch_size=batch_size, shuffle=False, collate_fn=collate)

  # Определеяем модель

  class RNNClassifier(torch.nn.Module):
    def __init__(self, vocab_size, embed_dim, hidden_dim, output_dim, bidirectional=False):
      super().__init__()
      self.embedding = torch.nn.Embedding(vocab_size, embed_dim, padding_idx=vocab['<PAD>'])
      self.rnn = torch.nn.RNN(embed_dim, hidden_dim, batch_first=True, bidirectional=bidirectional)
      self.fc = torch.nn.Linear(hidden_dim * (2 if bidirectional else 1), output_dim)

    def forward(self, text, lengths):
      embedded = self.embedding(text)
      packed = torch.nn.utils.rnn.pack_padded_sequence(embedded,
                                                      lengths.cpu(), batch_first=True,
                                                      enforce_sorted=False)
      packed_out, hidden = self.rnn(packed)
      if self.rnn.bidirectional:
        h = torch.cat([hidden[-2], hidden[-1]], dim=1)
      else:
        h = hidden[-1]
      return self.fc(h)

  # Функция для обучения

  def train_model(model, train_loader, criterion, optimizer, device):
    model.train()
    total_loss = 0
    for text, lengths, labels in train_loader:
      text, lengths, lables = text.to(device), lengths.to(device), labels.to(device)
      optimizer.zero_grad()
      preds = model(text, lengths)
      loss = criterion(preds, labels)
      loss.backward()
      optimizer.step()
      total_loss += loss.item() * labels.size(0)
    return total_loss / len(train_loader.dataset)

  # Функция для оценки модели

  from sklearn.metrics import accuracy_score

  def evaluate_model(model, test_loader, device):
    model.eval()
    preds_all, labels_all = [], []
    with torch.no_grad():
      for text, lengths, labels in test_loader:
        text, lengths = text.to(device), lengths.to(device)
        logits = model(text, lengths)
        preds = torch.argmax(logits, dim=1).cpu().numpy()
        preds_all.extend(preds)
        labels_all.extend(labels.numpy())
      return accuracy_score(labels_all, preds_all)

  # Цикл обучения -одно и -дунаправленной модели RNN

  import time

  device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
  vocab_size = len(vocab)
  embed_dim = 100
  hidden_dim = 128
  output_dim = 2
  num_epochs = 5

  results = {}
  for bidir in [False, True]:
    model = RNNClassifier(vocab_size, embed_dim, hidden_dim, output_dim, bidirectional=bidir).to(device)
    criterion = torch.nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters())
    mode = 'Bidirectional' if bidir else 'Undirectional'
    start = time.time()
    for epoch in range(num_epochs):
      train_loss = train_model(model, dl_train, criterion, optimizer, device)
    elapsed = time.time() - start
    acc = evaluate_model(model, dl_test, device)
    results[mode] = {'accuracy': acc, 'train_time_sec': elapsed}

  # Результаты

  print("Результаты")
  for u, v in results.items():
    print(f"{u}: Accuracy = {v['accuracy']:.4f}, Training Time = {v['train_time_sec']:.2f}s")

def nodata_create_embedding_class_pytorch_ops():
  """## №3 Tags: PyTorch | CustomEmbedding

  3 вопрос (20 баллов) Используя базовые операции для работы с тензорами PyTorch, создайте слой, повторяющий логику nn.Embedding из пакета PyTorch. Созданный модуль должен иметь следующие параметры: `num_embeddings`, `embedding_dim`, `padding_idx`, `max_norm`, `norm_type`. Продемонстрируйте все возможности разработанного слоя на примерах. Запрещается использовать готовый слой nn.Embedding.
  """

  import torch

  # Функция для того, чтобы заново нормировать веса эмбеддингов при каждом использовании класса
  # Делает это так, чтобы p-норма не превышала max_norm
  # Если норма больше строки больше max_norm, масштабирует её
  # new_row = row * (max_norm)/(||row||_p + eps)
  def _renorm_weights(weight, max_norm, norm_type, eps=1e-7):
    norms = weight.norm(p=norm_type, dim=1, keepdim=True)
    desired = torch.clamp(norms, max=max_norm)
    scale = desired / (norms + eps)
    return weight * scale

  class MyEmbedding(torch.nn.Module):
    def __init__(self, num_embeddings, embedding_dim,
                padding_idx=None, max_norm=None, norm_type=2.0):
      super().__init__()
      self.num_embeddings = num_embeddings
      self.embedding_dim = embedding_dim
      self.padding_idx = padding_idx
      self.max_norm = max_norm
      self.norm_type = norm_type

      # Инициализируем матрицу весов (пока пустая)
      self.weight = torch.nn.Parameter(
          torch.Tensor(num_embeddings, embedding_dim)
      )
      # Инициализируем весами из равномерного распределения. bound -- ограничение значений
      bound = 1.0 / embedding_dim**0.5
      torch.nn.init.uniform_(self.weight, -bound, bound)

      # Убираем ряд с токеном <PAD>, если он есть
      if padding_idx is not None:
        with torch.no_grad():
          self.weight.data[padding_idx].fill_(0)

    def forward(self, input):
      # используем max_norm на весах
      if self.max_norm is not None:
        with torch.no_grad():
          self.weight.data = _renorm_weights(
              self.weight.data, self.max_norm, self.norm_type
          )
        # Еще раз обнуляем эмбеддинги для <PAD>
        if self.padding_idx is not None:
          self.weight.data[self.padding_idx].fill_(0)

      return self.weight[input]

  # Демонстрируем возможности

  num_emb = 5 # кол-во токенов
  emb_dim = 3 # длина вектора эмбеддингов
  pad_idx = 0 # индекс токена <PAD>
  max_norm_val = 1.0 # норма эмбеддинга для одного токена не должна привышать это значение
  torch.manual_seed(42)
  emb = MyEmbedding(num_embeddings=num_emb,
                    embedding_dim=emb_dim,
                    padding_idx=pad_idx,
                    max_norm=max_norm_val,
                    norm_type=2.0)

  norms = emb.weight.data.norm(p=2, dim=1)
  print(f'Нормы векторов после создания класса слоя эмбеддингов (у <PAD> норма 0)\n{norms}')

  # Создадим для сравнения также слой nn.Embedding()
  torch_emb = torch.nn.Embedding(num_emb,
                          emb_dim,
                          padding_idx=pad_idx,
                          max_norm=max_norm_val)

  # Копируем начальные веса из нашего класса в nn.Embedding
  with torch.no_grad():
      torch_emb.weight.copy_(emb.weight)

  input_idx = torch.LongTensor([[0, 1, 2],
                                [3, 4, 0]])

  output_custom = emb(input_idx)
  output_torch = torch_emb(input_idx)

  print(f"Созданы одинаковые эмбеддинги {torch.allclose(output_custom, output_torch)}")

  print(f"Проверка того, что эмбеддинг токена <PAD> все еще нулевой:{output_custom[0, 0], output_custom[1, 2]}")
  print(emb.weight.data[2])
  # Увеличиваем один компоненты одного эмбеддинга, чтобы проверить работу max_norm
  with torch.no_grad():
    emb.weight.data[2] *= 10
  print(f"Норма эмебдиинга токена с id = 2 после увеличения {emb.weight.data[2].norm()}")

  # Делаем прямой проход через слой, чтобы сработал _renorm
  _ = emb(torch.LongTensor([[2]]))
  print(f"Норма эмбеддинга токена с id = 2 после перенормировки {emb.weight.data[2].norm()}")

  # Проверим работу L_1 нормы
  print('Проверям работу с L_1 нормой')
  emb_l1 = MyEmbedding(6, 3, padding_idx=0, max_norm=2.0, norm_type=1.0)
  with torch.no_grad():
    emb_l1.weight.data[1] = torch.tensor([3., -4., 0.])
  print(f"L1 норма до: {emb_l1.weight.data[1].norm(p=1)}")
  _ = emb_l1(torch.LongTensor([[1]]))
  print(f"L1 norm after:", emb_l1.weight.data[1].norm(p=1))

def pos_part_of_speech_RNN():
  """# tags: pos.json | определение части речи | RNN  

  Определить части речи для каждого слова, разделить на train/test. Вывести метрики качества кривые обучения, пример предсказания
  """

  import pandas as pd
  import torch
  import torch.nn as nn
  from torch.utils.data import Dataset, DataLoader
  from sklearn.model_selection import train_test_split
  from sklearn.metrics import classification_report, accuracy_score
  import matplotlib.pyplot as plt

  df = pd.read_json('/content/unzipped_07_exam/07_exam/nlp/pos.json')
  # Колонки: 'sentence' и 'tags'
  sentences = df['sentence'].str.split().tolist()  # список списков слов
  tags = df['tags'].tolist()                   # список списков меток
  print(f"Всего предложений: {len(df)}")

  # Построение словаря
  from collections import Counter
  word_counter = Counter(w for sent in sentences for w in sent)
  tag_set = sorted({t for tag_seq in tags for t in tag_seq})

  min_freq = 1
  vocab = {w: i+2 for i, (w, c) in enumerate(word_counter.items()) if c >= min_freq}
  vocab['<PAD>'] = 0
  vocab['<UNK>'] = 1

  tag2idx = {t: i for i, t in enumerate(tag_set)}
  idx2tag = {i: t for t, i in tag2idx.items()}

  # 3. Train/Test split
  train_s, test_s, train_t, test_t = train_test_split(
      sentences, tags, test_size=0.2, random_state=42
  )

  # Датасет
  class POSDataset(Dataset):
      def __init__(self, sents, tags, w2i, t2i):
          self.sents = sents
          self.tags = tags
          self.w2i = w2i
          self.t2i = t2i

      def __len__(self):
          return len(self.sents)

      def __getitem__(self, idx):
          words = self.sents[idx]
          tags = self.tags[idx]
          w_idxs = [self.w2i.get(w, self.w2i['<UNK>']) for w in words]
          t_idxs = [self.t2i[t] for t in tags]
          return torch.tensor(w_idxs, dtype=torch.long), torch.tensor(t_idxs, dtype=torch.long)

  def collate_fn(batch):
      seqs, labs = zip(*batch)
      lengths = torch.tensor([len(s) for s in seqs], dtype=torch.long)
      padded_seqs = nn.utils.rnn.pad_sequence(seqs, batch_first=True, padding_value=vocab['<PAD>'])
      padded_labs = nn.utils.rnn.pad_sequence(labs, batch_first=True, padding_value=-100)
      return padded_seqs, lengths, padded_labs

  batch_size = 64
  device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

  train_ds = POSDataset(train_s, train_t, vocab, tag2idx)
  test_ds  = POSDataset(test_s,  test_t,  vocab, tag2idx)
  train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, collate_fn=collate_fn)
  test_loader  = DataLoader(test_ds,  batch_size=batch_size, shuffle=False, collate_fn=collate_fn)

  # Модель
  class RNNTagger(nn.Module):
      def __init__(self, vocab_size, emb_dim, hidden_dim, tagset_size, pad_idx):
          super().__init__()
          self.embedding = nn.Embedding(vocab_size, emb_dim, padding_idx=pad_idx)
          self.lstm = nn.LSTM(emb_dim, hidden_dim, batch_first=True)
          self.fc = nn.Linear(hidden_dim, tagset_size)

      def forward(self, x, lengths):
          embedded = self.embedding(x)
          packed = nn.utils.rnn.pack_padded_sequence(embedded, lengths.cpu(), batch_first=True, enforce_sorted=False)
          output_packed, _ = self.lstm(packed)
          output, _ = nn.utils.rnn.pad_packed_sequence(output_packed, batch_first=True)
          logits = self.fc(output)
          return logits

  # Цикл обучения
  vocab_size = len(vocab)
  emb_dim = 100
  hidden_dim = 128
  tagset_size = len(tag2idx)
  pad_idx = vocab['<PAD>']

  model = RNNTagger(vocab_size, emb_dim, hidden_dim, tagset_size, pad_idx).to(device)
  criterion = nn.CrossEntropyLoss(ignore_index=-100)
  optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
  num_epochs = 5
  train_losses, val_losses = [], []

  for epoch in range(num_epochs):
      model.train()
      total_loss = 0
      for x, lengths, y in train_loader:
          x, lengths, y = x.to(device), lengths.to(device), y.to(device)
          optimizer.zero_grad()
          logits = model(x, lengths)
          loss = criterion(logits.view(-1, tagset_size), y.view(-1))
          loss.backward()
          optimizer.step()
          total_loss += loss.item() * x.size(0)
      train_losses.append(total_loss / len(train_ds))

      model.eval()
      val_loss = 0
      with torch.no_grad():
          for x, lengths, y in test_loader:
              x, lengths, y = x.to(device), lengths.to(device), y.to(device)
              logits = model(x, lengths)
              val_loss += criterion(logits.view(-1, tagset_size), y.view(-1)).item() * x.size(0)
      val_losses.append(val_loss / len(test_ds))
      print(f"Epoch {epoch+1}: train_loss={train_losses[-1]:.4f}, val_loss={val_losses[-1]:.4f}")

  plt.figure()
  plt.plot(train_losses, label='Train Loss')
  plt.plot(val_losses,   label='Val Loss')
  plt.xlabel('Epoch')
  plt.ylabel('Loss')
  plt.legend()
  plt.show()

  # Оценка на тесте
  all_preds, all_labels = [], []
  model.eval()
  with torch.no_grad():
      for x, lengths, y in test_loader:
          x, lengths = x.to(device), lengths.to(device)
          logits = model(x, lengths)
          preds = torch.argmax(logits, dim=-1).cpu().numpy()
          labels = y.cpu().numpy()
          for p_seq, l_seq, l in zip(preds, labels, lengths):
              all_preds.extend(p_seq[:l])
              all_labels.extend(l_seq[:l])

  print(classification_report(all_labels, all_preds, target_names=tag_set))
  print(f"Accuracy: {accuracy_score(all_labels, all_preds):.4f}")

  # Пример предсказания
  model.eval()
  with torch.no_grad():
      sample_sent = test_s[0]
      sample_idx = [vocab.get(w, vocab['<UNK>']) for w in sample_sent]
      length = torch.tensor([len(sample_idx)])
      input_tensor = torch.tensor(sample_idx, dtype=torch.long).unsqueeze(0).to(device)
      logits = model(input_tensor, length)
      preds = torch.argmax(logits, dim=-1).cpu().squeeze().tolist()

  print(f"Sentence: {' '.join(sample_sent)}")
  print(f"True tags: {test_t[0]}")
  print(f"Pred tags: {[idx2tag[i] for i in preds]}")

def pos_part_of_speech_linear():
  """

  # tags: pos.json | определение части речи |  nn.Linear
  Определить части речи для каждого слова, разделить на train/test. Вывести метрики качества кривые обучения, пример предсказания
  """

  import pandas as pd
  import torch
  import torch.nn as nn
  from torch.utils.data import Dataset, DataLoader
  from sklearn.model_selection import train_test_split
  from sklearn.metrics import classification_report, accuracy_score
  import matplotlib.pyplot as plt
  from collections import Counter

  # 1. Загрузка данных
  # Читаем JSON-массив объектов
  df = pd.read_json('/content/unzipped_07_exam/07_exam/nlp/pos.json')
  sentences = df['sentence'].str.split().tolist()
  tags = df['tags'].tolist()
  print(f"Всего предложений: {len(df)}")

  # 2. Словари
  word_counter = Counter(w for sent in sentences for w in sent)
  tag_set = sorted({t for tag_seq in tags for t in tag_seq})

  # Вокабуляр: <PAD>=0, <UNK>=1, остальные с 2
  vocab = {w: i+2 for i, (w, _) in enumerate(word_counter.items())}
  vocab['<PAD>'] = 0
  vocab['<UNK>'] = 1

  tag2idx = {t: i for i, t in enumerate(tag_set)}
  idx2tag = {i: t for t, i in tag2idx.items()}

  # 3. Train/Test split
  train_s, test_s, train_t, test_t = train_test_split(sentences, tags, test_size=0.2, random_state=42)

  class POSDataset(Dataset):
      def __init__(self, sents, tags, w2i, t2i):
          self.sents = sents
          self.tags = tags
          self.w2i = w2i
          self.t2i = t2i
      def __len__(self): return len(self.sents)
      def __getitem__(self, idx):
          words = self.sents[idx]
          tag_seq = self.tags[idx]
          w_idxs = [self.w2i.get(w, self.w2i['<UNK>']) for w in words]
          t_idxs = [self.t2i[t] for t in tag_seq]
          return torch.tensor(w_idxs, dtype=torch.long), torch.tensor(t_idxs, dtype=torch.long)

  def collate_fn(batch):
      seqs, labs = zip(*batch)
      lengths = torch.tensor([len(s) for s in seqs], dtype=torch.long)
      padded_seqs = nn.utils.rnn.pad_sequence(seqs, batch_first=True, padding_value=vocab['<PAD>'])
      padded_labs = nn.utils.rnn.pad_sequence(labs, batch_first=True, padding_value=-100)
      return padded_seqs, lengths, padded_labs

  # 5. DataLoader
  batch_size = 64
  device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
  train_ds = POSDataset(train_s, train_t, vocab, tag2idx)
  test_ds = POSDataset(test_s, test_t, vocab, tag2idx)
  train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, collate_fn=collate_fn)
  test_loader = DataLoader(test_ds, batch_size=batch_size, shuffle=False, collate_fn=collate_fn)

  class LinearTagger(nn.Module):
      def __init__(self, vocab_size, emb_dim, tagset_size, pad_idx):
          super().__init__()
          self.embedding = nn.Embedding(vocab_size, emb_dim, padding_idx=pad_idx)
          self.fc = nn.Linear(emb_dim, tagset_size)
      def forward(self, x):
          # x: [B, L]
          emb = self.embedding(x)        # [B, L, E]
          logits = self.fc(emb)          # [B, L, T]
          return logits

  vocab_size = len(vocab)
  emb_dim = 100
  tagset_size = len(tag2idx)
  pad_idx = vocab['<PAD>']
  model = LinearTagger(vocab_size, emb_dim, tagset_size, pad_idx).to(device)
  criterion = nn.CrossEntropyLoss(ignore_index=-100)
  optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)

  # 7. Training loop
  num_epochs = 5
  train_losses, val_losses = [], []
  for epoch in range(num_epochs):
      model.train(); total_loss = 0
      for x, lengths, y in train_loader:
          x, y = x.to(device), y.to(device)
          optimizer.zero_grad()
          logits = model(x)  # [B, L, T]
          loss = criterion(logits.view(-1, tagset_size), y.view(-1))
          loss.backward(); optimizer.step()
          total_loss += loss.item() * x.size(0)
      train_losses.append(total_loss / len(train_ds))
      # Validation
      model.eval(); val_loss = 0
      with torch.no_grad():
          for x, lengths, y in test_loader:
              x, y = x.to(device), y.to(device)
              logits = model(x)
              val_loss += criterion(logits.view(-1, tagset_size), y.view(-1)).item() * x.size(0)
      val_losses.append(val_loss / len(test_ds))
      print(f"Epoch {epoch+1}: train_loss={train_losses[-1]:.4f}, val_loss={val_losses[-1]:.4f}")

  plt.figure()
  plt.plot(train_losses, label='Train Loss')
  plt.plot(val_losses, label='Val Loss')
  plt.xlabel('Epoch'); plt.ylabel('Loss'); plt.legend(); plt.show()

  # 9. Test metrics
  all_preds, all_labels = [], []
  model.eval()
  with torch.no_grad():
      for x, lengths, y in test_loader:
          x = x.to(device)
          logits = model(x)
          preds = torch.argmax(logits, dim=-1).cpu().numpy()
          labels = y.numpy()
          for p_seq, l_seq, l in zip(preds, labels, lengths):
              all_preds.extend(p_seq[:l]); all_labels.extend(l_seq[:l])
  print(classification_report(all_labels, all_preds, target_names=tag_set))
  print(f"Accuracy: {accuracy_score(all_labels, all_preds):.4f}")

  # 10. Example prediction
  model.eval()
  with torch.no_grad():
      sent = test_s[0]
      idxs = [vocab.get(w, vocab['<UNK>']) for w in sent]
      x = torch.tensor(idxs, dtype=torch.long).unsqueeze(0).to(device)
      logits = model(x)
      preds = torch.argmax(logits, dim=-1).cpu().squeeze().tolist()
  print(f"Sentence: {' '.join(sent)}")
  print(f"True tags: {test_t[0]}")
  print(f"Pred tags: {[idx2tag[i] for i in preds]}")

def tweet_cat_char_level_gen_RNN():
  """# tags: tweet_cat | посимвольная генерация текста | RNN

  Создать модель для посимвольной генерации текста с использованием RNN.
  """

  import pandas as pd
  import torch
  import torch.nn as nn
  from torch.utils.data import Dataset, DataLoader
  import matplotlib.pyplot as plt
  import numpy as np

  # 1. Загрузка данных
  # Читаем CSV с твитами
  df = pd.read_csv('/content/unzipped_07_exam/07_exam/nlp/tweet_cat.csv')
  texts = df['text'].astype(str).tolist()
  print(f"Всего текстов: {len(texts)}")

  # 2. Построение словаря символов
  all_text = "\n".join(texts)
  chars = sorted(list(set(all_text)))
  vocab_size = len(chars)
  char2idx = {ch: i for i, ch in enumerate(chars)}
  idx2char = {i: ch for ch, i in char2idx.items()}

  # 3. Подготовка датасета: посимвольные последовательности
  class CharDataset(Dataset):
      def __init__(self, texts, char2idx, seq_len=100):
          self.data = []
          self.seq_len = seq_len
          self.char2idx = char2idx
          # объединяем все тексты в одну строку для непрерывного текста
          text = "\n".join(texts)
          # создаем пары (seq, next_char)
          for i in range(0, len(text) - seq_len):
              seq = text[i:i+seq_len]
              target = text[i+seq_len]
              self.data.append((seq, target))
      def __len__(self):
          return len(self.data)
      def __getitem__(self, idx):
          seq, target = self.data[idx]
          x = torch.tensor([self.char2idx.get(ch, 0) for ch in seq], dtype=torch.long)
          y = torch.tensor(self.char2idx.get(target, 0), dtype=torch.long)
          return x, y

  # Параметры
  seq_len = 20
  batch_size = 64
  device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

  # Создаем набор и загрузчики
  dataset = CharDataset(texts, char2idx, seq_len)
  train_size = int(0.9 * len(dataset))
  train_ds, val_ds = torch.utils.data.random_split(dataset, [train_size, len(dataset)-train_size])
  train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
  val_loader   = DataLoader(val_ds,   batch_size=batch_size, shuffle=False)

  # 4. Модель RNN для генерации текста
  class CharRNN(nn.Module):
      def __init__(self, vocab_size, emb_dim, hidden_dim, num_layers=1):
          super().__init__()
          self.embedding = nn.Embedding(vocab_size, emb_dim)
          self.rnn = nn.RNN(emb_dim, hidden_dim, num_layers, batch_first=True)
          self.fc = nn.Linear(hidden_dim, vocab_size)

      def forward(self, x, hidden=None):
          emb = self.embedding(x)
          output, hidden = self.rnn(emb, hidden)
          logits = self.fc(output[:, -1, :])  # берем последний timestep
          return logits, hidden

  # Инициализация модели
  emb_dim = 64
  hidden_dim = 128
  model = CharRNN(vocab_size, emb_dim, hidden_dim).to(device)
  criterion = nn.CrossEntropyLoss()
  optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)

  # 5. Цикл обучения
  num_epochs = 5
  train_losses, val_losses = [], []
  for epoch in range(num_epochs):
      model.train()
      total_loss = 0
      for x, y in train_loader:
          x, y = x.to(device), y.to(device)
          optimizer.zero_grad()
          logits, _ = model(x)
          loss = criterion(logits, y)
          loss.backward()
          optimizer.step()
          total_loss += loss.item() * x.size(0)
      train_losses.append(total_loss / len(train_ds))

      model.eval()
      val_loss = 0
      with torch.no_grad():
          for x, y in val_loader:
              x, y = x.to(device), y.to(device)
              logits, _ = model(x)
              val_loss += criterion(logits, y).item() * x.size(0)
      val_losses.append(val_loss / len(val_ds))
      print(f"Epoch {epoch+1}: train_loss={train_losses[-1]:.4f}, val_loss={val_losses[-1]:.4f}")

  # 6. Кривые обучения
  plt.figure()
  plt.plot(train_losses, label='Train Loss')
  plt.plot(val_losses,   label='Val Loss')
  plt.xlabel('Epoch'); plt.ylabel('Loss'); plt.legend(); plt.show()

  # 7. Генерация примера текста
  model.eval()
  with torch.no_grad():
      # выбираем случайный начальный фрагмент
      start_idx = np.random.randint(0, len(dataset))
      seq, _ = dataset[start_idx]
      input_seq = seq.unsqueeze(0).to(device)
      generated = [idx2char[idx.item()] for idx in seq]
      hidden = None
      for _ in range(200):
          logits, hidden = model(input_seq, hidden)
          probs = torch.softmax(logits, dim=-1).cpu().numpy().ravel()
          next_idx = np.random.choice(range(vocab_size), p=probs)
          generated.append(idx2char[next_idx])
          # обновляем вход: сдвигаем окно
          input_seq = torch.cat([input_seq[:,1:], torch.tensor([[next_idx]], device=device)], dim=1)
      print("".join(generated))

def tweet_cat_next_token_pred_RNN():
  """# tags: tweet.cat | предсказание токена | RNN

  Создать модель для предсказания токена текста с использованием RNN.
  """

  import pandas as pd
  import torch
  import torch.nn as nn
  from torch.utils.data import Dataset, DataLoader
  from sklearn.model_selection import train_test_split
  import matplotlib.pyplot as plt
  from collections import Counter
  import numpy as np

  # 1. Загрузка данных и токенизация
  # Читаем CSV с твитами
  df = pd.read_csv('/content/unzipped_07_exam/07_exam/nlp/tweet_cat.csv')
  texts = df['text'].astype(str).tolist()

  # Простая токенизация по пробелам
  tokenized = [t.split() for t in texts]
  all_tokens = [tok for seq in tokenized for tok in seq]
  print(f"Всего токенов: {len(all_tokens)}, уникальных: {len(set(all_tokens))}")

  # 2. Построение словаря токенов
  counter = Counter(all_tokens)
  vocab = {tok: i+2 for i, (tok, _) in enumerate(counter.items())}
  vocab['<PAD>'] = 0
  vocab['<UNK>'] = 1
  idx2tok = {i: tok for tok, i in vocab.items()}
  vocab_size = len(vocab)

  # 3. Подготовка данных для предсказания следующего токена
  seq_len = 10
  sequences = []
  for seq in tokenized:
      if len(seq) <= seq_len:
          continue
      for i in range(len(seq) - seq_len):
          src = seq[i:i+seq_len]
          tgt = seq[i+seq_len]
          sequences.append((src, tgt))
  print(f"Всего примеров: {len(sequences)}")

  # 4. Dataset
  class TokenDataset(Dataset):
      def __init__(self, sequences, vocab):
          self.sequences = sequences
          self.vocab = vocab
      def __len__(self):
          return len(self.sequences)
      def __getitem__(self, idx):
          src, tgt = self.sequences[idx]
          src_idx = [self.vocab.get(tok, self.vocab['<UNK>']) for tok in src]
          tgt_idx = self.vocab.get(tgt, self.vocab['<UNK>'])
          return torch.tensor(src_idx, dtype=torch.long), torch.tensor(tgt_idx, dtype=torch.long)

  # 5. Train/Test split and DataLoader
  train_seq, test_seq = train_test_split(sequences, test_size=0.2, random_state=42)
  train_ds = TokenDataset(train_seq, vocab)
  test_ds  = TokenDataset(test_seq,  vocab)
  batch_size = 128
  train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
  test_loader  = DataLoader(test_ds,  batch_size=batch_size, shuffle=False)

  # 6. Модель RNN Language Model
  class TokenRNN(nn.Module):
      def __init__(self, vocab_size, emb_dim, hidden_dim, num_layers=1):
          super().__init__()
          self.embedding = nn.Embedding(vocab_size, emb_dim, padding_idx=vocab['<PAD>'])
          self.rnn = nn.LSTM(emb_dim, hidden_dim, num_layers, batch_first=True)
          self.fc = nn.Linear(hidden_dim, vocab_size)
      def forward(self, x, hidden=None):
          emb = self.embedding(x)
          output, hidden = self.rnn(emb, hidden)
          # output: [B, L, H]
          logits = self.fc(output[:, -1, :])  # прогноз на основе последнего состояния
          return logits, hidden

  # 7. Инициализация и обучение
  device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
  model = TokenRNN(vocab_size, emb_dim=128, hidden_dim=256).to(device)
  criterion = nn.CrossEntropyLoss()
  optimizer = torch.optim.Adam(model.parameters(), lr=0.01)

  num_epochs = 5
  train_losses, test_losses = [], []
  for epoch in range(num_epochs):
      model.train(); total_train, total_test = 0, 0
      for x, y in train_loader:
          x, y = x.to(device), y.to(device)
          optimizer.zero_grad()
          logits, _ = model(x)
          loss = criterion(logits, y)
          loss.backward(); optimizer.step()
          total_train += loss.item() * x.size(0)
      train_losses.append(total_train / len(train_ds))

      model.eval(); tot = 0
      with torch.no_grad():
          for x, y in test_loader:
              x, y = x.to(device), y.to(device)
              logits, _ = model(x)
              tot += criterion(logits, y).item() * x.size(0)
      test_losses.append(tot / len(test_ds))
      print(f"Epoch {epoch+1}: train_loss={train_losses[-1]:.4f}, test_loss={test_losses[-1]:.4f}")

  # 8. Кривые обучения
  plt.figure()
  plt.plot(train_losses, label='Train Loss')
  # plt.plot(test_losses,  label='Test Loss')
  plt.xlabel('Epoch'); plt.ylabel('Loss'); plt.legend(); plt.show()

  # 9. Пример предсказания следующего токена
  model.eval()
  with torch.no_grad():
      example_src, example_tgt = test_seq[0]
      idxs = [vocab.get(tok, vocab['<UNK>']) for tok in example_src]
      x = torch.tensor(idxs, dtype=torch.long).unsqueeze(0).to(device)
      logits, _ = model(x)
      pred_idx = torch.argmax(logits, dim=-1).item()
      print(f"Input sequence: {' '.join(example_src)}")
      print(f"True next token: {example_tgt}")
      print(f"Predicted next token: {idx2tok[pred_idx]}")

def tweets_disaster_create_RNN_with_linear():
  """# tags: tweets_disaster.csv | реализовать модель RNN, используя nn.linear

  Реализовать модель rnn, исользуя полнозвязные слои nn.Linear на данных tweets_diaster.csv. Использовать поля text и target.
  """

  import pandas as pd
  import torch
  import torch.nn as nn
  from torch.utils.data import Dataset, DataLoader
  from sklearn.model_selection import train_test_split
  from sklearn.metrics import classification_report, accuracy_score
  import matplotlib.pyplot as plt
  from collections import Counter
  import nltk
  from nltk.tokenize import word_tokenize

  # 1. Загрузка данных
  # CSV с полями text и target
  df = pd.read_csv('/content/unzipped_07_exam/07_exam/nlp/tweets_disaster.csv')
  texts = df['text'].astype(str)
  labels = df['target'].astype(int)
  print(f"Всего примеров: {len(df)}, позитивных (disaster=1): {labels.sum()}, негативных: {len(df)-labels.sum()}")

  # 2. Токенизация и словарь слов
  nltk.download('punkt_tab')
  tokenized = texts.apply(lambda x: word_tokenize(x.lower()))
  word_counter = Counter(tok for seq in tokenized for tok in seq)
  vocab = {w: i+2 for i, (w, _) in enumerate(word_counter.items())}
  vocab['<PAD>'] = 0
  vocab['<UNK>'] = 1

  # 3. Train/Test split и DataLoader
  train_idx, test_idx = train_test_split(df.index, test_size=0.2, stratify=labels, random_state=42)

  class DisasterDataset(Dataset):
      def __init__(self, indices):
          self.idx = indices
      def __len__(self):
        return len(self.idx)
      def __getitem__(self, i):
          idx = self.idx[i]
          seq = tokenized[idx]
          x = [vocab.get(w, vocab['<UNK>']) for w in seq]
          y = labels[idx]
          return torch.tensor(x, dtype=torch.long), torch.tensor(y, dtype=torch.float)

  def collate_fn(batch):
      seqs, labs = zip(*batch)
      lengths = torch.tensor([len(s) for s in seqs], dtype=torch.long)
      padded = nn.utils.rnn.pad_sequence(seqs, batch_first=True, padding_value=vocab['<PAD>'])
      return padded, lengths, torch.stack(labs)

  batch_size = 64
  device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
  train_loader = DataLoader(DisasterDataset(train_idx), batch_size=batch_size, shuffle=True, collate_fn=collate_fn)
  test_loader  = DataLoader(DisasterDataset(test_idx),  batch_size=batch_size, shuffle=False, collate_fn=collate_fn)

  # 4. Модель: Simple RNN через nn.Linear
  class SimpleRNNClassifier(nn.Module):
      def __init__(self, vocab_size, emb_dim, hidden_dim, pad_idx):
          super().__init__()
          self.embedding = nn.Embedding(vocab_size, emb_dim, padding_idx=pad_idx)
          self.rnn_x = nn.Linear(emb_dim, hidden_dim)
          self.rnn_h = nn.Linear(hidden_dim, hidden_dim)
          self.fc = nn.Linear(hidden_dim, 1)

      def forward(self, x, lengths):
          emb = self.embedding(x)
          h = torch.zeros(x.size(0), self.rnn_h.out_features, device=x.device)
          for t in range(emb.size(1)):
              h = torch.tanh(self.rnn_x(emb[:, t, :]) + self.rnn_h(h))
          logits = self.fc(h).squeeze(1)
          return logits

  # 5. Обучение и оценка
  vocab_size = len(vocab)
  model = SimpleRNNClassifier(vocab_size, emb_dim=100, hidden_dim=128, pad_idx=vocab['<PAD>']).to(device)
  criterion = nn.BCEWithLogitsLoss()
  optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)

  num_epochs = 5
  train_losses, val_losses = [], []
  for epoch in range(num_epochs):
      model.train()
      total_loss = 0
      for x, lengths, y in train_loader:
          x, lengths, y = x.to(device), lengths.to(device), y.to(device)
          optimizer.zero_grad()
          logits = model(x, lengths)
          loss = criterion(logits, y)
          loss.backward()
          optimizer.step()
          total_loss += loss.item() * x.size(0)
      train_losses.append(total_loss / len(train_idx))

      model.eval()
      val_loss = 0
      with torch.no_grad():
          for x, lengths, y in test_loader:
              x, lengths, y = x.to(device), lengths.to(device), y.to(device)
              logits = model(x, lengths)
              val_loss += criterion(logits, y).item() * x.size(0)
      val_losses.append(val_loss / len(test_idx))
      print(f"Epoch {epoch+1}: train_loss={train_losses[-1]:.4f}, val_loss={val_losses[-1]:.4f}")

  # 6. Кривые обучения
  plt.figure()
  plt.plot(train_losses, label='Train Loss')
  plt.plot(val_losses,   label='Val Loss')
  plt.xlabel('Epoch'); plt.ylabel('Loss'); plt.legend(); plt.show()

  # 7. Метрики на тесте
  all_preds, all_labels = [], []
  model.eval()
  with torch.no_grad():
      for x, lengths, y in test_loader:
          x, lengths = x.to(device), lengths.to(device)
          logits = model(x, lengths)
          preds = (torch.sigmoid(logits) > 0.5).int().cpu().numpy()
          all_preds.extend(preds)
          all_labels.extend(y.cpu().numpy().astype(int))
  print(classification_report(all_labels, all_preds))
  print(f"Accuracy: {accuracy_score(all_labels, all_preds):.4f}")

  # 8. Пример предсказания
  model.eval()
  with torch.no_grad():
      x, lengths, y = next(iter(test_loader))
      x, lengths, y = x.to(device), lengths.to(device), y.to(device)
      logits = model(x, lengths)
      preds = (torch.sigmoid(logits) > 0.5).long()
      seq = x[0, :lengths[0]].cpu().numpy()
      words = [list(vocab.keys())[list(vocab.values()).index(idx)] if idx in vocab.values() else '<UNK>' for idx in seq]
      print("Text:", ' '.join(words))
      print("True:", y[0].item(), "Pred:", preds[0].item())

def tweet_cat_create_word2vec_using_embedding():
  """# tags: tweet_cat.csv | реализовать word2vec и спользованием nn.Embeddings

  Реализовать word2vec с использованием nn.Embeddings. Показать возможности разработанной модели на примерах.
  """

  import pandas as pd
  import torch
  import torch.nn as nn
  from torch.utils.data import Dataset, DataLoader
  import torch.optim as optim
  import numpy as np
  import nltk
  from nltk.tokenize import word_tokenize
  from collections import Counter

  # 1. Сбор корпуса
  nltk.download('punkt_tab')
  df = pd.read_csv('/content/unzipped_07_exam/07_exam/nlp/tweet_cat.csv')
  texts = df['text'].astype(str).tolist()
  # Токенизация пословно через word_tokenize
  tokenized = [word_tokenize(text.lower()) for text in texts]

  # 2. Построение словаря
  all_tokens = [tok for seq in tokenized for tok in seq]
  vocab_count = Counter(all_tokens)
  vocab = {w: i for i, (w, _) in enumerate(vocab_count.items())}
  id2word = {i: w for w, i in vocab.items()}
  vocab_size = len(vocab)

  # 3. Генерация примеров для skip-gram
  window_size = 2
  pairs = []
  for seq in tokenized:
      seq_ids = [vocab[w] for w in seq]
      for i, target in enumerate(seq_ids):
          context_indices = list(range(max(0, i-window_size), i)) + \
                            list(range(i+1, min(len(seq_ids), i+window_size+1)))
          for ctx_i in context_indices:
              pairs.append((target, seq_ids[ctx_i]))

  # 4. Negative sampling
  dist = np.array([vocab_count[id2word[i]] for i in range(vocab_size)], dtype=np.float32)
  dist = dist / dist.sum()
  K = 5

  class Word2VecDataset(Dataset):
      def __init__(self, pairs, vocab_size, dist, K):
          self.pairs = pairs
          self.vocab_size = vocab_size
          self.dist = dist
          self.K = K

      def __len__(self):
          return len(self.pairs)

      def __getitem__(self, idx):
          target, context = self.pairs[idx]
          neg_contexts = np.random.choice(self.vocab_size, size=self.K, p=self.dist)
          return target, context, neg_contexts

  # 5. DataLoader
  dataset = Word2VecDataset(pairs, vocab_size, dist, K)
  dataloader = DataLoader(dataset, batch_size=512, shuffle=True)

  device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

  # 6. Модель Skip-gram с негативным сэмплированием
  class SkipGramNeg(nn.Module):
      def __init__(self, vocab_size, emb_dim):
          super().__init__()
          self.in_embed = nn.Embedding(vocab_size, emb_dim)
          self.out_embed = nn.Embedding(vocab_size, emb_dim)

      def forward(self, targets, contexts, neg_contexts):
          v_t = self.in_embed(targets)                    # [B, E]
          u_c = self.out_embed(contexts)                  # [B, E]
          pos_score = torch.sum(v_t * u_c, dim=1)         # [B]
          pos_loss = -torch.log(torch.sigmoid(pos_score) + 1e-10)

          u_neg = self.out_embed(neg_contexts)            # [B, K, E]
          neg_score = torch.bmm(u_neg, v_t.unsqueeze(2)).squeeze(2)  # [B, K]
          neg_loss = -torch.sum(torch.log(1 - torch.sigmoid(neg_score) + 1e-10), dim=1)  # [B]

          return torch.mean(pos_loss + neg_loss)

  # 7. Обучение модели
  emb_dim = 100
  model = SkipGramNeg(vocab_size, emb_dim).to(device)
  optimizer = optim.Adam(model.parameters(), lr=1e-3)
  num_epochs = 3

  for epoch in range(1, num_epochs+1):
      total_loss = 0
      for targets, contexts, neg_contexts in dataloader:
          targets = targets.to(device)
          contexts = contexts.to(device)
          neg_contexts = neg_contexts.to(device)

          optimizer.zero_grad()
          loss = model(targets, contexts, neg_contexts)
          loss.backward()
          optimizer.step()
          total_loss += loss.item()
      print(f"Epoch {epoch}, loss: {total_loss/len(dataloader):.4f}")

  # 8. Пример ближайших соседей
  enb_weights = model.in_embed.weight.data.cpu().numpy()

  def find_nearest(word, topn=5):
      if word not in vocab:
          print(f"'{word}' not in vocab")
          return
      idx = vocab[word]
      vec = enb_weights[idx]
      sims = np.dot(enb_weights, vec)
      norms = np.linalg.norm(enb_weights, axis=1) * np.linalg.norm(vec)
      cosine = sims / (norms + 1e-10)
      nearest = np.argsort(-cosine)[1:topn+1]
      print(f"Nearest to '{word}':", [id2word[i] for i in nearest])

  # Демонстрация
  for w in ['love', 'hate', 'disaster', 'win', 'lose']:
      find_nearest(w)

def activities_create_RNN_cell_one_gate_using_torch():
  """# tags: activities.csv | реализовать логику RNN с одним gate

  Реализовать логику RNN с одним Gate при помощи полносвязных слоев. Проверить работу на activities.csv


  """

  import pandas as pd
  import torch
  import torch.nn as nn
  from torch.utils.data import Dataset, DataLoader
  from sklearn.model_selection import train_test_split
  from sklearn.metrics import classification_report, accuracy_score
  import matplotlib.pyplot as plt
  import nltk
  from nltk.tokenize import word_tokenize
  from collections import Counter

  # 1. Загрузка и фильтрация данных
  nltk.download('punkt')
  df = pd.read_csv('/content/unzipped_07_exam/07_exam/nlp/activities.csv')  # столбцы: Text, Review-Activity, Season
  # Оставляем только строки с Review-Activity == 'ACTIVITY'
  df = df[df['Review-Activity'] == 'ACTIVITY']
  # Убираем неинформативные или неподходящие метки сезона
  valid_seasons = ['SUMMER', 'WINTER', 'SPRING', 'FALL']
  # Оставляем только эти сезоны
  df = df[df['Season'].isin(valid_seasons)].reset_index(drop=True)

  # Целевые метки: Season (categorical)
  seasons = df['Season'].unique().tolist()
  season2idx = {s: i for i, s in enumerate(seasons)}
  idx2season = {i: s for s, i in season2idx.items()}

  # 2. Токенизация и словарь
  texts = df['Text'].astype(str).tolist()
  tokenized = [word_tokenize(text.lower()) for text in texts]
  word_counter = Counter(tok for seq in tokenized for tok in seq)
  vocab = {w: i+2 for i, (w, _) in enumerate(word_counter.items())}
  vocab['<PAD>'] = 0
  vocab['<UNK>'] = 1
  vocab_size = len(vocab)

  # 3. Разбиение на train/test
  labels = df['Season'].map(season2idx)
  train_idx, test_idx = train_test_split(df.index, test_size=0.2, stratify=labels, random_state=42)

  # 4. Dataset и collate_fn
  class ActivityDataset(Dataset):
      def __init__(self, indices):
          self.indices = indices
      def __len__(self):
          return len(self.indices)
      def __getitem__(self, idx):
          i = self.indices[idx]
          seq = tokenized[i]
          x = [vocab.get(w, vocab['<UNK>']) for w in seq]
          y = season2idx[df.loc[i, 'Season']]
          return torch.tensor(x, dtype=torch.long), torch.tensor(y, dtype=torch.long)

  def collate_fn(batch):
      seqs, labs = zip(*batch)
      lengths = torch.tensor([len(s) for s in seqs], dtype=torch.long)
      padded = nn.utils.rnn.pad_sequence(seqs, batch_first=True, padding_value=vocab['<PAD>'])
      return padded, lengths, torch.stack(labs)

  batch_size = 32
  device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
  train_loader = DataLoader(ActivityDataset(train_idx), batch_size=batch_size, shuffle=True, collate_fn=collate_fn)
  test_loader  = DataLoader(ActivityDataset(test_idx),  batch_size=batch_size, shuffle=False, collate_fn=collate_fn)

  # 5. Модель RNN с одним gate
  def gated_rnn_cell(x_t, h_prev, W_xh, W_hh, W_xg, W_hg, b_h=None, b_g=None):
      g_t = torch.sigmoid(x_t @ W_xg.T + h_prev @ W_hg.T + (b_g if b_g is not None else 0))
      h_tilde = torch.tanh(x_t @ W_xh.T + h_prev @ W_hh.T + (b_h if b_h is not None else 0))
      h_t = g_t * h_tilde + (1 - g_t) * h_prev
      return h_t

  class OneGateRNNClassifier(nn.Module):
      def __init__(self, vocab_size, emb_dim, hidden_dim, num_classes, pad_idx):
          super().__init__()
          self.embedding = nn.Embedding(vocab_size, emb_dim, padding_idx=pad_idx)
          self.W_xh = nn.Parameter(torch.Tensor(hidden_dim, emb_dim))
          self.W_hh = nn.Parameter(torch.Tensor(hidden_dim, hidden_dim))
          self.b_h = nn.Parameter(torch.zeros(hidden_dim))
          self.W_xg = nn.Parameter(torch.Tensor(hidden_dim, emb_dim))
          self.W_hg = nn.Parameter(torch.Tensor(hidden_dim, hidden_dim))
          self.b_g = nn.Parameter(torch.zeros(hidden_dim))
          self.fc = nn.Linear(hidden_dim, num_classes)
          self.init_parameters()

      def init_parameters(self):
          for param in [self.W_xh, self.W_hh, self.W_xg, self.W_hg]:
              nn.init.xavier_uniform_(param)

      def forward(self, x, lengths):
          emb = self.embedding(x)
          batch_size, L, _ = emb.size()
          h = torch.zeros(batch_size, self.W_hh.size(0), device=emb.device)
          for t in range(L):
              h = gated_rnn_cell(emb[:, t, :], h, self.W_xh, self.W_hh, self.W_xg, self.W_hg, self.b_h, self.b_g)
          return self.fc(h)

  # 6. Инициализация и обучение
  num_classes = len(seasons)
  model = OneGateRNNClassifier(vocab_size, emb_dim=64, hidden_dim=128, num_classes=num_classes, pad_idx=vocab['<PAD>']).to(device)
  criterion = nn.CrossEntropyLoss()
  optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)

  num_epochs = 10
  train_losses, val_losses = [], []
  for epoch in range(1, num_epochs+1):
      model.train(); total_loss = 0
      for x, lengths, y in train_loader:
          x, lengths, y = x.to(device), lengths.to(device), y.to(device)
          optimizer.zero_grad()
          logits = model(x, lengths)
          loss = criterion(logits, y)
          loss.backward(); optimizer.step()
          total_loss += loss.item() * x.size(0)
      train_losses.append(total_loss / len(train_idx))

      model.eval(); val_loss = 0; all_preds, all_labels = [], []
      with torch.no_grad():
          for x, lengths, y in test_loader:
              x, lengths, y = x.to(device), lengths.to(device), y.to(device)
              logits = model(x, lengths)
              val_loss += criterion(logits, y).item() * x.size(0)
              all_preds.extend(torch.argmax(logits, dim=1).cpu().tolist())
              all_labels.extend(y.cpu().tolist())
      val_losses.append(val_loss / len(test_idx))
      print(f"Epoch {epoch}: train_loss={train_losses[-1]:.4f}, val_loss={val_losses[-1]:.4f}")

  # 7. Кривые обучения
  plt.figure()
  plt.plot(train_losses, label='Train Loss')
  plt.plot(val_losses,   label='Val Loss')
  plt.xlabel('Epoch'); plt.ylabel('Loss'); plt.legend(); plt.show()

  # 8. Отчет и пример
  print(classification_report(all_labels, all_preds, target_names=seasons))
  print(f"Accuracy: {accuracy_score(all_labels, all_preds):.4f}")
  text, true = texts[test_idx[0]], df.loc[test_idx[0], 'Season']
  seq = tokenized[test_idx[0]]
  input_ids = torch.tensor([vocab.get(w, vocab['<UNK>']) for w in seq], dtype=torch.long).unsqueeze(0).to(device)
  pred = idx2season[torch.argmax(model(input_ids, torch.tensor([len(seq)]).to(device)), dim=1).item()]
  print(f"Text: {text}\nTrue: {true}, Pred: {pred}")

def activities_use_conv1d_for_nlp_torch():
  """# tags: activities.csv | Применить одномерный сверточный слой для nlp задачи

  Для классификации применить одномерный сверточный слой. Данные: activities.csv


  """

  import pandas as pd
  import torch
  import torch.nn as nn
  from torch.utils.data import Dataset, DataLoader
  from sklearn.model_selection import train_test_split
  from sklearn.metrics import classification_report, accuracy_score
  import matplotlib.pyplot as plt
  import nltk
  from nltk.tokenize import word_tokenize
  from collections import Counter

  # 1. Загрузка и фильтрация данных
  nltk.download('punkt_tab')
  df = pd.read_csv('/content/unzipped_07_exam/07_exam/nlp/activities.csv')
  df = df[df['Review-Activity']=='ACTIVITY']
  valid_seasons = ['SUMMER','WINTER','SPRING','FALL']
  df = df[df['Season'].isin(valid_seasons)].reset_index(drop=True)

  # Метки сезонов
  seasons = df['Season'].unique().tolist()
  season2idx = {s:i for i,s in enumerate(seasons)}
  idx2season = {i:s for s,i in season2idx.items()}

  # 2. Токенизация и словарь
  texts = df['Text'].astype(str).tolist()
  tokenized = [word_tokenize(t.lower()) for t in texts]
  word_counter = Counter(tok for seq in tokenized for tok in seq)
  vocab = {w:i+2 for i,(w,_) in enumerate(word_counter.items())}
  vocab['<PAD>']=0; vocab['<UNK>']=1
  vocab_size = len(vocab)

  # 3. Разбиение на train/test
  labels = df['Season'].map(season2idx)
  train_idx, test_idx = train_test_split(df.index, test_size=0.2, stratify=labels, random_state=42)

  # 4. Dataset и collate_fn
  class ActivityDataset(Dataset):
      def __init__(self, indices): self.indices = indices
      def __len__(self): return len(self.indices)
      def __getitem__(self, i):
          idx = self.indices[i]
          seq = tokenized[idx]
          x = [vocab.get(w,vocab['<UNK>']) for w in seq]
          y = season2idx[df.loc[idx,'Season']]
          return torch.tensor(x,dtype=torch.long), torch.tensor(y,dtype=torch.long)

  def collate_fn(batch):
      seqs, labs = zip(*batch)
      lengths = torch.tensor([len(s) for s in seqs])
      padded = nn.utils.rnn.pad_sequence(seqs, batch_first=True, padding_value=vocab['<PAD>'])
      return padded, lengths, torch.stack(labs)

  batch_size=32; device=torch.device('cuda' if torch.cuda.is_available() else 'cpu')
  train_loader = DataLoader(ActivityDataset(train_idx), batch_size=batch_size, shuffle=True, collate_fn=collate_fn)
  test_loader  = DataLoader(ActivityDataset(test_idx),  batch_size=batch_size, shuffle=False, collate_fn=collate_fn)

  # 5. Модель с Conv1d
  class CNNClassifier(nn.Module):
      def __init__(self, vocab_size, emb_dim, num_filters, kernel_size, num_classes, pad_idx):
          super().__init__()
          self.embedding = nn.Embedding(vocab_size, emb_dim, padding_idx=pad_idx)
          self.conv = nn.Conv1d(in_channels=emb_dim, out_channels=num_filters, kernel_size=kernel_size, padding=kernel_size//2)
          self.pool = nn.AdaptiveMaxPool1d(1)
          self.fc = nn.Linear(num_filters, num_classes)

      def forward(self, x, lengths=None):
          # x: [B,L]
          emb = self.embedding(x)        # [B,L,E]
          emb = emb.permute(0,2,1)       # [B,E,L]
          c = torch.relu(self.conv(emb)) # [B,F,L]
          p = self.pool(c).squeeze(2)    # [B,F]
          logits = self.fc(p)            # [B,C]
          return logits

  # 6. Инициализация и обучение
  model = CNNClassifier(vocab_size, emb_dim=64, num_filters=128, kernel_size=5, num_classes=len(seasons), pad_idx=vocab['<PAD>']).to(device)
  criterion = nn.CrossEntropyLoss()
  optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)

  epochs=10; train_losses=[]; val_losses=[]
  for epoch in range(1,epochs+1):
      model.train(); total=0
      for x,lengths,y in train_loader:
          x,y = x.to(device), y.to(device)
          optimizer.zero_grad()
          logits = model(x,lengths)
          loss = criterion(logits,y)
          loss.backward(); optimizer.step()
          total += loss.item()*x.size(0)
      train_losses.append(total/len(train_idx))
      # валидация
      model.eval(); total_v=0; preds, trues = [], []
      with torch.no_grad():
          for x,lengths,y in test_loader:
              x,y = x.to(device), y.to(device)
              logits = model(x,lengths)
              total_v += criterion(logits,y).item()*x.size(0)
              pred = torch.argmax(logits,dim=1)
              preds.extend(pred.cpu().tolist()); trues.extend(y.cpu().tolist())
      val_losses.append(total_v/len(test_idx))
      print(f"Epoch {epoch}: train_loss={train_losses[-1]:.4f}, val_loss={val_losses[-1]:.4f}")

  # 7. Кривые обучения и отчет
  plt.figure(); plt.plot(train_losses,label='Train'); plt.plot(val_losses,label='Val'); plt.xlabel('Epoch'); plt.ylabel('Loss'); plt.legend(); plt.show()
  print(classification_report(trues,preds,target_names=seasons))
  print(f"Accuracy: {accuracy_score(trues,preds):.4f}")

  # 8. Пример предсказания
  idx = test_idx[0]
  seq = tokenized[idx]
  input_ids = torch.tensor([[vocab.get(w,vocab['<UNK>']) for w in seq]],dtype=torch.long).to(device)
  pred = idx2season[torch.argmax(model(input_ids),dim=1).item()]
  print(f"Text: {' '.join(seq)}\nTrue: {df.loc[idx,'Season']}, Pred: {pred}")

def corona_cls_tf_idf():
  """# tags: corona.csv | Использовать tf-idf для NLP задачи

  Решить задачу классификации с применением tf-idf. Использовать датасет corona.csv.
  """

  import pandas as pd
  import numpy as np
  import torch
  import torch.nn as nn
  from torch.utils.data import Dataset, DataLoader
  from sklearn.feature_extraction.text import TfidfVectorizer
  from sklearn.model_selection import train_test_split
  from sklearn.preprocessing import LabelEncoder
  from sklearn.metrics import classification_report, accuracy_score
  import matplotlib.pyplot as plt

  # 1. Загрузка и очистка данных
  df = pd.read_csv('/content/unzipped_07_exam/07_exam/nlp/corona.csv')
  # Оставляем только строки с валидными метками
  valid_labels = ['Positive', 'Neutral', 'Negative']
  df = df[['OriginalTweet', 'Sentiment']].dropna()
  df = df[df['Sentiment'].isin(valid_labels)].reset_index(drop=True)
  print(f"Всего твитов после фильтрации: {len(df)}")

  # 2. Преобразование меток
  le = LabelEncoder()
  y = le.fit_transform(df['Sentiment'])  # ['Negative','Neutral','Positive'] -> [0,1,2]
  texts = df['OriginalTweet'].astype(str)

  # 3. Train/Test split
  X_train_texts, X_test_texts, y_train, y_test = train_test_split(
      texts, y, test_size=0.2, random_state=42, stratify=y
  )

  # 4. TF-IDF векторизация
  vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1,2), stop_words='english')
  X_train = vectorizer.fit_transform(X_train_texts)
  X_test  = vectorizer.transform(X_test_texts)

  # 5. Dataset для PyTorch
  tfX_train = torch.tensor(X_train.toarray(), dtype=torch.float32)
  tfX_test  = torch.tensor(X_test.toarray(), dtype=torch.float32)
  tfy_train = torch.tensor(y_train, dtype=torch.long)
  tfy_test  = torch.tensor(y_test, dtype=torch.long)

  class TfidfDataset(Dataset):
      def __init__(self, X, y):
          self.X = X
          self.y = y
      def __len__(self): return self.X.size(0)
      def __getitem__(self, idx): return self.X[idx], self.y[idx]

  train_ds = TfidfDataset(tfX_train, tfy_train)
  test_ds  = TfidfDataset(tfX_test,  tfy_test)
  train_loader = DataLoader(train_ds, batch_size=64, shuffle=True)
  test_loader  = DataLoader(test_ds,  batch_size=64)

  device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

  # 6. Модель Feedforward Neural Network
  class FFNNClassifier(nn.Module):
      def __init__(self, input_dim, hidden_dim, num_classes):
          super().__init__()
          self.net = nn.Sequential(
              nn.Linear(input_dim, hidden_dim),
              nn.ReLU(),
              nn.Dropout(0.3),
              nn.Linear(hidden_dim, num_classes)
          )
      def forward(self, x):
          return self.net(x)

  input_dim = tfX_train.size(1)
  hidden_dim = 256
  num_classes = len(le.classes_)
  model = FFNNClassifier(input_dim, hidden_dim, num_classes).to(device)
  criterion = nn.CrossEntropyLoss()
  optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)

  # 7. Training loop
  num_epochs = 10
  train_losses, val_losses = [], []
  for epoch in range(num_epochs):
      model.train(); total_loss = 0
      for X_batch, y_batch in train_loader:
          X_batch, y_batch = X_batch.to(device), y_batch.to(device)
          optimizer.zero_grad()
          logits = model(X_batch)
          loss = criterion(logits, y_batch)
          loss.backward(); optimizer.step()
          total_loss += loss.item() * X_batch.size(0)
      train_losses.append(total_loss / len(train_ds))

      # validation
      model.eval(); val_loss = 0
      all_preds, all_labels = [], []
      with torch.no_grad():
          for X_batch, y_batch in test_loader:
              X_batch, y_batch = X_batch.to(device), y_batch.to(device)
              logits = model(X_batch)
              val_loss += criterion(logits, y_batch).item() * X_batch.size(0)
              preds = torch.argmax(logits, dim=1)
              all_preds.extend(preds.cpu().tolist()); all_labels.extend(y_batch.cpu().tolist())
      val_losses.append(val_loss / len(test_ds))
      print(f"Epoch {epoch+1}: train_loss={train_losses[-1]:.4f}, val_loss={val_losses[-1]:.4f}")

  # 8. Learning curves
  plt.figure(); plt.plot(train_losses, label='Train'); plt.plot(val_losses, label='Val')
  plt.xlabel('Epoch'); plt.ylabel('Loss'); plt.legend(); plt.show()

  # 9. Evaluation
  print("Classification Report:")
  print(classification_report(all_labels, all_preds, target_names=le.classes_))
  print(f"Accuracy: {accuracy_score(all_labels, all_preds):.4f}")

  # 10. Example Predictions
  for i in range(3):
      text = X_test_texts.iloc[i]
      true_label = le.inverse_transform([y_test[i]])[0]
      x_tensor = tfX_test[i].unsqueeze(0).to(device)
      pred = le.inverse_transform([torch.argmax(model(x_tensor), dim=1).item()])[0]
      print(f"Tweet: {text}\nTrue: {true_label}, Pred: {pred}\n")

def corona_embed_cls_word2vec():
  """#tags: corona.csv | word2vec | classfication

  Обучить word2vec для создания эмбеддингов и провести классиффикацию на датасете corona.csv
  """

  import pandas as pd
  import numpy as np
  import torch
  import torch.nn as nn
  from torch.utils.data import Dataset, DataLoader
  from sklearn.model_selection import train_test_split
  from sklearn.preprocessing import LabelEncoder
  from sklearn.metrics import classification_report, accuracy_score
  import nltk
  from nltk.tokenize import word_tokenize
  from gensim.models import Word2Vec
  import matplotlib.pyplot as plt

  # 1. Загрузка и очистка данных
  df = pd.read_csv('/content/unzipped_07_exam/07_exam/nlp/corona.csv')
  valid_labels = ['Positive', 'Neutral', 'Negative']
  df = df[['OriginalTweet', 'Sentiment']].dropna()
  df = df[df['Sentiment'].isin(valid_labels)].reset_index(drop=True)
  print(f"Всего твитов: {len(df)}")
  texts = df['OriginalTweet'].astype(str).tolist()

  # 2. Преобразование меток
  y = LabelEncoder().fit_transform(df['Sentiment'])  # Negative=0, Neutral=1, Positive=2
  le = LabelEncoder().fit(df['Sentiment'])

  # 3. Токенизация
  nltk.download('punkt_tab')
  tokenized = [word_tokenize(text.lower()) for text in texts]

  # 4. Обучение Word2Vec эмбеддингов
  w2v_model = Word2Vec(sentences=tokenized, vector_size=100, window=5, min_count=2, workers=4)
  vocab = {word: idx+2 for idx, word in enumerate(w2v_model.wv.index_to_key)}
  vocab['<PAD>'] = 0
  vocab['<UNK>'] = 1

  # 5. Создание Embedding матрицы
  embedding_dim = w2v_model.vector_size
  num_tokens = len(vocab)
  embedding_matrix = np.zeros((num_tokens, embedding_dim))
  for word, idx in vocab.items():
      if word in w2v_model.wv:
          embedding_matrix[idx] = w2v_model.wv[word]
      else:
          embedding_matrix[idx] = np.random.normal(scale=0.6, size=(embedding_dim,))

  # 6. Подготовка данных: кодирование, паддинг и разбиение через индексы
  max_len = 50
  encoded = [[vocab.get(t, vocab['<UNK>']) for t in seq][:max_len] + [vocab['<PAD>']]*(max_len - min(len(seq), max_len))
            for seq in tokenized]
  indices = list(range(len(encoded)))
  train_idx, test_idx = train_test_split(indices, test_size=0.2, random_state=42, stratify=y)
  X_train = [encoded[i] for i in train_idx]
  X_test  = [encoded[i] for i in test_idx]
  texts_test = [texts[i] for i in test_idx]
  y_train = [y[i] for i in train_idx]
  y_test  = [y[i] for i in test_idx]

  class CoronaDataset(Dataset):
      def __init__(self, X, y):
          self.X = torch.tensor(X, dtype=torch.long)
          self.y = torch.tensor(y, dtype=torch.long)
      def __len__(self): return len(self.X)
      def __getitem__(self, idx): return self.X[idx], self.y[idx]

  train_ds = CoronaDataset(X_train, y_train)
  test_ds  = CoronaDataset(X_test,  y_test)
  train_loader = DataLoader(train_ds, batch_size=64, shuffle=True)
  test_loader  = DataLoader(test_ds,  batch_size=64)

  device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

  # 7. Модель на основе pretrained эмбеддингов + среднее по словам + FFNN
  class W2VClassifier(nn.Module):
      def __init__(self, embedding_matrix, hidden_dim, num_classes):
          super().__init__()
          num_embeddings, emb_dim = embedding_matrix.shape
          self.embedding = nn.Embedding(num_embeddings, emb_dim, padding_idx=0)
          self.embedding.weight = nn.Parameter(torch.tensor(embedding_matrix, dtype=torch.float32))
          self.embedding.weight.requires_grad = False
          self.fc = nn.Sequential(
              nn.Linear(emb_dim, hidden_dim),
              nn.ReLU(),
              nn.Dropout(0.3),
              nn.Linear(hidden_dim, num_classes)
          )

      def forward(self, x):
          emb = self.embedding(x)      # [B, L, E]
          avg = emb.mean(dim=1)        # [B, E]
          return self.fc(avg)

  model = W2VClassifier(embedding_matrix, hidden_dim=128, num_classes=len(valid_labels)).to(device)
  criterion = nn.CrossEntropyLoss()
  optimizer = torch.optim.Adam(filter(lambda p: p.requires_grad, model.parameters()), lr=1e-3)

  # 8. Обучение
  num_epochs = 10
  train_losses, val_losses = [], []
  for epoch in range(1, num_epochs+1):
      model.train(); total_loss = 0
      for X_batch, y_batch in train_loader:
          X_batch, y_batch = X_batch.to(device), y_batch.to(device)
          optimizer.zero_grad()
          logits = model(X_batch)
          loss = criterion(logits, y_batch)
          loss.backward(); optimizer.step()
          total_loss += loss.item() * X_batch.size(0)
      train_losses.append(total_loss/len(train_ds))

      model.eval(); val_loss = 0; preds, trues = [], []
      with torch.no_grad():
          for X_batch, y_batch in test_loader:
              X_batch, y_batch = X_batch.to(device), y_batch.to(device)
              logits = model(X_batch)
              val_loss += criterion(logits, y_batch).item() * X_batch.size(0)
              pred = torch.argmax(logits, dim=1)
              preds.extend(pred.cpu().tolist()); trues.extend(y_batch.cpu().tolist())
      val_losses.append(val_loss/len(test_ds))
      print(f"Epoch {epoch}: train_loss={train_losses[-1]:.4f}, val_loss={val_losses[-1]:.4f}")

  # 9. Кривые обучения
  plt.figure(); plt.plot(train_losses, label='Train'); plt.plot(val_losses, label='Val')
  plt.xlabel('Epoch'); plt.ylabel('Loss'); plt.legend(); plt.show()

  # 10. Оценка и примеры
  print(classification_report(trues, preds, target_names=valid_labels))
  print(f"Accuracy: {accuracy_score(trues, preds):.4f}")

  # 11. Пример предсказаний
  for i in range(3):
      text = texts_test[i]
      true_label = le.inverse_transform([y_test[i]])[0]
      seq_tensor = torch.tensor([X_test[i]], dtype=torch.long).to(device)
      with torch.no_grad():
          pred_label = le.inverse_transform([torch.argmax(model(seq_tensor), dim=1).item()])[0]
      print(f"Tweet: {text}\nTrue: {true_label}, Pred: {pred_label}\n")

def sents_pairs_jaccard_index_embedding_linear():
  """# tags: sents_pairs.pt, sents_pairs_itos.json, jaccard.pt | посчитать коеф жакара| nn.Embedding | nn.Linear

  Полносвязная NN посчитать коеффициент жакара на основе эмбедингов. Использовать файлы: sents_pairs.pt, sents_pairs_itos.json. Результат записать в файл jaccard.pt.
  Что решал чат гпт, по его мнению:

  Реализовать вычисление бинарифицированного коэффициента Жаккара для пар предложений, используя one-hot эмбеддинги через nn.Embedding и суммирующий слой nn.Linear, и сохранить результат в jaccard.pt, а также вывести его в консоль.
  """

  import torch
  import torch.nn as nn
  import json

  # 1. Загрузка данных
  sents_pairs = torch.load('/content/unzipped_07_exam/07_exam/sents/sents_pairs.pt')  # tensor [N, 2, L]

  # 2. Параметры
  vocab_size = int(sents_pairs.max().item()) + 1

  # 3. One-hot эмбеддинг через Identity в Embedding
  embed = nn.Embedding(vocab_size, vocab_size, padding_idx=0)
  with torch.no_grad():
      embed.weight.copy_(torch.eye(vocab_size))
      embed.weight[0].zero_()

  # 4. Линейный слой для подсчёта сумм
  sum_lin = nn.Linear(vocab_size, 1, bias=False)
  with torch.no_grad():
      sum_lin.weight.copy_(torch.ones(1, vocab_size))

  # 5. Вычисление Jaccard
  jaccard_vals = []
  for sentA, sentB in sents_pairs:
      # one-hot sums по длине
      A_oh = embed(sentA)  # [L, V]
      B_oh = embed(sentB)
      A_pres = (A_oh.sum(dim=0) > 0).float()  # [V]
      B_pres = (B_oh.sum(dim=0) > 0).float()
      inter_cnt = sum_lin((A_pres * B_pres).unsqueeze(0))
      union_cnt = sum_lin(((A_pres + B_pres) > 0).float().unsqueeze(0))
      j = (inter_cnt / (union_cnt + 1e-8)).item()
      jaccard_vals.append(j)

  # 6. Формируем тензор: 1 если j>0, иначе 0
  jaccard_tensor = torch.tensor([1 if v > 0 else 0 for v in jaccard_vals], dtype=torch.long)

  # 7. Сохранение
  torch.save(jaccard_tensor, '/content/unzipped_07_exam/07_exam/sents/jaccard.pt')

  # 8. Вывод результатов
  print("First 20 Jaccard coefficients (binarized):", jaccard_tensor[:20])
  print(f"Overall mean Jaccard (binarized): {jaccard_tensor.float().mean().item():.4f}")

def seek(message):
  """Please install OpenAI SDK first: pip3 install openai"""
  from openai import OpenAI

  client = OpenAI(api_key="sk-6fb5fbe077664909bb292ec646d978e7", base_url="https://api.deepseek.com")

  response = client.chat.completions.create(
      model="deepseek-chat",
      messages=[
          {"role": "system", "content": "You are a helpful assistant"},
          {"role": "user", "content": message},
      ],
      stream=False
  )

  print(response.choices[0].message.content)