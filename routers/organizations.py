import json
from typing import List, Optional, Literal

from fastapi import APIRouter, Depends, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from database import get_db
from logger.logging_templates import log_info, log_warning, log_error
from models import Organization, Activity, Building
from schemas import OrganizationRequestSchema
from utils.calculating import haversine_distance
from utils.responses import BaseResponse, error_response, success_response

router = APIRouter()


@router.get(
    "/by_building/{building_id}",
    status_code=status.HTTP_200_OK,
    response_model=BaseResponse[List[OrganizationRequestSchema]]
)
async def get_by_building(building_id: int, db: Session = Depends(get_db)):
    """
    Поиск организаций в здании
    """
    log_info(
        action="Запрос организаций расположенных в указанном здании",
        message=f"Запросили организации в здании с id {building_id}"
    )
    try:
        organizations = (
            db.query(Organization)
            .options(
                joinedload(Organization.activities),  # Подгружаем связанные виды деятельности
                joinedload(Organization.building)  # Подгружаем информацию о здании
            )
            .filter(Organization.building_id == building_id)
            .all()
        )
        if not organizations:
            log_warning(
                action="Запрос организаций расположенных в указанном здании",
                message=f"Здания с id {building_id} нет в базе данных"

            )
            error_response(
                message="Здания с данным ID не найдена",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Переделываем ответ в Pydantic
        result = [
            OrganizationRequestSchema(
                id=org.id,
                name=org.name,
                phone_numbers=json.loads(org.phone_numbers),
                activities=[activity.name for activity in org.activities],
                address=org.building.address,
                latitude=org.building.latitude,
                longitude=org.building.longitude

            )
            for org in organizations
        ]

        log_info(
            action="Запрос организаций расположенных в указанном здании",
            message=f"Найдено {len(result)} значений"
        )

        return success_response(
            message="Данные успешно получены",
            data=result
        )
    except SQLAlchemyError as e:
        log_error(
            action="Запрос организаций расположенных в указанном здании",
            message=f"Ошибка SQLAlchemy: {str(e)}"
        )
        db.rollback()
        return error_response(
            message="Ошибка сервера при обработке запроса",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get("/by_activity/{activity_id}", status_code=status.HTTP_200_OK,
            response_model=BaseResponse[List[OrganizationRequestSchema]])
async def get_by_activity(activity_id: int, db: Session = Depends(get_db)):
    """
    Поиск организаций по виду деятельности
    """
    log_info(
        action="Запрос организаций занимающиеся указанным видом деятельности",
        message=f"Запросили организации с видом деятельности с id {activity_id}"
    )
    try:
        activity = db.query(Activity).filter(Activity.id == activity_id).first()
        if not activity:
            log_warning(
                action="Запрос организаций занимающиеся указанным видом деятельности",
                message=f"Деятельности с данным ID {activity_id} не найдена"

            )
            error_response(
                message="Деятельности с данным ID не найдена",
                status_code=status.HTTP_404_NOT_FOUND
            )

        organizations = (
            db.query(Organization)
            .join(Organization.activities)  # Подключаем связь многие-ко-многим
            .join(Organization.building)  # Подключаем здание
            .filter(Organization.activities.any(id=activity_id))  # Фильтруем по указанному activity_id
            .all()
        )

        if not organizations:
            log_warning(
                action="Запрос организаций занимающиеся указанным видом деятельности",
                message=f"Организаций которые занимаются деятельностью с id {activity_id} не найдено"

            )
            error_response(
                message="Организации не найдены",
                status_code=status.HTTP_404_NOT_FOUND
            )

        result = [
            OrganizationRequestSchema(
                id=org.id,
                name=org.name,
                phone_numbers=json.loads(org.phone_numbers),
                activities=[activity.name for activity in org.activities],
                address=org.building.address,
                latitude=org.building.latitude,
                longitude=org.building.longitude

            )
            for org in organizations
        ]

        log_info(
            action="Запрос организаций занимающиеся указанным видом деятельности",
            message=f"Найдено {len(result)} значений"
        )

        return success_response(
            message="Данные успешно получены",
            data=result
        )

    except SQLAlchemyError as e:
        log_error(
            action="Запрос организаций занимающиеся указанным видом деятельности",
            message=f"Ошибка SQLAlchemy: {str(e)}"
        )
        db.rollback()
        return error_response(
            message="Ошибка сервера при обработке запроса",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get("/by_location",
            status_code=status.HTTP_200_OK,
            response_model=BaseResponse[List[OrganizationRequestSchema]])
async def get_by_location(
        search_type: Literal["radius", "rectangle"],
        lat: float,
        lon: float,
        radius_km: Optional[float] = None,
        min_lat: Optional[float] = None,
        max_lat: Optional[float] = None,
        min_lon: Optional[float] = None,
        max_lon: Optional[float] = None,
        db: Session = Depends(get_db)
):
    """
    Поиск организаций по радиусу или прямоугольной области.
    """

    log_info(
        action="Запрос организаций по локации",
        message=f"Поиск организаций по {search_type}"
    )

    if search_type == "radius":
        if radius_km is None:
            return error_response(
                message="Для поиска по радиусу необходимо указать radius_km",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        if any([min_lat, max_lat, min_lon, max_lon]):
            return error_response(
                message="Для поиска по радиусу нельзя указывать min_lat, max_lat, min_lon, "
                        "max_lon",
                status_code=status.HTTP_400_BAD_REQUEST
            )

    elif search_type == "rectangle":
        if None in [min_lat, max_lat, min_lon, max_lon]:
            return error_response(
                message="Для поиска по прямоугольнику необходимо указать min_lat, max_lat, min_lon, "
                        "max_lon",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        if radius_km is not None:
            return error_response(
                message="Для поиска по прямоугольнику нельзя указывать radius_km",
                status_code=status.HTTP_400_BAD_REQUEST
            )

    try:
        buildings_query = db.query(Building)

        if search_type == "radius":
            # Загружаем все здания и фильтруем по расстоянию
            buildings = buildings_query.all()
            buildings_in_radius = [
                b for b in buildings if haversine_distance(
                    lat, lon,
                    b.latitude, b.longitude
                ) <= radius_km
            ]
            building_ids = [b.id for b in buildings_in_radius]

        elif search_type == "rectangle":
            # Фильтруем здания по границам прямоугольника
            buildings_in_rectangle = buildings_query.filter(
                Building.latitude.between(min_lat, max_lat),
                Building.longitude.between(min_lon, max_lon)
            ).all()
            building_ids = [b.id for b in buildings_in_rectangle]

        else:
            log_warning(
                action="Запрос организаций по локации",
                message="Передан некорректный параметр search_type"
            )
            return error_response(
                message="Неверный тип поиска",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        if not building_ids:
            log_warning(
                action="Запрос организаций по локации",
                message="Нет зданий в указанной области"
            )
            return error_response(
                message="Организации не найдены в данной области",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Получаем организации в найденных зданиях
        organizations = (
            db.query(Organization)
            .options(joinedload(Organization.building))
            .filter(Organization.building_id.in_(building_ids))
            .all()
        )

        if not organizations:
            log_warning(
                action="Запрос организаций по локации",
                message="Нет организаций в найденных зданиях"
            )
            return error_response(
                message="Организации не найдены",
                status_code=status.HTTP_404_NOT_FOUND
            )

        result = [
            OrganizationRequestSchema(
                id=org.id,
                name=org.name,
                phone_numbers=json.loads(org.phone_numbers),
                activities=[activity.name for activity in org.activities],
                address=org.building.address,
                latitude=org.building.latitude,
                longitude=org.building.longitude
            )
            for org in organizations
        ]

        log_info(
            action="Запрос организаций по локации",
            message=f"Найдено {len(result)} значений"
        )
        return success_response(
            message="Данные успешно получены",
            data=result
        )

    except SQLAlchemyError as e:
        db.rollback()
        log_error(
            action="Запрос организаций по локации",
            message=f"Ошибка SQLAlchemy: {str(e)}"
        )
        return error_response(
            message="Ошибка сервера при обработке запроса",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get("/by_id/{organization_id}",
            status_code=status.HTTP_200_OK,
            response_model=BaseResponse[OrganizationRequestSchema]
            )
async def get_by_id(organization_id: int, db: Session = Depends(get_db)):
    """
    Поиск организаций по её идентификатору
    """

    log_info(
        action='Поиск организации по ее ID',
        message=f"organization_id: {organization_id}"
    )

    try:
        organization = (
            db.query(Organization)
            .options(joinedload(Organization.activities), joinedload(Organization.building))
            .filter(Organization.id == organization_id)
            .first()
        )

        if not organization:
            log_warning(
                action="Поиск организации по ее ID",
                message=f"Организации с данным ID {organization_id} нет"
            )
            return error_response(
                message="Организация не найдена",
                status_code=status.HTTP_404_NOT_FOUND
            )

        result = OrganizationRequestSchema(
            id=organization.id,
            name=organization.name,
            phone_numbers=json.loads(organization.phone_numbers),
            activities=[activity.name for activity in organization.activities],
            address=organization.building.address,
            latitude=organization.building.latitude,
            longitude=organization.building.longitude
        )

        log_info(
            action='Поиск организации по ее ID',
            message="Успешный запрос"
        )

        return success_response(
            message="Данные успешно получены",
            data=result
        )

    except SQLAlchemyError as e:
        db.rollback()
        log_error(
            action="Поиск организации по ее ID",
            message=f"Ошибка SQLAlchemy: {str(e)}"
        )
        return error_response(
            message="Ошибка сервера при обработке запроса",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get(
    "/by_activity_hierarchy/{activity_id}",
    status_code=status.HTTP_200_OK,
    response_model=BaseResponse[List[OrganizationRequestSchema]]
)
async def get_by_activity_hierarchy(activity_id: int, db: Session = Depends(get_db)):
    """
    Поиск организаций по виду деятельности, включая вложенность до 3 уровней.
    """

    log_info(
        action="Поиск организаций по иерархии видов деятельности",
        message=f"activity_id: {activity_id}"
    )

    try:
        # Проверяем, существует ли указанный вид деятельности
        root_activity = db.query(Activity).filter(Activity.id == activity_id).first()
        if not root_activity:
            return error_response(
                message=f"Вид деятельности с ID {activity_id} не найден",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Рекурсивно ищем всех потомков до 3 уровня
        def get_child_activities(parent_ids, depth=0):
            if depth >= 3:  # Ограничение глубины поиска
                return set()
            child_activities = db.query(Activity.id).filter(Activity.parent_id.in_(parent_ids)).all()
            child_ids = {a[0] for a in child_activities}
            if child_ids:
                return child_ids | get_child_activities(child_ids, depth + 1)
            return child_ids

        activity_ids = {activity_id} | get_child_activities({activity_id})

        organizations = (
            db.query(Organization)
            .join(Organization.activities)
            .outerjoin(Organization.building)
            .options(
                joinedload(Organization.activities),  # Чтобы не было доп. SQL-запросов
                joinedload(Organization.building)  # Загружаем информацию о здании
            )
            .filter(Organization.activities.any(Activity.id.in_(activity_ids)))  # Фильтр по списку ID
            .all()
        )

        if not organizations:
            return error_response(
                message="Организации не найдены",
                status_code=status.HTTP_404_NOT_FOUND
            )

        result = [
            OrganizationRequestSchema(
                id=org.id,
                name=org.name,
                phone_numbers=json.loads(org.phone_numbers),
                activities=[activity.name for activity in org.activities],
                address=org.building.address,
                latitude=org.building.latitude,
                longitude=org.building.longitude
            )
            for org in organizations
        ]

        log_info(
            action="Поиск организаций по иерархии видов деятельности",
            message=f"Найдено {len(result)} значений"
        )

        return success_response(
            message="Данные успешно получены",
            data=result
        )

    except SQLAlchemyError as e:
        db.rollback()
        log_error(
            action="Поиск организаций по иерархии видов деятельности",
            message=f"Ошибка SQLAlchemy: {str(e)}"
        )
        return error_response(
            message="Ошибка сервера при обработке запроса",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get(
    "/by_name",
    status_code=status.HTTP_200_OK,
    response_model=BaseResponse[List[OrganizationRequestSchema]]
)
async def get_by_name(
        name: str,
        db: Session = Depends(get_db)
):
    """
    Поиск организаций по названию (частичное совпадение).
    """

    log_info(
        action="Поиск организаций по названию",
        message=f"Ищем организации, содержащие: {name}"
    )

    try:
        organizations = (
            db.query(Organization)
            .options(joinedload(Organization.building))
            .filter(Organization.name.ilike(f"%{name}%"))  #  регистронезависимо
            .all()
        )

        if not organizations:
            log_warning(
                action="Поиск организаций по названию",
                message=f"Организации с именем, содержащим '{name}', не найдены"
            )
            return error_response(
                message="Организации не найдены",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # 🔹 Формируем ответ
        result = [
            OrganizationRequestSchema(
                id=org.id,
                name=org.name,
                phone_numbers=json.loads(org.phone_numbers),
                activities=[activity.name for activity in org.activities],
                address=org.building.address,
                latitude=org.building.latitude,
                longitude=org.building.longitude
            )
            for org in organizations
        ]

        log_info(
            action="Поиск организаций по названию",
            message=f"Найдено {len(result)} значений"
        )

        return success_response(
            message="Данные успешно получены",
            data=result
        )

    except SQLAlchemyError as e:
        db.rollback()
        log_error(
            action="Поиск организаций по названию",
            message=f"Ошибка SQLAlchemy: {str(e)}"
        )
        return error_response(
            message="Ошибка сервера при обработке запроса",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
