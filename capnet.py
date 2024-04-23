import keras.losses
from tensorflow.keras.preprocessing import sequence
from tensorflow.keras.datasets import imdb

from caslayer import Capsule_bojone, CapsuleLayer, PrimaryCap, Length, Mask
from tensorflow.keras.layers import Conv1D, Conv2D, MaxPool2D, Concatenate, SpatialDropout1D
from tensorflow.keras.layers import Bidirectional, LSTM, GRU
from tensorflow.keras.layers import Dropout, Dense, Flatten
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.layers import Reshape, Input, Embedding
from tensorflow.keras.models import Model
from tensorflow.keras import backend as K
import numpy as np


def build_capsmodel():
    input = Input(shape=(300,), dtype='int32')
    embed = Embedding(5000, 300)(input)
    embed_layer = SpatialDropout1D(0.5)(embed)
    embedding_reshape = Reshape((300, 300, 1))(embed_layer)
    # Layer 1: Just a conventional Conv2D layer
    conv1 = Conv2D(filters=256,
                   kernel_size=3,
                   strides=1,
                   padding='valid',
                   activation='relu', )(embedding_reshape)
    primarycaps = PrimaryCap(inputs=conv1,
                             dim_capsule=2,
                             n_channels=6,
                             kernel_size=2,
                             strides=2,
                             padding='valid')

    # Layer 3: Capsule layer. Routing algorithm works here.
    x = CapsuleLayer(num_capsule=2,
                     dim_capsule=16,
                     routings=5)(primarycaps)
    x = Dropout(0.5)(x)
    out_caps = Length(name='capsnet')(x)
    model = Model(inputs=input, outputs=out_caps)
    return model

def load_imdb3():
    (x_train, y_train), (x_test, y_test) = imdb.load_data(path='imdb.npz', num_words=5000)
    x_train = sequence.pad_sequences(x_train, maxlen=300, padding='post')
    x_test = sequence.pad_sequences(x_test, maxlen=300, padding='post')
    return (x_train, y_train), (x_test, y_test)

(x_train, y_train), (x_test, y_test) = load_imdb3()
model = build_capsmodel()
model.compile(loss=keras.losses.SparseCategoricalCrossentropy(), optimizer=keras.optimizers.Adam(),metrics=['accuracy'])
model.fit(x_train, y_train, batch_size=40, epochs=50, validation_data=(x_test, y_test))