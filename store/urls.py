from django.urls import path, include
from rest_framework.routers import DefaultRouter
from store.views import ProductViewSet, OrderViewSet, AdminViewSet, ObtainTokenView

router = DefaultRouter()
router.register(r'products', ProductViewSet)
router.register(r'orders', OrderViewSet)
router.register(r'admin', AdminViewSet, basename='admin')

urlpatterns = [
    path('', include(router.urls)),
    path('token/', ObtainTokenView.as_view(), name='token_obtain'),
]
