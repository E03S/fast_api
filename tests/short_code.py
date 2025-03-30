import pytest
from app.models import Link
from fastapi import HTTPException
import random
import string

@pytest.fixture
def db_session():
    session = SessionLocal()
    yield session
    session.close()

def test_short_code_generation(db_session: Session):
    # Тест 1: Проверка генерации уникального short_code
    existing_link = Link(short_code='test123', original_url='https://example.com')
    db_session.add(existing_link)
    db_session.commit()

    # Попытка сгенерировать короткий код с уже существующим short_code
    with pytest.raises(HTTPException):
        generate_short_code(db_session)

    # Тест 2: Проверка длины генерируемого short_code
    db_session.delete(existing_link)
    db_session.commit()

    random_code = generate_short_code(db_session)
    assert len(random_code) == 6  # предположим, что длина кода 6 символов

    # Тест 3: Проверка уникальности и корректности символов
    generated_codes = set()
    for _ in range(10):
        code = generate_short_code(db_session)
        generated_codes.add(code)
    
    assert len(generated_codes) == 10  # все сгенерированные коды уникальны
    for code in generated_codes:
        assert len(code) == 6
        # Проверка, что код состоит только из разрешенных символов
        allowed_chars = set(string.ascii_letters + string.digits)
        for char in code:
            assert char in allowed_chars

    # Очистка созданных кодов
    for code in generated_codes:
        link = db_session.query(Link).filter(Link.short_code == code).first()
        if link:
            db_session.delete(link)
    db_session.commit()