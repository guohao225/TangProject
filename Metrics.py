import tensorflow as tf
from sklearn.metrics import precision_score, f1_score, recall_score

AVER = 'micro'
class PrecisionMetrics(tf.keras.metrics.Metric):
    def __init__(self, name='precision', **kwargs):
        super(PrecisionMetrics, self).__init__(name, **kwargs)
        self.score = self.add_weight(name='precision', initializer='zeros')
        self.total = self.add_weight(name='ptotal', initializer='zeros')

    def update_state(self, y_true, y_pred, sample_weight=None):
        y_pred = tf.argmax(y_pred, axis=-1)
        if y_true.shape != y_pred.shape:
            y_true = tf.reshape(y_true, [-1])

        def compute(true_v, pred_v):
            true_v = true_v.numpy().tolist()
            pred_v = pred_v.numpy().tolist()
            res = precision_score(true_v, pred_v, average=AVER, zero_division=1)
            return res

        score = tf.py_function(compute, [y_true, y_pred], tf.float32)
        self.score.assign_add(score)
        self.total.assign_add(1.)

    def result(self):
        return self.score / self.total

    def reset_state(self):
        self.score.assign(0.)
        self.total.assign(0.)


class RecallMetrics(tf.keras.metrics.Metric):
    def __init__(self, name='recall', **kwargs):
        super(RecallMetrics, self).__init__(name, **kwargs)
        self.score = self.add_weight(name='recall', initializer='zeros')
        self.total = self.add_weight(name='=rtotal', initializer='zeros')

    def update_state(self, y_true, y_pred, sample_weight=None):
        y_pred = tf.argmax(y_pred, axis=-1)
        if y_true.shape != y_pred.shape:
            y_true = tf.reshape(y_true, [-1])

        def compute(true_v, pred_v):
            true_v = true_v.numpy().tolist()
            pred_v = pred_v.numpy().tolist()
            res = recall_score(true_v, pred_v, average=AVER, zero_division=1)
            return res

        score = tf.py_function(compute, [y_true, y_pred], tf.float32)
        self.score.assign_add(score)
        self.total.assign_add(1.)

    def result(self):
        return self.score / self.total

    def reset_state(self):
        self.score.assign(0.)
        self.total.assign(0.)


class F1Metrics(tf.keras.metrics.Metric):
    def __init__(self, name='f1', **kwargs):
        super(F1Metrics, self).__init__(name, **kwargs)
        self.score = self.add_weight(name='f1', initializer='zeros')
        self.total = self.add_weight(name='ftotal', initializer='zeros')

    def update_state(self, y_true, y_pred, sample_weight=None):
        y_pred = tf.argmax(y_pred, axis=-1)
        if y_true.shape != y_pred.shape:
            y_true = tf.reshape(y_true, [-1])
        def compute(true_v, pred_v):
            true_v = true_v.numpy().tolist()
            pred_v = pred_v.numpy().tolist()
            res = f1_score(true_v, pred_v, average=AVER)
            return res

        score = tf.py_function(compute, [y_true, y_pred], tf.float32)
        self.score.assign_add(score)
        self.total.assign_add(1.)

    def result(self):
        return self.score / self.total

    def reset_state(self):
        self.score.assign(0.)
        self.total.assign(0.)
