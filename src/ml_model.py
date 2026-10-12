"""
Employee Performance Analytics - ML Model Training & Evaluation Pipeline
Provides robust Decision Tree and Random Forest Classifiers built on NumPy/Pandas.
Auto-persists model metadata and metrics into SQLite relational database.
"""

import os
import joblib
import numpy as np
import pandas as pd
from src.database import log_model_metadata, populate_db_from_df

FEATURE_COLS_NUMERIC = [
    'attendance_rate', 'task_completion_rate', 'training_hours',
    'experience_years', 'previous_performance', 'projects_delivered',
    'overtime_hours', 'peer_review_score', 'communication_score'
]

FEATURE_COLS_CATEGORICAL = ['department']

TARGET_COL = 'performance_category'
TARGET_CLASSES = ['Needs Support', 'Moderate', 'High']


# -----------------------------------------------------------------------------
# Preprocessing Utilities (NumPy / Pandas)
# -----------------------------------------------------------------------------
class CustomPreprocessor:
    def __init__(self, num_cols, cat_cols):
        self.num_cols = num_cols
        self.cat_cols = cat_cols
        self.means_ = {}
        self.stds_ = {}
        self.categories_ = {}
        self.feature_names_ = []

    def fit(self, X):
        for col in self.num_cols:
            self.means_[col] = float(X[col].mean())
            std_val = float(X[col].std())
            self.stds_[col] = std_val if std_val > 1e-6 else 1.0

        for col in self.cat_cols:
            self.categories_[col] = sorted(X[col].unique().tolist())

        self.feature_names_ = self.num_cols.copy()
        for col in self.cat_cols:
            for cat in self.categories_[col]:
                self.feature_names_.append(f"{col}_{cat}")

        return self

    def transform(self, X):
        X_num = X[self.num_cols].copy()
        for col in self.num_cols:
            X_num[col] = (X_num[col] - self.means_[col]) / self.stds_[col]

        cat_blocks = []
        for col in self.cat_cols:
            for cat in self.categories_[col]:
                cat_blocks.append((X[col] == cat).astype(float).values)

        if cat_blocks:
            cat_arr = np.column_stack(cat_blocks)
            X_mat = np.column_stack([X_num.values, cat_arr])
        else:
            X_mat = X_num.values

        return X_mat

    def fit_transform(self, X):
        return self.fit(X).transform(X)


# -----------------------------------------------------------------------------
# Decision Tree & Random Forest Implementations
# -----------------------------------------------------------------------------
class Node:
    def __init__(self, feature=None, threshold=None, left=None, right=None, *, value=None, probs=None):
        self.feature = feature
        self.threshold = threshold
        self.left = left
        self.right = right
        self.value = value
        self.probs = probs

    def is_leaf_node(self):
        return self.value is not None


class DecisionTreeClassifierCustom:
    def __init__(self, max_depth=5, min_samples_split=6, n_classes=3):
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.n_classes = n_classes
        self.root = None
        self.feature_importances_ = None

    def _gini(self, y):
        if len(y) == 0:
            return 0
        p = np.bincount(y, minlength=self.n_classes) / len(y)
        return 1.0 - np.sum(p ** 2)

    def _best_split(self, X, y):
        best_gain = -1.0
        split_idx, split_thresh = None, None
        current_gini = self._gini(y)
        n_samples, n_features = X.shape

        for feat_idx in range(n_features):
            X_column = X[:, feat_idx]
            thresholds = np.unique(X_column)
            if len(thresholds) > 10:
                thresholds = np.percentile(thresholds, np.linspace(10, 90, 8))

            for thresh in thresholds:
                left_mask = X_column <= thresh
                right_mask = ~left_mask

                if np.sum(left_mask) == 0 or np.sum(right_mask) == 0:
                    continue

                gini_left = self._gini(y[left_mask])
                gini_right = self._gini(y[right_mask])
                w_left = np.sum(left_mask) / n_samples
                w_right = np.sum(right_mask) / n_samples
                child_gini = w_left * gini_left + w_right * gini_right

                gain = current_gini - child_gini
                if gain > best_gain:
                    best_gain = gain
                    split_idx = feat_idx
                    split_thresh = thresh

        return split_idx, split_thresh, best_gain

    def _build_tree(self, X, y, depth=0):
        n_samples, n_features = X.shape
        n_labels = len(np.unique(y))

        if depth >= self.max_depth or n_labels == 1 or n_samples < self.min_samples_split:
            probs = np.bincount(y, minlength=self.n_classes) / (n_samples if n_samples > 0 else 1)
            most_common = np.argmax(probs)
            return Node(value=most_common, probs=probs)

        feat_idx, thresh, gain = self._best_split(X, y)
        if feat_idx is None or gain <= 1e-7:
            probs = np.bincount(y, minlength=self.n_classes) / n_samples
            most_common = np.argmax(probs)
            return Node(value=most_common, probs=probs)

        if self.feature_importances_ is not None:
            self.feature_importances_[feat_idx] += gain * n_samples

        left_mask = X[:, feat_idx] <= thresh
        right_mask = ~left_mask

        left_child = self._build_tree(X[left_mask], y[left_mask], depth + 1)
        right_child = self._build_tree(X[right_mask], y[right_mask], depth + 1)

        return Node(feature=feat_idx, threshold=thresh, left=left_child, right=right_child)

    def fit(self, X, y):
        self.n_classes = len(np.unique(y))
        self.feature_importances_ = np.zeros(X.shape[1])
        self.root = self._build_tree(X, y)
        if np.sum(self.feature_importances_) > 0:
            self.feature_importances_ /= np.sum(self.feature_importances_)
        return self

    def _traverse_tree(self, x, node):
        if node.is_leaf_node():
            return node.value, node.probs
        if x[node.feature] <= node.threshold:
            return self._traverse_tree(x, node.left)
        return self._traverse_tree(x, node.right)

    def predict(self, X):
        preds = [self._traverse_tree(x, self.root)[0] for x in X]
        return np.array(preds)

    def predict_proba(self, X):
        probs = [self._traverse_tree(x, self.root)[1] for x in X]
        return np.array(probs)


class RandomForestClassifierCustom:
    def __init__(self, n_estimators=25, max_depth=6, min_samples_split=6, n_classes=3):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.n_classes = n_classes
        self.trees = []
        self.feature_importances_ = None

    def fit(self, X, y):
        n_samples, n_features = X.shape
        self.n_classes = len(np.unique(y))
        self.trees = []
        self.feature_importances_ = np.zeros(n_features)

        np.random.seed(42)
        for _ in range(self.n_estimators):
            indices = np.random.choice(n_samples, size=n_samples, replace=True)
            X_sample, y_sample = X[indices], y[indices]

            tree = DecisionTreeClassifierCustom(
                max_depth=self.max_depth,
                min_samples_split=self.min_samples_split,
                n_classes=self.n_classes
            )
            tree.fit(X_sample, y_sample)
            self.trees.append(tree)

            if tree.feature_importances_ is not None:
                self.feature_importances_ += tree.feature_importances_

        if np.sum(self.feature_importances_) > 0:
            self.feature_importances_ /= np.sum(self.feature_importances_)
        return self

    def predict_proba(self, X):
        tree_probs = np.array([tree.predict_proba(X) for tree in self.trees])
        return np.mean(tree_probs, axis=0)

    def predict(self, X):
        probs = self.predict_proba(X)
        return np.argmax(probs, axis=1)


class CustomPipeline:
    def __init__(self, preprocessor, classifier, classes):
        self.preprocessor = preprocessor
        self.classifier = classifier
        self.classes_ = classes

    def fit(self, X, y):
        label_map = {cls: idx for idx, cls in enumerate(self.classes_)}
        y_encoded = np.array([label_map[item] for item in y if item in label_map])

        X_trans = self.preprocessor.fit_transform(X)
        self.classifier.fit(X_trans, y_encoded)
        return self

    def predict(self, X):
        X_trans = self.preprocessor.transform(X)
        preds_encoded = self.classifier.predict(X_trans)
        return np.array([self.classes_[idx] for idx in preds_encoded])

    def predict_proba(self, X):
        X_trans = self.preprocessor.transform(X)
        return self.classifier.predict_proba(X_trans)


# -----------------------------------------------------------------------------
# Model Evaluation Pipeline
# -----------------------------------------------------------------------------
def compute_metrics(y_true, y_pred, classes=TARGET_CLASSES):
    acc = float(np.mean(y_true == y_pred))

    cm = np.zeros((len(classes), len(classes)), dtype=int)
    class_map = {cls: idx for idx, cls in enumerate(classes)}

    for t, p in zip(y_true, y_pred):
        if t in class_map and p in class_map:
            cm[class_map[t], class_map[p]] += 1

    report = {}
    total_samples = len(y_true)
    weighted_prec, weighted_rec, weighted_f1 = 0.0, 0.0, 0.0

    for idx, cls in enumerate(classes):
        tp = cm[idx, idx]
        fp = np.sum(cm[:, idx]) - tp
        fn = np.sum(cm[idx, :]) - tp
        support = np.sum(cm[idx, :])

        prec = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
        rec = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
        f1 = float(2 * (prec * rec) / (prec + rec)) if (prec + rec) > 0 else 0.0

        report[cls] = {
            'precision': round(prec, 4),
            'recall': round(rec, 4),
            'f1-score': round(f1, 4),
            'support': int(support)
        }

        weight = support / total_samples
        weighted_prec += prec * weight
        weighted_rec += rec * weight
        weighted_f1 += f1 * weight

    report['accuracy'] = round(acc, 4)
    report['weighted avg'] = {
        'precision': round(weighted_prec, 4),
        'recall': round(weighted_rec, 4),
        'f1-score': round(weighted_f1, 4),
        'support': total_samples
    }

    return {
        'accuracy': round(acc, 4),
        'precision': round(weighted_prec, 4),
        'recall': round(weighted_rec, 4),
        'f1_score': round(weighted_f1, 4),
        'confusion_matrix': cm.tolist(),
        'classification_report': report
    }


def train_and_evaluate_models(df=None, data_path='data/employee_performance_dataset.csv', models_dir='models'):
    if df is None:
        if not os.path.exists(data_path):
            from src.dataset_generator import save_dataset
            df = save_dataset(data_path)
        else:
            df = pd.read_csv(data_path)

    try:
        populate_db_from_df(df)
    except Exception as e:
        print("Note: DB population warning:", e)

    np.random.seed(42)
    shuffled_indices = np.random.permutation(len(df))
    test_set_size = max(1, int(len(df) * 0.20))

    test_indices = shuffled_indices[:test_set_size]
    train_indices = shuffled_indices[test_set_size:]

    train_df = df.iloc[train_indices].reset_index(drop=True)
    test_df = df.iloc[test_indices].reset_index(drop=True)

    X_train = train_df[FEATURE_COLS_NUMERIC + FEATURE_COLS_CATEGORICAL]
    y_train = train_df[TARGET_COL].values

    X_test = test_df[FEATURE_COLS_NUMERIC + FEATURE_COLS_CATEGORICAL]
    y_test = test_df[TARGET_COL].values

    models = {
        'Decision Tree': DecisionTreeClassifierCustom(max_depth=5, min_samples_split=6, n_classes=3),
        'Random Forest': RandomForestClassifierCustom(n_estimators=25, max_depth=6, min_samples_split=6, n_classes=3)
    }

    results = {}
    fitted_pipelines = {}

    os.makedirs(models_dir, exist_ok=True)

    for name, clf in models.items():
        preprocessor = CustomPreprocessor(FEATURE_COLS_NUMERIC, FEATURE_COLS_CATEGORICAL)
        pipeline = CustomPipeline(preprocessor, clf, TARGET_CLASSES)

        pipeline.fit(X_train, y_train)
        y_pred = pipeline.predict(X_test)
        y_proba = pipeline.predict_proba(X_test)

        res = compute_metrics(y_test, y_pred, classes=TARGET_CLASSES)
        res['classes'] = TARGET_CLASSES
        res['y_test'] = y_test.tolist()
        res['y_pred'] = y_pred.tolist()
        res['y_proba'] = y_proba.tolist()

        results[name] = res
        fitted_pipelines[name] = pipeline

        filename = f"{name.lower().replace(' ', '_')}_pipeline.pkl"
        model_path = os.path.join(models_dir, filename)
        joblib.dump(pipeline, model_path)

        try:
            log_model_metadata(
                model_name=name,
                version="v1.0",
                algorithm=clf.__class__.__name__,
                metrics_dict=res,
                model_path=model_path
            )
        except Exception as e:
            print("Note: DB logging warning:", e)

    joblib.dump(results, os.path.join(models_dir, 'evaluation_summary.pkl'))
    return results, fitted_pipelines, (X_train, X_test, y_train, y_test)


def predict_employee_performance(input_dict, pipeline=None, model_name='Random Forest', models_dir='models'):
    """
    Predicts performance category and class probabilities for a single employee record.
    If pipeline is passed directly, uses that fitted pipeline (prevents model mismatch).
    """
    if pipeline is None:
        filename = f"{model_name.lower().replace(' ', '_')}_pipeline.pkl"
        model_path = os.path.join(models_dir, filename)

        if not os.path.exists(model_path):
            _, fitted_pipelines, _ = train_and_evaluate_models(models_dir=models_dir)
            pipeline = fitted_pipelines[model_name]
        else:
            pipeline = joblib.load(model_path)

    input_df = pd.DataFrame([input_dict])

    pred = pipeline.predict(input_df)[0]
    probas = pipeline.predict_proba(input_df)[0]
    prob_dict = {cls: round(float(prob), 4) for cls, prob in zip(pipeline.classes_, probas)}

    return pred, prob_dict, pipeline


if __name__ == '__main__':
    train_and_evaluate_models()
