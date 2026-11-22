"""My original model: a 4-layer CNN trained FROM SCRATCH on the same face photos.

It is kept to compare against the app's model (pretrained SFace + classifier). With only
~8 photos per person the CNN can't learn faces well, which is why the app uses transfer learning.

Needs TensorFlow:  pip install -r requirements-cnn.txt
Run (backend folder, after the photos are imported):  python -m scripts.train_cnn
"""
import numpy as np
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split

from app.face.dataset import load_training_set


def build_cnn(num_people: int):
    from tensorflow import keras
    from tensorflow.keras import layers
    model = keras.Sequential([
        keras.Input(shape=(100, 100, 3)),
        layers.Rescaling(1 / 255),                      # pixels 0-255 -> 0-1 (same in training and use)
        layers.RandomFlip("horizontal"),                # augmentation: only active while training
        layers.RandomRotation(0.08),
        layers.RandomZoom(0.1),
        layers.Conv2D(32, 4, activation="relu"), layers.MaxPooling2D(),    # 4 convolution blocks
        layers.Conv2D(64, 4, activation="relu"), layers.MaxPooling2D(),
        layers.Conv2D(128, 4, activation="relu"), layers.MaxPooling2D(),
        layers.Conv2D(256, 4, activation="relu"), layers.MaxPooling2D(),
        layers.Flatten(),
        layers.Dense(128, activation="relu"),
        layers.Dropout(0.3),
        layers.Dense(64, activation="relu"),
        layers.Dense(num_people, activation="softmax"),  # one probability per person
    ])
    model.compile(optimizer="adam", loss="sparse_categorical_crossentropy", metrics=["accuracy"])
    return model


def main():
    from tensorflow import keras
    images, labels = load_training_set()
    people = sorted(set(labels))
    X = np.stack([np.array(keras.utils.array_to_img(im).resize((100, 100))) for im in images]).astype("float32")
    y = np.array([people.index(p) for p in labels])
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

    keras.utils.set_random_seed(42)
    model = build_cnn(len(people))
    model.fit(X_train, y_train, validation_data=(X_test, y_test), epochs=60, batch_size=8, verbose=0,
              callbacks=[keras.callbacks.EarlyStopping(patience=10, restore_best_weights=True)])
    pred = model.predict(X_test, verbose=0).argmax(axis=1)
    print(f"4-layer CNN from scratch: {len(X_train)} train / {len(X_test)} test photos")
    print(f"Accuracy {accuracy_score(y_test, pred):.1%} | F1 {f1_score(y_test, pred, average='macro', zero_division=0):.2f}")


if __name__ == "__main__":
    main()
