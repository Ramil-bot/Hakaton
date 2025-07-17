from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

video_schema = {
    'list': extend_schema(
        description='Получить список видео с пагинацией',
        parameters=[
            OpenApiParameter('owner', OpenApiTypes.INT, description='Фильтр по владельцу'),
            OpenApiParameter('page_size', OpenApiTypes.INT, description='Количество элементов на странице')
        ]
    ),
    'create': extend_schema(description='Загрузить новое видео'),
    'like': extend_schema(description='Поставить лайк видео')
}