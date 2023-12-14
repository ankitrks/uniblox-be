# store/views.py
from django.forms import ValidationError
from django.shortcuts import get_object_or_404
from django.db.models import Count, Sum, F
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, get_user_model

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken


from store.models import Product, Order, OrderItem
from store.serializers import ProductSerializer, OrderSerializer


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=["post"])
    def add_to_cart(self, request, pk=None):
        product_id = request.data.get("product_id")
        quantity = request.data.get("quantity", 1)

        order_id = pk

        if order_id == "null":
            # Create a new order with default values or adjust based on your logic
            order_data = {
                "total_amount": 0,  # Set a default value or calculate based on your needs
                "user": request.user,  # Assuming you have a user associated with the order
                # Add other necessary fields here
            }
            order = Order.objects.create(**order_data)
        else:
            order = get_object_or_404(Order, pk=order_id)

        product = get_object_or_404(Product, pk=product_id)
        order_item, created = OrderItem.objects.get_or_create(
            order=order, product=product
        )
        order_item.quantity += int(quantity)
        order_item.save()
        order.total_amount += product.price * int(quantity)
        order.save()
        serializer = self.get_serializer(order)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def checkout(self, request, pk=None):
        order = self.get_object()
        discount_code = request.data.get("discount_code")
        if discount_code:
            try:
                self.apply_discount(order, discount_code)
            except ValidationError as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        order.is_executed = True
        order.save()
        serializer = self.get_serializer(order)
        return Response(serializer.data)

    def apply_discount(self, order, discount_code):
        if discount_code != order.discount_code:
            raise ValidationError("Invalid discount code")

        order.total_amount *= 0.9
        order.save()

class AdminViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=["post"])
    def generate_discount_code(self, request):
        # Assuming nth is 3, generate discount code for every 3rd order
        order_count = Order.objects.count()

        if order_count % 3 == 0:
            discount_code = f"DISCOUNT_{order_count // 3}"

            latest_order = Order.objects.latest("id")
            latest_order.discount_code = discount_code
            latest_order.save()

            return Response(
                {"discount_code": discount_code}, status=status.HTTP_201_CREATED
            )
        else:
            return Response(
                {"message": "No discount code available for the current order."},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=False, methods=["get"])
    def purchase_details(self, request):
        # Calculate total items purchased
        total_items_purchased = OrderItem.objects.filter(order__is_executed =True).aggregate(
            total_items=Sum("quantity")
        )["total_items"]

        # Calculate total purchase amount for orders with a discount code
        total_purchase_amount_with_discount = Order.objects.filter(
            discount_code__isnull=False,
            is_executed =True
        ).aggregate(total_amount=Sum("total_amount"))["total_amount"] or 0

        # Get a list of discount codes
        discount_codes = Order.objects.exclude(discount_code__isnull=True, is_executed =True).values_list(
            "discount_code", flat=True
        )

        # Calculate total discount amount
        total_discount_amount = Order.objects.filter(
            discount_code__isnull=False,
            is_executed =True
        ).aggregate(
            total_discount_amount=Sum(F("total_amount") * 0.1)
        )["total_discount_amount"] or 0

        response_data = {
            "total_items_purchased": total_items_purchased,
            "total_purchase_amount": total_purchase_amount_with_discount,
            "discount_codes": list(discount_codes),
            "total_discount_amount": total_discount_amount,
        }

        return Response(response_data)


class ObtainTokenView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        username = request.data.get("username")
        password = request.data.get("password")

        if username is None or password is None:
            return Response(
                {"error": "Please provide both username and password"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(username=username, password=password)

        if not user:
            return Response(
                {"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED
            )

        refresh = RefreshToken.for_user(user)
        data = {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }

        return Response(data, status=status.HTTP_200_OK)
