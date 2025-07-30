# ECDH X25519

Python-биндинги для [x25519-dalek](https://github.com/dalek-cryptography/x25519-dalek) на Rust через [PyO3](https://github.com/PyO3/pyo3).
Используется алгоритм X25519 для безопасного обмена ключами (ECDH).

---

## 🧠 Что такое ECDH (X25519)?

**X25519** — это алгоритм обмена ключами на основе эллиптических кривых (Elliptic Curve Diffie-Hellman, ECDH). Он широко применяется в современных криптопротоколах: TLS, SSH, Signal, WireGuard и других.

### Основные характеристики:

1. **Эллиптические кривые**

   * Основан на кривой Монтгомери Curve25519.
   * Обеспечивает высокую скорость и безопасность.
   * Оптимизирован под программную реализацию.

2. **Эффективность**

   * Быстрый обмен ключами даже на слабом железе.
   * Ключи занимают всего 32 байта (256 бит).
   * Поддерживается многими языками и библиотеками (OpenSSL, libsodium и др.).

3. **Безопасность**

   * Защищён от большинства классических атак.
   * Устойчив к атакам по времени выполнения.
   * Не устойчив к квантовым атакам (алгоритм Шора).

4. **Стандартизация**

   * Описан в [RFC 7748](https://datatracker.ietf.org/doc/html/rfc7748).
   * Рекомендован IETF как современный метод обмена ключами.

---

## 🚀 Как использовать?

```python
import ecdh_x25519

# Алиса
alice = ecdh_x25519.EcdhX25519()
alice_pk = alice.generate_keypair()

# Боб
bob = ecdh_x25519.EcdhX25519()
bob_pk = bob.generate_keypair()

# Обмен
shared_secret_alice = alice.generate_shared_secret(bob_pk)
shared_secret_bob = bob.generate_shared_secret(alice_pk)

assert shared_secret_alice == shared_secret_bob
```

---

## 📦 Установка

### 1. Установка через PyPI

```bash
pip install ecdh_x25519
```

### 2. Ручная установка (через git + maturin)

```bash
git clone https://github.com/kostya2023/ecdh_x25519.git
cd ecdh_x25519
pip install -r requirements.txt
maturin build --release
pip install target/wheels/*
```

---

## 👥 Авторы

* [@kostya2023](https://www.github.com/kostya2023)
* [Dalek Cryptography](https://github.com/dalek-cryptography)

---

## 🔒 Лицензия

 - [MIT](LICENSE)
 - [MIT](dalek-cryptography-LICENSE)