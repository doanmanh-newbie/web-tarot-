from app.shared.domain.exceptions import DomainError


class CardNotFound(DomainError): ...


class InvalidCardMeaning(DomainError):
    """Ý nghĩa lá bài rỗng hoặc quá dài."""
