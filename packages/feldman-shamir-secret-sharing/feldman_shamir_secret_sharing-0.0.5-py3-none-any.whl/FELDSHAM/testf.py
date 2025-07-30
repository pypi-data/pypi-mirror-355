import pytest
from share_generator import ShareGenerator
from share_verifier import ShareVerifier
from secret_reconstructor import SecretReconstructor
from utills import generate_prime, find_generator

# Фикстуры для тестов
@pytest.fixture
def crypto_params():
    p = generate_prime(256)  # Используем 256-битное простое для тестов
    g = find_generator(p)
    return p, g

@pytest.fixture
def setup_components(crypto_params):
    p, g = crypto_params
    generator = ShareGenerator(p, g)
    verifier = ShareVerifier(p, g)
    reconstructor = SecretReconstructor(p)
    return generator, verifier, reconstructor, p, g

# Тесты для генерации простых чисел и генераторов
class TestUtils:
    def test_generate_prime(self):
        p = generate_prime(256)
        assert p > 0
        assert p.bit_length() >= 256

    def test_find_generator(self, crypto_params):
        p, g = crypto_params
        seen = set()
        for i in range(1, p):
            val = pow(g, i, p)
            assert val not in seen
            seen.add(val)
            if len(seen) == p - 1:
                break

    def test_find_generator_with_non_prime(self):
        with pytest.raises(ValueError):
            find_generator(100)  # 100 - не простое число

# Тесты для генератора долей
class TestShareGenerator:
    def test_generate_shares_valid(self, setup_components):
        gen, _, _, p, _ = setup_components
        secret = 12345
        n, t = 5, 3
        
        shares, coeffs = gen.generate_shares(secret, n, t)
        
        assert len(shares) == n
        assert len(coeffs) == t
        assert coeffs[0] == secret

    def test_generate_shares_invalid_secret(self, setup_components):
        gen, _, _, p, _ = setup_components
        with pytest.raises(ValueError):
            gen.generate_shares(p + 1, 5, 3)

    def test_generate_shares_invalid_threshold(self, setup_components):
        gen, _, _, _, _ = setup_components
        with pytest.raises(ValueError):
            gen.generate_shares(12345, 3, 5)

    def test_generate_commitments(self, setup_components):
        gen, _, _, p, g = setup_components
        coeffs = [123, 456, 789]
        commitments = gen.generate_commitments(coeffs)
        
        assert len(commitments) == len(coeffs)
        for comm, coeff in zip(commitments, coeffs):
            assert pow(g, coeff, p) == comm

# Тесты для верификатора долей
class TestShareVerifier:
    def test_verify_valid_share(self, setup_components):
        gen, ver, _, _, _ = setup_components
        shares, coeffs = gen.generate_shares(12345, 5, 3)
        commitments = gen.generate_commitments(coeffs)
        
        for share in shares:
            assert ver.verify_share(share, commitments)

    def test_verify_tampered_share(self, setup_components):
        gen, ver, _, _, _ = setup_components
        shares, coeffs = gen.generate_shares(12345, 5, 3)
        commitments = gen.generate_commitments(coeffs)
        
        tampered_share = (shares[0][0], shares[0][1] + 1)
        assert not ver.verify_share(tampered_share, commitments)

    def test_verify_empty_commitments(self, setup_components):
        _, ver, _, _, _ = setup_components
        with pytest.raises(ValueError):
            ver.verify_share((1, 12345), [])

# Тесты для реконструктора секрета
class TestSecretReconstructor:
    def test_reconstruct_secret(self, setup_components):
        gen, _, recon, _, _ = setup_components
        secret = 123456
        shares, _ = gen.generate_shares(secret, 5, 3)
        
        recovered = recon.reconstruct_secret(shares[:3])
        assert recovered == secret

    def test_reconstruct_insufficient_shares(self, setup_components):
        gen, _, recon, _, _ = setup_components
        shares, _ = gen.generate_shares(12345, 5, 3)
        
        with pytest.raises(Exception):
            recon.reconstruct_secret(shares[:2])

    def test_reconstruct_invalid_shares(self, setup_components):
        _, _, recon, _, _ = setup_components
        invalid_shares = [(1, 100), (2, 200), (3, 999999)]
        with pytest.raises(Exception):
            recon.reconstruct_secret(invalid_shares)

# Интеграционный тест
def test_full_workflow(crypto_params):
    p, g = crypto_params
    
    # 1. Генерация параметров
    secret = 123456789
    generator = ShareGenerator(p, g)
    
    # 2. Создание долей
    shares, coeffs = generator.generate_shares(secret, 5, 3)
    commitments = generator.generate_commitments(coeffs)
    
    # 3. Проверка долей
    verifier = ShareVerifier(p, g)
    for share in shares:
        assert verifier.verify_share(share, commitments)
    
    # 4. Восстановление
    reconstructor = SecretReconstructor(p)
    recovered_secret = reconstructor.reconstruct_secret(shares[:3])
    
    assert recovered_secret == secret