"""A small Linear Autoencoder example for dimensionality reduction."""

import numpy as np
from sklearn.datasets import load_digits
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from typing import Optional


class LinearAutoencoder:
    """Lightweight encoder/decoder pair that uses tanh nonlinearities."""

    def __init__(self, input_dim: int, latent_dim: int, seed: int = 0) -> None:
        self.latent_dim = latent_dim
        self._rng = np.random.default_rng(seed)
        limit = np.sqrt(6 / (input_dim + latent_dim))
        self.W_enc = self._rng.uniform(-limit, limit, size=(input_dim, latent_dim))
        self.b_enc = np.zeros(latent_dim)
        self.W_dec = self._rng.uniform(-limit, limit, size=(latent_dim, input_dim))
        self.b_dec = np.zeros(input_dim)

    def encode(self, X: np.ndarray) -> np.ndarray:
        """Return the latent coordinates for a batch of samples."""
        z_linear = X @ self.W_enc + self.b_enc
        return np.tanh(z_linear)

    def decode(self, Z: np.ndarray) -> np.ndarray:
        """Reconstruct the original space from latent points."""
        return Z @ self.W_dec + self.b_dec

    def reconstruct(self, X: np.ndarray) -> np.ndarray:
        """Encode and decode in one shot."""
        return self.decode(self.encode(X))

    def train(
        self,
        X: np.ndarray,
        epochs: int = 40,
        batch_size: int = 64,
        lr: float = 0.01,
        val_data: Optional[np.ndarray] = None,
        verbose: bool = True,
    ) -> None:
        n_samples = X.shape[0]
        if batch_size > n_samples:
            batch_size = n_samples

        for epoch in range(1, epochs + 1):
            shuffled = self._rng.permutation(n_samples)
            epoch_loss = 0.0

            for start in range(0, n_samples, batch_size):
                end = start + batch_size
                batch = X[shuffled[start:end]]
                epoch_loss += self._train_batch(batch, lr)

            if verbose:
                info = f"Epoch {epoch}/{epochs} - train loss {epoch_loss / max(1, (n_samples // batch_size)):.4f}"
                if val_data is not None:
                    info += f", val loss {self.evaluate(val_data):.4f}"
                print(info)

    def _train_batch(self, batch: np.ndarray, lr: float) -> float:
        z_linear = batch @ self.W_enc + self.b_enc
        z = np.tanh(z_linear)
        recon = z @ self.W_dec + self.b_dec
        error = recon - batch
        batch_size = batch.shape[0]
        loss = np.mean(error ** 2)

        grad_recon = (2.0 / batch_size) * error
        grad_W_dec = z.T @ grad_recon
        grad_b_dec = np.sum(grad_recon, axis=0)

        grad_z = grad_recon @ self.W_dec.T
        grad_activation = 1.0 - np.tanh(z_linear) ** 2
        grad_hidden = grad_z * grad_activation
        grad_W_enc = batch.T @ grad_hidden
        grad_b_enc = np.sum(grad_hidden, axis=0)

        self.W_dec -= lr * grad_W_dec
        self.b_dec -= lr * grad_b_dec
        self.W_enc -= lr * grad_W_enc
        self.b_enc -= lr * grad_b_enc

        return loss

    def evaluate(self, X: np.ndarray) -> float:
        recon = self.reconstruct(X)
        return float(np.mean((recon - X) ** 2))


def load_digits_data() -> np.ndarray:
    digits = load_digits()
    scaler = StandardScaler()
    features = scaler.fit_transform(digits.data)
    return features


def main() -> None:
    features = load_digits_data()
    train_set, val_set = train_test_split(features, test_size=0.2, random_state=42)

    autoencoder = LinearAutoencoder(input_dim=features.shape[1], latent_dim=16)
    autoencoder.train(train_set, epochs=30, batch_size=64, lr=0.01, val_data=val_set)

    encoded = autoencoder.encode(val_set[:5])
    print(f"Latent space shape: {encoded.shape}")
    print("First encoded sample:", np.round(encoded[0], 4))

    reconstruction_error = autoencoder.evaluate(val_set)
    print(f"Final reconstruction MSE on validation set: {reconstruction_error:.6f}")


if __name__ == "__main__":
    main()

