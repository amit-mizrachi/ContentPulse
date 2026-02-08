from typing import TypeVar, Generic, Optional, List, Dict, Any, Type

from sqlalchemy.orm import Session

T = TypeVar("T")


class BaseRepository(Generic[T]):
    def __init__(self, session: Session, model: Type[T]):
        self._session = session
        self._model = model

    def create(self, data: Dict[str, Any]) -> T:
        instance = self._model(**data)
        self._session.add(instance)
        self._session.commit()
        self._session.refresh(instance)
        return instance

    def get_by_id(self, id: int) -> Optional[T]:
        return self._session.query(self._model).filter(self._model.id == id).first()

    def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        descending: bool = True
    ) -> List[T]:
        query = self._session.query(self._model)

        if filters:
            for field, value in filters.items():
                if hasattr(self._model, field):
                    query = query.filter(getattr(self._model, field) == value)

        if order_by and hasattr(self._model, order_by):
            column = getattr(self._model, order_by)
            query = query.order_by(column.desc() if descending else column.asc())

        return query.offset(offset).limit(limit).all()

    def update(self, id: int, data: Dict[str, Any]) -> Optional[T]:
        instance = self.get_by_id(id)
        if instance is None:
            return None

        for field, value in data.items():
            if hasattr(instance, field):
                setattr(instance, field, value)

        self._session.commit()
        self._session.refresh(instance)
        return instance

    def delete(self, id: int) -> bool:
        instance = self.get_by_id(id)
        if instance is None:
            return False

        self._session.delete(instance)
        self._session.commit()
        return True
