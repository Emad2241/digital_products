from django.shortcuts import render
from rest_framework import serializers
from rest_framework.response import Response
from django.utils import timezone
from .serializers import GatewaySerializer
from rest_framework.views import APIView
from subscriptions.models import Package,Subscription
from rest_framework.permissions import IsAuthenticated
from .models import Gateway, Payment
import uuid

from rest_framework import status


class GatewayView(APIView):
    def get(self, request):
        gateways = Gateway.objects.filter(is_enable=True)
        serializer = GatewaySerializer(gateways, many=True)
        return Response(serializer.data)


class PackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Package
        fields = ('title', 'sku', 'description', 'avatar', 'price', 'duration')


class SubscriptionSerializer(serializers.ModelSerializer):
    package = PackageSerializer()

    class Meta:
        model = Subscription
        fields = ('package', 'created_time', 'expire_time')

class PaymentView(APIView):
    permission_class = [IsAuthenticated]

    def get(self,request):
        gateway_id = request.query_params.get('gateway')
        package_id = request.query_params.get('package')

        try:
            package = Package.objects.get(pk=package_id, is_enable=True)
            gateway = Gateway.objects.get(pk=gateway_id, is_enbale=True)
        except (Package.DoesNotExist, Gateway.DoesNotExist):
            return Response(status=status.HTTP_400_BAD_REQUEST)

        payment = Payment.objects.create(
            user=request.user,
            package=package,
            gateway=gateway,
            price=package.price,
            phone_number=request.user.phone_number,
            token=str(uuid.uuid4())

        )

        return Response({'token':payment.token, 'callback_url': 'https://my-site.com/payments/pay/'})

    def post(self,request):
        token = request.data.get('token')
        st = request.data.get('status')

        try:
            payment = Payment.objects.get(token=token)
        except Payment.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        if st !=10:
            payment.status = Payment.STATUS_CANCELED
            payment.save()
            # render(request, 'payment-result.html', context={'status':Payment})
            return Response({'detail': 'Payment verification failed.'},
                            status=status.HTTP_400_BAD_REQUEST)

        r = request.post('bank_verify_url', data={})
        if r.status_code // 100 !=2:
            payment.status = Payment.STATUS_ERROR
            payment.save()
            # render(request, 'payment-result.html', context={'status':Payment})
            return Response({'detail': 'Payment verification failed.'},
                            status=status.HTTP_400_BAD_REQUEST)

        payment.status = Payment.STATUS_PAID
        payment.save()

        Subscription.objects.create(
            user=payment.user,
            package=payment.package,
            expire_time=timezone.now() + timezone.timedelta(days=payment.package.duration.days)
        )
        return Response({'detail': 'Payment is successfull'})