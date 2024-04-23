import numpy as np
import tensorflow as tf
import data_util as du
from model import REModel
from tensorflow.keras.losses import CategoricalCrossentropy
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.metrics import categorical_accuracy
from tqdm import tqdm

epochs = 30
bath_size = 20
learning_rate = 0.001
loss_fn = CategoricalCrossentropy()
optimizer = Adam(learning_rate=learning_rate)
print_bath = 10


def train():
    data_loader = du.DataLoader()
    remodel = REModel(vocab_size=data_loader.get_vocab_size(), use_en_pos=True)
    data_slice = tf.data.Dataset.from_tensor_slices(data_loader.load_train_data('train_file')).batch(bath_size)
    for epoch in range(epochs):
        total_loss = 0
        data_iterator = tqdm(data_slice, desc=f'Epoch {epoch + 1}/{epochs}', total=len(data_slice), unit='batch')
        for data in tqdm(data_iterator):
            tokens_id, type_ids, att_mask, e1, e2, tag = data
            x_train = np.stack((tokens_id, type_ids, att_mask, e1, e2),
                     axis=-1)
            with tf.GradientTape() as tape:
                logits = remodel(x_train)
                loss = loss_fn(tag, logits)
            gradients = tape.gradient(loss, remodel.trainable_variables)
            optimizer.apply_gradients(zip(gradients, remodel.trainable_variables))
            acc = tf.reduce_mean(categorical_accuracy(tag, logits))
            data_iterator.set_postfix(loss=loss.numpy(), accuracy=acc.numpy())
        # total_loss += loss
        # print(f"epoch_loss:{total_loss.numpy()}")



train()