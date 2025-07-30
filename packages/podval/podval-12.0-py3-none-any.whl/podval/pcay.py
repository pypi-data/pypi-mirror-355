import pyperclip as pc

def bank():
    """
    Набор данных: classification/bank.csv. Используя библиотеку PyTorch, решите задачу классификации (столбец deposit). Разделите набор данных на обучающее и тестовое множество. Выполните предобработку данных (корректно обработайте случаи категориальных и нечисловых столбцов, при наличии). Отобразите график значений функций потерь на обучающем множестве по эпохам. Отобразите confussion matrix и classification report, рассчитанные на основе тестового множества.

Модифицируйте функцию потерь с учетом несбалансированности классов и продемонстрируйте, как это влияет на результаты на тестовом множестве.


import pandas as pd
import numpy as np

import torch as th
from torch import nn, optim
from torch.utils.data import Dataset, DataLoader, TensorDataset

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder, LabelEncoder
from sklearn.compose import ColumnTransformer
from torch.utils.data import TensorDataset, DataLoader, WeightedRandomSampler, random_split
import torchmetrics as M
from sklearn.metrics import confusion_matrix, classification_report
import seaborn as sns
from sklearn.utils.class_weight import compute_class_weight

import matplotlib.pyplot as plt



data = pd.read_csv("for_exam/datasets/classification/bank.csv")

X = data.drop(columns=["deposit"])
y = data["deposit"]

categorical_cols = ['job', 'marital', 'education', 'default', 'housing',
       'loan', 'contact', 'day', 'month', 'campaign',
       'previous', 'poutcome']

numerical_cols = ['age', 'balance', 'duration', 'pdays']

preprocessor = ColumnTransformer(
    transformers=[
        ('num', StandardScaler(), numerical_cols),
        ('cat', OneHotEncoder(), categorical_cols)
    ])

l_e = LabelEncoder()

X_processed = th.FloatTensor(preprocessor.fit_transform(X).toarray())
y_enc = l_e.fit_transform(y.values)
y_tensor = th.FloatTensor(y_enc)

dataset = TensorDataset(X_processed, y_tensor)

generator = th.Generator().manual_seed(0)
train_dataset, test_dataset = random_split(dataset, [0.8, 0.2], generator=generator)

train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False)


class Model_1(nn.Module):
    def __init__(self, n_inputs: int, n_classes: int) -> None:
        super().__init__()
        self.layer_1 = nn.Linear(n_inputs, 16)
        self.layer_2 = nn.Linear(16, n_classes)
        self.relu = nn.ReLU()

    def forward(self, X: th.Tensor) -> th.Tensor:
        out = self.layer_1(X)
        out = self.relu(out)
        out = self.layer_2(out)
        return out
        
        
def train_func(model,
               loader,
               loss_func,
               optimizer,
               metric_dict,
               mean_metric=M.MeanMetric(),
               n_epochs: int = 100,
               print_every: int = 1,
               test_loader=None,
              ):
    
    out_dict = {}
    epoch_losses = []
    predictions = []
    metric_scores = {name: [] for name in metric_dict.keys()}
    test_metric_scores = {name: [] for name in metric_dict.keys()} if test_loader else None
    test_losses = [] if test_loader else None
    
    model.train()
    for epoch in range(n_epochs):
        mean_metric.reset()
        
        for name, metric in metric_dict.items():
            metric.reset()

        for X_batch, y_batch in loader:
            y_batch = y_batch.float()
            y_pred = model(X_batch)
            
            if isinstance(loss_func, nn.BCEWithLogitsLoss):
                loss = loss_func(y_pred.flatten(), y_batch)
                mean_metric.update(loss)
                y_pred_probs = th.sigmoid(y_pred)
                y_pred_classes = (y_pred_probs > 0.5).float()
                
                for name, metric in metric_dict.items():
                    metric.update(y_pred_classes.flatten(), y_batch)
            else:
                loss = loss_func(y_pred, y_batch.long())
                mean_metric.update(loss)
                y_pred_classes = y_pred.argmax(dim=1)

                for name, metric in metric_dict.items():
                    metric.update(y_pred_classes, y_batch.long())
            
            loss.backward()
            
            optimizer.step()
            optimizer.zero_grad()

        epoch_loss = mean_metric.compute()
        epoch_losses.append(epoch_loss.item())
        
        for name, metric in metric_dict.items():
            metric_score = metric.compute().item()
            metric_scores[name].append(metric_score)
        
        if test_loader:
            test_results, test_loss,_ ,_ = eval_metrics(model, test_loader, metric_dict, loss_func)
            test_losses.append(test_loss)
            for name, score in test_results.items():
                test_metric_scores[name].append(score)

        if print_every != 0 and (epoch % print_every == 0 or epoch == n_epochs - 1):
            metrics_str = ", ".join([f"{name}: {metric_scores[name][-1]:.4f}" for name in metric_dict.keys()])
            if test_loader:
                test_metrics_str = ", ".join([f"test_{name}: {test_results[name]:.4f}" for name in test_results.keys()])
                print(f"Epoch {epoch + 1}, Loss: {epoch_loss.item():.4f}, {metrics_str}, \n"
                      f"Test Loss: {test_loss:.4f}, {test_metrics_str}")
            else:
                print(f"Epoch {epoch + 1}, Loss: {epoch_loss.item():.4f}, {metrics_str}")
    
    out_dict['epoch_losses'] = epoch_losses
    out_dict['metric_scores'] = metric_scores
    if test_loader:
        out_dict['test_metric_scores'] = test_metric_scores
        out_dict['test_losses'] = test_losses
    return out_dict, model


@th.no_grad()
def eval_metrics(model, loader, metric_dict, loss_func):
    model.eval()
    results = {}
    mean_metric = M.MeanMetric()
    mean_metric.reset()

    for name, metric in metric_dict.items():
        metric.reset()

    all_preds = []
    all_targets = []

    for X_batch, y_batch in loader:
        y_batch = y_batch.float()
        y_pred = model(X_batch)
        
        if isinstance(loss_func, nn.BCEWithLogitsLoss):
            loss = loss_func(y_pred.flatten(), y_batch)
            y_pred_probs = th.sigmoid(y_pred).squeeze()
            y_pred_classes = (y_pred_probs > 0.5).float()
        else:
            loss = loss_func(y_pred, y_batch.long())
            y_pred_classes = y_pred.argmax(dim=1)
        
        mean_metric.update(loss)
        
        all_preds.append(y_pred_classes)
        all_targets.append(y_batch)

        for name, metric in metric_dict.items():
            metric.update(y_pred_classes, y_batch.long())
    
    for name, metric in metric_dict.items():
        results[name] = metric.compute().item()
    
    loss_value = mean_metric.compute().item()
    return results, loss_value, th.cat(all_preds), th.cat(all_targets)
    
model = Model_1(X_processed.shape[1], 2)

loss_func = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)
epochs = 10

metric_dict = {
    'Accuracy': M.Accuracy(task="binary"),
    'Precision': M.Precision(task="binary"),
    'Recall': M.Recall(task="binary"),
    'F1': M.F1Score(task="binary")
}

model_train = train_func(model=model,
                                loader=train_loader,
                                n_epochs=epochs,
                                loss_func=loss_func,
                                optimizer=optimizer,
                                metric_dict=metric_dict,
                                print_every=5,
                                test_loader=test_loader,
                               )
                               
epoch_losses = model_train[0]['epoch_losses']

plt.figure(figsize=(8, 5))
plt.plot(range(1, epochs + 1), epoch_losses, label="Loss")
plt.title("Значение функции потерь")
plt.xlabel("Эпоха")
plt.ylabel("Loss")
plt.legend()
plt.show()

test_results, test_loss, y_pred, y_true = eval_metrics(model_train[1], test_loader, metric_dict, loss_func)

y_pred = y_pred.numpy()
y_true = y_true.numpy()

cm = confusion_matrix(y_true, y_pred)

plt.figure(figsize=(4, 2))
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=["Class 0", "Class 1"], yticklabels=["Class 0", "Class 1"])
plt.xlabel("Predicted")
plt.ylabel("Actual")
plt.title("Confusion Matrix")
plt.show()

print("Classification Report:")
print(classification_report(y_true, y_pred, target_names=["Class 0", "Class 1"]))


1 Модифицируйте функцию потерь с учетом несбалансированности классов и продемонстрируйте, как это влияет на результаты на тестовом множестве

class_weights = compute_class_weight(class_weight='balanced', classes=np.array([0, 1]), y=y_enc)
pos_weight = class_weights[1] / class_weights[0]
pos_weight

model_2 = Model_1(X_processed.shape[1], 1)
loss_func = nn.BCEWithLogitsLoss(pos_weight=th.tensor(pos_weight, dtype=th.float32))
optimizer = optim.Adam(model_2.parameters(), lr=0.001)
epochs = 10

model_train_weights = train_func(model=model_2,
                                loader=train_loader,
                                n_epochs=epochs,
                                loss_func=loss_func,
                                optimizer=optimizer,
                                metric_dict=metric_dict,
                                print_every=5,
                                test_loader=test_loader,
                               )
                               
test_results_w, test_loss, y_pred, y_true = eval_metrics(model_train_weights[1], test_loader, metric_dict, loss_func)

y_pred = y_pred.numpy()
y_true = y_true.numpy()

cm = confusion_matrix(y_true, y_pred)

plt.figure(figsize=(4, 2))
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=["Class 0", "Class 1"], yticklabels=["Class 0", "Class 1"])
plt.xlabel("Predicted")
plt.ylabel("Actual")
plt.title("Confusion Matrix")
plt.show()

print("Classification Report:")
print(classification_report(y_true, y_pred, target_names=["Class 0", "Class 1"]))    


plt.plot(model_train_weights[0]["test_metric_scores"]["F1"], label="Weighted Model (F1)")
plt.plot(model_train[0]["test_metric_scores"]["F1"], label="Baseline Model (F1)")

plt.xlabel("Epochs")
plt.ylabel("F1 Score")
plt.title("F1 Score Over Epochs")
plt.legend()
plt.show()


2. Добавьте в модель слои dropout и графически продемонстрируйте, как это влияет на процесс обучения и результаты на тестовом множестве.
class Model_drop(nn.Module):
    def __init__(self, n_inputs: int, n_classes: int) -> None:
        super().__init__()
        self.layer_1 = nn.Linear(n_inputs, 16)
        self.layer_2 = nn.Linear(16, n_classes)
        self.relu = nn.ReLU()
        self.drop = nn.Dropout(p=0.5)

    def forward(self, X: th.Tensor) -> th.Tensor:
        out = self.layer_1(X)
        out = self.relu(out)
        out = self.drop(out)
        out = self.layer_2(out)
        return out
        
model_dr = Model_drop(X_processed.shape[1], 2)

loss_func = nn.CrossEntropyLoss()
optimizer = optim.Adam(model_dr.parameters(), lr=0.001)
epochs = 10

model_train_drop = train_func(model=model_dr,
                                loader=train_loader,
                                n_epochs=epochs,
                                loss_func=loss_func,
                                optimizer=optimizer,
                                metric_dict=metric_dict,
                                print_every=5,
                                test_loader=test_loader,
                               )
                               
plt.plot(model_train_drop[0]["epoch_losses"], label="Model with Dropout (F1)")
plt.plot(model_train[0]["epoch_losses"], label="Baseline Model (F1)")

plt.xlabel("Epochs")
plt.ylabel("Loss")
plt.legend()
plt.show()

_, _, y_pred, y_true = eval_metrics(model_train_drop[1], test_loader, metric_dict, loss_func)

y_pred = y_pred.numpy()
y_true = y_true.numpy()

cm = confusion_matrix(y_true, y_pred)

plt.figure(figsize=(4, 2))
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=["Class 0", "Class 1"], yticklabels=["Class 0", "Class 1"])
plt.xlabel("Predicted")
plt.ylabel("Actual")
plt.title("Confusion Matrix")
plt.show()

print("Classification Report:")
print(classification_report(y_true, y_pred, target_names=["Class 0", "Class 1"]))

plt.plot(model_train_drop[0]["test_metric_scores"]["F1"], label="Model with Dropout (F1)")
plt.plot(model_train[0]["test_metric_scores"]["F1"], label="Baseline Model (F1)")

plt.xlabel("Epochs")
plt.ylabel("F1 Score")
plt.title("F1 Score Over Epochs")
plt.legend()
plt.show()


3. Сравните несколько различных оптимизаторов и графически продемонстрируйте, как выбор оптимизатора влияет на процесс обучения и результаты на тестовом множестве.
optimizers = {
    "Adam": lambda params: optim.Adam(params, lr=0.001),
    "SGD": lambda params: optim.SGD(params, lr=0.01, momentum=0.9),
    "RMSprop": lambda params: optim.RMSprop(params, lr=0.001)
}

epochs=10
results = {}

for name, optimizer_fn in optimizers.items():
    print(f"Training {name} optimizer")
    model = Model_1(X_processed.shape[1], 2)
    optimizer = optimizer_fn(model.parameters())
    
    train_results, _ = train_func(
        model=model,
        loader=train_loader,
        n_epochs=epochs,
        loss_func=loss_func,
        optimizer=optimizer,
        metric_dict=metric_dict,
        print_every=epochs // 2,
        test_loader=test_loader,
    )
    results[name] = train_results

plt.figure(figsize=(12, 6))

plt.subplot(1, 2, 1)
for name, res in results.items():
    plt.plot(res["epoch_losses"], label=f"{name} Loss")
plt.xlabel("Epochs")
plt.ylabel("Loss")
plt.title("Train Loss)
plt.legend()

plt.subplot(1, 2, 2)
for name, res in results.items():
    plt.plot(res["test_metric_scores"]["F1"], label=f"{name} F1 Score")
plt.xlabel("Epochs")
plt.ylabel("F1 Score")
plt.title("Test F1 Score")
plt.legend()

plt.tight_layout()
plt.show()

    """
    
    
    text='''
import pandas as pd
import numpy as np

import torch as th
from torch import nn, optim
from torch.utils.data import Dataset, DataLoader, TensorDataset

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder, LabelEncoder
from sklearn.compose import ColumnTransformer
from torch.utils.data import TensorDataset, DataLoader, WeightedRandomSampler, random_split
import torchmetrics as M
from sklearn.metrics import confusion_matrix, classification_report
import seaborn as sns
from sklearn.utils.class_weight import compute_class_weight

import matplotlib.pyplot as plt



data = pd.read_csv("for_exam/datasets/classification/bank.csv")

X = data.drop(columns=["deposit"])
y = data["deposit"]

categorical_cols = ['job', 'marital', 'education', 'default', 'housing',
       'loan', 'contact', 'day', 'month', 'campaign',
       'previous', 'poutcome']

numerical_cols = ['age', 'balance', 'duration', 'pdays']

preprocessor = ColumnTransformer(
    transformers=[
        ('num', StandardScaler(), numerical_cols),
        ('cat', OneHotEncoder(), categorical_cols)
    ])

l_e = LabelEncoder()

X_processed = th.FloatTensor(preprocessor.fit_transform(X).toarray())
y_enc = l_e.fit_transform(y.values)
y_tensor = th.FloatTensor(y_enc)

dataset = TensorDataset(X_processed, y_tensor)

generator = th.Generator().manual_seed(0)
train_dataset, test_dataset = random_split(dataset, [0.8, 0.2], generator=generator)

train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False)


class Model_1(nn.Module):
    def __init__(self, n_inputs: int, n_classes: int) -> None:
        super().__init__()
        self.layer_1 = nn.Linear(n_inputs, 16)
        self.layer_2 = nn.Linear(16, n_classes)
        self.relu = nn.ReLU()

    def forward(self, X: th.Tensor) -> th.Tensor:
        out = self.layer_1(X)
        out = self.relu(out)
        out = self.layer_2(out)
        return out
        
        
def train_func(model,
               loader,
               loss_func,
               optimizer,
               metric_dict,
               mean_metric=M.MeanMetric(),
               n_epochs: int = 100,
               print_every: int = 1,
               test_loader=None,
              ):
    
    out_dict = {}
    epoch_losses = []
    predictions = []
    metric_scores = {name: [] for name in metric_dict.keys()}
    test_metric_scores = {name: [] for name in metric_dict.keys()} if test_loader else None
    test_losses = [] if test_loader else None
    
    model.train()
    for epoch in range(n_epochs):
        mean_metric.reset()
        
        for name, metric in metric_dict.items():
            metric.reset()

        for X_batch, y_batch in loader:
            y_batch = y_batch.float()
            y_pred = model(X_batch)
            
            if isinstance(loss_func, nn.BCEWithLogitsLoss):
                loss = loss_func(y_pred.flatten(), y_batch)
                mean_metric.update(loss)
                y_pred_probs = th.sigmoid(y_pred)
                y_pred_classes = (y_pred_probs > 0.5).float()
                
                for name, metric in metric_dict.items():
                    metric.update(y_pred_classes.flatten(), y_batch)
            else:
                loss = loss_func(y_pred, y_batch.long())
                mean_metric.update(loss)
                y_pred_classes = y_pred.argmax(dim=1)

                for name, metric in metric_dict.items():
                    metric.update(y_pred_classes, y_batch.long())
            
            loss.backward()
            
            optimizer.step()
            optimizer.zero_grad()

        epoch_loss = mean_metric.compute()
        epoch_losses.append(epoch_loss.item())
        
        for name, metric in metric_dict.items():
            metric_score = metric.compute().item()
            metric_scores[name].append(metric_score)
        
        if test_loader:
            test_results, test_loss,_ ,_ = eval_metrics(model, test_loader, metric_dict, loss_func)
            test_losses.append(test_loss)
            for name, score in test_results.items():
                test_metric_scores[name].append(score)

        if print_every != 0 and (epoch % print_every == 0 or epoch == n_epochs - 1):
            metrics_str = ", ".join([f"{name}: {metric_scores[name][-1]:.4f}" for name in metric_dict.keys()])
            if test_loader:
                test_metrics_str = ", ".join([f"test_{name}: {test_results[name]:.4f}" for name in test_results.keys()])
                print(f"Epoch {epoch + 1}, Loss: {epoch_loss.item():.4f}, {metrics_str}, \n"
                      f"Test Loss: {test_loss:.4f}, {test_metrics_str}")
            else:
                print(f"Epoch {epoch + 1}, Loss: {epoch_loss.item():.4f}, {metrics_str}")
    
    out_dict['epoch_losses'] = epoch_losses
    out_dict['metric_scores'] = metric_scores
    if test_loader:
        out_dict['test_metric_scores'] = test_metric_scores
        out_dict['test_losses'] = test_losses
    return out_dict, model


@th.no_grad()
def eval_metrics(model, loader, metric_dict, loss_func):
    model.eval()
    results = {}
    mean_metric = M.MeanMetric()
    mean_metric.reset()

    for name, metric in metric_dict.items():
        metric.reset()

    all_preds = []
    all_targets = []

    for X_batch, y_batch in loader:
        y_batch = y_batch.float()
        y_pred = model(X_batch)
        
        if isinstance(loss_func, nn.BCEWithLogitsLoss):
            loss = loss_func(y_pred.flatten(), y_batch)
            y_pred_probs = th.sigmoid(y_pred).squeeze()
            y_pred_classes = (y_pred_probs > 0.5).float()
        else:
            loss = loss_func(y_pred, y_batch.long())
            y_pred_classes = y_pred.argmax(dim=1)
        
        mean_metric.update(loss)
        
        all_preds.append(y_pred_classes)
        all_targets.append(y_batch)

        for name, metric in metric_dict.items():
            metric.update(y_pred_classes, y_batch.long())
    
    for name, metric in metric_dict.items():
        results[name] = metric.compute().item()
    
    loss_value = mean_metric.compute().item()
    return results, loss_value, th.cat(all_preds), th.cat(all_targets)
    
model = Model_1(X_processed.shape[1], 2)

loss_func = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)
epochs = 10

metric_dict = {
    'Accuracy': M.Accuracy(task="binary"),
    'Precision': M.Precision(task="binary"),
    'Recall': M.Recall(task="binary"),
    'F1': M.F1Score(task="binary")
}

model_train = train_func(model=model,
                                loader=train_loader,
                                n_epochs=epochs,
                                loss_func=loss_func,
                                optimizer=optimizer,
                                metric_dict=metric_dict,
                                print_every=5,
                                test_loader=test_loader,
                               )
                               
epoch_losses = model_train[0]['epoch_losses']

plt.figure(figsize=(8, 5))
plt.plot(range(1, epochs + 1), epoch_losses, label="Loss")
plt.title("Значение функции потерь")
plt.xlabel("Эпоха")
plt.ylabel("Loss")
plt.legend()
plt.show()

test_results, test_loss, y_pred, y_true = eval_metrics(model_train[1], test_loader, metric_dict, loss_func)

y_pred = y_pred.numpy()
y_true = y_true.numpy()

cm = confusion_matrix(y_true, y_pred)

plt.figure(figsize=(4, 2))
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=["Class 0", "Class 1"], yticklabels=["Class 0", "Class 1"])
plt.xlabel("Predicted")
plt.ylabel("Actual")
plt.title("Confusion Matrix")
plt.show()

print("Classification Report:")
print(classification_report(y_true, y_pred, target_names=["Class 0", "Class 1"]))


1 Модифицируйте функцию потерь с учетом несбалансированности классов и продемонстрируйте, как это влияет на результаты на тестовом множестве

class_weights = compute_class_weight(class_weight='balanced', classes=np.array([0, 1]), y=y_enc)
pos_weight = class_weights[1] / class_weights[0]
pos_weight

model_2 = Model_1(X_processed.shape[1], 1)
loss_func = nn.BCEWithLogitsLoss(pos_weight=th.tensor(pos_weight, dtype=th.float32))
optimizer = optim.Adam(model_2.parameters(), lr=0.001)
epochs = 10

model_train_weights = train_func(model=model_2,
                                loader=train_loader,
                                n_epochs=epochs,
                                loss_func=loss_func,
                                optimizer=optimizer,
                                metric_dict=metric_dict,
                                print_every=5,
                                test_loader=test_loader,
                               )
                               
test_results_w, test_loss, y_pred, y_true = eval_metrics(model_train_weights[1], test_loader, metric_dict, loss_func)

y_pred = y_pred.numpy()
y_true = y_true.numpy()

cm = confusion_matrix(y_true, y_pred)

plt.figure(figsize=(4, 2))
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=["Class 0", "Class 1"], yticklabels=["Class 0", "Class 1"])
plt.xlabel("Predicted")
plt.ylabel("Actual")
plt.title("Confusion Matrix")
plt.show()

print("Classification Report:")
print(classification_report(y_true, y_pred, target_names=["Class 0", "Class 1"]))    


plt.plot(model_train_weights[0]["test_metric_scores"]["F1"], label="Weighted Model (F1)")
plt.plot(model_train[0]["test_metric_scores"]["F1"], label="Baseline Model (F1)")

plt.xlabel("Epochs")
plt.ylabel("F1 Score")
plt.title("F1 Score Over Epochs")
plt.legend()
plt.show()


2. Добавьте в модель слои dropout и графически продемонстрируйте, как это влияет на процесс обучения и результаты на тестовом множестве.
class Model_drop(nn.Module):
    def __init__(self, n_inputs: int, n_classes: int) -> None:
        super().__init__()
        self.layer_1 = nn.Linear(n_inputs, 16)
        self.layer_2 = nn.Linear(16, n_classes)
        self.relu = nn.ReLU()
        self.drop = nn.Dropout(p=0.5)

    def forward(self, X: th.Tensor) -> th.Tensor:
        out = self.layer_1(X)
        out = self.relu(out)
        out = self.drop(out)
        out = self.layer_2(out)
        return out
        
model_dr = Model_drop(X_processed.shape[1], 2)

loss_func = nn.CrossEntropyLoss()
optimizer = optim.Adam(model_dr.parameters(), lr=0.001)
epochs = 10

model_train_drop = train_func(model=model_dr,
                                loader=train_loader,
                                n_epochs=epochs,
                                loss_func=loss_func,
                                optimizer=optimizer,
                                metric_dict=metric_dict,
                                print_every=5,
                                test_loader=test_loader,
                               )
                               
plt.plot(model_train_drop[0]["epoch_losses"], label="Model with Dropout (F1)")
plt.plot(model_train[0]["epoch_losses"], label="Baseline Model (F1)")

plt.xlabel("Epochs")
plt.ylabel("Loss")
plt.legend()
plt.show()

_, _, y_pred, y_true = eval_metrics(model_train_drop[1], test_loader, metric_dict, loss_func)

y_pred = y_pred.numpy()
y_true = y_true.numpy()

cm = confusion_matrix(y_true, y_pred)

plt.figure(figsize=(4, 2))
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=["Class 0", "Class 1"], yticklabels=["Class 0", "Class 1"])
plt.xlabel("Predicted")
plt.ylabel("Actual")
plt.title("Confusion Matrix")
plt.show()

print("Classification Report:")
print(classification_report(y_true, y_pred, target_names=["Class 0", "Class 1"]))

plt.plot(model_train_drop[0]["test_metric_scores"]["F1"], label="Model with Dropout (F1)")
plt.plot(model_train[0]["test_metric_scores"]["F1"], label="Baseline Model (F1)")

plt.xlabel("Epochs")
plt.ylabel("F1 Score")
plt.title("F1 Score Over Epochs")
plt.legend()
plt.show()


3. Сравните несколько различных оптимизаторов и графически продемонстрируйте, как выбор оптимизатора влияет на процесс обучения и результаты на тестовом множестве.
optimizers = {
    "Adam": lambda params: optim.Adam(params, lr=0.001),
    "SGD": lambda params: optim.SGD(params, lr=0.01, momentum=0.9),
    "RMSprop": lambda params: optim.RMSprop(params, lr=0.001)
}

epochs=10
results = {}

for name, optimizer_fn in optimizers.items():
    print(f"Training {name} optimizer")
    model = Model_1(X_processed.shape[1], 2)
    optimizer = optimizer_fn(model.parameters())
    
    train_results, _ = train_func(
        model=model,
        loader=train_loader,
        n_epochs=epochs,
        loss_func=loss_func,
        optimizer=optimizer,
        metric_dict=metric_dict,
        print_every=epochs // 2,
        test_loader=test_loader,
    )
    results[name] = train_results

plt.figure(figsize=(12, 6))

plt.subplot(1, 2, 1)
for name, res in results.items():
    plt.plot(res["epoch_losses"], label=f"{name} Loss")
plt.xlabel("Epochs")
plt.ylabel("Loss")
plt.title("Train Loss)
plt.legend()

plt.subplot(1, 2, 2)
for name, res in results.items():
    plt.plot(res["test_metric_scores"]["F1"], label=f"{name} F1 Score")
plt.xlabel("Epochs")
plt.ylabel("F1 Score")
plt.title("Test F1 Score")
plt.legend()

plt.tight_layout()
plt.show()
    '''
    pc.copy(text)
    
def gold():
    """
Набор данных: regression/gold.csv. Используя библиотеку PyTorch, решите задачу
одновременного предсказания столбцов 'Gold_T-7, Gold_T-14, Gold _Т-22 и Gold T+22 (задача регрессии). Разделите набор данных на обучающее и тестовое множество. Выполните предобработку данных (корректно обработайте случаи категориальных и нечисловых столбцов, при наличии). Сравните несколько различных оптимизаторов и графически продемонстрируйте, как выбор оптимизатора влияет на процесс обучения и результаты на тестовом множестве. (20 баллов)

import pandas as pd
import numpy as np

import torch as th
from torch import nn, optim
from torch.utils.data import Dataset, DataLoader, TensorDataset

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder, LabelEncoder
from sklearn.compose import ColumnTransformer
from torch.utils.data import TensorDataset, DataLoader, WeightedRandomSampler, random_split
import torchmetrics as M
from sklearn.metrics import confusion_matrix, classification_report
import seaborn as sns
from sklearn.utils.class_weight import compute_class_weight

import matplotlib.pyplot as plt


data = pd.read_csv("for_exam/datasets/regression/gold.csv")
scaler = StandardScaler()
data[data.columns] = scaler.fit_transform(data[data.columns])

y_cols = ["Gold_T-7", "Gold_T-14", "Gold_T-22", "Gold_T+22"]
X = data.drop(columns=y_cols)
y = data[y_cols]

X = th.FloatTensor(X.values)
y = th.FloatTensor(y.values)

dataset = TensorDataset(X, y)

generator = th.Generator().manual_seed(0)
train_dataset, test_dataset = random_split(dataset, [0.8, 0.2], generator=generator)

train_loader = DataLoader(train_dataset, batch_size=8, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=8, shuffle=False)

def train_func(model,
               loader,
               loss_func,
               optimizer,
               metric_dict,
               mean_metric=M.MeanMetric(),
               n_epochs: int = 100,
               print_every: int = 1,
               test_loader=None,
               ):

    out_dict = {}
    epoch_losses = []
    metric_scores = {name: [] for name in metric_dict.keys()}
    test_metric_scores = {name: [] for name in metric_dict.keys()} if test_loader else None
    test_losses = [] if test_loader else None
    
    model.train()
    for epoch in range(n_epochs):
        mean_metric.reset()
        
        for name, metric in metric_dict.items():
            metric.reset()

        for X_batch, y_batch in loader:
            y_batch = y_batch.float()
            y_pred = model(X_batch)
            
            loss = loss_func(y_pred, y_batch)
            mean_metric.update(loss)
            
            for name, metric in metric_dict.items():
                metric.update(y_pred, y_batch)
            
            loss.backward()
            
            optimizer.step()
            optimizer.zero_grad()

        epoch_loss = mean_metric.compute()
        epoch_losses.append(epoch_loss.item())
        
        for name, metric in metric_dict.items():
            metric_score = metric.compute().item()
            metric_scores[name].append(metric_score)
        
        if test_loader:
            test_results, test_loss, _, _ = eval_metrics(model, test_loader, metric_dict, loss_func)
            test_losses.append(test_loss)
            for name, score in test_results.items():
                test_metric_scores[name].append(score)

        if print_every != 0 and (epoch % print_every == 0 or epoch == n_epochs - 1):
            metrics_str = ", ".join([f"{name}: {metric_scores[name][-1]:.4f}" for name in metric_dict.keys()])
            if test_loader:
                test_metrics_str = ", ".join([f"test_{name}: {test_results[name]:.4f}" for name in test_results.keys()])
                print(f"Epoch {epoch + 1}, Loss: {epoch_loss.item():.4f}, {metrics_str}, \n"
                      f"Test Loss: {test_loss:.4f}, {test_metrics_str}")
            else:
                print(f"Epoch {epoch + 1}, Loss: {epoch_loss.item():.4f}, {metrics_str}")
    
    out_dict['epoch_losses'] = epoch_losses
    out_dict['metric_scores'] = metric_scores
    if test_loader:
        out_dict['test_metric_scores'] = test_metric_scores
        out_dict['test_losses'] = test_losses
    return out_dict, model


@th.no_grad()
def eval_metrics(model, loader, metric_dict, loss_func):
    model.eval()
    results = {}
    mean_metric = M.MeanMetric()
    mean_metric.reset()

    for name, metric in metric_dict.items():
        metric.reset()

    all_preds = []
    all_targets = []

    for X_batch, y_batch in loader:
        y_batch = y_batch.float()
        y_pred = model(X_batch)
        
        loss = loss_func(y_pred, y_batch)
        mean_metric.update(loss)
        
        all_preds.append(y_pred)
        all_targets.append(y_batch)

        for name, metric in metric_dict.items():
            metric.update(y_pred, y_batch)
    
    for name, metric in metric_dict.items():
        results[name] = metric.compute().item()
    
    loss_value = mean_metric.compute().item()
    return results, loss_value, th.cat(all_preds), th.cat(all_targets)
    
    
class Model_1(nn.Module):
    def __init__(self, n_inputs: int, n_classes: int) -> None:
        super().__init__()
        self.layer_1 = nn.Linear(n_inputs, 10)
        self.layer_2 = nn.Linear(10, n_classes)
        self.relu = nn.ReLU()

    def forward(self, X: th.Tensor) -> th.Tensor:
        out = self.layer_1(X)
        out = self.relu(out)
        out = self.layer_2(out)
        return out
        
model = Model_1(X.shape[1], 4)

loss_func = nn.MSELoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)
epochs = 50

metric_dict = {
    'R2':M.R2Score(num_outputs=4),
}

model_train = train_func(model=model,
                                loader=train_loader,
                                n_epochs=epochs,
                                loss_func=loss_func,
                                optimizer=optimizer,
                                metric_dict=metric_dict,
                                print_every=5,
                                test_loader=test_loader,
                               )
optimizers = {
    "Adam": lambda params: optim.Adam(params, lr=0.001),
    "SGD": lambda params: optim.SGD(params, lr=0.01, momentum=0.9),
    "RMSprop": lambda params: optim.RMSprop(params, lr=0.001)
}

epochs=20
results = {}

for name, optimizer_fn in optimizers.items():
    print(f"Training {name} optimizer")
    model = Model_1(X.shape[1], 4)
    optimizer = optimizer_fn(model.parameters())
    
    train_results, _ = train_func(
        model=model,
        loader=train_loader,
        n_epochs=epochs,
        loss_func=loss_func,
        optimizer=optimizer,
        metric_dict=metric_dict,
        print_every=5,
        test_loader=test_loader,
    )
    results[name] = train_results

plt.figure(figsize=(12, 6))

plt.subplot(1, 2, 1)
for name, res in results.items():
    plt.plot(res["epoch_losses"], label=f"{name} Loss")
plt.xlabel("Epochs")
plt.ylabel("Loss")
plt.title("Train Loss")
plt.legend()

plt.subplot(1, 2, 2)
for name, res in results.items():
    plt.plot(res["test_metric_scores"]["R2"], label=f"{name} R2")
plt.xlabel("Epochs")
plt.ylabel("R2")
plt.title("Test R2")
plt.legend()

plt.tight_layout()
plt.show()
    """
    
    text = '''
    import pandas as pd
import numpy as np

import torch as th
from torch import nn, optim
from torch.utils.data import Dataset, DataLoader, TensorDataset

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder, LabelEncoder
from sklearn.compose import ColumnTransformer
from torch.utils.data import TensorDataset, DataLoader, WeightedRandomSampler, random_split
import torchmetrics as M
from sklearn.metrics import confusion_matrix, classification_report
import seaborn as sns
from sklearn.utils.class_weight import compute_class_weight

import matplotlib.pyplot as plt


data = pd.read_csv("for_exam/datasets/regression/gold.csv")
scaler = StandardScaler()
data[data.columns] = scaler.fit_transform(data[data.columns])

y_cols = ["Gold_T-7", "Gold_T-14", "Gold_T-22", "Gold_T+22"]
X = data.drop(columns=y_cols)
y = data[y_cols]

X = th.FloatTensor(X.values)
y = th.FloatTensor(y.values)

dataset = TensorDataset(X, y)

generator = th.Generator().manual_seed(0)
train_dataset, test_dataset = random_split(dataset, [0.8, 0.2], generator=generator)

train_loader = DataLoader(train_dataset, batch_size=8, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=8, shuffle=False)

def train_func(model,
               loader,
               loss_func,
               optimizer,
               metric_dict,
               mean_metric=M.MeanMetric(),
               n_epochs: int = 100,
               print_every: int = 1,
               test_loader=None,
               ):

    out_dict = {}
    epoch_losses = []
    metric_scores = {name: [] for name in metric_dict.keys()}
    test_metric_scores = {name: [] for name in metric_dict.keys()} if test_loader else None
    test_losses = [] if test_loader else None
    
    model.train()
    for epoch in range(n_epochs):
        mean_metric.reset()
        
        for name, metric in metric_dict.items():
            metric.reset()

        for X_batch, y_batch in loader:
            y_batch = y_batch.float()
            y_pred = model(X_batch)
            
            loss = loss_func(y_pred, y_batch)
            mean_metric.update(loss)
            
            for name, metric in metric_dict.items():
                metric.update(y_pred, y_batch)
            
            loss.backward()
            
            optimizer.step()
            optimizer.zero_grad()

        epoch_loss = mean_metric.compute()
        epoch_losses.append(epoch_loss.item())
        
        for name, metric in metric_dict.items():
            metric_score = metric.compute().item()
            metric_scores[name].append(metric_score)
        
        if test_loader:
            test_results, test_loss, _, _ = eval_metrics(model, test_loader, metric_dict, loss_func)
            test_losses.append(test_loss)
            for name, score in test_results.items():
                test_metric_scores[name].append(score)

        if print_every != 0 and (epoch % print_every == 0 or epoch == n_epochs - 1):
            metrics_str = ", ".join([f"{name}: {metric_scores[name][-1]:.4f}" for name in metric_dict.keys()])
            if test_loader:
                test_metrics_str = ", ".join([f"test_{name}: {test_results[name]:.4f}" for name in test_results.keys()])
                print(f"Epoch {epoch + 1}, Loss: {epoch_loss.item():.4f}, {metrics_str}, \n"
                      f"Test Loss: {test_loss:.4f}, {test_metrics_str}")
            else:
                print(f"Epoch {epoch + 1}, Loss: {epoch_loss.item():.4f}, {metrics_str}")
    
    out_dict['epoch_losses'] = epoch_losses
    out_dict['metric_scores'] = metric_scores
    if test_loader:
        out_dict['test_metric_scores'] = test_metric_scores
        out_dict['test_losses'] = test_losses
    return out_dict, model


@th.no_grad()
def eval_metrics(model, loader, metric_dict, loss_func):
    model.eval()
    results = {}
    mean_metric = M.MeanMetric()
    mean_metric.reset()

    for name, metric in metric_dict.items():
        metric.reset()

    all_preds = []
    all_targets = []

    for X_batch, y_batch in loader:
        y_batch = y_batch.float()
        y_pred = model(X_batch)
        
        loss = loss_func(y_pred, y_batch)
        mean_metric.update(loss)
        
        all_preds.append(y_pred)
        all_targets.append(y_batch)

        for name, metric in metric_dict.items():
            metric.update(y_pred, y_batch)
    
    for name, metric in metric_dict.items():
        results[name] = metric.compute().item()
    
    loss_value = mean_metric.compute().item()
    return results, loss_value, th.cat(all_preds), th.cat(all_targets)
    
    
class Model_1(nn.Module):
    def __init__(self, n_inputs: int, n_classes: int) -> None:
        super().__init__()
        self.layer_1 = nn.Linear(n_inputs, 10)
        self.layer_2 = nn.Linear(10, n_classes)
        self.relu = nn.ReLU()

    def forward(self, X: th.Tensor) -> th.Tensor:
        out = self.layer_1(X)
        out = self.relu(out)
        out = self.layer_2(out)
        return out
        
model = Model_1(X.shape[1], 4)

loss_func = nn.MSELoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)
epochs = 50

metric_dict = {
    'R2':M.R2Score(num_outputs=4),
}

model_train = train_func(model=model,
                                loader=train_loader,
                                n_epochs=epochs,
                                loss_func=loss_func,
                                optimizer=optimizer,
                                metric_dict=metric_dict,
                                print_every=5,
                                test_loader=test_loader,
                               )
optimizers = {
    "Adam": lambda params: optim.Adam(params, lr=0.001),
    "SGD": lambda params: optim.SGD(params, lr=0.01, momentum=0.9),
    "RMSprop": lambda params: optim.RMSprop(params, lr=0.001)
}

epochs=20
results = {}

for name, optimizer_fn in optimizers.items():
    print(f"Training {name} optimizer")
    model = Model_1(X.shape[1], 4)
    optimizer = optimizer_fn(model.parameters())
    
    train_results, _ = train_func(
        model=model,
        loader=train_loader,
        n_epochs=epochs,
        loss_func=loss_func,
        optimizer=optimizer,
        metric_dict=metric_dict,
        print_every=5,
        test_loader=test_loader,
    )
    results[name] = train_results

plt.figure(figsize=(12, 6))

plt.subplot(1, 2, 1)
for name, res in results.items():
    plt.plot(res["epoch_losses"], label=f"{name} Loss")
plt.xlabel("Epochs")
plt.ylabel("Loss")
plt.title("Train Loss")
plt.legend()

plt.subplot(1, 2, 2)
for name, res in results.items():
    plt.plot(res["test_metric_scores"]["R2"], label=f"{name} R2")
plt.xlabel("Epochs")
plt.ylabel("R2")
plt.title("Test R2")
plt.legend()

plt.tight_layout()
plt.show()
    '''
    pc.copy(text)
    
    
def import_A():
    """
import pandas as pd
import numpy as np

import torch
from torch import nn, optim
from torch.utils.data import Dataset, DataLoader, TensorDataset

from torchvision import transforms
from torchvision.datasets import ImageFolder

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder, LabelEncoder
from sklearn.metrics import confusion_matrix, classification_report, accuracy_score, f1_score
from sklearn.compose import ColumnTransformer

import matplotlib.pyplot as plt

import torch
import torch.nn as nn
import torch.optim as optim

from torch.utils.data import DataLoader
from torchvision import transforms
from torchvision.datasets import ImageFolder
import torch.nn.functional as F

import matplotlib.pyplot as plt
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import PCA
import seaborn as sns
import numpy as np
    """
    text = '''
import pandas as pd
import numpy as np

import torch
from torch import nn, optim
from torch.utils.data import Dataset, DataLoader, TensorDataset

from torchvision import transforms
from torchvision.datasets import ImageFolder

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder, LabelEncoder
from sklearn.metrics import confusion_matrix, classification_report, accuracy_score, f1_score
from sklearn.compose import ColumnTransformer

import matplotlib.pyplot as plt
import torch
import torch.nn as nn
import torch.optim as optim

from torch.utils.data import DataLoader
from torchvision import transforms
from torchvision.datasets import ImageFolder
import torch.nn.functional as F

import matplotlib.pyplot as plt
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import PCA
import seaborn as sns
import numpy as np
    '''
    pc.copy(text)
    
    
def bank_A_optims():
    """
2. Набор данных: classification/bank.csv. Используя библиотеку PyTorch, решите задачу
классификации (столбец deposit). Разделите набор данных на обучающее и тестовое множество. Выполните предобработку данных (корректно обработайте случаи категориальных и нечисловых столбцов, при наличии). Отобразите график значений функции потерь на обучающем множестве по эпохам. Отобразите confusion matrix и classification report, рассчитанные на основе тестового множества. Сравните несколько различных оптимизаторов и графически продемонстрируйте, как выбор оптимизатора влияет на процесс обучения и результаты на тестовом множестве. (20 баллов)


data = pd.read_csv('/content/drive/MyDrive/Файлы/datasets/classification/bank.csv')
data.head()


X = data.drop(['deposit'], axis=1)
y = data['deposit']

categorical_cols = ['job', 'marital',	'education', 'default', 'housing', 'loan', 'contact', 'month', 'poutcome']
numerical_cols = ['age', 'balance', 'day', 'duration', 'campaign', 'pdays', 'previous']

label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y)

preprocessor = ColumnTransformer(
    transformers=[
        ('num', StandardScaler(), numerical_cols),
        ('cat', OneHotEncoder(), categorical_cols)
    ])

X_processed = preprocessor.fit_transform(X)

X_train, X_test, y_train, y_test = train_test_split(X_processed, y_encoded, test_size=0.2, random_state=42)

X_train = torch.tensor(X_train, dtype=torch.float32)
y_train = torch.tensor(y_train, dtype=torch.float32)
X_test = torch.tensor(X_test, dtype=torch.float32)
y_test = torch.tensor(y_test, dtype=torch.float32)

train_dataset = TensorDataset(X_train, y_train)
test_dataset = TensorDataset(X_test, y_test)


class Model(nn.Module):
    def __init__(self, n_features, n_hidden):
        super().__init__()
        self.model = nn.Sequential(
            nn.Linear(n_features, n_hidden),
            nn.ReLU(),
            nn.Linear(n_hidden, 2)
        )

    def forward(self, x):
        return self.model(x)
        
batch_size = 64
epochs = 5
print_every = 1
n_features = train_dataset[0][0].shape[0]
n_hidden = 16


optimizers = {
    "SGD": torch.optim.SGD,
    "Adam": torch.optim.Adam,
    "AdamW": torch.optim.AdamW
}

losses_per_optimizer = {name: [] for name in optimizers}

for opt_name, opt_class in optimizers.items():
    model = Model(n_features, n_hidden)
    criterion = nn.CrossEntropyLoss()
    optimizer = opt_class(model.parameters(), lr=0.01)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    epoch_losses = []

    for epoch in range(epochs):
        epoch_loss = 0
        for batch_X, batch_y in train_loader:
            # Forward pass
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y.long())

            # Backward pass
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            epoch_loss += loss.item()

        epoch_losses.append(epoch_loss / len(train_loader))
        if (epoch + 1) % print_every == 0:
            print(f"[{opt_name}] Epoch {epoch+1}/{epochs}, Loss: {epoch_loss / len(train_loader):.4f}")

    losses_per_optimizer[opt_name] = epoch_losses

plt.figure(figsize=(10, 6))
for opt_name, losses in losses_per_optimizer.items():
    plt.plot(range(1, epochs + 1), losses, label=opt_name)
plt.xlabel("Epoch")
plt.ylabel("Loss")
plt.title("Функции потерь для разных оптимизаторов")
plt.legend()
plt.show()

batch_size = 64
epochs = 5
n_features = train_dataset[0][0].shape[0]
n_hidden = 16

optimizers = {
    "SGD": torch.optim.SGD,
    "Adam": torch.optim.Adam,
    "AdamW": torch.optim.AdamW
}

metrics_per_optimizer = {name: {"Accuracy": [], "F1-score": []} for name in optimizers}

for opt_name, opt_class in optimizers.items():
    print(f"\nEvaluation for {opt_name}:")

    model = Model(n_features, n_hidden)
    criterion = nn.CrossEntropyLoss()
    optimizer = opt_class(model.parameters(), lr=0.01)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    for epoch in range(epochs):
        for batch_X, batch_y in train_loader:
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y.long())
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)
    y_pred = []
    y_true = []

    with torch.no_grad():
        for batch_X, batch_y in test_loader:
            outputs = model(batch_X)
            _, predicted = torch.max(outputs, 1)
            y_pred.extend(predicted.cpu().numpy())
            y_true.extend(batch_y.cpu().numpy())

    accuracy = accuracy_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred, pos_label=1, average='weighted')

    metrics_per_optimizer[opt_name]["Accuracy"].append(accuracy)

    metrics_per_optimizer[opt_name]["F1-score"].append(f1)

    cm = confusion_matrix(y_true, y_pred)
    print(f"Confusion Matrix:\n{cm}")
    cr = classification_report(y_true, y_pred, target_names=["Class 0", "Class 1"])
    print(f"Classification Report:\n{cr}")

    print(f"Accuracy: {accuracy:.4f}")
    print(f"F1-score: {f1:.4f}")


metrics = ["Accuracy", "F1-score"]
fig, axes = plt.subplots(1, len(metrics), figsize=(20, 5))

for i, metric in enumerate(metrics):
    ax = axes[i]
    values = [metrics_per_optimizer[opt_name][metric][0] for opt_name in optimizers]
    ax.bar(optimizers.keys(), values, color=["b", "r", "g"])
    ax.set_title(metric)
    ax.set_ylim(0, 1)
    ax.set_ylabel(metric)
    ax.set_xlabel("Optimizers")

plt.tight_layout()
plt.show()

    """
    text = '''
    data = pd.read_csv('/content/drive/MyDrive/Файлы/datasets/classification/bank.csv')
data.head()


X = data.drop(['deposit'], axis=1)
y = data['deposit']

categorical_cols = ['job', 'marital',	'education', 'default', 'housing', 'loan', 'contact', 'month', 'poutcome']
numerical_cols = ['age', 'balance', 'day', 'duration', 'campaign', 'pdays', 'previous']

label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y)

preprocessor = ColumnTransformer(
    transformers=[
        ('num', StandardScaler(), numerical_cols),
        ('cat', OneHotEncoder(), categorical_cols)
    ])

X_processed = preprocessor.fit_transform(X)

X_train, X_test, y_train, y_test = train_test_split(X_processed, y_encoded, test_size=0.2, random_state=42)

X_train = torch.tensor(X_train, dtype=torch.float32)
y_train = torch.tensor(y_train, dtype=torch.float32)
X_test = torch.tensor(X_test, dtype=torch.float32)
y_test = torch.tensor(y_test, dtype=torch.float32)

train_dataset = TensorDataset(X_train, y_train)
test_dataset = TensorDataset(X_test, y_test)


class Model(nn.Module):
    def __init__(self, n_features, n_hidden):
        super().__init__()
        self.model = nn.Sequential(
            nn.Linear(n_features, n_hidden),
            nn.ReLU(),
            nn.Linear(n_hidden, 2)
        )

    def forward(self, x):
        return self.model(x)
        
batch_size = 64
epochs = 5
print_every = 1
n_features = train_dataset[0][0].shape[0]
n_hidden = 16


optimizers = {
    "SGD": torch.optim.SGD,
    "Adam": torch.optim.Adam,
    "AdamW": torch.optim.AdamW
}

losses_per_optimizer = {name: [] for name in optimizers}

for opt_name, opt_class in optimizers.items():
    model = Model(n_features, n_hidden)
    criterion = nn.CrossEntropyLoss()
    optimizer = opt_class(model.parameters(), lr=0.01)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    epoch_losses = []

    for epoch in range(epochs):
        epoch_loss = 0
        for batch_X, batch_y in train_loader:
            # Forward pass
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y.long())

            # Backward pass
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            epoch_loss += loss.item()

        epoch_losses.append(epoch_loss / len(train_loader))
        if (epoch + 1) % print_every == 0:
            print(f"[{opt_name}] Epoch {epoch+1}/{epochs}, Loss: {epoch_loss / len(train_loader):.4f}")

    losses_per_optimizer[opt_name] = epoch_losses

plt.figure(figsize=(10, 6))
for opt_name, losses in losses_per_optimizer.items():
    plt.plot(range(1, epochs + 1), losses, label=opt_name)
plt.xlabel("Epoch")
plt.ylabel("Loss")
plt.title("Функции потерь для разных оптимизаторов")
plt.legend()
plt.show()

batch_size = 64
epochs = 5
n_features = train_dataset[0][0].shape[0]
n_hidden = 16

optimizers = {
    "SGD": torch.optim.SGD,
    "Adam": torch.optim.Adam,
    "AdamW": torch.optim.AdamW
}

metrics_per_optimizer = {name: {"Accuracy": [], "F1-score": []} for name in optimizers}

for opt_name, opt_class in optimizers.items():
    print(f"\nEvaluation for {opt_name}:")

    model = Model(n_features, n_hidden)
    criterion = nn.CrossEntropyLoss()
    optimizer = opt_class(model.parameters(), lr=0.01)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    for epoch in range(epochs):
        for batch_X, batch_y in train_loader:
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y.long())
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)
    y_pred = []
    y_true = []

    with torch.no_grad():
        for batch_X, batch_y in test_loader:
            outputs = model(batch_X)
            _, predicted = torch.max(outputs, 1)
            y_pred.extend(predicted.cpu().numpy())
            y_true.extend(batch_y.cpu().numpy())

    accuracy = accuracy_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred, pos_label=1, average='weighted')

    metrics_per_optimizer[opt_name]["Accuracy"].append(accuracy)

    metrics_per_optimizer[opt_name]["F1-score"].append(f1)

    cm = confusion_matrix(y_true, y_pred)
    print(f"Confusion Matrix:\n{cm}")
    cr = classification_report(y_true, y_pred, target_names=["Class 0", "Class 1"])
    print(f"Classification Report:\n{cr}")

    print(f"Accuracy: {accuracy:.4f}")
    print(f"F1-score: {f1:.4f}")


metrics = ["Accuracy", "F1-score"]
fig, axes = plt.subplots(1, len(metrics), figsize=(20, 5))

for i, metric in enumerate(metrics):
    ax = axes[i]
    values = [metrics_per_optimizer[opt_name][metric][0] for opt_name in optimizers]
    ax.bar(optimizers.keys(), values, color=["b", "r", "g"])
    ax.set_title(metric)
    ax.set_ylim(0, 1)
    ax.set_ylabel(metric)
    ax.set_xlabel("Optimizers")

plt.tight_layout()
plt.show()
    '''
    pc.copy(text)
    
    
    
def bank_A_dropout():
    """
    2. Набор данных: classification/bank.csv. Используя библиотеку PyTorch, решите задачу
классификации (столбец deposit). Разделите набор данных на обучающее и тестовое множество. Выполните предобработку данных. Отобразите график значений функции потерь на обучающем множестве по эпохам. Отобразите confusion matrix и
classification report, рассчитанные на основе тестового множества. Добавьте в модель слои DropOut и графически продемонстрируйте влияние на процесс обучения и результаты на тестовом множестве. (20 баллов)

data = pd.read_csv('/content/drive/MyDrive/Файлы/datasets/classification/bank.csv')

X = data.drop(['deposit'], axis=1)
y = data['deposit']

categorical_cols = ['job', 'marital',	'education', 'default', 'housing', 'loan', 'contact', 'month', 'poutcome']
numerical_cols = ['age', 'balance', 'day', 'duration', 'campaign', 'pdays', 'previous']

label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y)

preprocessor = ColumnTransformer(
    transformers=[
        ('num', StandardScaler(), numerical_cols),
        ('cat', OneHotEncoder(), categorical_cols)
    ])

X_processed = preprocessor.fit_transform(X)

X_train, X_test, y_train, y_test = train_test_split(X_processed, y_encoded, test_size=0.2, random_state=42)

X_train = torch.tensor(X_train, dtype=torch.float32)
y_train = torch.tensor(y_train, dtype=torch.float32)
X_test = torch.tensor(X_test, dtype=torch.float32)
y_test = torch.tensor(y_test, dtype=torch.float32)

train_dataset = TensorDataset(X_train, y_train)
test_dataset = TensorDataset(X_test, y_test)

class Model(nn.Module):
    def __init__(self, n_features, n_hidden):
        super().__init__()
        self.model = nn.Sequential(
            nn.Linear(n_features, n_hidden),
            nn.ReLU(),
            nn.Linear(n_hidden, 2)
        )

    def forward(self, x):
        return self.model(x)
        
class ModelDropOut(nn.Module):
    def __init__(self, n_features, n_hidden, p):
        super().__init__()
        self.model = nn.Sequential(
            nn.Linear(n_features, n_hidden),
            nn.ReLU(),
            nn.Dropout(p),
            nn.Linear(n_hidden, 2)
        )

    def forward(self, x):
        return self.model(x)
        
batch_size = 64
epochs = 5
print_every = 1
n_features = train_dataset[0][0].shape[0]
n_hidden = 16
p = 0.2

models = {
    "No DropOut": Model(n_features, n_hidden),
    "DropOut": ModelDropOut(n_features, n_hidden, p),
}

losses_per_model = {name: [] for name in models}

for model_name, model_class in models.items():
    model = model_class
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    epoch_losses = []

    for epoch in range(epochs):
        epoch_loss = 0
        for batch_X, batch_y in train_loader:
            # Forward pass
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y.long())

            # Backward pass
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            epoch_loss += loss.item()

        epoch_losses.append(epoch_loss / len(train_loader))
        if (epoch + 1) % print_every == 0:
            print(f"[{model_name}] Epoch {epoch+1}/{epochs}, Loss: {epoch_loss / len(train_loader):.4f}")

    losses_per_model[model_name] = epoch_losses

plt.figure(figsize=(10, 6))
for model_name, losses in losses_per_model.items():
    plt.plot(range(1, epochs + 1), losses, label=model_name)
plt.xlabel("Epoch")
plt.ylabel("Loss")
plt.title("Функции потерь для разных моделей")
plt.legend()
plt.show()


batch_size = 64
epochs = 5
n_features = train_dataset[0][0].shape[0]
n_hidden = 16
p = 0.2

models = {
    "No DropOut": Model(n_features, n_hidden),
    "DropOut": ModelDropOut(n_features, n_hidden, p),
}

metrics_per_model = {name: {"Accuracy": [], "F1-score": []} for name in models}

for model_name, model_class in models.items():
    print(f"\nEvaluation for {model_name}:")

    model = model_class
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    for epoch in range(epochs):
        for batch_X, batch_y in train_loader:
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y.long())
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)
    y_pred = []
    y_true = []

    with torch.no_grad():
        for batch_X, batch_y in test_loader:
            outputs = model(batch_X)
            _, predicted = torch.max(outputs, 1)
            y_pred.extend(predicted.cpu().numpy())
            y_true.extend(batch_y.cpu().numpy())

    accuracy = accuracy_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred, pos_label=1, average='weighted')

    metrics_per_model[model_name]["Accuracy"].append(accuracy)
    metrics_per_model[model_name]["F1-score"].append(f1)

    cm = confusion_matrix(y_true, y_pred)
    print(f"Confusion Matrix:\n{cm}")
    cr = classification_report(y_true, y_pred, target_names=["Class 0", "Class 1"])
    print(f"Classification Report:\n{cr}")

    print(f"Accuracy: {accuracy:.4f}")
    print(f"F1-score: {f1:.4f}")


metrics = ["Accuracy", "F1-score"]
fig, axes = plt.subplots(1, len(metrics), figsize=(20, 5))

for i, metric in enumerate(metrics):
    ax = axes[i]
    values = [metrics_per_model[model_name][metric][0] for model_name in models]
    ax.bar(models.keys(), values, color=["b", "r", "g"])
    ax.set_title(metric)
    ax.set_ylim(0, 1)
    ax.set_ylabel(metric)
    ax.set_xlabel("models")

plt.tight_layout()
plt.show()



    """
    text = '''
    
data = pd.read_csv('/content/drive/MyDrive/Файлы/datasets/classification/bank.csv')

X = data.drop(['deposit'], axis=1)
y = data['deposit']

categorical_cols = ['job', 'marital',	'education', 'default', 'housing', 'loan', 'contact', 'month', 'poutcome']
numerical_cols = ['age', 'balance', 'day', 'duration', 'campaign', 'pdays', 'previous']

label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y)

preprocessor = ColumnTransformer(
    transformers=[
        ('num', StandardScaler(), numerical_cols),
        ('cat', OneHotEncoder(), categorical_cols)
    ])

X_processed = preprocessor.fit_transform(X)

X_train, X_test, y_train, y_test = train_test_split(X_processed, y_encoded, test_size=0.2, random_state=42)

X_train = torch.tensor(X_train, dtype=torch.float32)
y_train = torch.tensor(y_train, dtype=torch.float32)
X_test = torch.tensor(X_test, dtype=torch.float32)
y_test = torch.tensor(y_test, dtype=torch.float32)

train_dataset = TensorDataset(X_train, y_train)
test_dataset = TensorDataset(X_test, y_test)

class Model(nn.Module):
    def __init__(self, n_features, n_hidden):
        super().__init__()
        self.model = nn.Sequential(
            nn.Linear(n_features, n_hidden),
            nn.ReLU(),
            nn.Linear(n_hidden, 2)
        )

    def forward(self, x):
        return self.model(x)
        
class ModelDropOut(nn.Module):
    def __init__(self, n_features, n_hidden, p):
        super().__init__()
        self.model = nn.Sequential(
            nn.Linear(n_features, n_hidden),
            nn.ReLU(),
            nn.Dropout(p),
            nn.Linear(n_hidden, 2)
        )

    def forward(self, x):
        return self.model(x)
        
batch_size = 64
epochs = 5
print_every = 1
n_features = train_dataset[0][0].shape[0]
n_hidden = 16
p = 0.2

models = {
    "No DropOut": Model(n_features, n_hidden),
    "DropOut": ModelDropOut(n_features, n_hidden, p),
}

losses_per_model = {name: [] for name in models}

for model_name, model_class in models.items():
    model = model_class
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    epoch_losses = []

    for epoch in range(epochs):
        epoch_loss = 0
        for batch_X, batch_y in train_loader:
            # Forward pass
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y.long())

            # Backward pass
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            epoch_loss += loss.item()

        epoch_losses.append(epoch_loss / len(train_loader))
        if (epoch + 1) % print_every == 0:
            print(f"[{model_name}] Epoch {epoch+1}/{epochs}, Loss: {epoch_loss / len(train_loader):.4f}")

    losses_per_model[model_name] = epoch_losses

plt.figure(figsize=(10, 6))
for model_name, losses in losses_per_model.items():
    plt.plot(range(1, epochs + 1), losses, label=model_name)
plt.xlabel("Epoch")
plt.ylabel("Loss")
plt.title("Функции потерь для разных моделей")
plt.legend()
plt.show()


batch_size = 64
epochs = 5
n_features = train_dataset[0][0].shape[0]
n_hidden = 16
p = 0.2

models = {
    "No DropOut": Model(n_features, n_hidden),
    "DropOut": ModelDropOut(n_features, n_hidden, p),
}

metrics_per_model = {name: {"Accuracy": [], "F1-score": []} for name in models}

for model_name, model_class in models.items():
    print(f"\nEvaluation for {model_name}:")

    model = model_class
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    for epoch in range(epochs):
        for batch_X, batch_y in train_loader:
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y.long())
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)
    y_pred = []
    y_true = []

    with torch.no_grad():
        for batch_X, batch_y in test_loader:
            outputs = model(batch_X)
            _, predicted = torch.max(outputs, 1)
            y_pred.extend(predicted.cpu().numpy())
            y_true.extend(batch_y.cpu().numpy())

    accuracy = accuracy_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred, pos_label=1, average='weighted')

    metrics_per_model[model_name]["Accuracy"].append(accuracy)
    metrics_per_model[model_name]["F1-score"].append(f1)

    cm = confusion_matrix(y_true, y_pred)
    print(f"Confusion Matrix:\n{cm}")
    cr = classification_report(y_true, y_pred, target_names=["Class 0", "Class 1"])
    print(f"Classification Report:\n{cr}")

    print(f"Accuracy: {accuracy:.4f}")
    print(f"F1-score: {f1:.4f}")


metrics = ["Accuracy", "F1-score"]
fig, axes = plt.subplots(1, len(metrics), figsize=(20, 5))

for i, metric in enumerate(metrics):
    ax = axes[i]
    values = [metrics_per_model[model_name][metric][0] for model_name in models]
    ax.bar(models.keys(), values, color=["b", "r", "g"])
    ax.set_title(metric)
    ax.set_ylim(0, 1)
    ax.set_ylabel(metric)
    ax.set_xlabel("models")

plt.tight_layout()
plt.show()
    '''
    pc.copy(text)
    

def bank_A_disbalance():
    """
    2. Набор данных: classification/bank.csv. Используя библиотеку PyTorch, решите задачу
множество. Выполните предобработку данных (корректно обработайте случаи категориальных и нечисловых столбцов, при наличии). Отобразите график значений функции потерь на обучающем множестве по эпохам. Отобразите confusion matrix и classification report, рассчитанные на основе тестового множества. Модифицируйте функцию потерь с учетом несбалансированности классов и продемонстируйте, как это влияет на результаты на тестовом множестве. (20 баллов)

data = pd.read_csv('/content/drive/MyDrive/Файлы/datasets/classification/bank.csv')

X = data.drop(['deposit'], axis=1)
y = data['deposit']

categorical_cols = ['job', 'marital',	'education', 'default', 'housing', 'loan', 'contact', 'month', 'poutcome']
numerical_cols = ['age', 'balance', 'day', 'duration', 'campaign', 'pdays', 'previous']

label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y)

preprocessor = ColumnTransformer(
    transformers=[
        ('num', StandardScaler(), numerical_cols),
        ('cat', OneHotEncoder(), categorical_cols)
    ])

X_processed = preprocessor.fit_transform(X)

X_train, X_test, y_train, y_test = train_test_split(X_processed, y_encoded, test_size=0.2, random_state=42)

X_train = torch.tensor(X_train, dtype=torch.float32)
y_train = torch.tensor(y_train, dtype=torch.float32)
X_test = torch.tensor(X_test, dtype=torch.float32)
y_test = torch.tensor(y_test, dtype=torch.float32)

train_dataset = TensorDataset(X_train, y_train)
test_dataset = TensorDataset(X_test, y_test)

class Model(nn.Module):
    def __init__(self, n_features, n_hidden):
        super().__init__()
        self.model = nn.Sequential(
            nn.Linear(n_features, n_hidden),
            nn.ReLU(),
            nn.Linear(n_hidden, 2)
        )

    def forward(self, x):
        return self.model(x)
        
batch_size = 64
epochs = 5
print_every = 1
n_features = train_dataset[0][0].shape[0]
n_hidden = 16

class_counts = [0.89, 0.11]
class_weights = torch.tensor([1.0 / class_counts[0], 1.0 / class_counts[1]], dtype=torch.float32)

criterions = {
    "CE Loss": nn.CrossEntropyLoss(),
    "CE Loss Weighted": nn.CrossEntropyLoss(weight=class_weights),
}

losses_per_criterion = {name: [] for name in criterions}

for criterion_name, criterion_class in criterions.items():
    model = Model(n_features, n_hidden)
    criterion = criterion_class
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    epoch_losses = []

    for epoch in range(epochs):
        epoch_loss = 0
        for batch_X, batch_y in train_loader:
            # Forward pass
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y.long())

            # Backward pass
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            epoch_loss += loss.item()

        epoch_losses.append(epoch_loss / len(train_loader))
        if (epoch + 1) % print_every == 0:
            print(f"[{criterion_name}] Epoch {epoch+1}/{epochs}, Loss: {epoch_loss / len(train_loader):.4f}")

    losses_per_criterion[criterion_name] = epoch_losses

plt.figure(figsize=(10, 6))
for criterion_name, losses in losses_per_criterion.items():
    plt.plot(range(1, epochs + 1), losses, label=criterion_name)
plt.xlabel("Epoch")
plt.ylabel("Loss")
plt.title("Функции потерь для разных критериев")
plt.legend()
plt.show()


batch_size = 64
epochs = 5
n_features = train_dataset[0][0].shape[0]
n_hidden = 16


criterions = {
    "CE Loss": nn.CrossEntropyLoss(),
    "CE Loss Weighted": nn.CrossEntropyLoss(weight=class_weights),
}

metrics_per_criterion = {name: {"Accuracy": [], "F1-score": []} for name in criterions}

for criterion_name, criterion_class in criterions.items():
    print(f"\nEvaluation for {criterion_name}:")

    model = Model(n_features, n_hidden)
    criterion = criterion_class
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    for epoch in range(epochs):
        for batch_X, batch_y in train_loader:
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y.long())
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)
    y_pred = []
    y_true = []

    with torch.no_grad():
        for batch_X, batch_y in test_loader:
            outputs = model(batch_X)
            _, predicted = torch.max(outputs, 1)
            y_pred.extend(predicted.cpu().numpy())
            y_true.extend(batch_y.cpu().numpy())

    accuracy = accuracy_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred, pos_label=1, average='weighted')

    metrics_per_criterion[criterion_name]["Accuracy"].append(accuracy)
    metrics_per_criterion[criterion_name]["F1-score"].append(f1)

    cm = confusion_matrix(y_true, y_pred)
    print(f"Confusion Matrix:\n{cm}")
    cr = classification_report(y_true, y_pred, target_names=["Class 0", "Class 1"])
    print(f"Classification Report:\n{cr}")

    print(f"Accuracy: {accuracy:.4f}")
    print(f"F1-score: {f1:.4f}")


metrics = ["Accuracy", "F1-score"]
fig, axes = plt.subplots(1, len(metrics), figsize=(20, 5))

for i, metric in enumerate(metrics):
    ax = axes[i]
    values = [metrics_per_criterion[criterion_name][metric][0] for criterion_name in criterions]
    ax.bar(criterions.keys(), values, color=["b", "r"])
    ax.set_title(metric)
    ax.set_ylim(0, 1)
    ax.set_ylabel(metric)
    ax.set_xlabel("criterions")

plt.tight_layout()
plt.show()


    """
    text = '''
data = pd.read_csv('/content/drive/MyDrive/Файлы/datasets/classification/bank.csv')

X = data.drop(['deposit'], axis=1)
y = data['deposit']

categorical_cols = ['job', 'marital',	'education', 'default', 'housing', 'loan', 'contact', 'month', 'poutcome']
numerical_cols = ['age', 'balance', 'day', 'duration', 'campaign', 'pdays', 'previous']

label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y)

preprocessor = ColumnTransformer(
    transformers=[
        ('num', StandardScaler(), numerical_cols),
        ('cat', OneHotEncoder(), categorical_cols)
    ])

X_processed = preprocessor.fit_transform(X)

X_train, X_test, y_train, y_test = train_test_split(X_processed, y_encoded, test_size=0.2, random_state=42)

X_train = torch.tensor(X_train, dtype=torch.float32)
y_train = torch.tensor(y_train, dtype=torch.float32)
X_test = torch.tensor(X_test, dtype=torch.float32)
y_test = torch.tensor(y_test, dtype=torch.float32)

train_dataset = TensorDataset(X_train, y_train)
test_dataset = TensorDataset(X_test, y_test)

class Model(nn.Module):
    def __init__(self, n_features, n_hidden):
        super().__init__()
        self.model = nn.Sequential(
            nn.Linear(n_features, n_hidden),
            nn.ReLU(),
            nn.Linear(n_hidden, 2)
        )

    def forward(self, x):
        return self.model(x)
        
batch_size = 64
epochs = 5
print_every = 1
n_features = train_dataset[0][0].shape[0]
n_hidden = 16

class_counts = [0.89, 0.11]
class_weights = torch.tensor([1.0 / class_counts[0], 1.0 / class_counts[1]], dtype=torch.float32)

criterions = {
    "CE Loss": nn.CrossEntropyLoss(),
    "CE Loss Weighted": nn.CrossEntropyLoss(weight=class_weights),
}

losses_per_criterion = {name: [] for name in criterions}

for criterion_name, criterion_class in criterions.items():
    model = Model(n_features, n_hidden)
    criterion = criterion_class
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    epoch_losses = []

    for epoch in range(epochs):
        epoch_loss = 0
        for batch_X, batch_y in train_loader:
            # Forward pass
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y.long())

            # Backward pass
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            epoch_loss += loss.item()

        epoch_losses.append(epoch_loss / len(train_loader))
        if (epoch + 1) % print_every == 0:
            print(f"[{criterion_name}] Epoch {epoch+1}/{epochs}, Loss: {epoch_loss / len(train_loader):.4f}")

    losses_per_criterion[criterion_name] = epoch_losses

plt.figure(figsize=(10, 6))
for criterion_name, losses in losses_per_criterion.items():
    plt.plot(range(1, epochs + 1), losses, label=criterion_name)
plt.xlabel("Epoch")
plt.ylabel("Loss")
plt.title("Функции потерь для разных критериев")
plt.legend()
plt.show()


batch_size = 64
epochs = 5
n_features = train_dataset[0][0].shape[0]
n_hidden = 16


criterions = {
    "CE Loss": nn.CrossEntropyLoss(),
    "CE Loss Weighted": nn.CrossEntropyLoss(weight=class_weights),
}

metrics_per_criterion = {name: {"Accuracy": [], "F1-score": []} for name in criterions}

for criterion_name, criterion_class in criterions.items():
    print(f"\nEvaluation for {criterion_name}:")

    model = Model(n_features, n_hidden)
    criterion = criterion_class
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    for epoch in range(epochs):
        for batch_X, batch_y in train_loader:
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y.long())
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)
    y_pred = []
    y_true = []

    with torch.no_grad():
        for batch_X, batch_y in test_loader:
            outputs = model(batch_X)
            _, predicted = torch.max(outputs, 1)
            y_pred.extend(predicted.cpu().numpy())
            y_true.extend(batch_y.cpu().numpy())

    accuracy = accuracy_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred, pos_label=1, average='weighted')

    metrics_per_criterion[criterion_name]["Accuracy"].append(accuracy)
    metrics_per_criterion[criterion_name]["F1-score"].append(f1)

    cm = confusion_matrix(y_true, y_pred)
    print(f"Confusion Matrix:\n{cm}")
    cr = classification_report(y_true, y_pred, target_names=["Class 0", "Class 1"])
    print(f"Classification Report:\n{cr}")

    print(f"Accuracy: {accuracy:.4f}")
    print(f"F1-score: {f1:.4f}")


metrics = ["Accuracy", "F1-score"]
fig, axes = plt.subplots(1, len(metrics), figsize=(20, 5))

for i, metric in enumerate(metrics):
    ax = axes[i]
    values = [metrics_per_criterion[criterion_name][metric][0] for criterion_name in criterions]
    ax.bar(criterions.keys(), values, color=["b", "r"])
    ax.set_title(metric)
    ax.set_ylim(0, 1)
    ax.set_ylabel(metric)
    ax.set_xlabel("criterions")

plt.tight_layout()
plt.show()
    
    '''
    pc.copy(text)
    
    
def gold_A():
    """
    2. Набор данных: regression/gold.csv. Используя библиотеку PyTorch, решите задачу
одновременного предсказания столбцов 'Gold_T-7, Gold_T-14, Gold _Т-22 и Gold T+22 (задача регрессии). Разделите набор данных на обучающее и тестовое множество. Выполните предобработку данных (корректно обработайте случаи категориальных и нечисловых столбцов, при наличии). Сравните несколько различных оптимизаторов и графически продемонстрируйте, как выбор оптимизатора влияет на процесс обучения и результаты на тестовом множестве. (20 баллов)

data = pd.read_csv('/content/drive/MyDrive/Файлы/datasets/regression/gold.csv')
X = data.drop(['Gold_T-7', 'Gold_T-14', 'Gold_T-22', 'Gold_T+22'], axis=1)
y = data[['Gold_T-7', 'Gold_T-14', 'Gold_T-22', 'Gold_T+22']]

X_train, X_test, y_train, y_test = train_test_split(X.to_numpy(), y.to_numpy(), test_size=0.2, random_state=42)

X_train = torch.tensor(X_train, dtype=torch.float32)
y_train = torch.tensor(y_train, dtype=torch.float32)
X_test = torch.tensor(X_test, dtype=torch.float32)
y_test = torch.tensor(y_test, dtype=torch.float32)

train_dataset = TensorDataset(X_train, y_train)
test_dataset = TensorDataset(X_test, y_test)

class Model(nn.Module):
    def __init__(self, n_features, n_hidden):
        super().__init__()
        self.model = nn.Sequential(
            nn.Linear(n_features, n_hidden),
            nn.ReLU(),
            nn.Linear(n_hidden, 4)
        )

    def forward(self, x):
        return self.model(x)
batch_size = 64
epochs = 10
print_every = 1
n_features = train_dataset[0][0].shape[0]
n_hidden = 16


optimizers = {
    "SGD": torch.optim.SGD,
    "Adam": torch.optim.Adam,
    "AdamW": torch.optim.AdamW
}

losses_per_optimizer = {name: [] for name in optimizers}

for opt_name, opt_class in optimizers.items():
    model = Model(n_features, n_hidden)
    criterion = nn.MSELoss()
    optimizer = opt_class(model.parameters(), lr=0.01)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    epoch_losses = []

    for epoch in range(epochs):
        epoch_loss = 0
        for batch_X, batch_y in train_loader:
            # Forward pass
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y)

            # Backward pass
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            epoch_loss += loss.item()

        epoch_losses.append(epoch_loss / len(train_loader))
        if (epoch + 1) % print_every == 0:
            print(f"[{opt_name}] Epoch {epoch+1}/{epochs}, Loss: {epoch_loss / len(train_loader):.4f}")

    losses_per_optimizer[opt_name] = epoch_losses

plt.figure(figsize=(10, 6))
for opt_name, losses in losses_per_optimizer.items():
    plt.plot(range(1, epochs + 1), losses, label=opt_name)
plt.xlabel("Epoch")
plt.ylabel("Loss")
plt.title("Функции потерь для разных оптимизаторов")
plt.legend()
plt.show()
    
from sklearn.metrics import mean_squared_error, mean_absolute_error

optimizers = {
    "SGD": torch.optim.SGD,
    "Adam": torch.optim.Adam,
    "AdamW": torch.optim.AdamW,
}

metrics_per_optimizer = {name: {"MSE": [], "MAE": []} for name in optimizers}

batch_size = 64
epochs = 10
n_features = train_dataset[0][0].shape[0]
n_hidden = 16

for opt_name, opt_class in optimizers.items():
    model = Model(n_features, n_hidden)
    criterion = nn.MSELoss()
    optimizer = opt_class(model.parameters(), lr=0.01)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

    for epoch in range(epochs):
        model.train()
        for batch_X, batch_y in train_loader:
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

    model.eval()
    with torch.no_grad():
        y_true = []
        y_pred = []
        for batch_X, batch_y in test_loader:
            outputs = model(batch_X)
            y_true.extend(batch_y.cpu().numpy())
            y_pred.extend(outputs.cpu().numpy())

    y_true = torch.tensor(y_true)
    y_pred = torch.tensor(y_pred)
    mse = mean_squared_error(y_true, y_pred)
    mae = mean_absolute_error(y_true, y_pred)


    metrics_per_optimizer[opt_name]["MSE"].append(mse)
    metrics_per_optimizer[opt_name]["MAE"].append(mae)

# Plot metrics
fig, axes = plt.subplots(1, 2, figsize=(18, 5))

for i, metric in enumerate(["MSE", "MAE"]):
    ax = axes[i]
    for opt_name, metrics in metrics_per_optimizer.items():
        ax.bar(opt_name, metrics[metric][0], label=opt_name)
    ax.set_title(metric)
    ax.set_ylabel(metric)
    ax.set_xlabel("Optimizer")
    ax.legend()

plt.tight_layout()
plt.show()

    """
    text = '''
data = pd.read_csv('/content/drive/MyDrive/Файлы/datasets/regression/gold.csv')
X = data.drop(['Gold_T-7', 'Gold_T-14', 'Gold_T-22', 'Gold_T+22'], axis=1)
y = data[['Gold_T-7', 'Gold_T-14', 'Gold_T-22', 'Gold_T+22']]

X_train, X_test, y_train, y_test = train_test_split(X.to_numpy(), y.to_numpy(), test_size=0.2, random_state=42)

X_train = torch.tensor(X_train, dtype=torch.float32)
y_train = torch.tensor(y_train, dtype=torch.float32)
X_test = torch.tensor(X_test, dtype=torch.float32)
y_test = torch.tensor(y_test, dtype=torch.float32)

train_dataset = TensorDataset(X_train, y_train)
test_dataset = TensorDataset(X_test, y_test)

class Model(nn.Module):
    def __init__(self, n_features, n_hidden):
        super().__init__()
        self.model = nn.Sequential(
            nn.Linear(n_features, n_hidden),
            nn.ReLU(),
            nn.Linear(n_hidden, 4)
        )

    def forward(self, x):
        return self.model(x)
batch_size = 64
epochs = 10
print_every = 1
n_features = train_dataset[0][0].shape[0]
n_hidden = 16


optimizers = {
    "SGD": torch.optim.SGD,
    "Adam": torch.optim.Adam,
    "AdamW": torch.optim.AdamW
}

losses_per_optimizer = {name: [] for name in optimizers}

for opt_name, opt_class in optimizers.items():
    model = Model(n_features, n_hidden)
    criterion = nn.MSELoss()
    optimizer = opt_class(model.parameters(), lr=0.01)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    epoch_losses = []

    for epoch in range(epochs):
        epoch_loss = 0
        for batch_X, batch_y in train_loader:
            # Forward pass
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y)

            # Backward pass
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            epoch_loss += loss.item()

        epoch_losses.append(epoch_loss / len(train_loader))
        if (epoch + 1) % print_every == 0:
            print(f"[{opt_name}] Epoch {epoch+1}/{epochs}, Loss: {epoch_loss / len(train_loader):.4f}")

    losses_per_optimizer[opt_name] = epoch_losses

plt.figure(figsize=(10, 6))
for opt_name, losses in losses_per_optimizer.items():
    plt.plot(range(1, epochs + 1), losses, label=opt_name)
plt.xlabel("Epoch")
plt.ylabel("Loss")
plt.title("Функции потерь для разных оптимизаторов")
plt.legend()
plt.show()
    
from sklearn.metrics import mean_squared_error, mean_absolute_error

optimizers = {
    "SGD": torch.optim.SGD,
    "Adam": torch.optim.Adam,
    "AdamW": torch.optim.AdamW,
}

metrics_per_optimizer = {name: {"MSE": [], "MAE": []} for name in optimizers}

batch_size = 64
epochs = 10
n_features = train_dataset[0][0].shape[0]
n_hidden = 16

for opt_name, opt_class in optimizers.items():
    model = Model(n_features, n_hidden)
    criterion = nn.MSELoss()
    optimizer = opt_class(model.parameters(), lr=0.01)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

    for epoch in range(epochs):
        model.train()
        for batch_X, batch_y in train_loader:
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

    model.eval()
    with torch.no_grad():
        y_true = []
        y_pred = []
        for batch_X, batch_y in test_loader:
            outputs = model(batch_X)
            y_true.extend(batch_y.cpu().numpy())
            y_pred.extend(outputs.cpu().numpy())

    y_true = torch.tensor(y_true)
    y_pred = torch.tensor(y_pred)
    mse = mean_squared_error(y_true, y_pred)
    mae = mean_absolute_error(y_true, y_pred)


    metrics_per_optimizer[opt_name]["MSE"].append(mse)
    metrics_per_optimizer[opt_name]["MAE"].append(mae)

# Plot metrics
fig, axes = plt.subplots(1, 2, figsize=(18, 5))

for i, metric in enumerate(["MSE", "MAE"]):
    ax = axes[i]
    for opt_name, metrics in metrics_per_optimizer.items():
        ax.bar(opt_name, metrics[metric][0], label=opt_name)
    ax.set_title(metric)
    ax.set_ylabel(metric)
    ax.set_xlabel("Optimizer")
    ax.legend()

plt.tight_layout()
plt.show()
    
    '''
    pc.copy(text)
    
    
def bike_cnt():
    """
    2. Набор данных: regression/bike_cnt.csv. Используя библиотеку PyTorch, решите задачу
предсказания столбца 'cnt' (задача регрессии). Разделите набор данных на обучающее и тестовое множество. Выполните предобработку данных (корректно обработайте случаи категориальных и нечисловых столбцов, при наличии). Отобразите графики значений функции потерь и метрики R^2 на обучающем множестве по эпохам. Рассчитайте значение метрики R^2 на тестовом множестве. Добавьте в модель слои BatchNorm1d и графически продемонстрируйте, как это влияет на процесс обучения и результаты на тестовом множестве. (20 баллов)

data = pd.read_csv('/content/drive/MyDrive/Файлы/datasets/regression/bike_cnt.csv')
X = data.drop(['instant', 'dteday', 'cnt'], axis=1)
y = data['cnt']

scaler = StandardScaler()
y_transformed = scaler.fit_transform(np.array(y).reshape(-1, 1))

X_train, X_test, y_train, y_test = train_test_split(X.to_numpy(), y.to_numpy(), test_size=0.2, random_state=42)

X_train = torch.tensor(X_train, dtype=torch.float32)
y_train = torch.tensor(y_train, dtype=torch.float32)
X_test = torch.tensor(X_test, dtype=torch.float32)
y_test = torch.tensor(y_test, dtype=torch.float32)

train_dataset = TensorDataset(X_train, y_train)
test_dataset = TensorDataset(X_test, y_test)

class Model(nn.Module):
    def __init__(self, n_features, n_hidden):
        super().__init__()
        self.model = nn.Sequential(

            nn.Linear(n_features, n_hidden),
            nn.ReLU(),

            nn.Linear(n_hidden, n_hidden),
            nn.ReLU(),
            nn.Linear(n_hidden, 1)
        )

    def forward(self, x):
        return self.model(x)
        
class ModelBatchNorm(nn.Module):
    def __init__(self, n_features, n_hidden):
        super().__init__()
        self.model = nn.Sequential(

            nn.Linear(n_features, n_hidden),
            nn.BatchNorm1d(n_hidden),
            nn.ReLU(),

            nn.Linear(n_hidden, n_hidden),
            nn.BatchNorm1d(n_hidden),
            nn.ReLU(),
            nn.Linear(n_hidden, 1)
        )

    def forward(self, x):
        return self.model(x)
        
        
batch_size = 64
epochs = 5
print_every = 1
n_features = train_dataset[0][0].shape[0]
n_hidden = 16

models = {
    "No BatchNorm": Model(n_features, n_hidden),
    "BatchNorm": ModelBatchNorm(n_features, n_hidden),
}

losses_per_model = {name: [] for name in models}

for model_name, model_class in models.items():
    model = model_class
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    epoch_losses = []

    for epoch in range(epochs):
        epoch_loss = 0
        for batch_X, batch_y in train_loader:
            # Forward pass
            batch_y = batch_y.unsqueeze(1)
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y)

            # Backward pass
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            epoch_loss += loss.item()

        epoch_losses.append(epoch_loss / len(train_loader))
        if (epoch + 1) % print_every == 0:
            print(f"[{model_name}] Epoch {epoch+1}/{epochs}, Loss: {epoch_loss / len(train_loader):.4f}")

    losses_per_model[model_name] = epoch_losses

plt.figure(figsize=(10, 6))
for model_name, losses in losses_per_model.items():
    plt.plot(range(1, epochs + 1), losses, label=model_name)
plt.xlabel("Epoch")
plt.ylabel("Loss")
plt.title("Функции потерь для разных моделей")
plt.legend()
plt.show()


from sklearn.metrics import r2_score

batch_size = 64
epochs = 5
print_every = 1
n_features = train_dataset[0][0].shape[0]
n_hidden = 16

models = {
    "No BatchNorm": Model(n_features, n_hidden),
    "BatchNorm": ModelBatchNorm(n_features, n_hidden),
}

losses_per_model = {name: [] for name in models}
r2_per_model = {name: [] for name in models}

for model_name, model_class in models.items():
    model = model_class
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    epoch_losses = []
    epoch_r2_scores = []

    for epoch in range(epochs):
        epoch_loss = 0
        all_outputs = []
        all_targets = []

        for batch_X, batch_y in train_loader:
            # Forward pass
            batch_y = batch_y.unsqueeze(1)
            outputs = model(batch_X)

            all_outputs.append(outputs.detach().numpy())
            all_targets.append(batch_y.detach().numpy())

            loss = criterion(outputs, batch_y)

            # Backward pass
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            epoch_loss += loss.item()

        all_outputs = np.vstack(all_outputs)
        all_targets = np.vstack(all_targets)
        r2 = r2_score(all_targets, all_outputs)
        epoch_r2_scores.append(r2)

        epoch_losses.append(epoch_loss / len(train_loader))
        if (epoch + 1) % print_every == 0:
            print(f"[{model_name}] Epoch {epoch+1}/{epochs}, Loss: {epoch_loss / len(train_loader):.4f}, R²: {r2:.4f}")

    losses_per_model[model_name] = epoch_losses
    r2_per_model[model_name] = epoch_r2_scores


for model_name, losses in losses_per_model.items():
    plt.plot(range(1, epochs + 1), losses, label=f"{model_name} - Loss")
plt.xlabel("Epoch")
plt.ylabel("Loss")
plt.title("Функции потерь для разных моделей")
plt.legend()
plt.show()


for model_name, r2_scores in r2_per_model.items():
    plt.plot(range(1, epochs + 1), r2_scores, label=f"{model_name} - R²")
plt.xlabel("Epoch")
plt.ylabel("R² Score")
plt.title("R² для разных моделей")
plt.legend()
plt.show()

batch_size = 64
epochs = 5
n_features = train_dataset[0][0].shape[0]
n_hidden = 16

models = {
    "No BatchNorm": Model(n_features, n_hidden),
    "BatchNorm": ModelBatchNorm(n_features, n_hidden),
}

metrics_per_model = {name: {"R²": []} for name in models}

for model_name, model_class in models.items():
    print(f"\nEvaluation for {model_name}:")

    model = model_class
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    for epoch in range(epochs):
        for batch_X, batch_y in train_loader:
            batch_y = batch_y.unsqueeze(1)
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

    # Evaluation loop
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)
    y_pred = []
    y_true = []

    with torch.no_grad():
        for batch_X, batch_y in test_loader:
            batch_y = batch_y.unsqueeze(1)
            outputs = model(batch_X)
            y_pred.extend(outputs.cpu().numpy())
            y_true.extend(batch_y.cpu().numpy())

    r2 = r2_score(y_true, y_pred)
    metrics_per_model[model_name]["R²"].append(r2)

    print(f"R² Score: {r2:.4f}")

r2_scores = [metrics_per_model[model_name]["R²"][0] for model_name in models]
plt.figure(figsize=(10, 6))
plt.bar(models.keys(), r2_scores, color=["b", "r"])
plt.title("R² Scores for Models")
plt.ylim(0, 1)
plt.ylabel("R² Score")
plt.xlabel("Models")
plt.show()


    """
    
    text = '''
data = pd.read_csv('/content/drive/MyDrive/Файлы/datasets/regression/bike_cnt.csv')
X = data.drop(['instant', 'dteday', 'cnt'], axis=1)
y = data['cnt']

scaler = StandardScaler()
y_transformed = scaler.fit_transform(np.array(y).reshape(-1, 1))

X_train, X_test, y_train, y_test = train_test_split(X.to_numpy(), y.to_numpy(), test_size=0.2, random_state=42)

X_train = torch.tensor(X_train, dtype=torch.float32)
y_train = torch.tensor(y_train, dtype=torch.float32)
X_test = torch.tensor(X_test, dtype=torch.float32)
y_test = torch.tensor(y_test, dtype=torch.float32)

train_dataset = TensorDataset(X_train, y_train)
test_dataset = TensorDataset(X_test, y_test)

class Model(nn.Module):
    def __init__(self, n_features, n_hidden):
        super().__init__()
        self.model = nn.Sequential(

            nn.Linear(n_features, n_hidden),
            nn.ReLU(),

            nn.Linear(n_hidden, n_hidden),
            nn.ReLU(),
            nn.Linear(n_hidden, 1)
        )

    def forward(self, x):
        return self.model(x)
        
class ModelBatchNorm(nn.Module):
    def __init__(self, n_features, n_hidden):
        super().__init__()
        self.model = nn.Sequential(

            nn.Linear(n_features, n_hidden),
            nn.BatchNorm1d(n_hidden),
            nn.ReLU(),

            nn.Linear(n_hidden, n_hidden),
            nn.BatchNorm1d(n_hidden),
            nn.ReLU(),
            nn.Linear(n_hidden, 1)
        )

    def forward(self, x):
        return self.model(x)
        
        
batch_size = 64
epochs = 5
print_every = 1
n_features = train_dataset[0][0].shape[0]
n_hidden = 16

models = {
    "No BatchNorm": Model(n_features, n_hidden),
    "BatchNorm": ModelBatchNorm(n_features, n_hidden),
}

losses_per_model = {name: [] for name in models}

for model_name, model_class in models.items():
    model = model_class
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    epoch_losses = []

    for epoch in range(epochs):
        epoch_loss = 0
        for batch_X, batch_y in train_loader:
            # Forward pass
            batch_y = batch_y.unsqueeze(1)
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y)

            # Backward pass
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            epoch_loss += loss.item()

        epoch_losses.append(epoch_loss / len(train_loader))
        if (epoch + 1) % print_every == 0:
            print(f"[{model_name}] Epoch {epoch+1}/{epochs}, Loss: {epoch_loss / len(train_loader):.4f}")

    losses_per_model[model_name] = epoch_losses

plt.figure(figsize=(10, 6))
for model_name, losses in losses_per_model.items():
    plt.plot(range(1, epochs + 1), losses, label=model_name)
plt.xlabel("Epoch")
plt.ylabel("Loss")
plt.title("Функции потерь для разных моделей")
plt.legend()
plt.show()


from sklearn.metrics import r2_score

batch_size = 64
epochs = 5
print_every = 1
n_features = train_dataset[0][0].shape[0]
n_hidden = 16

models = {
    "No BatchNorm": Model(n_features, n_hidden),
    "BatchNorm": ModelBatchNorm(n_features, n_hidden),
}

losses_per_model = {name: [] for name in models}
r2_per_model = {name: [] for name in models}

for model_name, model_class in models.items():
    model = model_class
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    epoch_losses = []
    epoch_r2_scores = []

    for epoch in range(epochs):
        epoch_loss = 0
        all_outputs = []
        all_targets = []

        for batch_X, batch_y in train_loader:
            # Forward pass
            batch_y = batch_y.unsqueeze(1)
            outputs = model(batch_X)

            all_outputs.append(outputs.detach().numpy())
            all_targets.append(batch_y.detach().numpy())

            loss = criterion(outputs, batch_y)

            # Backward pass
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            epoch_loss += loss.item()

        all_outputs = np.vstack(all_outputs)
        all_targets = np.vstack(all_targets)
        r2 = r2_score(all_targets, all_outputs)
        epoch_r2_scores.append(r2)

        epoch_losses.append(epoch_loss / len(train_loader))
        if (epoch + 1) % print_every == 0:
            print(f"[{model_name}] Epoch {epoch+1}/{epochs}, Loss: {epoch_loss / len(train_loader):.4f}, R²: {r2:.4f}")

    losses_per_model[model_name] = epoch_losses
    r2_per_model[model_name] = epoch_r2_scores


for model_name, losses in losses_per_model.items():
    plt.plot(range(1, epochs + 1), losses, label=f"{model_name} - Loss")
plt.xlabel("Epoch")
plt.ylabel("Loss")
plt.title("Функции потерь для разных моделей")
plt.legend()
plt.show()


for model_name, r2_scores in r2_per_model.items():
    plt.plot(range(1, epochs + 1), r2_scores, label=f"{model_name} - R²")
plt.xlabel("Epoch")
plt.ylabel("R² Score")
plt.title("R² для разных моделей")
plt.legend()
plt.show()

batch_size = 64
epochs = 5
n_features = train_dataset[0][0].shape[0]
n_hidden = 16

models = {
    "No BatchNorm": Model(n_features, n_hidden),
    "BatchNorm": ModelBatchNorm(n_features, n_hidden),
}

metrics_per_model = {name: {"R²": []} for name in models}

for model_name, model_class in models.items():
    print(f"\nEvaluation for {model_name}:")

    model = model_class
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    for epoch in range(epochs):
        for batch_X, batch_y in train_loader:
            batch_y = batch_y.unsqueeze(1)
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

    # Evaluation loop
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)
    y_pred = []
    y_true = []

    with torch.no_grad():
        for batch_X, batch_y in test_loader:
            batch_y = batch_y.unsqueeze(1)
            outputs = model(batch_X)
            y_pred.extend(outputs.cpu().numpy())
            y_true.extend(batch_y.cpu().numpy())

    r2 = r2_score(y_true, y_pred)
    metrics_per_model[model_name]["R²"].append(r2)

    print(f"R² Score: {r2:.4f}")

r2_scores = [metrics_per_model[model_name]["R²"][0] for model_name in models]
plt.figure(figsize=(10, 6))
plt.bar(models.keys(), r2_scores, color=["b", "r"])
plt.title("R² Scores for Models")
plt.ylim(0, 1)
plt.ylabel("R² Score")
plt.xlabel("Models")
plt.show()
    
    '''
    pc.copy(text)
    

def sign_lang_pokhozhie():
    """
3. Набор данных: images/sign_language.zip. Реализовав сверточную нейронную сеть при
помощи библиотеки PyTorch, решите задачу классификации изображений. Разделите набор данных на обучающее и тестовое множество. Выполните предобработку данных (приведите изображения к одному размеру, нормализуйте и преобразуйте изображения в тензоры). Отобразите confusion matrix и classification report, рассчитанные на основе тестового множества. Выберите один пример из тестового множества, для которого модель ошиблась. Найдите несколько наиболее похожих на данное изображений на основе векторов скрытых представлений, полученных сетью. Визуализируйте оригинальное изображение и найденные похожие изображения. (20 баллов)

data_dir = "/content/sign_language/sign_language"

# Предобработка изображений
transform = transforms.Compose([
    transforms.Resize(100),
    transforms.ToTensor(),
    transforms.Normalize(mean=(0.5, 0.5, 0.5), std=(0.5, 0.5, 0.5))
])

# Загрузка данных
full_dataset = ImageFolder(data_dir, transform=transform)

train_size = int(0.7 * len(full_dataset))
test_size = len(full_dataset) - train_size
train_dataset, test_dataset = torch.utils.data.random_split(full_dataset, [train_size, test_size])

plt.imshow(full_dataset[0][0].permute(1, 2, 0))

train_dataset[0][0].shape

class CNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv2d(3, 6, 5)
        self.pool = nn.MaxPool2d(2, 2)
        self.conv2 = nn.Conv2d(6, 16, 5)
        self.fc1 = nn.Linear(16 * 22 * 22, 120)
        self.fc2 = nn.Linear(120, 84)
        self.fc3 = nn.Linear(84, 10)

    def forward(self, x, return_features=False):
        x = self.pool(F.relu(self.conv1(x)))
        x = self.pool(F.relu(self.conv2(x)))
        features = torch.flatten(x, 1)
        x = F.relu(self.fc1(features))
        x = F.relu(self.fc2(x))
        x = self.fc3(x)
        if return_features:
            return x, features
        return x
        
batch_size = 64
num_epochs = 5
print_every = 1
num_classes = len(full_dataset.classes)


model = CNN()
criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=batch_size)

epoch_losses = []

for epoch in range(num_epochs):
    model.train()
    epoch_loss = 0

    for i, data in enumerate(train_loader, 0):
        inputs, labels = data

        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        epoch_loss += loss.item()

    epoch_losses.append(epoch_loss / len(train_loader))

    if (epoch + 1) % print_every == 0:
        print(f"Epoch {epoch+1}/{num_epochs}, Loss: {epoch_loss / len(train_loader):.4f}")

plt.figure(figsize=(10, 6))
plt.plot(range(1, num_epochs + 1), epoch_losses, label="Training Loss")
plt.xlabel("Epoch")
plt.ylabel("Loss")
plt.title("Training Loss Curve")
plt.legend()
plt.show() 

model.eval()
correct = 0
total = 0
all_preds = []
all_labels = []

with torch.no_grad():
    for data in test_loader:
        inputs, labels = data
        outputs = model(inputs)
        _, predicted = torch.max(outputs.data, 1)
        total += labels.size(0)
        correct += (predicted == labels).sum().item()

        all_preds.extend(predicted.cpu().numpy())
        all_labels.extend(labels.cpu().numpy())

print("\nClassification Report:")
print(classification_report(all_labels, all_preds, target_names=full_dataset.classes))

conf_matrix = confusion_matrix(all_labels, all_preds)
print("\nConfusion Matrix:")
print(conf_matrix)

plt.figure(figsize=(10, 8))
sns.heatmap(conf_matrix, annot=True, fmt="d", cmap="Blues", xticklabels=full_dataset.classes, yticklabels=full_dataset.classes)
plt.xlabel("Predicted Labels")
plt.ylabel("True Labels")
plt.title("Confusion Matrix")
plt.show()


model.eval()

with torch.no_grad():
    embeddings = torch.cat([model(inputs) for inputs, _ in test_loader])
    labels = torch.cat([labels for _, labels in test_loader])
    y_pred = embeddings.argmax(dim=1)

miss_ind = (y_pred != labels).nonzero().squeeze()
miss_embed = embeddings[miss_ind[0]].unsqueeze(0)

sim_ind = cosine_similarity(miss_embed, embeddings).argsort()[0][-5:-1][::-1]

plt.figure(figsize=(15, 10))
plt.subplot(1, 5, 1)
plt.imshow(full_dataset[miss_ind[0]][0].permute(1, 2, 0).numpy() / 2 + 0.5)
plt.title(f"True: {full_dataset.classes[labels[miss_ind[0]]]}\nPred: {full_dataset.classes[y_pred[miss_ind[0]]]}")

for i, idx in enumerate(sim_ind[1:]):
    plt.subplot(1, 5, i + 2)
    plt.imshow(full_dataset[idx][0].permute(1, 2, 0).numpy() / 2 + 0.5)

plt.tight_layout()
plt.show()
    """
    
    text = '''
data_dir = "/content/sign_language/sign_language"

# Предобработка изображений
transform = transforms.Compose([
    transforms.Resize(100),
    transforms.ToTensor(),
    transforms.Normalize(mean=(0.5, 0.5, 0.5), std=(0.5, 0.5, 0.5))
])

# Загрузка данных
full_dataset = ImageFolder(data_dir, transform=transform)

train_size = int(0.7 * len(full_dataset))
test_size = len(full_dataset) - train_size
train_dataset, test_dataset = torch.utils.data.random_split(full_dataset, [train_size, test_size])

plt.imshow(full_dataset[0][0].permute(1, 2, 0))

train_dataset[0][0].shape

class CNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv2d(3, 6, 5)
        self.pool = nn.MaxPool2d(2, 2)
        self.conv2 = nn.Conv2d(6, 16, 5)
        self.fc1 = nn.Linear(16 * 22 * 22, 120)
        self.fc2 = nn.Linear(120, 84)
        self.fc3 = nn.Linear(84, 10)

    def forward(self, x, return_features=False):
        x = self.pool(F.relu(self.conv1(x)))
        x = self.pool(F.relu(self.conv2(x)))
        features = torch.flatten(x, 1)
        x = F.relu(self.fc1(features))
        x = F.relu(self.fc2(x))
        x = self.fc3(x)
        if return_features:
            return x, features
        return x
        
batch_size = 64
num_epochs = 5
print_every = 1
num_classes = len(full_dataset.classes)


model = CNN()
criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=batch_size)

epoch_losses = []

for epoch in range(num_epochs):
    model.train()
    epoch_loss = 0

    for i, data in enumerate(train_loader, 0):
        inputs, labels = data

        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        epoch_loss += loss.item()

    epoch_losses.append(epoch_loss / len(train_loader))

    if (epoch + 1) % print_every == 0:
        print(f"Epoch {epoch+1}/{num_epochs}, Loss: {epoch_loss / len(train_loader):.4f}")

plt.figure(figsize=(10, 6))
plt.plot(range(1, num_epochs + 1), epoch_losses, label="Training Loss")
plt.xlabel("Epoch")
plt.ylabel("Loss")
plt.title("Training Loss Curve")
plt.legend()
plt.show() 

model.eval()
correct = 0
total = 0
all_preds = []
all_labels = []

with torch.no_grad():
    for data in test_loader:
        inputs, labels = data
        outputs = model(inputs)
        _, predicted = torch.max(outputs.data, 1)
        total += labels.size(0)
        correct += (predicted == labels).sum().item()

        all_preds.extend(predicted.cpu().numpy())
        all_labels.extend(labels.cpu().numpy())

print("\nClassification Report:")
print(classification_report(all_labels, all_preds, target_names=full_dataset.classes))

conf_matrix = confusion_matrix(all_labels, all_preds)
print("\nConfusion Matrix:")
print(conf_matrix)

plt.figure(figsize=(10, 8))
sns.heatmap(conf_matrix, annot=True, fmt="d", cmap="Blues", xticklabels=full_dataset.classes, yticklabels=full_dataset.classes)
plt.xlabel("Predicted Labels")
plt.ylabel("True Labels")
plt.title("Confusion Matrix")
plt.show()


model.eval()

with torch.no_grad():
    embeddings = torch.cat([model(inputs) for inputs, _ in test_loader])
    labels = torch.cat([labels for _, labels in test_loader])
    y_pred = embeddings.argmax(dim=1)

miss_ind = (y_pred != labels).nonzero().squeeze()
miss_embed = embeddings[miss_ind[0]].unsqueeze(0)

sim_ind = cosine_similarity(miss_embed, embeddings).argsort()[0][-5:-1][::-1]

plt.figure(figsize=(15, 10))
plt.subplot(1, 5, 1)
plt.imshow(full_dataset[miss_ind[0]][0].permute(1, 2, 0).numpy() / 2 + 0.5)
plt.title(f"True: {full_dataset.classes[labels[miss_ind[0]]]}\nPred: {full_dataset.classes[y_pred[miss_ind[0]]]}")

for i, idx in enumerate(sim_ind[1:]):
    plt.subplot(1, 5, i + 2)
    plt.imshow(full_dataset[idx][0].permute(1, 2, 0).numpy() / 2 + 0.5)

plt.tight_layout()
plt.show()
    '''
    pc.copy(text)

    
    
def sign_lang_blocks():
    """
3. Набор данных: images/sign_language.zip. Реализовав сверточную нейронную сеть при
помощи библиотеки Py Torch, решите задачу классификации изображений. Разделите набор данных на обучающее и тестовое множество. Выполните предобработку данных (приведите изображения к одному размеру, нормализуйте и преобразуйте изображения в тензоры). Графически отобразите, как качество на тестовом множестве (micro F1) зависит от количества сверточных блоков (свертка, активация, пулинг). (20 баллов)

data_dir = "/content/sign_language/sign_language"

# Предобработка изображений
transform = transforms.Compose([
    transforms.Resize(100),
    transforms.ToTensor(),
    transforms.Normalize(mean=(0.5, 0.5, 0.5), std=(0.5, 0.5, 0.5))
])

# Загрузка данных
full_dataset = ImageFolder(data_dir, transform=transform)

train_size = int(0.7 * len(full_dataset))
test_size = len(full_dataset) - train_size
train_dataset, test_dataset = torch.utils.data.random_split(full_dataset, [train_size, test_size])

class CNN(nn.Module):
    def __init__(self, num_conv_blocks):
        super().__init__()
        self.conv_blocks = nn.ModuleList()
        in_channels = 3
        out_channels = 6
        for _ in range(num_conv_blocks):
            self.conv_blocks.append(nn.Sequential(
                nn.Conv2d(in_channels, out_channels, kernel_size=5, padding=2),
                nn.ReLU(),
                nn.MaxPool2d(kernel_size=2, stride=2)
            ))
            in_channels = out_channels
            out_channels *= 2
        self.fc = nn.Sequential(
            nn.LazyLinear(120),
            nn.ReLU(),
            nn.Linear(120, 10)
        )

    def forward(self, x):
        for block in self.conv_blocks:
            x = block(x)
        x = torch.flatten(x, 1)
        x = self.fc(x)
        return x
        
batch_size = 64
num_epochs = 5
print_every = 1
num_classes = len(full_dataset.classes)


train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=batch_size)

def train_and_evaluate(model, train_loader, test_loader, num_epochs=10):
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    for epoch in range(num_epochs):
        model.train()
        for inputs, labels in train_loader:
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

    # Evaluate on test set
    model.eval()
    y_true, y_pred = [], []
    with torch.no_grad():
        for inputs, labels in test_loader:
            outputs = model(inputs)
            _, predicted = torch.max(outputs, 1)
            y_true.extend(labels.numpy())
            y_pred.extend(predicted.numpy())

    # Calculate micro F1 score
    return f1_score(y_true, y_pred, average="micro")

# Experiment with different numbers of convolutional blocks
num_conv_blocks_list = [1, 2, 3, 4]
micro_f1_scores = [train_and_evaluate(CNN(num_conv_blocks), train_loader, test_loader) for num_conv_blocks in num_conv_blocks_list]

# Plot results
plt.figure(figsize=(10, 6))
plt.plot(num_conv_blocks_list, micro_f1_scores, marker="o", linestyle="-", color="b")
plt.xlabel("Number of Convolutional Blocks")
plt.ylabel("Micro F1 Score")
plt.title("Micro F1 Score vs Number of Convolutional Blocks")
plt.grid(True)
plt.show()


    """
    text = '''
    
data_dir = "/content/sign_language/sign_language"

# Предобработка изображений
transform = transforms.Compose([
    transforms.Resize(100),
    transforms.ToTensor(),
    transforms.Normalize(mean=(0.5, 0.5, 0.5), std=(0.5, 0.5, 0.5))
])

# Загрузка данных
full_dataset = ImageFolder(data_dir, transform=transform)

train_size = int(0.7 * len(full_dataset))
test_size = len(full_dataset) - train_size
train_dataset, test_dataset = torch.utils.data.random_split(full_dataset, [train_size, test_size])

class CNN(nn.Module):
    def __init__(self, num_conv_blocks):
        super().__init__()
        self.conv_blocks = nn.ModuleList()
        in_channels = 3
        out_channels = 6
        for _ in range(num_conv_blocks):
            self.conv_blocks.append(nn.Sequential(
                nn.Conv2d(in_channels, out_channels, kernel_size=5, padding=2),
                nn.ReLU(),
                nn.MaxPool2d(kernel_size=2, stride=2)
            ))
            in_channels = out_channels
            out_channels *= 2
        self.fc = nn.Sequential(
            nn.LazyLinear(120),
            nn.ReLU(),
            nn.Linear(120, 10)
        )

    def forward(self, x):
        for block in self.conv_blocks:
            x = block(x)
        x = torch.flatten(x, 1)
        x = self.fc(x)
        return x
        
batch_size = 64
num_epochs = 5
print_every = 1
num_classes = len(full_dataset.classes)


train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=batch_size)

def train_and_evaluate(model, train_loader, test_loader, num_epochs=10):
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    for epoch in range(num_epochs):
        model.train()
        for inputs, labels in train_loader:
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

    # Evaluate on test set
    model.eval()
    y_true, y_pred = [], []
    with torch.no_grad():
        for inputs, labels in test_loader:
            outputs = model(inputs)
            _, predicted = torch.max(outputs, 1)
            y_true.extend(labels.numpy())
            y_pred.extend(predicted.numpy())

    # Calculate micro F1 score
    return f1_score(y_true, y_pred, average="micro")

# Experiment with different numbers of convolutional blocks
num_conv_blocks_list = [1, 2, 3, 4]
micro_f1_scores = [train_and_evaluate(CNN(num_conv_blocks), train_loader, test_loader) for num_conv_blocks in num_conv_blocks_list]

# Plot results
plt.figure(figsize=(10, 6))
plt.plot(num_conv_blocks_list, micro_f1_scores, marker="o", linestyle="-", color="b")
plt.xlabel("Number of Convolutional Blocks")
plt.ylabel("Micro F1 Score")
plt.title("Micro F1 Score vs Number of Convolutional Blocks")
plt.grid(True)
plt.show()
    '''
    pc.copy(text)
    

def sign_lang_PCA():
    """
3. Набор данных: images/sign _language.zip. Реализовав сверточную нейронную сеть при
помощи pytorch. Разделите набор данных на обучающее и тестовое множество.Выполните предобработку данных (приведите изображения к одному размеру, нормализуйте и преобразуйте изображения в тензоры). Отобразите графики значений функции потерь по эпохам на обучающем множестве. Отобразите confusion matrix и classification report, рассчитанные на основе тестового множества. Уменьшите размерность скрытых представлений с помощью РСА и визуализируйте полученные представления, раскрасив точки в соответствии с классами. (20 баллов)

data_dir = "/content/sign_language/sign_language"

# Предобработка изображений
transform = transforms.Compose([
    transforms.Resize(100),
    transforms.ToTensor(),
    transforms.Normalize(mean=(0.5, 0.5, 0.5), std=(0.5, 0.5, 0.5))
])

# Загрузка данных
full_dataset = ImageFolder(data_dir, transform=transform)

train_size = int(0.7 * len(full_dataset))
test_size = len(full_dataset) - train_size
train_dataset, test_dataset = torch.utils.data.random_split(full_dataset, [train_size, test_size])

class CNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv2d(3, 6, 5)
        self.pool = nn.MaxPool2d(2, 2)
        self.conv2 = nn.Conv2d(6, 16, 5)
        self.fc1 = nn.Linear(16 * 22 * 22, 120)
        self.fc2 = nn.Linear(120, 84)
        self.fc3 = nn.Linear(84, 10)

    def forward(self, x, return_features=False):
        x = self.pool(F.relu(self.conv1(x)))
        x = self.pool(F.relu(self.conv2(x)))
        features = torch.flatten(x, 1)
        x = F.relu(self.fc1(features))
        x = F.relu(self.fc2(x))
        x = self.fc3(x)
        if return_features:
            return x, features
        return x
        
batch_size = 64
num_epochs = 5
print_every = 1
num_classes = len(full_dataset.classes)

model = CNN()
criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=batch_size)

epoch_losses = []

for epoch in range(num_epochs):
    model.train()
    epoch_loss = 0

    for i, data in enumerate(train_loader, 0):
        inputs, labels = data

        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        epoch_loss += loss.item()

    epoch_losses.append(epoch_loss / len(train_loader))

    if (epoch + 1) % print_every == 0:
        print(f"Epoch {epoch+1}/{num_epochs}, Loss: {epoch_loss / len(train_loader):.4f}")

plt.figure(figsize=(10, 6))
plt.plot(range(1, num_epochs + 1), epoch_losses, label="Training Loss")
plt.xlabel("Epoch")
plt.ylabel("Loss")
plt.title("Training Loss Curve")
plt.legend()
plt.show()

model.eval()
correct = 0
total = 0
all_preds = []
all_labels = []

with torch.no_grad():
    for data in test_loader:
        inputs, labels = data
        outputs = model(inputs)
        _, predicted = torch.max(outputs.data, 1)
        total += labels.size(0)
        correct += (predicted == labels).sum().item()

        all_preds.extend(predicted.cpu().numpy())
        all_labels.extend(labels.cpu().numpy())

print("\nClassification Report:")
print(classification_report(all_labels, all_preds, target_names=full_dataset.classes))

conf_matrix = confusion_matrix(all_labels, all_preds)
print("\nConfusion Matrix:")
print(conf_matrix)

plt.figure(figsize=(10, 8))
sns.heatmap(conf_matrix, annot=True, fmt="d", cmap="Blues", xticklabels=full_dataset.classes, yticklabels=full_dataset.classes)
plt.xlabel("Predicted Labels")
plt.ylabel("True Labels")
plt.title("Confusion Matrix")
plt.show()

embeddings = []
true_labels = []
with torch.no_grad():
    for inputs, labels in test_loader:
        _, features = model(inputs, return_features=True)
        embeddings.append(features)
        true_labels.append(labels)

embeddings = torch.cat(embeddings, dim=0).numpy()
true_labels = torch.cat(true_labels, dim=0).numpy()

pca = PCA(n_components=2)
embeddings_2d = pca.fit_transform(embeddings)

plt.figure(figsize=(10, 8))
scatter = plt.scatter(embeddings_2d[:, 0], embeddings_2d[:, 1], c=true_labels, cmap="tab10", alpha=0.6)
plt.colorbar(scatter, ticks=range(num_classes), label="Class")
plt.xlabel("PCA Component 1")
plt.ylabel("PCA Component 2")
plt.title("2D PCA Visualization of Hidden Representations")
plt.show()

    """
    text = '''
    
data_dir = "/content/sign_language/sign_language"

# Предобработка изображений
transform = transforms.Compose([
    transforms.Resize(100),
    transforms.ToTensor(),
    transforms.Normalize(mean=(0.5, 0.5, 0.5), std=(0.5, 0.5, 0.5))
])

# Загрузка данных
full_dataset = ImageFolder(data_dir, transform=transform)

train_size = int(0.7 * len(full_dataset))
test_size = len(full_dataset) - train_size
train_dataset, test_dataset = torch.utils.data.random_split(full_dataset, [train_size, test_size])

class CNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv2d(3, 6, 5)
        self.pool = nn.MaxPool2d(2, 2)
        self.conv2 = nn.Conv2d(6, 16, 5)
        self.fc1 = nn.Linear(16 * 22 * 22, 120)
        self.fc2 = nn.Linear(120, 84)
        self.fc3 = nn.Linear(84, 10)

    def forward(self, x, return_features=False):
        x = self.pool(F.relu(self.conv1(x)))
        x = self.pool(F.relu(self.conv2(x)))
        features = torch.flatten(x, 1)
        x = F.relu(self.fc1(features))
        x = F.relu(self.fc2(x))
        x = self.fc3(x)
        if return_features:
            return x, features
        return x
        
batch_size = 64
num_epochs = 5
print_every = 1
num_classes = len(full_dataset.classes)

model = CNN()
criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=batch_size)

epoch_losses = []

for epoch in range(num_epochs):
    model.train()
    epoch_loss = 0

    for i, data in enumerate(train_loader, 0):
        inputs, labels = data

        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        epoch_loss += loss.item()

    epoch_losses.append(epoch_loss / len(train_loader))

    if (epoch + 1) % print_every == 0:
        print(f"Epoch {epoch+1}/{num_epochs}, Loss: {epoch_loss / len(train_loader):.4f}")

plt.figure(figsize=(10, 6))
plt.plot(range(1, num_epochs + 1), epoch_losses, label="Training Loss")
plt.xlabel("Epoch")
plt.ylabel("Loss")
plt.title("Training Loss Curve")
plt.legend()
plt.show()

model.eval()
correct = 0
total = 0
all_preds = []
all_labels = []

with torch.no_grad():
    for data in test_loader:
        inputs, labels = data
        outputs = model(inputs)
        _, predicted = torch.max(outputs.data, 1)
        total += labels.size(0)
        correct += (predicted == labels).sum().item()

        all_preds.extend(predicted.cpu().numpy())
        all_labels.extend(labels.cpu().numpy())

print("\nClassification Report:")
print(classification_report(all_labels, all_preds, target_names=full_dataset.classes))

conf_matrix = confusion_matrix(all_labels, all_preds)
print("\nConfusion Matrix:")
print(conf_matrix)

plt.figure(figsize=(10, 8))
sns.heatmap(conf_matrix, annot=True, fmt="d", cmap="Blues", xticklabels=full_dataset.classes, yticklabels=full_dataset.classes)
plt.xlabel("Predicted Labels")
plt.ylabel("True Labels")
plt.title("Confusion Matrix")
plt.show()

embeddings = []
true_labels = []
with torch.no_grad():
    for inputs, labels in test_loader:
        _, features = model(inputs, return_features=True)
        embeddings.append(features)
        true_labels.append(labels)

embeddings = torch.cat(embeddings, dim=0).numpy()
true_labels = torch.cat(true_labels, dim=0).numpy()

pca = PCA(n_components=2)
embeddings_2d = pca.fit_transform(embeddings)

plt.figure(figsize=(10, 8))
scatter = plt.scatter(embeddings_2d[:, 0], embeddings_2d[:, 1], c=true_labels, cmap="tab10", alpha=0.6)
plt.colorbar(scatter, ticks=range(num_classes), label="Class")
plt.xlabel("PCA Component 1")
plt.ylabel("PCA Component 2")
plt.title("2D PCA Visualization of Hidden Representations")
plt.show()
    '''
    pc.copy(text)
    
    
def clothes_multi():
    """
3. Набор данных: images/clothes_multi.zip. Реализовав сверточную нейронную сеть при
помощи библиотеки PyTorch, решите задачу множественной (multi-label) классификации изображений. Для каждого изображения модель должна предсказывать два класса: цвет и предмет одежды. Разделите набор данных на обучающее и тестовое множество. Выполните предобработку данных (приведите изображения к одному размеру, нормализуйте и преобразуйте в тензоры). Выведите итоговое значение F1 обучающем множестве и F1 на тестовом множестве. (20 баллов)

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, random_split
from torchvision import transforms, datasets
from sklearn.metrics import f1_score
import numpy as np
from tqdm import tqdm
import os
import glob
from PIL import Image

# Data preparation
data_dir = "/content/clothes_multi/clothes_multi"

# Transformation for the dataset
transform = transforms.Compose([
    transforms.Resize((100, 100)),  # Resize images to 100x100
    transforms.ToTensor(),          # Convert images to tensors
    transforms.Normalize(mean=(0.5, 0.5, 0.5), std=(0.5, 0.5, 0.5))  # Normalize
])

# Dataset
class MultiLabelDataset(Dataset):
    def __init__(self, data_dir, transform):
        self.image_paths = glob.glob(f"{data_dir}/*/*")
        self.transform = transform
        self.colors = sorted({p.split("/")[-2].split("_")[0] for p in self.image_paths})
        self.items = sorted({p.split("/")[-2].split("_")[1] for p in self.image_paths})
        self.color_to_idx = {c: i for i, c in enumerate(self.colors)}
        self.item_to_idx = {i: j for j, i in enumerate(self.items)}

    def __len__(self):
        return len(self.image_paths)

    def __getitem__(self, idx):
        path = self.image_paths[idx]
        color, item = path.split("/")[-2].split("_")
        image = self.transform(Image.open(path).convert("RGB"))
        return image, torch.tensor(self.color_to_idx[color]), torch.tensor(self.item_to_idx[item])

dataset = MultiLabelDataset(data_dir, transform)
train_size = int(0.7 * len(dataset))
train_set, test_set = random_split(dataset, [train_size, len(dataset) - train_size])
train_loader = DataLoader(train_set, batch_size=64, shuffle=True)
test_loader = DataLoader(test_set, batch_size=64)

class MultiLabelCNN(nn.Module):
    def __init__(self, num_colors, num_items):
        super().__init__()
        self.conv1 = nn.Conv2d(3, 16, 3)
        self.conv2 = nn.Conv2d(16, 32, 3)
        self.pool = nn.MaxPool2d(2, 2)
        self.fc1 = nn.Linear(32 * 23 * 23, 128)
        self.fc_color = nn.Linear(128, num_colors)
        self.fc_item = nn.Linear(128, num_items)

    def forward(self, x):
        x = self.pool(F.relu(self.conv1(x)))
        x = self.pool(F.relu(self.conv2(x)))
        x = torch.flatten(x, 1)
        x = F.relu(self.fc1(x))
        return self.fc_color(x), self.fc_item(x)
        
model = MultiLabelCNN(len(dataset.colors), len(dataset.items))
criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

# Training loop
epochs = 5
print_every = 1

for epoch in range(epochs):
    epoch_loss = 0
    model.train()

    for images, color_labels, item_labels in train_loader:
        images, color_labels, item_labels = images, color_labels, item_labels

        # Forward pass
        color_output, item_output = model(images)

        # Compute loss
        loss_color = criterion(color_output, color_labels)
        loss_item = criterion(item_output, item_labels)
        loss = loss_color + loss_item

        # Backward pass and optimization
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        epoch_loss += loss.item()

    if (epoch + 1) % print_every == 0:
        print(f"Epoch {epoch+1}/{epochs}, Loss: {epoch_loss:.4f}")

# Evaluation
def evaluate(loader):
    model.eval()
    all_color_preds, all_item_preds, all_color_labels, all_item_labels = [], [], [], []
    with torch.no_grad():
        for images, color_labels, item_labels in loader:
            images = images
            color_output, item_output = model(images)
            all_color_preds.extend(torch.argmax(color_output, 1).cpu().numpy())
            all_item_preds.extend(torch.argmax(item_output, 1).cpu().numpy())
            all_color_labels.extend(color_labels.numpy())
            all_item_labels.extend(item_labels.numpy())
    f1_color = f1_score(all_color_labels, all_color_preds, average="weighted")
    f1_item = f1_score(all_item_labels, all_item_preds, average="weighted")
    return f1_color, f1_item

f1_train = evaluate(train_loader)
f1_test = evaluate(test_loader)
print(f"Train F1 Scores - Color: {f1_train[0]:.4f}, Item: {f1_train[1]:.4f}")
print(f"Test F1 Scores - Color: {f1_test[0]:.4f}, Item: {f1_test[1]:.4f}")
    """
    text = '''
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, random_split
from torchvision import transforms, datasets
from sklearn.metrics import f1_score
import numpy as np
from tqdm import tqdm
import os
import glob
from PIL import Image

# Data preparation
data_dir = "/content/clothes_multi/clothes_multi"

# Transformation for the dataset
transform = transforms.Compose([
    transforms.Resize((100, 100)),  # Resize images to 100x100
    transforms.ToTensor(),          # Convert images to tensors
    transforms.Normalize(mean=(0.5, 0.5, 0.5), std=(0.5, 0.5, 0.5))  # Normalize
])

# Dataset
class MultiLabelDataset(Dataset):
    def __init__(self, data_dir, transform):
        self.image_paths = glob.glob(f"{data_dir}/*/*")
        self.transform = transform
        self.colors = sorted({p.split("/")[-2].split("_")[0] for p in self.image_paths})
        self.items = sorted({p.split("/")[-2].split("_")[1] for p in self.image_paths})
        self.color_to_idx = {c: i for i, c in enumerate(self.colors)}
        self.item_to_idx = {i: j for j, i in enumerate(self.items)}

    def __len__(self):
        return len(self.image_paths)

    def __getitem__(self, idx):
        path = self.image_paths[idx]
        color, item = path.split("/")[-2].split("_")
        image = self.transform(Image.open(path).convert("RGB"))
        return image, torch.tensor(self.color_to_idx[color]), torch.tensor(self.item_to_idx[item])

dataset = MultiLabelDataset(data_dir, transform)
train_size = int(0.7 * len(dataset))
train_set, test_set = random_split(dataset, [train_size, len(dataset) - train_size])
train_loader = DataLoader(train_set, batch_size=64, shuffle=True)
test_loader = DataLoader(test_set, batch_size=64)

class MultiLabelCNN(nn.Module):
    def __init__(self, num_colors, num_items):
        super().__init__()
        self.conv1 = nn.Conv2d(3, 16, 3)
        self.conv2 = nn.Conv2d(16, 32, 3)
        self.pool = nn.MaxPool2d(2, 2)
        self.fc1 = nn.Linear(32 * 23 * 23, 128)
        self.fc_color = nn.Linear(128, num_colors)
        self.fc_item = nn.Linear(128, num_items)

    def forward(self, x):
        x = self.pool(F.relu(self.conv1(x)))
        x = self.pool(F.relu(self.conv2(x)))
        x = torch.flatten(x, 1)
        x = F.relu(self.fc1(x))
        return self.fc_color(x), self.fc_item(x)
        
model = MultiLabelCNN(len(dataset.colors), len(dataset.items))
criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

# Training loop
epochs = 5
print_every = 1

for epoch in range(epochs):
    epoch_loss = 0
    model.train()

    for images, color_labels, item_labels in train_loader:
        images, color_labels, item_labels = images, color_labels, item_labels

        # Forward pass
        color_output, item_output = model(images)

        # Compute loss
        loss_color = criterion(color_output, color_labels)
        loss_item = criterion(item_output, item_labels)
        loss = loss_color + loss_item

        # Backward pass and optimization
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        epoch_loss += loss.item()

    if (epoch + 1) % print_every == 0:
        print(f"Epoch {epoch+1}/{epochs}, Loss: {epoch_loss:.4f}")

# Evaluation
def evaluate(loader):
    model.eval()
    all_color_preds, all_item_preds, all_color_labels, all_item_labels = [], [], [], []
    with torch.no_grad():
        for images, color_labels, item_labels in loader:
            images = images
            color_output, item_output = model(images)
            all_color_preds.extend(torch.argmax(color_output, 1).cpu().numpy())
            all_item_preds.extend(torch.argmax(item_output, 1).cpu().numpy())
            all_color_labels.extend(color_labels.numpy())
            all_item_labels.extend(item_labels.numpy())
    f1_color = f1_score(all_color_labels, all_color_preds, average="weighted")
    f1_item = f1_score(all_item_labels, all_item_preds, average="weighted")
    return f1_color, f1_item

f1_train = evaluate(train_loader)
f1_test = evaluate(test_loader)
print(f"Train F1 Scores - Color: {f1_train[0]:.4f}, Item: {f1_train[1]:.4f}")
print(f"Test F1 Scores - Color: {f1_test[0]:.4f}, Item: {f1_test[1]:.4f}")
    '''
    pc.copy(text)
    
    
def eng_handwritten():
    """
3. Набор данных: images/eng_handwritten.zip. Реализовав сверточную нейронную сеть при
помощи библиотеки PyTorch, решите задачу классификации изображений. Разделите набор данных на обучающее, валидационное и тестовое множество. Выполните предобработку данных (вырежьте центральную область изображений одинакового размера и преобразуйте изображения в тензоры). Реализуйте логику ранней остановки (на основе метрики micro F1 на валидационном множестве). Выведите значение mісго F1 на тестовом множестве. (20 баллов)

batch_size = 64

# Data preprocessing and augmentation
transform = transforms.Compose([
    transforms.Resize((128, 128)),
    transforms.CenterCrop((112, 112)),
    transforms.ToTensor()
])

# Load dataset
data_dir = "/content/eng_handwritten/eng_handwritten"
dataset = datasets.ImageFolder(root=data_dir, transform=transform)

# Split dataset into train, validation, and test sets
train_size = int(0.7 * len(dataset))
val_size = int(0.15 * len(dataset))
test_size = len(dataset) - train_size - val_size
train_dataset, val_dataset, test_dataset = random_split(dataset, [train_size, val_size, test_size])

# Data loaders
train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

model = nn.Sequential(
    nn.Conv2d(3, 16, (3, 3)),
    nn.ReLU(),
    nn.MaxPool2d(2, 2),
    nn.Conv2d(16, 16, (5,5)),
    nn.ReLU(),
    nn.MaxPool2d(2, 2),
    nn.Flatten(),
    nn.Linear(10000, 128),
    nn.ReLU(),
    nn.Linear(128, 26)
)

num_classes = len(dataset.classes)

batch_size = 64
num_epochs = 5
learning_rate = 0.001
patience = 2

# Loss and optimizer
criterion = nn.CrossEntropyLoss()
optimizer = optim.AdamW(model.parameters(), lr=learning_rate)

# Training loop with early stopping
best_f1 = -1
patience_counter = 0

for epoch in range(num_epochs):
    model.train()

    # Train phase
    for X_batch, y_batch in tqdm(train_loader):

        optimizer.zero_grad()
        outputs = model(X_batch)
        loss = criterion(outputs, y_batch)
        loss.backward()
        optimizer.step()

    # Validation phase
    model.eval()
    val_true = []
    val_preds = []
    with torch.no_grad():
        for X_batch, y_batch in val_loader:
            X_batch, y_batch = X_batch, y_batch
            outputs = model(X_batch)
            _, predicted = torch.max(outputs, 1)
            val_true.extend(y_batch.cpu().numpy())
            val_preds.extend(predicted.cpu().numpy())

    # Calculate validation micro F1 score
    micro_f1 = f1_score(val_true, val_preds, average='micro')
    print(f"Epoch {epoch + 1}, Val Micro F1: {micro_f1:.4f}")

    # Early stopping
    if micro_f1 > best_f1:
        best_f1 = micro_f1
        patience_counter = 0
        torch.save(model.state_dict(), "best_model.pth")
    else:
        patience_counter += 1

    if patience_counter >= patience:
        print(f"Early stopping triggered at epoch {epoch + 1}.")
        break
        
# Load the best model
model.load_state_dict(torch.load("best_model.pth"))

# Test set evaluation
model.eval()
test_preds, test_labels = [], []
with torch.no_grad():
    for images, labels in test_loader:
        outputs = model(images)
        preds = torch.argmax(outputs, dim=1)
        test_preds.extend(preds.cpu().numpy())
        test_labels.extend(labels.cpu().numpy())

# Calculate test micro F1
test_f1 = f1_score(test_labels, test_preds, average="micro")
print(f"Test Micro F1: {test_f1:.4f}")
    """
    text = '''
batch_size = 64

# Data preprocessing and augmentation
transform = transforms.Compose([
    transforms.Resize((128, 128)),
    transforms.CenterCrop((112, 112)),
    transforms.ToTensor()
])

# Load dataset
data_dir = "/content/eng_handwritten/eng_handwritten"
dataset = datasets.ImageFolder(root=data_dir, transform=transform)

# Split dataset into train, validation, and test sets
train_size = int(0.7 * len(dataset))
val_size = int(0.15 * len(dataset))
test_size = len(dataset) - train_size - val_size
train_dataset, val_dataset, test_dataset = random_split(dataset, [train_size, val_size, test_size])

# Data loaders
train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

model = nn.Sequential(
    nn.Conv2d(3, 16, (3, 3)),
    nn.ReLU(),
    nn.MaxPool2d(2, 2),
    nn.Conv2d(16, 16, (5,5)),
    nn.ReLU(),
    nn.MaxPool2d(2, 2),
    nn.Flatten(),
    nn.Linear(10000, 128),
    nn.ReLU(),
    nn.Linear(128, 26)
)

num_classes = len(dataset.classes)

batch_size = 64
num_epochs = 5
learning_rate = 0.001
patience = 2

# Loss and optimizer
criterion = nn.CrossEntropyLoss()
optimizer = optim.AdamW(model.parameters(), lr=learning_rate)

# Training loop with early stopping
best_f1 = -1
patience_counter = 0

for epoch in range(num_epochs):
    model.train()

    # Train phase
    for X_batch, y_batch in tqdm(train_loader):

        optimizer.zero_grad()
        outputs = model(X_batch)
        loss = criterion(outputs, y_batch)
        loss.backward()
        optimizer.step()

    # Validation phase
    model.eval()
    val_true = []
    val_preds = []
    with torch.no_grad():
        for X_batch, y_batch in val_loader:
            X_batch, y_batch = X_batch, y_batch
            outputs = model(X_batch)
            _, predicted = torch.max(outputs, 1)
            val_true.extend(y_batch.cpu().numpy())
            val_preds.extend(predicted.cpu().numpy())

    # Calculate validation micro F1 score
    micro_f1 = f1_score(val_true, val_preds, average='micro')
    print(f"Epoch {epoch + 1}, Val Micro F1: {micro_f1:.4f}")

    # Early stopping
    if micro_f1 > best_f1:
        best_f1 = micro_f1
        patience_counter = 0
        torch.save(model.state_dict(), "best_model.pth")
    else:
        patience_counter += 1

    if patience_counter >= patience:
        print(f"Early stopping triggered at epoch {epoch + 1}.")
        break
        
# Load the best model
model.load_state_dict(torch.load("best_model.pth"))

# Test set evaluation
model.eval()
test_preds, test_labels = [], []
with torch.no_grad():
    for images, labels in test_loader:
        outputs = model(images)
        preds = torch.argmax(outputs, dim=1)
        test_preds.extend(preds.cpu().numpy())
        test_labels.extend(labels.cpu().numpy())

# Calculate test micro F1
test_f1 = f1_score(test_labels, test_preds, average="micro")
print(f"Test Micro F1: {test_f1:.4f}")
    '''
    pc.copy(text)
    
    
def chars():
    """
3. Набор данных: images/chars.zip. Реализовав сверточную нейронную сеть при помощи
библиотеки PyTorch, решите задачу классификации изображений. Разделите набор данных на обучающее и тестовое множество. Выполните предобработку данных (приведите изображения к одному размеру, нормализуйте и преобразуйте в тензоры). Выведите значение F1 на тестовом множестве. Повторите решение задачи, применяя к обучающему множеству преобразования, случайным образом изменяющие изображения. Выведите значение F1 на тестовом множестве для модели, которая обучалась на расширенном датасете. (20 баллов)

data_dir = "/content/chars/chars/"

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, random_split
from torchvision import datasets, transforms
from sklearn.metrics import f1_score
from tqdm import tqdm

# Define image size and batch size
image_size = 64
batch_size = 64
num_classes = 26  # Assuming it's a dataset with 26 character classes (A-Z)

# Data preprocessing
base_transform = transforms.Compose([
    transforms.Resize((image_size, image_size)),
    transforms.ToTensor(),
    transforms.Normalize(mean=(0.5,), std=(0.5,))
])

# Data augmentation for training
augmented_transform = transforms.Compose([
    transforms.Resize((image_size, image_size)),
    transforms.RandomRotation(15),
    transforms.RandomHorizontalFlip(),
    transforms.ToTensor(),
    transforms.Normalize(mean=(0.5,), std=(0.5,))
])

# Load dataset
dataset = datasets.ImageFolder(root=data_dir, transform=base_transform)

# Split dataset into training (70%) and test (30%) sets
train_size = int(0.7 * len(dataset))
test_size = len(dataset) - train_size
train_dataset, test_dataset = random_split(dataset, [train_size, test_size])

# Create data loaders
train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

# Define the CNN model
class SimpleCNN(nn.Module):
    def __init__(self, num_classes):
        super(SimpleCNN, self).__init__()
        self.conv1 = nn.Conv2d(3, 16, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(16, 32, kernel_size=3, padding=1)
        self.pool = nn.MaxPool2d(kernel_size=2, stride=2)
        self.fc1 = nn.Linear(32 * (image_size // 4) * (image_size // 4), 128)
        self.fc2 = nn.Linear(128, num_classes)

    def forward(self, x):
        x = self.pool(torch.relu(self.conv1(x)))
        x = self.pool(torch.relu(self.conv2(x)))
        x = torch.flatten(x, 1)
        x = torch.relu(self.fc1(x))
        x = self.fc2(x)
        return x

# Initialize model, loss function, and optimizer
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = SimpleCNN(num_classes=num_classes).to(device)
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)

# Training loop function
def train_model(model, train_loader, val_loader=None, epochs=20):
    model.train()
    for epoch in range(epochs):
        running_loss = 0.0
        for images, labels in tqdm(train_loader, desc=f"Epoch {epoch+1}/{epochs}"):
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            running_loss += loss.item()
        print(f"Epoch {epoch+1} Loss: {running_loss / len(train_loader):.4f}")

# Evaluation function
def evaluate_model(model, test_loader):
    model.eval()
    y_true, y_pred = [], []
    with torch.no_grad():
        for images, labels in test_loader:
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            _, predicted = torch.max(outputs, 1)
            y_true.extend(labels.cpu().numpy())
            y_pred.extend(predicted.cpu().numpy())
    f1 = f1_score(y_true, y_pred, average='micro')
    return f1

# Train on the original dataset
print("Training on original dataset...")
train_model(model, train_loader, epochs=5)
f1_original = evaluate_model(model, test_loader)
print(f"F1-score on test set (original dataset): {f1_original:.4f}")

# Train on the augmented dataset
print("\nTraining on augmented dataset...")
# Apply data augmentation to the training dataset
train_dataset.dataset.transform = augmented_transform
train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)

# Reinitialize model, optimizer, and train again
model = SimpleCNN(num_classes=num_classes).to(device)
optimizer = optim.Adam(model.parameters(), lr=0.001)
train_model(model, train_loader, epochs=20)
f1_augmented = evaluate_model(model, test_loader)
print(f"F1-score on test set (augmented dataset): {f1_augmented:.4f}")

    """
    text = '''
data_dir = "/content/chars/chars/"

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, random_split
from torchvision import datasets, transforms
from sklearn.metrics import f1_score
from tqdm import tqdm

# Define image size and batch size
image_size = 64
batch_size = 64
num_classes = 26  # Assuming it's a dataset with 26 character classes (A-Z)

# Data preprocessing
base_transform = transforms.Compose([
    transforms.Resize((image_size, image_size)),
    transforms.ToTensor(),
    transforms.Normalize(mean=(0.5,), std=(0.5,))
])

# Data augmentation for training
augmented_transform = transforms.Compose([
    transforms.Resize((image_size, image_size)),
    transforms.RandomRotation(15),
    transforms.RandomHorizontalFlip(),
    transforms.ToTensor(),
    transforms.Normalize(mean=(0.5,), std=(0.5,))
])

# Load dataset
dataset = datasets.ImageFolder(root=data_dir, transform=base_transform)

# Split dataset into training (70%) and test (30%) sets
train_size = int(0.7 * len(dataset))
test_size = len(dataset) - train_size
train_dataset, test_dataset = random_split(dataset, [train_size, test_size])

# Create data loaders
train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

# Define the CNN model
class SimpleCNN(nn.Module):
    def __init__(self, num_classes):
        super(SimpleCNN, self).__init__()
        self.conv1 = nn.Conv2d(3, 16, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(16, 32, kernel_size=3, padding=1)
        self.pool = nn.MaxPool2d(kernel_size=2, stride=2)
        self.fc1 = nn.Linear(32 * (image_size // 4) * (image_size // 4), 128)
        self.fc2 = nn.Linear(128, num_classes)

    def forward(self, x):
        x = self.pool(torch.relu(self.conv1(x)))
        x = self.pool(torch.relu(self.conv2(x)))
        x = torch.flatten(x, 1)
        x = torch.relu(self.fc1(x))
        x = self.fc2(x)
        return x

# Initialize model, loss function, and optimizer
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = SimpleCNN(num_classes=num_classes).to(device)
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)

# Training loop function
def train_model(model, train_loader, val_loader=None, epochs=20):
    model.train()
    for epoch in range(epochs):
        running_loss = 0.0
        for images, labels in tqdm(train_loader, desc=f"Epoch {epoch+1}/{epochs}"):
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            running_loss += loss.item()
        print(f"Epoch {epoch+1} Loss: {running_loss / len(train_loader):.4f}")

# Evaluation function
def evaluate_model(model, test_loader):
    model.eval()
    y_true, y_pred = [], []
    with torch.no_grad():
        for images, labels in test_loader:
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            _, predicted = torch.max(outputs, 1)
            y_true.extend(labels.cpu().numpy())
            y_pred.extend(predicted.cpu().numpy())
    f1 = f1_score(y_true, y_pred, average='micro')
    return f1

# Train on the original dataset
print("Training on original dataset...")
train_model(model, train_loader, epochs=5)
f1_original = evaluate_model(model, test_loader)
print(f"F1-score on test set (original dataset): {f1_original:.4f}")

# Train on the augmented dataset
print("\nTraining on augmented dataset...")
# Apply data augmentation to the training dataset
train_dataset.dataset.transform = augmented_transform
train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)

# Reinitialize model, optimizer, and train again
model = SimpleCNN(num_classes=num_classes).to(device)
optimizer = optim.Adam(model.parameters(), lr=0.001)
train_model(model, train_loader, epochs=20)
f1_augmented = evaluate_model(model, test_loader)
print(f"F1-score on test set (augmented dataset): {f1_augmented:.4f}")
    '''
    pc.copy(text)
    